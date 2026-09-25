"""
Architecture guard (arch-audit 2026-09).

Enforces the layering rules the audit established and ratchets the remaining
debt so it can only go down:

* no upward imports (data -> service/api, service -> api)
* no import cycles between modules
* no imports of another package's internal submodules
* environment variables are read only in app/config.py
* repositories never import FastAPI
* app/api/ runs no MongoDB operation itself (AST check: no pymongo import,
  no collection handles derived from a database object, no pymongo calls on
  *_col/*_collection handles, no cursor chains on repository results). A
  database handle may only be passed into a lower layer; the number of API
  modules doing that is ratcheted.
* frontend files importing axios directly may not grow (ratchet).

Pure static analysis — no DB, no network.
"""
import ast
import os
import re
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
FRONTEND_SRC = BACKEND.parent / 'frontend' / 'src'

# Ratchets — only ever lower these.
API_DB_CALL_SITES_MAX = 0
API_DB_HANDLE_MODULES_MAX = 12      # api modules wiring get_database() into services
FRONTEND_AXIOS_IMPORT_FILES_MAX = 0
FRONTEND_RAW_FETCH_SITES_MAX = 52   # legacy fetch() calls bypassing services/http.ts

PYMONGO_OPS = {
    'find', 'find_one', 'find_one_and_update', 'find_one_and_delete', 'find_one_and_replace',
    'insert_one', 'insert_many', 'update_one', 'update_many', 'delete_one', 'delete_many',
    'replace_one', 'bulk_write', 'aggregate', 'count_documents', 'estimated_document_count',
    'distinct', 'create_index', 'create_indexes', 'drop_index', 'drop', 'command',
    'list_collection_names', 'watch',
}
CURSOR_OPS = {'sort', 'skip', 'limit', 'batch_size', 'hint'}
HANDLE_SUFFIXES = ('_col', '_collection', 'collection')


def _python_files():
    for base in [BACKEND / 'app']:
        for p in base.rglob('*.py'):
            if '__pycache__' not in p.parts:
                yield p
    for p in BACKEND.glob('*.py'):
        yield p


def _modname(path: Path) -> str:
    rel = path.relative_to(BACKEND).with_suffix('')
    parts = list(rel.parts)
    if parts[-1] == '__init__':
        parts = parts[:-1]
    return '.'.join(parts)


MODULES = {_modname(p): p for p in _python_files()}


def _layer(mod: str) -> str:
    p = mod.split('.')
    if p[0] != 'app' or len(p) < 2:
        return 'other'
    return {'api': 'api', 'services': 'service', 'collectors': 'service',
            'repositories': 'data', 'database': 'data'}.get(p[1], 'other')


RANK = {'api': 3, 'service': 2, 'data': 1}


def _resolve(cur: str, is_pkg: bool, node: ast.ImportFrom):
    if node.level == 0:
        return node.module
    base = cur.split('.') if is_pkg else cur.split('.')[:-1]
    if node.level > 1:
        base = base[:-(node.level - 1)]
    return '.'.join(base + ([node.module] if node.module else []))


def _known(target: str):
    while target and target not in MODULES:
        if '.' not in target:
            return None
        target = target.rsplit('.', 1)[0]
    return target


def _edges():
    edges = []
    for mod, path in MODULES.items():
        tree = ast.parse(path.read_text(encoding='utf-8', errors='ignore'))
        is_pkg = path.name == '__init__.py'
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                tgt = _resolve(mod, is_pkg, node)
                if not tgt or not (tgt.startswith('app') or tgt in MODULES):
                    continue
                for alias in node.names:
                    cand = f'{tgt}.{alias.name}'
                    k = _known(cand if cand in MODULES else tgt)
                    if k and k != mod:
                        edges.append((mod, k, node.lineno))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('app'):
                        k = _known(alias.name)
                        if k and k != mod:
                            edges.append((mod, k, node.lineno))
    return edges


EDGES = _edges()


def test_no_upward_imports():
    bad = [f'{MODULES[a].relative_to(BACKEND)}:{ln} -> {b}'
           for a, b, ln in EDGES
           if _layer(a) in RANK and _layer(b) in RANK and RANK[_layer(a)] < RANK[_layer(b)]]
    assert not bad, 'lower layer imports higher layer:\n' + '\n'.join(bad)


