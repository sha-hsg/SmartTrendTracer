import re
import json
import logging
from typing import Dict, List, Set, Optional, Any
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────
# Data classes and enums (shared by both strategies)
# ──────────────────────────────────────────────────

class AliasType(Enum):
    SYNONYM = "synonym"
    VARIANT = "variant"
    MISSPELLING = "misspelling"
    ABBREVIATION = "abbreviation"
    PLURAL = "plural"
    DEPRECATED = "deprecated"
    LEGACY = "legacy"

class ConceptStatus(Enum):
    ACTIVE = "active"
    SUGGESTED = "suggested"
    DEPRECATED = "deprecated"
    MERGED = "merged"

@dataclass
class Concept:
    id: str
    slug: str
    display_name: str
    description: str = ""
    parents: List[str] = field(default_factory=list)
    children: Set[str] = field(default_factory=set)
    status: ConceptStatus = ConceptStatus.ACTIVE
    usage_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Alias:
    alias_text: str
    canonical_slug: str
    alias_type: AliasType
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Relation:
    source: str
    target: str
    relation_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────
# Shared utilities (slug/display name canonicalization)
# ──────────────────────────────────────────────────

# Known acronym mappings for display name generation
_SPECIAL_CASES = {
    "gpt": "GPT", "llm": "LLM", "llms": "LLMs", "nlp": "NLP",
    "ml": "ML", "ai": "AI", "rl": "RL", "rlhf": "RLHF",
    "bert": "BERT", "lstm": "LSTM", "gan": "GAN", "gans": "GANs",
    "vae": "VAE", "api": "API", "apis": "APIs", "gpu": "GPU",
    "gpus": "GPUs", "cpu": "CPU", "tpu": "TPU", "rnn": "RNN",
    "cnn": "CNN", "sota": "SOTA", "agi": "AGI", "cv": "CV",
    "ocr": "OCR", "asr": "ASR", "tts": "TTS", "rag": "RAG",
    "dpo": "DPO", "ppo": "PPO", "sft": "SFT", "kl": "KL", "moe": "MoE",
}

def canonicalize_slug(tag: str) -> str:
    if not tag:
        return ""
    tag = str(tag).strip()
    tag = re.sub(r'[\s\-\.]+', '_', tag)
    tag = re.sub(r'[^a-zA-Z0-9_]', '', tag)
    tag = tag.lower()
    tag = re.sub(r'_+', '_', tag)
    return tag.strip('_')

def generate_display_name(slug: str) -> str:
    parts = slug.split('_')
    display_parts = []
    for part in parts:
        if part.isdigit():
            display_parts.append(part)
        elif part.lower() in _SPECIAL_CASES:
            display_parts.append(_SPECIAL_CASES[part.lower()])
        elif part.isupper() and len(part) > 1:
            display_parts.append(part)
        else:
            display_parts.append(part.capitalize())
    if len(display_parts) == 2 and display_parts[1].isdigit():
        return f"{display_parts[0]}-{display_parts[1]}"
    return " ".join(display_parts)


# ──────────────────────────────────────────────────
# Root categories (shared taxonomy)
# ──────────────────────────────────────────────────

ROOT_CATEGORIES = {
    "ai_ml_fundamentals": {"display_name": "AI/ML Fundamentals", "description": "Core concepts, theories, and foundations of artificial intelligence and machine learning"},
    "models_architectures": {"display_name": "Models & Architectures", "description": "Specific models, neural network architectures, and model families"},
    "techniques_methods": {"display_name": "Techniques & Methods", "description": "Algorithms, training techniques, optimization methods, and approaches"},
    "applications_domains": {"display_name": "Applications & Domains", "description": "Real-world applications and specific domain implementations"},
    "data_datasets": {"display_name": "Data & Datasets", "description": "Datasets, data processing, and data-related topics"},
    "evaluation_metrics": {"display_name": "Evaluation & Metrics", "description": "Performance metrics, benchmarks, and evaluation methods"},
    "tools_infrastructure": {"display_name": "Tools & Infrastructure", "description": "Software tools, frameworks, platforms, and infrastructure"},
    "research_development": {"display_name": "Research & Development", "description": "Research topics, papers, conferences, and development practices"},
    "industry_business": {"display_name": "Industry & Business", "description": "Companies, products, business applications, and industry trends"},
    "ethics_society": {"display_name": "Ethics & Society", "description": "AI ethics, safety, societal impact, and governance"},
}


