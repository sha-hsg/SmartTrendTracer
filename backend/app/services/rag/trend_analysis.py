import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# backend/ directory (config files live there) - resolved from this file, not cwd (CFG-006)
_BACKEND_DIR = Path(__file__).resolve().parents[3]


def _load_prompt_template(prompt_key: str) -> str:
    """Load a user_template from backend/prompts_config.json; fail loudly if missing."""
    prompts_config_path = _BACKEND_DIR / 'prompts_config.json'
    with open(prompts_config_path, 'r') as f:
        prompts_config = json.load(f)

    template = prompts_config.get(prompt_key, {}).get('user_template')
    if not template:
        raise KeyError(
            f"Missing '{prompt_key}.user_template' in {prompts_config_path}"
        )
    return template


# Single words are matched on word boundaries (so 'hot' does not fire inside
# 'photo' or 'hotel'); multi-word phrases are matched as substrings after
# lowercasing and normalizing curly apostrophes.
_TREND_WORDS = [
    # English
    'trend', 'trends', 'trending', 'popular', 'latest', 'emerging', 'buzz',
    'hot', 'hottest', 'biggest',
    # German
    'angesagt', 'meistdiskutiert', 'beliebt', 'beliebtesten', 'trendthemen',
    'gesprächsthemen',
]
_TREND_PHRASES = [
    'what are people talking about', "what's happening", 'most discussed',
    'frequently mentioned', 'current topics', 'main topics', 'key topics',
    'wichtigsten themen', 'aktuellen themen', 'aktuelle themen',
    'heiße themen', 'heisse themen', 'aufkommende themen',
]
TREND_KEYWORDS = _TREND_WORDS + _TREND_PHRASES  # kept for external references

_TREND_WORD_RE = re.compile(r'\b(?:' + '|'.join(map(re.escape, _TREND_WORDS)) + r')\b')


def is_trend_query(question: str) -> bool:
    """
    Detect if a question is asking about trends or hot topics

    Args:
        question: The user's question

    Returns:
        True if the question is trend-related, False otherwise
    """
    question_lower = question.lower().replace('\u2019', "'")
    if _TREND_WORD_RE.search(question_lower):
        return True
    return any(phrase in question_lower for phrase in _TREND_PHRASES)


