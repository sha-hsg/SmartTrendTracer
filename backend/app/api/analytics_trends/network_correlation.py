"""
Network graph and correlation endpoints for analytics trends.
Split from visualizations.py.
"""

from fastapi import APIRouter, Query
from collections import defaultdict
from bson import ObjectId

from app.database.mongodb import concept_id_query_variants

from .utils import (
    db,
    get_date_range,
)
from app.repositories import analytics_trends_network_correlation_queries as queries

router = APIRouter()


@router.get("/network")
def get_concept_network(
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    min_connections: int = Query(2, ge=1, le=10, description="Minimum connections to include"),
    top_n: int = Query(40, ge=10, le=100, description="Number of top concepts")
):
    """
    Get network graph data for concept relationships based on co-occurrence.
    """
    from app.services.anomaly_detection import get_concept_cooccurrence

    start_date, end_date = get_date_range(days)

    # Get co-occurrence data
    cooc_data = get_concept_cooccurrence(db, days=days, min_cooccurrence=min_connections, top_n=top_n)

    # Entity type colors
    colors = {
        'person': '#3B82F6',
        'organisation': '#10B981',
        'location': '#F59E0B',
        'concept': '#8B5CF6',
        'product': '#EC4899',
        'event': '#14B8A6',
        'technology': '#F97316',
        'default': '#6366F1'
    }

    # Build nodes
    nodes = []
    node_connections = defaultdict(int)

    for pair in cooc_data['pairs']:
        node_connections[pair['concept_a_id']] += 1
        node_connections[pair['concept_b_id']] += 1

    for i, concept_id in enumerate(cooc_data['concept_ids']):
        concept = queries.tag_concepts_v2_find_one__get_concept_network(concept_id)
        if concept:
            entity_type = concept.get('entity_type', 'concept')
            activity = node_connections.get(concept_id, 0)

            nodes.append({
                'id': concept_id,
                'name': concept.get('display_name', 'Unknown'),
                'val': max(1, activity),
                'color': colors.get(entity_type, colors['default']),
                'entity_type': entity_type,
                'activity': activity
            })

    # Build links
    links = []
    for pair in cooc_data['pairs']:
        links.append({
            'source': pair['concept_a_id'],
            'target': pair['concept_b_id'],
            'value': pair['count'],
            'strength': pair['strength']
        })

    # Cluster detection: real connected components over the links (union-find)
    clusters = []
    if nodes:
        parent = {node['id']: node['id'] for node in nodes}

        def find(x):
            # Iterative find with path compression
            root = x
            while parent[root] != root:
                root = parent[root]
            while parent[x] != root:
                parent[x], x = root, parent[x]
            return root

        def union(a, b):
            root_a, root_b = find(a), find(b)
            if root_a != root_b:
                parent[root_b] = root_a

        for link in links:
            if link['source'] in parent and link['target'] in parent:
                union(link['source'], link['target'])

        components = defaultdict(list)
        for node in nodes:
            components[find(node['id'])].append(node)

        cluster_colors = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899']

        # Largest components first; each cluster is named after its most active node
        sorted_components = sorted(
            components.values(),
            key=lambda comp: (len(comp), max(n['activity'] for n in comp)),
            reverse=True
        )
        for i, component in enumerate(sorted_components):
            representative = max(component, key=lambda n: n['activity'])
            clusters.append({
                'id': i,
                'name': representative['name'],
                'nodes': [n['id'] for n in component],
                'color': cluster_colors[i % len(cluster_colors)]
            })

    # Statistics
    total_connections = sum(node_connections.values())
    isolated = len([n for n in nodes if node_connections.get(n['id'], 0) == 0])

    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "nodes": nodes,
        "links": links,
        "clusters": clusters,
        "statistics": {
            "total_nodes": len(nodes),
            "total_edges": len(links),
            "avg_connections": round(total_connections / len(nodes), 1) if nodes else 0,
            "density": round(len(links) / (len(nodes) * (len(nodes) - 1) / 2), 3) if len(nodes) > 1 else 0,
            "isolated_nodes": isolated
        }
    }