def test_no_import_cycles():
    graph = defaultdict(set)
    for a, b, _ in EDGES:
        graph[a].add(b)
    index, low, stack, on, sccs, counter = {}, {}, [], set(), [], [0]

    def strong(v):
        index[v] = low[v] = counter[0]; counter[0] += 1
        stack.append(v); on.add(v)
        for w in graph[v]:
            if w not in index:
                strong(w); low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop(); on.discard(w); comp.append(w)
                if w == v:
                    break
            # a package importing its own submodules (via __init__) is not a cycle
            if len(comp) > 1 and not all(c.startswith(min(comp, key=len)) for c in comp):
                sccs.append(sorted(comp))

    import sys
    sys.setrecursionlimit(10000)
    for v in list(graph):
        if v not in index:
            strong(v)
    assert not sccs, f'import cycles: {sccs}'


def test_no_reaching_into_package_internals():
    packages = {m for m, p in MODULES.items() if p.name == '__init__.py' and m.count('.') >= 2}
    bad = []
    for a, b, ln in EDGES:
        for pkg in packages:
            if b.startswith(pkg + '.') and not (a == pkg or a.startswith(pkg + '.')):
                bad.append(f'{MODULES[a].relative_to(BACKEND)}:{ln} -> {b} (use {pkg})')
    assert not bad, 'imports bypass a package interface:\n' + '\n'.join(bad)


def test_env_reads_only_in_config():
    bad = []
    for mod, path in MODULES.items():
        if mod == 'app.config':
            continue
        tree = ast.parse(path.read_text(encoding='utf-8', errors='ignore'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                f = node.func
                name = ''
                if isinstance(f.value, ast.Name):
                    name = f'{f.value.id}.{f.attr}'
                elif isinstance(f.value, ast.Attribute) and isinstance(f.value.value, ast.Name):
                    name = f'{f.value.value.id}.{f.value.attr}.{f.attr}'
                if name in ('os.getenv', 'os.environ.get'):
                    bad.append(f'{path.relative_to(BACKEND)}:{node.lineno}')
            # os.environ['X'] reads (assignments are process setup and allowed)
            if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load) \
               and isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name) \
               and node.value.value.id == 'os' and node.value.attr == 'environ':
                bad.append(f'{path.relative_to(BACKEND)}:{node.lineno}')
    assert not bad, 'read env via app.config.settings instead:\n' + '\n'.join(bad)


def test_repositories_do_not_import_fastapi():
    bad = []
    for mod, path in MODULES.items():
        if not mod.startswith('app.repositories'):
            continue
        src = path.read_text()
        if re.search(r'^\s*(from|import) (fastapi|starlette)', src, re.M):
            bad.append(str(path.relative_to(BACKEND)))
    assert not bad, f'repositories must raise app.repositories.errors, not HTTP types: {bad}'


def _db_handle_names(tree) -> set:
    """Names bound to a pymongo Database: `x = get_database()` or `x=Depends(get_database)`."""
    names = {'db'}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and 'get_database' in ast.unparse(n.value):
            names |= {t.id for t in n.targets if isinstance(t, ast.Name)}
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = n.args.args + n.args.kwonlyargs
            defaults = [None] * (len(n.args.args) - len(n.args.defaults)) + n.args.defaults + n.args.kw_defaults
            for arg, default in zip(args, defaults):
                if default is not None and 'get_database' in ast.unparse(default):
                    names.add(arg.arg)
    return names


def _api_db_call_sites(tree) -> list:
    handles = _db_handle_names(tree)
    hits = []
    for n in ast.walk(tree):
        # collection handle derived from a database object: db.papers, db['papers'], db.command
        if isinstance(n, (ast.Attribute, ast.Subscript)) and isinstance(n.value, ast.Name) \
                and n.value.id in handles:
            hits.append((n.lineno, ast.unparse(n)))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            recv = n.func.value
            root = recv
            while isinstance(root, (ast.Attribute, ast.Subscript, ast.Call)):
                root = root.func if isinstance(root, ast.Call) else root.value
            # pymongo operation on a *_col / *_collection handle
            if n.func.attr in PYMONGO_OPS and isinstance(root, ast.Name) \
                    and root.id.endswith(HANDLE_SUFFIXES):
                hits.append((n.lineno, ast.unparse(n.func)))
            # cursor shaping on a repository result: queries.x(...).sort(...)
            if n.func.attr in CURSOR_OPS and isinstance(root, ast.Name) and root.id == 'queries' \
                    and isinstance(recv, ast.Call):
                hits.append((n.lineno, ast.unparse(n.func)))
    return hits