# ──────────────────────────────────────────────────
# Category keywords for rule-based classification
# ──────────────────────────────────────────────────

CATEGORY_KEYWORDS = {
    "ai_ml_fundamentals": ["machine learning","deep learning","artificial intelligence","neural network","supervised","unsupervised","reinforcement learning","classification","regression","clustering","theory","fundamental","concept","principle","foundation","basic","introduction"],
    "models_architectures": ["model","architecture","network","transformer","bert","gpt","resnet","vgg","inception","mobilenet","efficientnet","vit","lstm","gru","rnn","cnn","gan","vae","autoencoder","diffusion","llm","language model","vision model"],
    "techniques_methods": ["technique","method","algorithm","optimization","training","fine-tuning","distillation","pruning","quantization","attention","dropout","batch norm","layer norm","regularization","gradient","backprop","learning rate","scheduler","augmentation"],
    "applications_domains": ["application","use case","nlp","computer vision","robotics","healthcare","finance","education","gaming","art","music","translation","summarization","generation","detection","recognition","segmentation","tracking","prediction","forecasting","recommendation"],
    "data_datasets": ["data","dataset","corpus","benchmark","imagenet","coco","mnist","cifar","wikitext","squad","glue","superglue","common crawl","wikipedia","preprocessing","cleaning","annotation","labeling","synthetic","augmentation","collection"],
    "evaluation_metrics": ["metric","evaluation","accuracy","precision","recall","f1","bleu","rouge","perplexity","loss","error","score","benchmark","leaderboard","performance","sota","baseline","ablation","comparison","analysis","measurement"],
    "tools_infrastructure": ["tool","framework","library","platform","infrastructure","pytorch","tensorflow","jax","keras","scikit","numpy","pandas","huggingface","wandb","mlflow","docker","kubernetes","gpu","tpu","cuda","cloud","aws","gcp","azure","api"],
    "research_development": ["research","paper","study","conference","journal","arxiv","neurips","icml","iclr","cvpr","acl","emnlp","aaai","publication","preprint","review","survey","tutorial","experiment","hypothesis","methodology","contribution"],
    "industry_business": ["company","startup","product","service","business","market","openai","anthropic","google","microsoft","meta","amazon","commercial","enterprise","saas","platform","monetization","pricing","customer","user","adoption","deployment"],
    "ethics_society": ["ethics","bias","fairness","safety","alignment","privacy","security","transparency","explainability","interpretability","accountability","governance","regulation","policy","impact","society","risk","harm","benefit","trust","responsible"],
}


# ──────────────────────────────────────────────────
# Detection helpers (misspelling, abbreviation, plural)
# ──────────────────────────────────────────────────

def is_misspelling(s1: str, s2: str) -> bool:
    if abs(len(s1) - len(s2)) > 2:
        return False
    pairs = [('reccomend','recommend'),('occured','occurred'),('seperate','separate'),('definately','definitely'),('recieve','receive'),('beleive','believe'),('wierd','weird'),('calender','calendar'),('grammer','grammar'),('harrass','harass'),('untill','until'),('wich','which'),('occassion','occasion'),('aquire','acquire'),('arguement','argument'),('existance','existence'),('experiance','experience'),('relavant','relevant'),('persistant','persistent'),('rythm','rhythm')]
    return any((w in s1 and r in s2) or (w in s2 and r in s1) for w, r in pairs)