def analyze_trends(search_fn, llm_manager, user_id: str,
                   question: str, content_types: Optional[List[str]] = None,
                   concept_filter: Optional[List[str]] = None,
                   k: int = 50, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze trends across documents using LLM to identify hot topics

    Args:
        search_fn: Callable that performs search (signature matches ConceptBasedRAGService.search)
        llm_manager: LLM manager instance
        user_id: User ID for LLM tracking
        question: The trend analysis question
        content_types: Optional list of content types to analyze ('tweet', 'article', 'paper')
        k: Number of documents to retrieve for analysis (default 50 for better trend detection)
        model: Optional user-selected model for LLM generation

    Returns:
        Dictionary with trend analysis and sources
    """
    # Determine source type for the prompt
    if content_types:
        plurals = [t + 's' for t in content_types]
        if len(plurals) == 1:
            source_type = plurals[0]
        else:
            source_type = ', '.join(plurals[:-1]) + ' and ' + plurals[-1]
    else:
        source_type = 'documents'

    logger.info(f"Analyzing trends in {source_type} with k={k}")

    # Use the user's actual question as the search query for relevant results
    search_results = search_fn(question, k=k, concept_filter=concept_filter,
                               content_types=content_types)

    logger.info(f"Retrieved {len(search_results)} documents for trend analysis")

    if not search_results:
        return {
            'answer': f"I couldn't find enough {source_type} to analyze trends.",
            'sources': [],
            'is_trend_analysis': True
        }

    # Build documents list for LLM analysis
    documents_text = []
    sources = []

    for i, result in enumerate(search_results, 1):
        content = result.get('content', '')

        # Format document based on type
        if result['type'] == 'tweet':
            author = result.get('author', 'Unknown')
            doc_text = f"{i}. Tweet by @{author}: {content[:300]}"
        elif result['type'] == 'article':
            title = result.get('metadata', {}).get('title', 'Untitled')
            doc_text = f"{i}. Article: {title}\n{content[:500]}"
        elif result['type'] == 'paper':
            title = result.get('metadata', {}).get('title', 'Untitled')
            doc_text = f"{i}. Paper: {title}\n{content[:500]}"
        else:
            doc_text = f"{i}. {content[:300]}"

        documents_text.append(doc_text)

        # Build source reference
        source = {
            'type': result['type'],
            'id': result['id'],
            'score': result['score'],
            'content': result.get('content', '')[:300]  # Include content preview for frontend
        }

        if result['type'] == 'tweet':
            source['author'] = result.get('author')
        elif result['type'] in ['article', 'paper']:
            source['title'] = result.get('metadata', {}).get('title')

        # Add concepts
        if result.get('concepts'):
            source['concepts'] = result['concepts']

        sources.append(source)

    # Join all documents
    documents_combined = "\n\n".join(documents_text)

    # Load prompt template for trend analysis and build the prompt
    trend_prompt_template = _load_prompt_template('rag_trend_analysis')
    prompt = trend_prompt_template.format(
        count=len(search_results),
        source_type=source_type,
        documents=documents_combined
    )

    # Log which model will be used
    if model:
        logger.info(f"Using user-selected model for trend analysis: {model}")
    else:
        logger.info("Using default model for trend analysis")

    # Convert prompt to OpenAI message format
    messages = [
        {"role": "user", "content": prompt}
    ]

    # Call LLM Manager with trend_analysis task type
    # If user selected a model, pass it as override
    override_params = {'model': model} if model else None
    response = llm_manager.completion_sync(
        task_type='trend_analysis',
        messages=messages,
        user_id=user_id,
        override_params=override_params
    )

    analysis = response.choices[0].message.content

    return {
        'answer': analysis,
        'sources': sources,
        'is_trend_analysis': True,
        'documents_analyzed': len(search_results),
        'source_type': source_type
    }


def ask(search_fn, llm_manager, user_id: str,
        question: str, k: int = 10, use_concepts: bool = True,
        content_types: Optional[List[str]] = None,
        concept_filter: Optional[List[str]] = None,
        model: Optional[str] = None) -> Dict[str, Any]:
    """
    Answer a question using RAG with concept enhancement

    Args:
        search_fn: Callable that performs search
        llm_manager: LLM manager instance
        user_id: User ID for LLM tracking
        question: The question to answer
        k: Number of documents to retrieve
        use_concepts: Whether to use concept information in the answer
        content_types: Optional list of content types to search ('tweet', 'article', 'paper')
        model: Optional user-selected model override
    """
    # Check if this is a trend analysis query
    if is_trend_query(question):
        logger.info(f"Detected trend query, routing to trend analysis: {question}")
        # Use more documents for trend analysis (50 instead of 10)
        return analyze_trends(search_fn, llm_manager, user_id, question,
                              content_types=content_types,
                              concept_filter=concept_filter, k=50, model=model)

    # Normal RAG search for non-trend queries
    # Search for relevant documents
    search_results = search_fn(question, k=k, concept_filter=concept_filter,
                               content_types=content_types)

    logger.info(f"Found {len(search_results)} search results for question: {question[:100]}")

    if not search_results:
        return {
            'answer': "I couldn't find relevant information to answer your question.",
            'sources': []
        }

    # Build context from search results
    context_parts = []
    sources = []

    for result in search_results:
        context_parts.append(result['content'])

        source = {
            'type': result['type'],
            'id': result['id'],
            'score': result['score']
        }

        # Add content preview (first 500 chars)
        content = result.get('content', '')
        if content:
            # Clean up the content for preview
            preview = content.replace('\n', ' ').strip()
            # Remove document type prefix if present
            if preview.startswith('Tweet: '):
                preview = preview[7:]
            elif preview.startswith('Article: '):
                preview = preview[9:]
            elif preview.startswith('Paper: '):
                preview = preview[7:]
            # Limit to 500 characters
            source['content'] = preview[:500] + ('...' if len(preview) > 500 else '')

        if result['type'] == 'tweet':
            source['author'] = result.get('author')
        elif result['type'] in ['article', 'paper']:
            source['title'] = result.get('metadata', {}).get('title')

        if use_concepts and result.get('concepts'):
            source['concepts'] = result['concepts']

        sources.append(source)

    context = "\n\n---\n\n".join(context_parts)
    logger.info(f"Built context with {len(context)} characters from {len(context_parts)} documents")

    # Build prompt with concept awareness
    all_concepts = set()
    if use_concepts:
        # Collect all unique concepts from results
        for result in search_results:
            all_concepts.update(result.get('concepts', []))

        concept_context = ""
        if all_concepts:
            concept_context = f"\n\nKey concepts in the sources: {', '.join(sorted(all_concepts))}"
    else:
        concept_context = ""

    # Load prompt template from prompts_config.json and build the prompt
    rag_prompt_template = _load_prompt_template('rag_query')
    prompt = rag_prompt_template.format(
        context=context,
        question=question
    )
    # Add concept context if available
    if concept_context:
        prompt = prompt.replace("Answer:", f"{concept_context}\n\nAnswer:")

    # Log which model will be used
    if model:
        logger.info(f"Using user-selected model for RAG answer: {model}")
    else:
        logger.info("Using default model for RAG answer generation")

    # Convert prompt to OpenAI message format
    messages = [
        {"role": "user", "content": prompt}
    ]

    # Call LLM Manager with rag_answer task type
    # If user selected a model, pass it as override
    override_params = {'model': model} if model else None
    response = llm_manager.completion_sync(
        task_type='rag_answer',
        messages=messages,
        user_id=user_id,
        override_params=override_params
    )

    answer = response.choices[0].message.content

    return {
        'answer': answer,
        'sources': sources,
        'concepts_used': list(all_concepts) if use_concepts else []
    }