def test_api_db_call_sites_ratchet():
    count, sites = 0, []
    for mod, path in MODULES.items():
        if mod.startswith('app.api'):
            hits = _api_db_call_sites(ast.parse(path.read_text()))
            count += len(hits)
            sites += [f'{path.relative_to(BACKEND)}:{line} {txt}' for line, txt in hits]
    assert count <= API_DB_CALL_SITES_MAX, (
        f'{count} MongoDB call sites in app/api (max {API_DB_CALL_SITES_MAX}): '
        f'put new queries in app/repositories/\n' + '\n'.join(sites[:20]))
    if count < API_DB_CALL_SITES_MAX:
        print(f'NOTE: api db call sites down to {count} — lower API_DB_CALL_SITES_MAX')


def test_api_does_not_import_pymongo():
    bad = [str(p.relative_to(BACKEND)) for m, p in MODULES.items()
           if m.startswith('app.api') and re.search(r'^\s*(from|import) (pymongo|bson\.son)\b', p.read_text(), re.M)]
    assert not bad, f'app/api must not use pymongo (queries belong in app/repositories): {bad}'


def test_api_db_handle_modules_ratchet():
    mods = sorted(str(p.relative_to(BACKEND)) for m, p in MODULES.items()
                  if m.startswith('app.api') and re.search(
                      r'^from app\.database\.mongodb import [^\n]*\b(get_database|get_client)\b',
                      p.read_text(), re.M))
    assert len(mods) <= API_DB_HANDLE_MODULES_MAX, (
        f'{len(mods)} api modules take a database handle (max {API_DB_HANDLE_MODULES_MAX}): {mods}')


def test_frontend_axios_ratchet():
    if not FRONTEND_SRC.exists():
        return
    n = 0
    for p in list(FRONTEND_SRC.rglob('*.ts')) + list(FRONTEND_SRC.rglob('*.tsx')):
        if 'services' in p.relative_to(FRONTEND_SRC).parts:
            continue
        if re.search(r"from ['\"]axios['\"]", p.read_text(encoding='utf-8', errors='ignore')):
            n += 1
    assert n <= FRONTEND_AXIOS_IMPORT_FILES_MAX, (
        f'{n} frontend files import axios directly (max {FRONTEND_AXIOS_IMPORT_FILES_MAX}): '
        f'use an API client in src/services/')


def test_no_flat_components():
    """components/ holds feature folders only (+ ui/); no new top-level files."""
    comp = FRONTEND_SRC / 'components'
    if not comp.exists():
        return
    flat = [p.name for p in comp.iterdir() if p.is_file() and p.suffix in ('.ts', '.tsx')]
    assert not flat, f'put components into a feature folder, not components/ root: {flat}'


def test_frontend_raw_fetch_ratchet():
    """fetch() to the backend bypasses services/http.ts (base URL, error
    normalization). Existing sites are ratcheted; migrate them to http.*."""
    if not FRONTEND_SRC.exists():
        return
    pat = re.compile(r"""fetch\(\s*[`'"](/api|\$\{API_BASE)""")
    n = sum(len(pat.findall(p.read_text(encoding='utf-8', errors='ignore')))
            for p in list(FRONTEND_SRC.rglob('*.ts')) + list(FRONTEND_SRC.rglob('*.tsx'))
            if 'services' not in p.relative_to(FRONTEND_SRC).parts)
    assert n <= FRONTEND_RAW_FETCH_SITES_MAX, (
        f'{n} raw fetch() calls to the backend (max {FRONTEND_RAW_FETCH_SITES_MAX}): use services/http.ts')