def is_abbreviation(short: str, long: str) -> bool:
    short_u, long_u = short.upper(), long.upper()
    if len(short_u) <= 4 and len(long_u) > len(short_u):
        words = re.split(r'[\s\-_]+', long_u)
        if len(words) == len(short_u):
            if ''.join(w[0] for w in words if w) == short_u:
                return True
    known = {'ML':'MACHINE LEARNING','DL':'DEEP LEARNING','NLP':'NATURAL LANGUAGE PROCESSING','CV':'COMPUTER VISION','RL':'REINFORCEMENT LEARNING','GAN':'GENERATIVE ADVERSARIAL NETWORK','VAE':'VARIATIONAL AUTOENCODER','RNN':'RECURRENT NEURAL NETWORK','CNN':'CONVOLUTIONAL NEURAL NETWORK','LSTM':'LONG SHORT TERM MEMORY','BERT':'BIDIRECTIONAL ENCODER REPRESENTATIONS FROM TRANSFORMERS','GPT':'GENERATIVE PRE TRAINED TRANSFORMER','LLM':'LARGE LANGUAGE MODEL','AGI':'ARTIFICIAL GENERAL INTELLIGENCE','API':'APPLICATION PROGRAMMING INTERFACE','SDK':'SOFTWARE DEVELOPMENT KIT','IDE':'INTEGRATED DEVELOPMENT ENVIRONMENT','GUI':'GRAPHICAL USER INTERFACE','CLI':'COMMAND LINE INTERFACE','REST':'REPRESENTATIONAL STATE TRANSFER','HTTP':'HYPERTEXT TRANSFER PROTOCOL','JSON':'JAVASCRIPT OBJECT NOTATION','XML':'EXTENSIBLE MARKUP LANGUAGE','SQL':'STRUCTURED QUERY LANGUAGE'}
    return short_u in known and known[short_u] in long_u

def is_plural(s1: str, s2: str) -> bool:
    if s1.endswith('s') and s1[:-1] == s2: return True
    if s2.endswith('s') and s2[:-1] == s1: return True
    if s1.endswith('ies') and s2 == s1[:-3] + 'y': return True
    if s2.endswith('ies') and s1 == s2[:-3] + 'y': return True
    if s1.endswith('es') and s1[:-2] == s2: return True
    if s2.endswith('es') and s2[:-2] == s1: return True
    return False


# ──────────────────────────────────────────────────
# Tag categorization
# ──────────────────────────────────────────────────

def categorize_tag(tag: str, display_name: str = None) -> str:
    tag_lower, display_lower = tag.lower(), (display_name or "").lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in tag_lower or kw in display_lower:
                score += 3 if (kw == tag_lower or kw == display_lower) else 1
        scores[cat] = score
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        if re.search(r'\d', tag) or any(x in tag_lower for x in ['bert','gpt','net','former']):
            return "models_architectures"
        if tag[0].isupper() and len(tag) > 3:
            return "industry_business"
        return "ai_ml_fundamentals"
    return best


# ──────────────────────────────────────────────────
# JSON extraction helpers
# ──────────────────────────────────────────────────

def extract_json_from_markdown(text: str) -> Optional[Dict[str, Any]]:
    try:
        m = re.search(r'```json\s*([\s\S]*?)\s*```', text, re.IGNORECASE | re.MULTILINE)
        if m:
            try:
                return json.loads(m.group(1).strip())
            except json.JSONDecodeError:
                pass
        for block in re.findall(r'```(?:\w+)?\s*([\s\S]*?)\s*```', text, re.MULTILINE):
            block = block.strip()
            if block.startswith(('{', '[')):
                try:
                    return json.loads(block)
                except json.JSONDecodeError:
                    continue
        m2 = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if m2:
            try:
                s = re.sub(r',\s*([}\]])', r'\1', m2.group(0))
                return json.loads(s)
            except json.JSONDecodeError:
                pass
    except Exception:
        pass
    return None

def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    cleaned = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    for attempt in [cleaned, text]:
        try:
            return json.loads(attempt)
        except json.JSONDecodeError:
            pass
    first = cleaned.find('{')
    last = cleaned.rfind('}')
    if first >= 0 and last > first:
        try:
            return json.loads(cleaned[first:last + 1])
        except json.JSONDecodeError:
            pass
    return None
