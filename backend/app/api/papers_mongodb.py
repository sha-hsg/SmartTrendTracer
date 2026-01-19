"""
Complete MongoDB-based papers API.
All data operations use MongoDB - no SQLite dependencies.
"""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Body, BackgroundTasks, Request
from fastapi.responses import FileResponse, Response
from pymongo import ASCENDING, DESCENDING
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from bson import ObjectId
import json
import os
import hashlib
import uuid
from pathlib import Path

from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.services.readability_service import ReadabilityService

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
from app.database.mongodb import get_database

db = get_database()

# Initialize concept service
concept_service = ConceptOnlyTagService()

# Task status tracking (in production, use Redis or database)
analysis_tasks = {}  # task_id -> {status, progress, results, error}

# Marker processing semaphore (limit to 1 concurrent Marker process)
import asyncio
marker_semaphore = asyncio.Semaphore(1)

def run_analysis_in_background(task_id: str, paper_id: str, analysis_types: List[str]):
    """Background task to run LLM analysis without blocking the server"""
    import uuid
    import asyncio
    from datetime import datetime

    try:
        analysis_tasks[task_id] = {
            "status": "running",
            "progress": 0,
            "results": {},
            "error": None,
            "started_at": datetime.utcnow().isoformat()
        }

        # Get paper
        try:
            if len(paper_id) == 24:
                paper = db.papers.find_one({'_id': ObjectId(paper_id)})
            else:
                paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
        except:
            paper = None

        if not paper:
            analysis_tasks[task_id]["status"] = "failed"
            analysis_tasks[task_id]["error"] = "Paper not found"
            return

        # Get paper content for context
        context = f"Title: {paper.get('title', '')}\n\n"
        if paper.get('abstract'):
            context += f"Abstract: {paper['abstract']}\n\n"
        if paper.get('content'):
            context += f"Content: {paper['content'][:5000]}..."

        existing_analyses = paper.get('analyses', [])
        results = {}

        # Import services and configs
        from app.services.llm_service import LLMService
        llm_service = LLMService()

        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        with open(os.path.join(backend_dir, 'prompts_config.json'), 'r') as f:
            prompts_config = json.load(f)
        with open(os.path.join(backend_dir, 'llm.json'), 'r') as f:
            llm_config = json.load(f)

        total_analyses = len(analysis_types)

        for i, analysis_type in enumerate(analysis_types):
            try:
                # Update progress
                analysis_tasks[task_id]["progress"] = int((i / total_analyses) * 100)

                # Check if already exists
                existing = next((a for a in existing_analyses if (a.get('type') == analysis_type or a.get('analysis_type') == analysis_type)), None)
                if existing:
                    results[analysis_type] = {
                        "success": True,
                        "content": existing.get('content', ''),
                        "model": existing.get('model_used') or existing.get('model', 'gpt-4o-mini'),
                        "created_at": existing.get('created_at') or existing.get('generated_at')
                    }
                    continue

                # Generate new analysis
                paper_analyses = prompts_config.get('paper_analyses', {})
                analysis_config = paper_analyses.get(analysis_type, {
                    'system': 'You are an expert at analyzing research papers.',
                    'user_template': 'Analyze this paper:\n\n{paper_content}'
                })

                paper_content = paper.get('content', '')
                if not paper_content or len(paper_content) < 100:
                    paper_content = context

                system_prompt = analysis_config.get('system', '')
                user_template = analysis_config.get('user_template', '')
                user_prompt = user_template.replace('{paper_content}', paper_content)

                model_key = 'paper_analysis_deep' if analysis_type in ['review', 'sas_review', 'switt'] else 'paper_analysis'
                model_config = llm_config['models'].get(model_key, llm_config['models'].get('paper_analysis'))

                # This is the blocking LLM call - but now in background!
                full_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
                result = llm_service.generate_completion(
                    prompt=full_prompt,
                    max_tokens=model_config.get('max_tokens', 8000),
                    temperature=model_config.get('temperature', 0.3),
                    model=model_config.get('model')
                )

                # Create analysis object
                analysis = {
                    "type": analysis_type,
                    "analysis_type": analysis_type,
                    "content": result,
                    "created_at": datetime.utcnow().isoformat(),
                    "model": model_config.get('model'),
                    "model_used": model_config.get('model')
                }

                existing_analyses.append(analysis)
                results[analysis_type] = {
                    "success": True,
                    "content": result,
                    "model": model_config.get('model'),
                    "created_at": analysis["created_at"]
                }

            except Exception as e:
                logger.error(f"Error generating {analysis_type} analysis: {e}")
                results[analysis_type] = {
                    "success": False,
                    "error": str(e)
                }

        # Update paper with new analyses
        if len(paper_id) == 24:
            db.papers.update_one(
                {'_id': ObjectId(paper_id)},
                {'$set': {'analyses': existing_analyses}}
            )
        else:
            db.papers.update_one(
                {'old_sqlite_id': int(paper_id)},
                {'$set': {'analyses': existing_analyses}}
            )

        # Mark task as completed
        analysis_tasks[task_id]["status"] = "completed"
        analysis_tasks[task_id]["progress"] = 100
        analysis_tasks[task_id]["results"] = results
        analysis_tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        logger.error(f"Background analysis task {task_id} failed: {e}")
        analysis_tasks[task_id]["status"] = "failed"
        analysis_tasks[task_id]["error"] = str(e)

@router.get("/{paper_id}/analyses/task/{task_id}")
async def get_analysis_task_status(paper_id: str, task_id: str):
    """Get the status of a background analysis task"""
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    return analysis_tasks[task_id]
# Initialize readability service
readability_service = ReadabilityService()

def get_paper_by_id(paper_id: str):
    """Get paper by MongoDB ObjectId only - pure MongoDB standard - returns ObjectId converted to string"""
    try:
        if len(paper_id) == 24:
            # Try as MongoDB ObjectId
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
            if paper:
                # Convert ObjectId to string to prevent serialization errors
                paper['_id'] = str(paper['_id'])
                return paper
            return None
        else:
            # Invalid ID format
            return None
    except:
        return None

@router.get("/")
def get_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    concept_id: Optional[str] = None,
    concept_ids: Optional[List[str]] = Query(None),
    author: Optional[str] = None,
    conference: Optional[str] = None,
    conferences: Optional[List[str]] = Query(None),
    journal: Optional[str] = None,
    institution: Optional[str] = None,
    affiliations: Optional[List[str]] = Query(None),
    processor: Optional[str] = None,
    processors: Optional[List[str]] = Query(None),
    year: Optional[int] = None,
    years: Optional[List[int]] = Query(None),
    special_filter: Optional[str] = None,
    is_flagged: Optional[bool] = None,
    no_processor: Optional[bool] = None,
    no_year: Optional[bool] = None,
    no_conference: Optional[bool] = None,
    no_affiliation: Optional[bool] = None,
    no_annotations: Optional[bool] = None,
    # Rating filters
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="Minimum rating (1-5)"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Exact rating (1-5)"),
    unrated_only: bool = Query(False, description="Show only unrated papers"),
    # Sort options
    sort_by: str = Query("created_at", description="Sort field: created_at, publication_date, title, rating"),
    sort_order: str = Query("desc", description="Sort order: asc or desc")
):
    """Get papers with filtering and pagination from MongoDB"""
    
    # Build query
    query = {}
    
    if search:
        query['$text'] = {'$search': search}
    
    # Handle multiple concept IDs (AND logic - paper must have ALL selected concepts)
    if concept_ids and len(concept_ids) > 0:
        # Convert all concept_ids to ObjectIds
        concept_object_ids = []
        for cid in concept_ids:
            try:
                concept_object_ids.append(ObjectId(cid))
            except:
                # If invalid ObjectId format, skip
                pass
        
        if concept_object_ids:
            # Paper must have ALL selected concepts (AND logic)
            query['concept_ids'] = {'$all': concept_object_ids}
    elif concept_id:
        # Backward compatibility - single concept_id
        try:
            query['concept_ids'] = ObjectId(concept_id)
        except:
            # If invalid ObjectId format, try as string
            query['concept_ids'] = concept_id
    
    if author:
        # Search in authors_detailed array
        query['authors_detailed.name'] = {'$regex': author, '$options': 'i'}
    
    # Handle multiple conferences
    if conferences and len(conferences) > 0:
        if len(conferences) == 1:
            query['conference'] = {'$regex': conferences[0], '$options': 'i'}
        else:
            # Use $or for multiple conferences - add to $and array to avoid conflict
            conference_conditions = [{'conference': {'$regex': conf, '$options': 'i'}} for conf in conferences]
            if '$and' not in query:
                query['$and'] = []
            query['$and'].append({'$or': conference_conditions})
    elif conference:  # Fallback to single conference parameter
        query['conference'] = {'$regex': conference, '$options': 'i'}
    
    if journal:
        query['journal'] = {'$regex': journal, '$options': 'i'}
    
    # Handle multiple affiliations (institutions)
    if affiliations and len(affiliations) > 0:
        if len(affiliations) == 1:
            query['authors_detailed.affiliation'] = {'$regex': affiliations[0], '$options': 'i'}
        else:
            # Use $or for multiple affiliations - add to $and array to avoid conflict
            affiliation_conditions = [{'authors_detailed.affiliation': {'$regex': aff, '$options': 'i'}} for aff in affiliations]
            if '$and' not in query:
                query['$and'] = []
            query['$and'].append({'$or': affiliation_conditions})
    elif institution:  # Fallback to single institution parameter
        query['authors_detailed.affiliation'] = {'$regex': institution, '$options': 'i'}
    
    # Handle multiple processors
    if processors and len(processors) > 0:
        logger.info(f"Filtering by processors: {processors}")
        if len(processors) == 1:
            query['processor_used'] = processors[0]
        else:
            query['processor_used'] = {'$in': processors}
    elif processor:  # Fallback to single processor parameter
        logger.info(f"Filtering by single processor: {processor}")
        query['processor_used'] = processor
    
    # Handle multiple years
    if years and len(years) > 0:
        if len(years) == 1:
            year_value = years[0]
        else:
            # For multiple years, we need a different approach
            year_value = {'$in': years}
        
        # Filter by year from publication_date or created_at
        query['$expr'] = {
            '$in': [
                {
                    '$cond': {
                        'if': {
                            '$and': [
                                {'$ne': ['$publication_date', None]},
                                {'$ne': ['$publication_date', '']},
                                {'$eq': [{'$type': '$publication_date'}, 'string']},
                                {'$gt': [{'$strLenCP': '$publication_date'}, 4]}
                            ]
                        },
                        'then': {'$year': {'$dateFromString': {'dateString': '$publication_date', 'onError': None}}},
                        'else': {'$year': '$created_at'}
                    }
                },
                years if len(years) > 1 else [years[0]]
            ]
        }
    elif year:  # Fallback to single year parameter
        # Filter by year from publication_date or created_at
        query['$expr'] = {
            '$eq': [
                {
                    '$cond': {
                        'if': {
                            '$and': [
                                {'$ne': ['$publication_date', None]},
                                {'$ne': ['$publication_date', '']},
                                {'$eq': [{'$type': '$publication_date'}, 'string']},
                                {'$gt': [{'$strLenCP': '$publication_date'}, 4]}
                            ]
                        },
                        'then': {'$year': {'$dateFromString': {'dateString': '$publication_date', 'onError': None}}},
                        'else': {'$year': '$created_at'}
                    }
                },
                year
            ]
        }
    
    if special_filter:
        if special_filter == 'processed':
            query['processed'] = True
        elif special_filter == 'flagged':
            query['is_flagged'] = True
        elif special_filter == 'arxiv':
            query['arxiv_id'] = {'$ne': None, '$ne': ''}
        elif special_filter == 'has_doi':
            query['doi'] = {'$ne': None, '$ne': ''}
        elif special_filter == 'has_repository':
            query['repository'] = {'$ne': None, '$ne': ''}
    
    # Handle special boolean filters
    if is_flagged is not None:
        query['is_flagged'] = is_flagged
    
    if no_processor:
        query['$or'] = [
            {'processor_used': None},
            {'processor_used': ''},
            {'processor_used': {'$exists': False}},
            {'processed': False},
            {'processed': {'$exists': False}}
        ]
    
    if no_year:
        query['$and'] = query.get('$and', []) + [
            {'$or': [
                {'publication_date': None},
                {'publication_date': ''},
                {'publication_date': {'$exists': False}}
            ]}
        ]
    
    if no_conference:
        query['$and'] = query.get('$and', []) + [
            {'$or': [
                {'conference': None},
                {'conference': ''},
                {'conference': {'$exists': False}}
            ]}
        ]
    
    if no_affiliation:
        # Find papers that either:
        # 1. Have no authors_detailed field at all
        # 2. Have empty authors_detailed array
        # 3. Have authors_detailed where at least one author has no affiliation
        query['$or'] = [
            # Papers with no authors_detailed field or empty array
            {'authors_detailed': {'$in': [None, []]}},
            # Papers where authors_detailed doesn't exist
            {'authors_detailed': {'$exists': False}},
            # Papers where at least one author has no affiliation
            {
                'authors_detailed': {
                    '$elemMatch': {
                        '$or': [
                            {'affiliation': None},
                            {'affiliation': ''},
                            {'affiliation': {'$exists': False}}
                        ]
                    }
                }
            }
        ]
    
    if no_annotations:
        # Find papers that have no tag instances (no annotations)
        # First get all paper IDs that have tag instances
        papers_with_tags = db.tag_instances.distinct('content_id', {'content_type': 'paper'})
        
        # Convert the paper IDs to both ObjectId and string formats for comparison
        objectid_list = []
        string_list = []
        int_list = []
        
        for pid in papers_with_tags:
            pid_str = str(pid)
            string_list.append(pid_str)
            
            # Try to convert to ObjectId if it's a valid 24-char hex string
            try:
                if len(pid_str) == 24:
                    objectid_list.append(ObjectId(pid_str))
            except:
                pass
            
            # Try to convert to int for old_sqlite_id
            try:
                int_list.append(int(pid_str))
            except:
                pass
        
        # Papers must NOT be in any of these lists
        if objectid_list or int_list:
            conditions = []
            if objectid_list:
                conditions.append({'_id': {'$nin': objectid_list}})
            if int_list:
                conditions.append({'old_sqlite_id': {'$nin': int_list}})
            
            if len(conditions) == 1:
                # Merge with existing query
                for key, value in conditions[0].items():
                    query[key] = value
            else:
                # Both conditions must be true (paper not in either list)
                query['$and'] = query.get('$and', []) + conditions

    # Rating filters
    if min_rating:
        query['user_rating'] = {'$gte': min_rating}
    elif rating:
        query['user_rating'] = rating
    elif unrated_only:
        # Papers without user_rating field or with null value
        query['$and'] = query.get('$and', []) + [
            {'$or': [
                {'user_rating': {'$exists': False}},
                {'user_rating': None}
            ]}
        ]

    # Log the final query for debugging
    logger.info(f"Final query for papers: {query}")
    
    # Count total
    total = db.papers.count_documents(query)

    # Get papers with pagination
    skip = (page - 1) * page_size

    # Determine sort direction
    sort_direction = DESCENDING if sort_order == "desc" else ASCENDING

    # Build sort criteria
    if sort_by == "rating":
        # For rating sort, put unrated papers last
        # Use secondary sort by created_at for consistent ordering
        sort_criteria = [
            ('user_rating', DESCENDING if sort_order == "desc" else ASCENDING),
            ('created_at', DESCENDING)
        ]
        cursor = db.papers.find(query).sort(sort_criteria).skip(skip).limit(page_size)
    elif sort_by == "title":
        cursor = db.papers.find(query).sort('title', sort_direction).skip(skip).limit(page_size)
    elif sort_by == "publication_date":
        cursor = db.papers.find(query).sort('publication_date', sort_direction).skip(skip).limit(page_size)
    else:
        # Default: created_at
        cursor = db.papers.find(query).sort('created_at', sort_direction).skip(skip).limit(page_size)

    papers = list(cursor)

    paper_id_strings = []
    legacy_ids = []
    for paper in papers:
        paper_id_strings.append(str(paper['_id']))
        legacy_id = paper.get('old_sqlite_id')
        if legacy_id:
            legacy_ids.append(str(legacy_id))

    tag_instances_by_paper = {}
    concept_ids_needed = set()

    if paper_id_strings:
        id_query = {'content_type': 'paper', 'content_id': {'$in': paper_id_strings + legacy_ids}}
        tag_instances_batch = list(db.tag_instances.find(id_query))
        for instance in tag_instances_batch:
            content_id = instance.get('content_id')
            if not content_id:
                continue
            tag_instances_by_paper.setdefault(content_id, []).append(instance)
            concept_id = instance.get('concept_id')
            if concept_id:
                concept_ids_needed.add(str(concept_id))

    concept_map = {}
    if concept_ids_needed:
        object_ids = []
        string_ids = []
        for cid in concept_ids_needed:
            if len(cid) == 24:
                try:
                    object_ids.append(ObjectId(cid))
                    continue
                except Exception:
                    pass
            string_ids.append(cid)

        concepts_query = {'$or': []}
        if object_ids:
            concepts_query['$or'].append({'_id': {'$in': object_ids}})
        if string_ids:
            concepts_query['$or'].append({'id': {'$in': string_ids}})

        if concepts_query['$or']:
            concept_docs = concept_service.tag_concepts.find(concepts_query)
            for doc in concept_docs:
                concept_map[str(doc['_id'])] = doc
                if doc.get('id'):
                    concept_map[doc['id']] = doc

    # Format response
    result = []
    for paper in papers:
        paper_id = str(paper['_id'])
        sqlite_id = str(paper.get('old_sqlite_id', '')) if paper.get('old_sqlite_id') else None

        tag_instances = list(tag_instances_by_paper.get(paper_id, []))
        if sqlite_id:
            tag_instances.extend(tag_instances_by_paper.get(sqlite_id, []))

        concept_refs = []
        seen = set()
        for instance in tag_instances:
            cid = instance.get('concept_id')
            key = None
            if isinstance(cid, ObjectId):
                key = str(cid)
            elif cid:
                key = str(cid)
            if key and key not in seen:
                seen.add(key)
                doc = concept_map.get(key)
                if doc:
                    concept_refs.append({
                        'concept_id': str(doc['_id']),
                        'display_name': doc.get('display_name'),
                        'slug': doc.get('slug')
                    })

        # Use stored readability metrics (don't calculate on the fly)
        readability_metrics = paper.get('readability', {})
        
        # Format analyses if they exist
        analyses_data = []
        if paper.get('analyses'):
            # Handle both dict and list formats
            if isinstance(paper['analyses'], dict):
                for analysis_type, analysis_content in paper['analyses'].items():
                    if isinstance(analysis_content, dict) and analysis_content.get('success'):
                        analyses_data.append({
                            'analysis_type': analysis_type,
                            'analysis_name': analysis_type,  # Add for compatibility
                            'content': analysis_content.get('content', ''),
                            'analysis_content': analysis_content.get('content', ''),  # Add for compatibility
                            'model': analysis_content.get('model'),
                            'created_at': analysis_content.get('created_at')
                        })
            elif isinstance(paper['analyses'], list):
                # If it's already a list, just use it as is
                analyses_data = paper['analyses']
        
        result.append({
            'id': str(paper['_id']),
            'title': paper.get('title'),
            'abstract': paper.get('abstract'),
            'authors': paper.get('authors', []),
            'authors_detailed': paper.get('authors_detailed', []),  # Include detailed author info
            'publication_date': paper.get('publication_date'),
            'conference': paper.get('conference'),
            'journal': paper.get('journal'),
            'arxiv_id': paper.get('arxiv_id'),
            'doi': paper.get('doi'),
            'pdf_path': paper.get('pdf_path'),
            'page_count': paper.get('page_count', 0),
            'word_count': paper.get('word_count', 0),
            'concepts': concept_refs,
            'tags': [c['display_name'] for c in concept_refs],  # For backwards compatibility - string array
            'is_processed': paper.get('processed', False),
            'processed': paper.get('processed', False),
            'processor': paper.get('processor_used'),
            'processor_used': paper.get('processor_used'),
            'processed_with_mineru': paper.get('processor_used') == 'mineru_service',
            'processed_with_marker': paper.get('processor_used') == 'marker_service',
            'is_flagged': paper.get('is_flagged', False),
            'user_rating': paper.get('user_rating'),  # Star rating (1-5 or None)
            'created_at': paper.get('created_at').isoformat() if paper.get('created_at') else None,
            'readability': readability_metrics,  # Add readability metrics
            'analyses': analyses_data  # Add analyses data
        })
    
    # Return both papers and total count for pagination
    return {
        'papers': result,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size  # Ceiling division
    }

@router.get("/facets")
def get_facets(
    search: Optional[str] = None,
    concept_ids: Optional[List[str]] = Query(None),
    author: Optional[str] = None,
    conference: Optional[str] = None,
    year: Optional[int] = None,
    affiliation: Optional[str] = None,
    processor: Optional[str] = None
):
    """Get facets for filtering papers - facets update based on current filters"""
    
    print("DEBUG: Starting facets generation with filters")
    
    # Build base query for filtering (same as in get_papers)
    base_query = {}
    
    if search:
        base_query['$text'] = {'$search': search}
    
    # Handle multiple concept IDs for filtering
    if concept_ids and len(concept_ids) > 0:
        concept_object_ids = []
        for cid in concept_ids:
            try:
                concept_object_ids.append(ObjectId(cid))
            except:
                pass
        if concept_object_ids:
            base_query['concept_ids'] = {'$all': concept_object_ids}
    
    if author:
        base_query['authors_detailed.name'] = {'$regex': author, '$options': 'i'}
    
    if conference:
        base_query['conference'] = {'$regex': conference, '$options': 'i'}
    
    if year:
        base_query['$expr'] = {
            '$eq': [
                {
                    '$cond': {
                        'if': {
                            '$and': [
                                {'$ne': ['$publication_date', None]},
                                {'$ne': ['$publication_date', '']},
                                {'$eq': [{'$type': '$publication_date'}, 'string']},
                                {'$gt': [{'$strLenCP': '$publication_date'}, 4]}
                            ]
                        },
                        'then': {'$year': {'$dateFromString': {'dateString': '$publication_date', 'onError': None}}},
                        'else': {'$year': '$created_at'}
                    }
                },
                year
            ]
        }
    
    if affiliation:
        base_query['authors_detailed.affiliation'] = {'$regex': affiliation, '$options': 'i'}
    
    if processor:
        base_query['processor_used'] = processor
    
    # Create base match stage for pipelines
    base_match = {'$match': base_query} if base_query else None
    
    # Get author facets from authors_detailed array
    author_pipeline = []
    if base_match:
        author_pipeline.append(base_match)
    author_pipeline.extend([
        {'$unwind': '$authors_detailed'},
        {'$group': {
            '_id': '$authors_detailed.name',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}},
        {'$limit': 50}
    ])
    author_facets = list(db.papers.aggregate(author_pipeline))
    print(f"DEBUG: Found {len(author_facets)} author facets")
    if author_facets:
        print(f"DEBUG: First author facet: {author_facets[0]}")
    else:
        # Try fallback to regular authors field if authors_detailed fails
        print("DEBUG: Trying fallback to regular authors field")
        fallback_pipeline = [
            {'$match': {'authors': {'$ne': None, '$ne': ''}}},
            {'$project': {'authors_split': {'$split': ['$authors', ', ']}}},
            {'$unwind': '$authors_split'},
            {'$group': {'_id': '$authors_split', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 50}
        ]
        author_facets = list(db.papers.aggregate(fallback_pipeline))
        print(f"DEBUG: Fallback found {len(author_facets)} author facets")
    
    # Get year facets from publication_date and created_at
    year_pipeline = []
    if base_match:
        year_pipeline.append(base_match)
    year_pipeline.extend([
        {
            '$addFields': {
                'year': {
                    '$cond': {
                        'if': {
                            '$and': [
                                {'$ne': ['$publication_date', None]},
                                {'$ne': ['$publication_date', '']},
                                {'$eq': [{'$type': '$publication_date'}, 'string']},
                                {'$gt': [{'$strLenCP': '$publication_date'}, 4]}
                            ]
                        },
                        'then': {'$year': {'$dateFromString': {'dateString': '$publication_date', 'onError': None}}},
                        'else': {'$year': '$created_at'}
                    }
                }
            }
        },
        {'$match': {'year': {'$ne': None}}},  # Filter out null years
        {'$group': {
            '_id': '$year',
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': -1}},
        {'$limit': 20}
    ])
    year_facets = list(db.papers.aggregate(year_pipeline))
    print(f"DEBUG: Found {len(year_facets)} year facets")
    
    # Get conference facets
    conference_pipeline = []
    if base_match:
        conference_pipeline.append(base_match)
    conference_pipeline.extend([
        {'$match': {'conference': {'$ne': None, '$ne': ''}}},
        {'$group': {
            '_id': '$conference',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}},
        {'$limit': 30}
    ])
    conference_facets = list(db.papers.aggregate(conference_pipeline))
    
    # Get journal facets
    journal_pipeline = []
    if base_match:
        journal_pipeline.append(base_match)
    journal_pipeline.extend([
        {'$match': {'journal': {'$ne': None, '$ne': ''}}},
        {'$group': {
            '_id': '$journal',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}},
        {'$limit': 30}
    ])
    journal_facets = list(db.papers.aggregate(journal_pipeline))
    
    # Get institution facets from authors_detailed
    # Count unique papers per institution, not author instances
    institution_pipeline = []
    if base_match:
        institution_pipeline.append(base_match)
    institution_pipeline.extend([
        {'$unwind': '$authors_detailed'},
        {'$match': {'authors_detailed.affiliation': {'$ne': None, '$ne': ''}}},
        {'$group': {
            '_id': {
                'paper_id': '$_id',
                'affiliation': '$authors_detailed.affiliation'
            }
        }},
        {'$group': {
            '_id': '$_id.affiliation',
            'count': {'$sum': 1}  # Count unique papers
        }},
        {'$sort': {'count': -1}},
        {'$limit': 30}
    ])
    institution_facets = list(db.papers.aggregate(institution_pipeline))
    
    # Get processor facets
    processor_pipeline = []
    if base_match:
        processor_pipeline.append(base_match)
    processor_pipeline.extend([
        {'$match': {'processor_used': {'$ne': None}}},
        {'$group': {
            '_id': '$processor_used',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}}
    ])
    processor_facets = list(db.papers.aggregate(processor_pipeline))

    # Get rating facets
    rating_pipeline = []
    if base_match:
        rating_pipeline.append(base_match)
    rating_pipeline.extend([
        {'$group': {
            '_id': '$user_rating',
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': -1}}
    ])
    rating_results = list(db.papers.aggregate(rating_pipeline))

    # Count unrated papers (user_rating doesn't exist or is null)
    unrated_query = {**base_query, '$or': [
        {'user_rating': {'$exists': False}},
        {'user_rating': None}
    ]} if base_query else {'$or': [
        {'user_rating': {'$exists': False}},
        {'user_rating': None}
    ]}
    unrated_count = db.papers.count_documents(unrated_query)

    # Build rating facet
    rating_facet = {
        '5_stars': next((r['count'] for r in rating_results if r['_id'] == 5), 0),
        '4_stars': next((r['count'] for r in rating_results if r['_id'] == 4), 0),
        '3_stars': next((r['count'] for r in rating_results if r['_id'] == 3), 0),
        '2_stars': next((r['count'] for r in rating_results if r['_id'] == 2), 0),
        '1_star': next((r['count'] for r in rating_results if r['_id'] == 1), 0),
        'unrated': unrated_count
    }
    print(f"DEBUG: Rating facet: {rating_facet}")

    # Get special filters facets
    special_filters = []
    
    # Count papers with different statuses - apply base_query if filters are active
    processed_query = {**base_query, 'processed': True} if base_query else {'processed': True}
    flagged_query = {**base_query, 'is_flagged': True} if base_query else {'is_flagged': True}
    arxiv_query = {**base_query, 'arxiv_id': {'$ne': None, '$ne': ''}} if base_query else {'arxiv_id': {'$ne': None, '$ne': ''}}
    doi_query = {**base_query, 'doi': {'$ne': None, '$ne': ''}} if base_query else {'doi': {'$ne': None, '$ne': ''}}
    repository_query = {**base_query, 'repository': {'$ne': None, '$ne': ''}} if base_query else {'repository': {'$ne': None, '$ne': ''}}
    
    processed_count = db.papers.count_documents(processed_query)
    flagged_count = db.papers.count_documents(flagged_query)
    arxiv_count = db.papers.count_documents(arxiv_query)
    doi_count = db.papers.count_documents(doi_query)
    repository_count = db.papers.count_documents(repository_query)
    
    if processed_count > 0:
        special_filters.append({'name': 'processed', 'label': 'Processed Papers', 'count': processed_count})
    if flagged_count > 0:
        special_filters.append({'name': 'flagged', 'label': 'Flagged Papers', 'count': flagged_count})
    if arxiv_count > 0:
        special_filters.append({'name': 'arxiv', 'label': 'ArXiv Papers', 'count': arxiv_count})
    if doi_count > 0:
        special_filters.append({'name': 'has_doi', 'label': 'Has DOI', 'count': doi_count})
    if repository_count > 0:
        special_filters.append({'name': 'has_repository', 'label': 'Has Repository', 'count': repository_count})
    
    # Get paper status counts - for flagged/unflagged
    paper_status = {}
    flagged_query = {**base_query, 'is_flagged': True} if base_query else {'is_flagged': True}
    unflagged_query = {**base_query, '$or': [{'is_flagged': False}, {'is_flagged': {'$exists': False}}]} if base_query else {'$or': [{'is_flagged': False}, {'is_flagged': {'$exists': False}}]}
    paper_status['flagged'] = db.papers.count_documents(flagged_query)
    paper_status['unflagged'] = db.papers.count_documents(unflagged_query)
    
    # Get missing data counts - these are for papers MISSING data
    missing_data_counts = {}
    
    # Count papers with no processor - apply base_query if filters are active
    no_processor_query = {**base_query, '$or': [{'processor_used': None}, {'processor_used': ''}]} if base_query else {'$or': [{'processor_used': None}, {'processor_used': ''}]}
    missing_data_counts['no_processor'] = db.papers.count_documents(no_processor_query)
    
    # Count papers with no year
    no_year_query = {**base_query, '$and': [
        {'$or': [{'publication_date': None}, {'publication_date': ''}]},
        {'$or': [{'year': None}, {'year': ''}]}
    ]} if base_query else {'$and': [
        {'$or': [{'publication_date': None}, {'publication_date': ''}]},
        {'$or': [{'year': None}, {'year': ''}]}
    ]}
    missing_data_counts['no_year'] = db.papers.count_documents(no_year_query)
    
    # Count papers with no conference
    no_conference_query = {**base_query, '$and': [
        {'$or': [{'conference': None}, {'conference': ''}]},
        {'$or': [{'venue': None}, {'venue': ''}]}
    ]} if base_query else {'$and': [
        {'$or': [{'conference': None}, {'conference': ''}]},
        {'$or': [{'venue': None}, {'venue': ''}]}
    ]}
    missing_data_counts['no_conference'] = db.papers.count_documents(no_conference_query)
    
    # Count papers with no affiliations - this is the critical one for your issue
    # A paper has no affiliation if:
    # 1. authors_detailed doesn't exist OR
    # 2. authors_detailed exists but no author has an affiliation
    # We need to use aggregation pipeline for this complex check
    no_affiliation_pipeline = []
    if base_match:
        no_affiliation_pipeline.append(base_match)
    no_affiliation_pipeline.extend([
        {'$match': {
            '$or': [
                # No authors_detailed field at all
                {'authors_detailed': {'$exists': False}},
                # authors_detailed is empty array
                {'authors_detailed': {'$size': 0}},
                # authors_detailed exists but check if ALL authors have no affiliation
                {'$expr': {
                    '$eq': [
                        {'$size': {
                            '$filter': {
                                'input': {'$ifNull': ['$authors_detailed', []]},
                                'cond': {
                                    '$and': [
                                        {'$ne': ['$$this.affiliation', None]},
                                        {'$ne': ['$$this.affiliation', '']}
                                    ]
                                }
                            }
                        }},
                        0
                    ]
                }}
            ]
        }},
        {'$count': 'total'}
    ])
    no_affiliation_result = list(db.papers.aggregate(no_affiliation_pipeline))
    missing_data_counts['no_affiliation'] = no_affiliation_result[0]['total'] if no_affiliation_result else 0
    
    # Count papers with no annotations (no tag instances)
    # First get all paper IDs that have tag instances
    papers_with_tags = db.tag_instances.distinct('content_id', {'content_type': 'paper'})
    no_annotations_query = {**base_query, '_id': {'$nin': [ObjectId(pid) if len(pid) == 24 else pid for pid in papers_with_tags]}} if base_query else {'_id': {'$nin': [ObjectId(pid) if len(pid) == 24 else pid for pid in papers_with_tags]}}
    missing_data_counts['no_annotations'] = db.papers.count_documents(no_annotations_query)
    
    # Get concept facets - only from filtered papers
    concept_facets = []
    
    # If filters are applied, get concepts only from filtered papers
    if base_query:
        print(f"DEBUG: Getting filtered concepts with base_query: {base_query}")
        # Build pipeline to get concepts from filtered papers
        concept_pipeline = [
            {'$match': base_query},
            {'$unwind': '$concept_ids'},
            {'$group': {
                '_id': '$concept_ids',
                'count': {'$sum': 1}
            }}
        ]
        
        # Get concept counts from filtered papers
        filtered_concepts = list(db.papers.aggregate(concept_pipeline))
        print(f"DEBUG: Found {len(filtered_concepts)} unique concepts in filtered papers")
        
        # Get concept details for each concept_id
        if filtered_concepts:
            concept_ids = [c['_id'] for c in filtered_concepts]
            concept_details = list(db.tag_concepts_v2.find({'_id': {'$in': concept_ids}}))
            
            # Build concept facets with counts
            concept_map = {str(c['_id']): c['count'] for c in filtered_concepts}
            for concept in concept_details:
                concept_id = str(concept['_id'])
                if concept_id in concept_map:
                    concept_facets.append({
                        'concept_id': concept_id,
                        'id': f"c_{concept_id[:4]}",
                        'slug': concept.get('slug', ''),
                        'display_name': concept.get('display_name', ''),
                        'count': concept_map[concept_id]
                    })
            
            # Sort by count
            concept_facets.sort(key=lambda x: x['count'], reverse=True)
            print(f"DEBUG: Returning {len(concept_facets)} concept facets")
    else:
        # No filters - return all concepts for papers
        print("DEBUG: No filters - returning all paper concepts")
        all_concepts = concept_service.get_all_concepts_with_counts(content_type='paper')
        concept_facets = all_concepts
        print(f"DEBUG: Returning {len(concept_facets)} concept facets")
    
    result = {
        'authors': [{'name': f['_id'], 'count': f['count']} for f in author_facets if f['_id']],
        'years': [{'year': f['_id'], 'count': f['count']} for f in year_facets if f['_id']],
        'conferences': [{'name': f['_id'], 'count': f['count']} for f in conference_facets if f['_id']],
        'journals': [{'name': f['_id'], 'count': f['count']} for f in journal_facets if f['_id']],
        'institutions': [{'name': f['_id'], 'count': f['count']} for f in institution_facets if f['_id']],
        'processors': [{'name': f['_id'], 'count': f['count']} for f in processor_facets if f['_id']],
        'special_filters': special_filters,
        'concepts': concept_facets,
        'missing_data': missing_data_counts,  # Add missing data counts to the response
        'paper_status': paper_status,  # Add paper status counts
        'rating': rating_facet  # Add rating facet for star rating filter
    }
    
    print(f"DEBUG: Returning facets: authors={len(result['authors'])}, years={len(result['years'])}, institutions={len(result['institutions'])}, concepts={len(result['concepts'])}")
    return result

@router.get("/{paper_id}")
def get_paper(paper_id: str):
    """Get a specific paper by ID from MongoDB"""
    
    paper = get_paper_by_id(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get concepts from tag_instances collection
    # Try both MongoDB _id and old SQLite ID
    paper_id = str(paper['_id'])
    sqlite_id = str(paper.get('old_sqlite_id', ''))
    
    tag_instances = list(db.tag_instances.find({
        'content_type': 'paper',
        '$or': [
            {'content_id': paper_id},
            {'content_id': sqlite_id}
        ]
    }))
    
    # Deduplicate concept_ids to avoid React key warnings
    concept_ids = list(set(ti['concept_id'] for ti in tag_instances))
    
    # Get concept details
    concepts = []
    for cid in concept_ids:
        concept = concept_service.get_concept_by_id(cid)
        if concept:
            concepts.append({
                'concept_id': str(cid),  # Convert ObjectId to string for JSON serialization
                'display_name': concept.get('display_name'),
                'slug': concept.get('slug')
            })
    
    # Use stored readability metrics (don't calculate on the fly)
    readability_metrics = paper.get('readability', {})
    
    # Format response
    return {
        'id': str(paper['_id']),
        'title': paper.get('title'),
        'abstract': paper.get('abstract'),
        'content': paper.get('content'),
        'authors': paper.get('authors', []),
        'authors_detailed': paper.get('authors_detailed', []),  # Include detailed author info
        'sections': paper.get('sections', []),
        'references': paper.get('references', []),
        'publication_date': paper.get('publication_date'),
        'conference': paper.get('conference'),
        'journal': paper.get('journal'),
        'arxiv_id': paper.get('arxiv_id'),
        'doi': paper.get('doi'),
        'pdf_path': paper.get('pdf_path'),
        'pdf_url': paper.get('pdf_url'),
        'page_count': paper.get('page_count', 0),
        'word_count': paper.get('word_count', 0),
        'citation_count': paper.get('citation_count', 0),
        'concepts': concepts,
        'tags': [c['display_name'] for c in concepts],  # For backwards compatibility - string array
        'is_processed': paper.get('processed', False),  # Use correct field name
        'processor': paper.get('processor_used'),  # Use correct field name
        'processed': paper.get('processed', False),  # Include both for compatibility
        'processor_used': paper.get('processor_used'),  # Include both for compatibility
        'processed_with_mineru': paper.get('processor_used') == 'mineru_service',
        'processed_with_marker': paper.get('processor_used') == 'marker_service',
        'is_flagged': paper.get('is_flagged', False),
        'snippets': paper.get('snippets', []),
        'analyses': paper.get('analyses', []),
        'repository': paper.get('repository'),
        'bibtex': paper.get('bibtex'),  # Include BibTeX citation
        'dblp_key': paper.get('dblp_key'),  # Include DBLP key if available
        'dblp_url': paper.get('dblp_url'),  # Include DBLP URL if available
        'created_at': paper.get('created_at').isoformat() if paper.get('created_at') and hasattr(paper.get('created_at'), 'isoformat') else paper.get('created_at'),
        'updated_at': paper.get('updated_at').isoformat() if paper.get('updated_at') and hasattr(paper.get('updated_at'), 'isoformat') else paper.get('updated_at'),
        'readability': readability_metrics  # Add readability metrics
    }

@router.post("/{paper_id}/concepts")
def add_concept_to_paper(
    paper_id: str,
    text: str = Query(..., description="Text to create/find concept from")
):
    """Add a concept to a paper"""
    
    try:
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Add concept using the service
    success, concept_id = concept_service.add_tag('paper', str(paper['_id']), text)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add concept")
    
    # Update paper's concept_ids in MongoDB
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$addToSet': {'concept_ids': concept_id}}
    )
    
    # Get concept details
    concept = concept_service.get_concept_by_id(concept_id)
    
    return {
        "message": "Concept added successfully",
        "concept": {
            "concept_id": concept_id,
            "slug": concept.get('slug', ''),
            "display_name": concept.get('display_name', '')
        }
    }

@router.delete("/{paper_id}/concepts/{concept_id}")
def remove_concept_from_paper(paper_id: str, concept_id: str):
    """Remove a concept from a paper"""
    
    try:
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Remove from concept service
    success = concept_service.remove_tag('paper', str(paper['_id']), concept_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Concept not found on this paper")
    
    # Update paper's concept_ids in MongoDB
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$pull': {'concept_ids': concept_id}}
    )
    
    return {"message": "Concept removed successfully"}

@router.put("/{paper_id}/content")
async def update_paper_content(paper_id: str, data: dict = Body(...)):
    """Update paper content/markdown content"""
    
    content = data.get('content', '')
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
            filter_query = {'_id': ObjectId(paper_id)}
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
            filter_query = {'old_sqlite_id': int(paper_id)}
    except:
        paper = None
        filter_query = None
    
    if not paper or not filter_query:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Update both content and markdown_content fields
    update_data = {
        'content': content,
        'markdown_content': content,
        'updated_at': datetime.utcnow().isoformat()
    }
    
    # Perform the update
    result = db.papers.update_one(
        filter_query,
        {'$set': update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update paper content")
    
    return {
        "success": True,
        "message": "Paper content updated successfully",
        "updated_at": update_data['updated_at']
    }

@router.put("/{paper_id}/metadata")
def update_paper_metadata(paper_id: str, metadata: dict):
    """Update paper metadata"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Prepare update data
    update_data = {}
    
    # Update basic metadata fields
    if 'title' in metadata:
        update_data['title'] = metadata['title']
    if 'abstract' in metadata:
        update_data['abstract'] = metadata['abstract']
    if 'publication_date' in metadata:
        update_data['publication_date'] = metadata['publication_date']
    if 'published_date' in metadata:
        # Also store as published_date (ArXiv format) for consistency
        update_data['published_date'] = metadata['published_date']
    if 'conference' in metadata:
        update_data['conference'] = metadata['conference']
    if 'journal' in metadata:
        update_data['journal'] = metadata['journal']
    if 'arxiv_id' in metadata:
        update_data['arxiv_id'] = metadata['arxiv_id']
    if 'doi' in metadata:
        update_data['doi'] = metadata['doi']
    
    # Handle authors - update both authors string and authors_detailed
    if 'authors' in metadata:
        if isinstance(metadata['authors'], list):
            # Build authors_detailed array
            authors_detailed = []
            author_names = []
            for idx, author in enumerate(metadata['authors']):
                if isinstance(author, dict):
                    author_detail = {
                        'name': author.get('name', ''),
                        'affiliation': author.get('affiliation', ''),
                        'email': author.get('email', ''),
                        'position': idx,
                        'is_corresponding': False
                    }
                    authors_detailed.append(author_detail)
                    author_names.append(author.get('name', ''))
                elif isinstance(author, str):
                    # Simple string author name
                    author_names.append(author)
            
            # Update both fields
            if authors_detailed:
                update_data['authors_detailed'] = authors_detailed
            update_data['authors'] = ', '.join(author_names) if author_names else ''
        elif isinstance(metadata['authors'], str):
            # Simple authors string
            update_data['authors'] = metadata['authors']
    
    # Add updated timestamp
    update_data['updated_at'] = datetime.utcnow()
    
    # Update the paper
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': update_data}
    )
    
    # Return updated paper
    updated_paper = db.papers.find_one({'_id': paper['_id']})
    
    # Format response (similar to get_paper)
    return {
        'id': str(updated_paper['_id']),
        'title': updated_paper.get('title'),
        'abstract': updated_paper.get('abstract'),
        'authors': updated_paper.get('authors', ''),
        'authors_detailed': updated_paper.get('authors_detailed', []),  # Include detailed author info
        'publication_date': updated_paper.get('publication_date'),
        'published_date': updated_paper.get('published_date'),
        'conference': updated_paper.get('conference'),
        'journal': updated_paper.get('journal'),
        'arxiv_id': updated_paper.get('arxiv_id'),
        'doi': updated_paper.get('doi'),
        'message': 'Metadata updated successfully'
    }

@router.post("/{paper_id}/flag")
def toggle_paper_flag(paper_id: str, flag_data: dict):
    """Toggle the flag status of a paper"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get the flag status from request
    is_flagged = flag_data.get('is_flagged', False)
    flag_notes = flag_data.get('flag_notes', '')
    
    # Update the paper
    update_data = {
        'is_flagged': is_flagged,
        'flag_notes': flag_notes if is_flagged else '',
        'updated_at': datetime.utcnow()
    }
    
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': update_data}
    )
    
    return {
        'id': str(paper['_id']),
        'is_flagged': is_flagged,
        'flag_notes': flag_notes if is_flagged else '',
        'message': f"Paper {'flagged' if is_flagged else 'unflagged'} successfully"
    }


@router.patch("/{paper_id}/rating")
def set_paper_rating(
    paper_id: str,
    rating: int = Query(..., ge=0, le=5, description="Rating 1-5, or 0 to clear")
):
    """Set user rating for a paper (1-5 stars, 0 to clear rating)"""

    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if rating == 0:
        # Clear rating
        db.papers.update_one(
            {'_id': paper['_id']},
            {'$unset': {'user_rating': ''}, '$set': {'updated_at': datetime.utcnow()}}
        )
        return {
            'id': str(paper['_id']),
            'user_rating': None,
            'message': 'Rating cleared successfully'
        }
    else:
        # Set rating
        db.papers.update_one(
            {'_id': paper['_id']},
            {'$set': {'user_rating': rating, 'updated_at': datetime.utcnow()}}
        )
        return {
            'id': str(paper['_id']),
            'user_rating': rating,
            'message': f'Rating set to {rating} stars'
        }


@router.get("/{paper_id}/content")
def get_paper_content(paper_id: str):
    """Get paper content (sections, references, etc.) from MongoDB"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Return content-specific fields
    return {
        'id': str(paper['_id']),
        'title': paper.get('title'),
        'content': paper.get('content', ''),
        'sections': paper.get('sections', []),
        'references': paper.get('references', []),
        'abstract': paper.get('abstract'),
        'pdf_path': paper.get('pdf_path')
    }


async def process_with_marker_background(paper_id: str, pdf_path: str):
    """Background task to process PDF with Marker service"""
    import httpx
    from pathlib import Path
    import traceback
    
    logger.info(f"=== MARKER BACKGROUND TASK STARTED ===")
    logger.info(f"Paper ID: {paper_id}")
    logger.info(f"PDF Path: {pdf_path}")
    
    # Update status to processing
    db.papers.update_one(
        {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
        {'$set': {
            'processing_status': 'processing_with_marker',
            'processing_started_at': datetime.utcnow()
        }}
    )
    logger.info(f"Updated paper status to 'processing_with_marker'")
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        # Try relative to backend directory
        pdf_file = Path(__file__).parent.parent.parent / pdf_path
        logger.info(f"Using relative path: {pdf_file}")
    
    if not pdf_file.exists():
        error_msg = f"PDF file not found: {pdf_file}"
        logger.error(error_msg)
        db.papers.update_one(
            {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
            {'$set': {
                'processing_status': 'failed',
                'processing_error': error_msg
            }}
        )
        return
    
    logger.info(f"PDF file exists: {pdf_file} (size: {pdf_file.stat().st_size} bytes)")
    
    marker_url = "http://localhost:8002/convert"
    logger.info(f"Marker URL: {marker_url}")
    
    try:
        # Test if Marker service is reachable
        logger.info("Testing Marker service connectivity...")
        async with httpx.AsyncClient(timeout=5.0) as test_client:
            try:
                health_response = await test_client.get("http://localhost:8002/")
                logger.info(f"Marker service health check: {health_response.status_code}")
            except Exception as e:
                logger.error(f"Marker service not reachable: {e}")
        
        # Use semaphore to limit concurrent Marker processing
        logger.info("Acquiring Marker semaphore...")
        async with marker_semaphore:
            logger.info("Marker semaphore acquired. Starting processing...")
            # Use a very long timeout for Marker (3 hours to handle complex PDFs)
            logger.info("Opening PDF file for upload...")
            async with httpx.AsyncClient(timeout=10800.0) as client:
                with open(pdf_file, 'rb') as f:
                    file_content = f.read()
                    logger.info(f"Read PDF file: {len(file_content)} bytes")

                    files = {'file': (pdf_file.name, file_content, 'application/pdf')}

                # Add callback URL for progress updates
                callback_url = f"http://localhost:8000/api/papers/{paper_id}/progress-callback"
                
                # CRITICAL: Must send paper_id for Marker to save images!
                # Check if this paper already has an old_sqlite_id (shouldn't happen for new processing)
                # For new papers, we need to generate a stable integer ID
                # We'll use the MongoDB ObjectId to generate a unique integer
                if len(paper_id) == 24:
                    # MongoDB ObjectId - convert to a stable integer
                    # Use last 8 hex chars converted to int for uniqueness
                    paper_id_int = int(paper_id[-8:], 16)
                else:
                    # Already an integer ID
                    paper_id_int = int(paper_id)
                
                data = {
                    'output_format': 'markdown',
                    'extract_images': 'true',
                    'debug': 'true',  # Enable debug for more info
                    'rewrite_to_files': 'false',
                    'paper_id': paper_id_int,  # CRITICAL: Must include paper_id for image saving!
                    'callback_url': callback_url  # Progress callback URL
                }
                
                logger.info(f"=== SENDING REQUEST TO MARKER ===")
                logger.info(f"File name: {pdf_file.name}")
                logger.info(f"File size: {len(file_content)} bytes")
                logger.info(f"Data params: {data}")
                
                response = await client.post(marker_url, files=files, data=data)
                logger.info(f"Marker response status: {response.status_code}")
                
                if response.status_code == 200:
                    logger.info(f"=== MARKER SUCCESS RESPONSE ===")
                    result = response.json()
                    logger.info(f"Response keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")
                    logger.info(f"Content length: {len(result.get('content', ''))} chars")
                    logger.info(f"Image count: {result.get('image_count', 0)}")
                    logger.info(f"Processing time: {result.get('elapsed', 0)} seconds")
                    
                    # Update paper with processed content
                    # Extract the kept_dir from debug info to know where images are stored
                    debug_info = result.get('_debug', {})
                    kept_dir = debug_info.get('kept_dir', '')
                    
                    # Extract just the session ID from the full path
                    # e.g., from "/path/to/marker_service/debug_runs/marker_cli_oyismanp/arxiv_2505.15105"
                    # we want "marker_cli_oyismanp"
                    marker_session_id = None
                    if kept_dir:
                        import re
                        match = re.search(r'(marker_cli_[^/]+)', kept_dir)
                        if match:
                            marker_session_id = match.group(1)
                    
                    # Calculate readability metrics for the processed content
                    readability_metrics = {}
                    content = result.get('content', '')
                    if content:
                        try:
                            readability_metrics = readability_service.get_readability_metrics(content)
                            logger.info(f"Calculated readability: {readability_metrics.get('difficulty', 'Unknown')}")
                        except Exception as e:
                            logger.warning(f"Could not calculate readability: {e}")
                    
                    update_data = {
                        'content': content,  # Fixed: Marker returns 'content', not 'markdown'
                        'processed': True,
                        'processor_used': 'marker_service',
                        'processed_at': datetime.utcnow(),
                        'processing_status': 'completed',
                        'readability': readability_metrics,  # Store readability scores
                        'marker_metadata': {
                            'method': result.get('method', 'marker'),
                            'image_count': result.get('image_count', 0),
                            'processing_time': result.get('elapsed', 0),
                            'images': result.get('images', []),
                            'kept_dir': kept_dir,
                            'session_id': marker_session_id
                        }
                    }
                    
                    db.papers.update_one(
                        {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
                        {'$set': update_data}
                    )
                    logger.info(f"=== SUCCESSFULLY UPDATED PAPER {paper_id} ===")
                else:
                    error_text = response.text[:500]  # First 500 chars of error
                    logger.error(f"=== MARKER ERROR RESPONSE ===")
                    logger.error(f"Status code: {response.status_code}")
                    logger.error(f"Error text: {error_text}")
                    
                    db.papers.update_one(
                        {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
                        {'$set': {
                            'processing_status': 'failed',
                            'processing_error': f"Marker service error {response.status_code}: {error_text}"
                        }}
                    )
    except httpx.TimeoutException as e:
        error_msg = f"Marker service timeout after 3 hours"
        logger.error(f"=== MARKER TIMEOUT ===")
        logger.error(error_msg)
        db.papers.update_one(
            {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
            {'$set': {
                'processing_status': 'failed',
                'processing_error': error_msg
            }}
        )
    except httpx.RequestError as e:
        error_msg = f"Marker service connection error: {str(e)}"
        logger.error(f"=== MARKER CONNECTION ERROR ===")
        logger.error(error_msg)
        db.papers.update_one(
            {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
            {'$set': {
                'processing_status': 'failed',
                'processing_error': error_msg
            }}
        )
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"=== MARKER UNEXPECTED ERROR ===")
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.papers.update_one(
            {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
            {'$set': {
                'processing_status': 'failed',
                'processing_error': error_msg
            }}
        )

@router.post("/{paper_id}/process-with-marker")
async def process_paper_with_marker(paper_id: str, background_tasks: BackgroundTasks):
    """Start async processing of paper's PDF using Marker service"""
    
    logger.info(f"=== PROCESS WITH MARKER ENDPOINT CALLED ===")
    logger.info(f"Paper ID: {paper_id}")
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
            logger.info(f"Found paper by ObjectId")
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
            logger.info(f"Found paper by old SQLite ID")
    except Exception as e:
        logger.error(f"Error finding paper: {e}")
        paper = None
    
    if not paper:
        logger.error(f"Paper not found: {paper_id}")
        raise HTTPException(status_code=404, detail="Paper not found")
    
    logger.info(f"Paper title: {paper.get('title', 'Unknown')}")
    
    pdf_path = paper.get('pdf_path')
    if not pdf_path:
        logger.error(f"No PDF path for paper {paper_id}")
        raise HTTPException(status_code=400, detail="No PDF path found for this paper")
    
    logger.info(f"PDF path: {pdf_path}")
    
    # Check if already processing
    current_status = paper.get('processing_status')
    logger.info(f"Current processing status: {current_status}")
    
    if current_status == 'processing_with_marker':
        logger.warning(f"Paper already being processed")
        return {
            'success': False,
            'message': 'Paper is already being processed with Marker',
            'status': 'processing'
        }
    
    # Check if file exists
    from pathlib import Path
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        # Try relative to backend directory
        pdf_file = Path(__file__).parent.parent.parent / pdf_path
        logger.info(f"Trying relative path: {pdf_file}")
        if not pdf_file.exists():
            logger.error(f"PDF file not found at: {pdf_file}")
            raise HTTPException(status_code=404, detail=f"PDF file not found: {pdf_path}")
    
    logger.info(f"PDF file found: {pdf_file}")
    logger.info(f"PDF file size: {pdf_file.stat().st_size} bytes")
    
    # Start background processing
    logger.info(f"=== ADDING BACKGROUND TASK ===")
    background_tasks.add_task(
        process_with_marker_background,
        str(paper['_id']),
        str(pdf_file)
    )
    logger.info(f"Background task added successfully")
    
    return {
        'success': True,
        'message': 'PDF processing with Marker has been started in the background',
        'status': 'processing',
        'paper_id': str(paper['_id']),
        'expected_time': 'Processing may take 10-15 minutes for complex papers'
    }

@router.post("/{paper_id}/cancel-processing")
async def cancel_processing(paper_id: str):
    """Cancel ongoing Marker processing"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if paper.get('processing_status') != 'processing_with_marker':
        return {
            'success': False,
            'message': 'Paper is not being processed',
            'status': paper.get('processing_status', 'not_started')
        }
    
    # Update status to cancelled
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {
            'processing_status': 'cancelled',
            'processing_cancelled_at': datetime.utcnow()
        }}
    )
    
    return {
        'success': True,
        'message': 'Processing has been cancelled',
        'paper_id': str(paper['_id'])
    }

@router.get("/{paper_id}/processing-status")
async def get_processing_status(paper_id: str):
    """Check the processing status of a paper"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    status = paper.get('processing_status', 'not_started')
    response = {
        'paper_id': str(paper['_id']),
        'status': status,
        'processed': paper.get('processed', False),
        'processor_used': paper.get('processor_used'),
        'processed_at': paper.get('processed_at').isoformat() if paper.get('processed_at') else None
    }
    
    if status == 'processing_with_marker':
        started_at = paper.get('processing_started_at')
        if started_at:
            elapsed = (datetime.utcnow() - started_at).total_seconds()
            response['elapsed_seconds'] = elapsed
            response['elapsed_minutes'] = round(elapsed / 60, 1)
        
        # Include detailed progress information
        progress_data = paper.get('processing_progress')
        if progress_data:
            response['progress'] = progress_data
            # Extract current stage and progress percentage for easy access
            response['current_stage'] = progress_data.get('stage', 'processing')
            response['progress_message'] = progress_data.get('message', 'Processing...')
            response['progress_percentage'] = progress_data.get('progress', 0)
    
    if status == 'failed':
        response['error'] = paper.get('processing_error')
    
    if status == 'completed' and paper.get('marker_metadata'):
        response['marker_metadata'] = paper['marker_metadata']
    
    return response

@router.get("/{paper_id}/process-health")
async def get_process_health(paper_id: str):
    """Get detailed process health information for currently running Marker process"""

    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    status = paper.get('processing_status', 'not_started')

    # Only return health info if actively processing
    if status not in ['processing_with_marker', 'processing_with_mineru', 'processing_pdf']:
        return {
            'paper_id': str(paper['_id']),
            'status': status,
            'is_processing': False,
            'message': 'No active processing'
        }

    # Get process health data from MongoDB
    health_data = paper.get('marker_process_health', {})

    response = {
        'paper_id': str(paper['_id']),
        'status': status,
        'is_processing': True,
        'processor': paper.get('processor_used', 'marker'),
        'health': {
            'pid': health_data.get('pid'),
            'cpu_time': health_data.get('cpu_time', 0),
            'memory_mb': health_data.get('memory_mb', 0),
            'cpu_percent': health_data.get('cpu_percent', 0),
            'last_updated': health_data.get('last_updated').isoformat() if health_data.get('last_updated') else None,
            'output_files': health_data.get('output_files', {
                'markdown_exists': False,
                'image_count': 0
            })
        }
    }

    # Add elapsed time
    started_at = paper.get('processing_started_at')
    if started_at:
        elapsed = (datetime.utcnow() - started_at).total_seconds()
        response['elapsed_seconds'] = elapsed
        response['elapsed_minutes'] = round(elapsed / 60, 1)

    return response

@router.post("/{paper_id}/process")
async def process_paper_pdf(paper_id: str, background_tasks: BackgroundTasks):
    """Process a paper's PDF to extract content"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    pdf_path = paper.get('pdf_path')
    if not pdf_path:
        raise HTTPException(status_code=400, detail="No PDF path found for this paper")
    
    # Check if file exists
    from pathlib import Path
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        # Try relative to backend directory
        pdf_file = Path(__file__).parent.parent.parent / pdf_path
        if not pdf_file.exists():
            raise HTTPException(status_code=404, detail=f"PDF file not found: {pdf_path}")
    
    # Process the PDF
    from ..services.pdf_processor_service import get_pdf_processor_service
    pdf_service = get_pdf_processor_service()
    
    logger.info(f"Processing PDF for paper {paper_id}: {pdf_path}")
    result = pdf_service.process_pdf(str(pdf_file), paper_id=str(paper['_id']))
    
    if result['success']:
        # Update paper with processed content
        # Note: pdf_processor_service returns 'markdown' not 'content'
        content = result.get('markdown', '') or result.get('content', '')
        update_data = {
            'content': content,
            'markdown_content': content,  # Store in both fields for compatibility
            'processed': True,
            'processor_used': result.get('method_used', 'unknown'),
            'processed_at': datetime.utcnow()
        }
        
        # Add metadata if available
        if result.get('metadata'):
            update_data['processing_metadata'] = result['metadata']
            # Store image count if extracted
            if result['metadata'].get('images_extracted'):
                update_data['images_extracted'] = result['metadata']['images_extracted']
        
        db.papers.update_one(
            {'_id': paper['_id']},
            {'$set': update_data}
        )
        
        return {
            'success': True,
            'message': f"Successfully processed PDF with {result.get('method_used', 'unknown')}",
            'content_length': len(content),
            'method_used': result.get('method_used', 'unknown'),
            'images_extracted': result.get('metadata', {}).get('images_extracted', 0)
        }
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to process PDF'))

@router.post("/{paper_id}/process-with-entities")
async def process_paper_with_entities(paper_id: str, background_tasks: BackgroundTasks):
    """Process a paper's PDF and extract entities"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    pdf_path = paper.get('pdf_path')
    if not pdf_path:
        raise HTTPException(status_code=400, detail="No PDF path found for this paper")
    
    # Check if file exists
    from pathlib import Path
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        # Try relative to backend directory
        pdf_file = Path(__file__).parent.parent.parent / pdf_path
        if not pdf_file.exists():
            raise HTTPException(status_code=404, detail=f"PDF file not found: {pdf_path}")
    
    # Process the PDF
    from ..services.pdf_processor_service import get_pdf_processor_service
    pdf_service = get_pdf_processor_service()
    
    logger.info(f"Processing PDF for paper {paper_id}: {pdf_path}")
    result = pdf_service.process_pdf(str(pdf_file), paper_id=str(paper['_id']))
    
    if result['success']:
        # Update paper with processed content
        # Note: pdf_processor_service returns 'markdown' not 'content'
        content = result.get('markdown', '') or result.get('content', '')
        update_data = {
            'content': content,
            'markdown_content': content,  # Store in both fields for compatibility
            'processed': True,
            'processor_used': result.get('method_used', 'unknown'),
            'processed_at': datetime.utcnow()
        }
        
        # Add metadata if available
        if result.get('metadata'):
            update_data['processing_metadata'] = result['metadata']
            # Store image count if extracted
            if result['metadata'].get('images_extracted'):
                update_data['images_extracted'] = result['metadata']['images_extracted']
        
        db.papers.update_one(
            {'_id': paper['_id']},
            {'$set': update_data}
        )
        
        # Extract entities
        try:
            from ..services.entity_extraction_service import EntityExtractionService
            entity_service = EntityExtractionService(use_fast_model=True)
            
            # Prepare text for entity extraction (use full content)
            extraction_text = f"""
            Title: {paper.get('title', '')}
            Authors: {', '.join(paper.get('authors', []))}
            Abstract: {paper.get('abstract', '')}
            Content: {result['content'][:10000]}  # Use more content for better extraction
            """
            
            logger.info(f"Extracting entities from {len(extraction_text)} characters of text")
            entities = entity_service.extract_entities(extraction_text, article_id=str(paper['_id']))
            
            # Save entities to concept hierarchy and add as tags
            saved_count = 0
            entity_list = []
            
            for entity in entities:
                parent_type = entity_service._get_parent_type_for_entity(entity.entity_type)
                if parent_type:
                    # Save to ontology
                    concept = entity_service.save_entity_to_ontology(None, entity, parent_type, user="system")
                    if concept:
                        saved_count += 1
                        # Also add as tag to the paper
                        from ..services.concept_only_tag_service import ConceptOnlyTagService
                        tag_service = ConceptOnlyTagService()
                        success, concept_id = tag_service.add_tag('paper', str(paper['_id']), entity.text, preserve_display_name=True)
                        
                        entity_list.append({
                            'text': entity.text,
                            'type': entity.entity_type,
                            'confidence': entity.confidence,
                            'added_as_tag': success
                        })
            
            logger.info(f"Extracted {len(entities)} entities, saved {saved_count} to ontology")
            
            return {
                'success': True,
                'message': f"Successfully processed PDF with {result.get('method_used', 'unknown')} and extracted entities",
                'content_length': len(result['content']),  # Fixed: use 'content' field
                'entities': {
                    'extracted': len(entities),
                    'saved': saved_count,
                    'list': entity_list
                }
            }
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            import traceback
            traceback.print_exc()
            # Still return success for PDF processing
            return {
                'success': True,
                'message': f"PDF processed successfully with {result.get('method_used', 'unknown')} (entity extraction failed)",
                'content_length': len(result['content']),  # Fixed: use 'content' field
                'entity_extraction_error': str(e)
            }

@router.post("/{paper_id}/progress-callback")
async def receive_marker_progress(
    paper_id: str,
    request: Request
):
    """Receive progress updates from Marker service during processing"""
    try:
        progress_data = await request.json()
        logger.info(f"Progress update for paper {paper_id}: {progress_data}")

        # Update paper with progress information
        paper = db.papers.find_one({'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id})

        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        # Store progress in database
        progress_update = {
            'processing_progress': progress_data,
            'last_progress_update': datetime.utcnow()
        }

        # If health data is included in the progress update, store it separately
        if 'health' in progress_data:
            health_data = progress_data['health']
            health_data['last_updated'] = datetime.utcnow()
            progress_update['marker_process_health'] = health_data
            logger.info(f"Stored process health data: PID={health_data.get('pid')}, CPU={health_data.get('cpu_percent')}%, RAM={health_data.get('memory_mb')}MB")

        db.papers.update_one(
            {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
            {'$set': progress_update}
        )

        return {'success': True, 'message': 'Progress updated'}
        
    except Exception as e:
        logger.error(f"Failed to update progress for paper {paper_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update progress")

@router.post("/{paper_id}/process-with-mineru")
async def process_paper_with_mineru(paper_id: str, background_tasks: BackgroundTasks):
    """Start async processing of paper's PDF using MinerU service"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Check if already processing
    current_status = paper.get('processing_status')
    if current_status in ['processing_with_marker', 'processing_with_mineru', 'processing_pdf']:
        logger.warning(f"Paper already being processed")
        return {
            'success': False,
            'message': 'Paper is already being processed',
            'status': 'processing'
        }
    
    pdf_path = paper.get('pdf_path')
    if not pdf_path:
        raise HTTPException(status_code=400, detail="No PDF path found for this paper")
    
    # Check if file exists
    from pathlib import Path
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        # Try relative to backend directory
        pdf_file = Path(__file__).parent.parent.parent / pdf_path
        if not pdf_file.exists():
            raise HTTPException(status_code=404, detail=f"PDF file not found: {pdf_path}")

    logger.info(f"Starting MinerU processing for paper {paper_id}")
    
    # Set initial processing status
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {
            'processing_status': 'processing_with_mineru',
            'processing_started_at': datetime.utcnow()
        }}
    )
    
    # Add background task for MinerU processing
    background_tasks.add_task(process_with_mineru_background, paper_id, str(pdf_file))
    
    return {
        'success': True,
        'message': 'PDF processing with MinerU has been started in the background',
        'status': 'processing',
        'paper_id': paper_id,
        'expected_time': 'Processing may take 5-10 minutes depending on paper complexity'
    }

async def process_with_mineru_background(paper_id: str, pdf_path: str):
    """Background task to process PDF with MinerU service"""
    logger.info(f"=== MINERU BACKGROUND TASK STARTED ===")
    logger.info(f"Paper ID: {paper_id}")
    logger.info(f"PDF Path: {pdf_path}")
    
    try:
        # Update paper with current timestamp
        db.papers.update_one(
            {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
            {'$set': {
                'processing_status': 'processing_with_mineru',
                'processing_started_at': datetime.utcnow()
            }}
        )
        logger.info("Updated paper status to 'processing_with_mineru'")
        
        # Convert MongoDB ObjectId to integer for MinerU image saving
        mongo_id = paper_id  # Keep the original MongoDB ID for URLs
        if len(paper_id) == 24:
            # MongoDB ObjectId - convert to a stable integer
            # Use last 8 hex chars converted to int for uniqueness
            paper_id_int = int(paper_id[-8:], 16)
            logger.info(f"Converted MongoDB ID {paper_id} to integer {paper_id_int} for MinerU")
        else:
            # Already an integer ID
            paper_id_int = int(paper_id)
        
        # Use the PDF processor service with MinerU preference
        from ..services.pdf_processor_service import get_pdf_processor_service
        pdf_service = get_pdf_processor_service()
        
        # Pass both the integer ID for file storage and MongoDB ID for callback URL
        logger.info(f"Processing PDF with MinerU service, paper_id_int={paper_id_int}, mongo_id={mongo_id}")
        result = pdf_service.process_pdf(
            pdf_path, 
            prefer_method='mineru', 
            paper_id=paper_id_int,
            mongo_paper_id=mongo_id  # Pass MongoDB ID for callback URL
        )
        
        if result['success'] and result.get('markdown'):
            logger.info(f"=== MINERU SUCCESS ===")
            logger.info(f"Content length: {len(result['markdown'])} chars")
            
            # Fix image URLs in markdown to use MongoDB ID instead of converted integer
            content = result['markdown']
            if len(paper_id) == 24:
                # Replace image URLs that use the converted integer with the MongoDB ID
                content = content.replace(f'/api/papers/{paper_id_int}/images/', f'/api/papers/{mongo_id}/images/')
                logger.info(f"Fixed image URLs: {paper_id_int} -> {mongo_id}")
            
            # Calculate readability metrics for the processed content
            readability_metrics = {}
            try:
                readability_metrics = readability_service.get_readability_metrics(content)
                logger.info(f"Calculated readability: {readability_metrics.get('difficulty', 'Unknown')}")
            except Exception as e:
                logger.warning(f"Could not calculate readability: {e}")
            
            # Update paper with processed content
            update_data = {
                'content': content,  # Fixed: use 'content' field
                'processed': True,
                'processor_used': 'mineru_service',
                'processed_at': datetime.utcnow(),
                'processing_status': 'completed',
                'readability': readability_metrics  # Store readability scores
            }
            
            # Store metadata if available
            if result.get('metadata'):
                update_data['mineru_metadata'] = result['metadata']
                logger.info(f"MinerU metadata: {result['metadata']}")
            
            db.papers.update_one(
                {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
                {'$set': update_data}
            )
            logger.info(f"=== SUCCESSFULLY UPDATED PAPER {paper_id} ===")
        else:
            error_msg = result.get('error', 'MinerU processing failed')
            logger.error(f"=== MINERU ERROR ===")
            logger.error(error_msg)
            
            db.papers.update_one(
                {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
                {'$set': {
                    'processing_status': 'failed',
                    'processing_error': f"MinerU processing error: {error_msg}"
                }}
            )
    except Exception as e:
        error_msg = f"MinerU service error: {str(e)}"
        logger.error(f"=== MINERU EXCEPTION ===")
        logger.error(error_msg)
        db.papers.update_one(
            {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id},
            {'$set': {
                'processing_status': 'failed',
                'processing_error': error_msg
            }}
        )

@router.post("/{paper_id}/extract-entities")
async def extract_entities_from_paper(paper_id: str):
    """Extract entities from an already processed paper"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if not paper.get('content'):
        raise HTTPException(status_code=400, detail="Paper has not been processed yet")
    
    try:
        from ..services.entity_extraction_service import EntityExtractionService
        entity_service = EntityExtractionService(use_fast_model=False)  # Use full model for better extraction
        
        # Prepare text for entity extraction (use full content)
        extraction_text = f"""
        Title: {paper.get('title', '')}
        Authors: {', '.join(paper.get('authors', []))}
        Abstract: {paper.get('abstract', '')}
        Content: {paper['content'][:15000]}  # Use more content for comprehensive extraction
        """
        
        logger.info(f"Extracting entities from paper {paper_id}")
        entities = entity_service.extract_entities(extraction_text, article_id=str(paper['_id']))
        
        # Validate entities if needed
        validated_entities = []
        for entity in entities[:20]:  # Validate top 20 entities
            is_valid, suggested_type, reasoning = entity_service.validate_entity(entity)
            if is_valid:
                validated_entities.append(entity)
                if suggested_type and suggested_type != entity.entity_type:
                    entity.entity_type = suggested_type
        
        # Save entities to concept hierarchy and add as tags
        saved_count = 0
        entity_list = []
        
        for entity in validated_entities:
            parent_type = entity_service._get_parent_type_for_entity(entity.entity_type)
            if parent_type:
                # Save to ontology
                concept = entity_service.save_entity_to_ontology(None, entity, parent_type, user="system")
                if concept:
                    saved_count += 1
                    # Also add as tag to the paper
                    from ..services.concept_only_tag_service import ConceptOnlyTagService
                    tag_service = ConceptOnlyTagService()
                    success, concept_id = tag_service.add_tag('paper', str(paper['_id']), entity.text, preserve_display_name=True)
                    
                    entity_list.append({
                        'text': entity.text,
                        'type': entity.entity_type,
                        'confidence': entity.confidence,
                        'added_as_tag': success,
                        'concept_id': concept_id if success else None
                    })
        
        logger.info(f"Extracted {len(entities)} entities, validated {len(validated_entities)}, saved {saved_count}")
        
        return {
            'success': True,
            'paper_id': str(paper['_id']),
            'paper_title': paper.get('title', 'Unknown'),
            'entities': {
                'extracted': len(entities),
                'validated': len(validated_entities),
                'saved': saved_count,
                'list': entity_list
            }
        }
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{paper_id}/tags/suggestions")
async def get_tag_suggestions(paper_id: str, model: str = None):
    """Get AI-powered concept suggestions for a paper"""

    logger.info(f"Getting tag suggestions for paper {paper_id} with model: {model}")

    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get existing concepts on this paper
    paper_id_str = str(paper['_id'])
    sqlite_id_str = str(paper.get('old_sqlite_id', ''))
    
    existing_tags = list(db.tag_instances.find({
        'content_type': 'paper',
        '$or': [
            {'content_id': paper_id_str},
            {'content_id': sqlite_id_str}
        ]
    }))
    
    existing_concept_ids = [ti['concept_id'] for ti in existing_tags if ti.get('concept_id')]
    
    # Get concept display names for already tagged (return strings for frontend compatibility)
    already_tagged = []
    for cid in existing_concept_ids:
        concept = concept_service.get_concept_by_id(cid)
        if concept:
            already_tagged.append(concept.get('display_name', ''))
    
    # Find similar existing concepts based on title/abstract
    existing_suggestions = []
    all_concepts = concept_service.get_all_concepts_with_counts(content_type='paper')
    
    # Simple text matching for suggestions
    paper_text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    
    for concept in all_concepts[:30]:  # Check top 30 concepts
        if concept['id'] not in existing_concept_ids:
            # Check if concept name appears in paper text
            if concept['display_name'].lower() in paper_text or \
               any(alias.lower() in paper_text for alias in concept.get('aliases', [])):
                existing_suggestions.append({
                    'concept_id': concept['id'],
                    'display_name': concept['display_name'],
                    'slug': concept['slug'],
                    'usage_count': concept.get('usage_count', 0)
                })
                if len(existing_suggestions) >= 5:
                    break
    
    # Generate new suggestions using LLM
    new_suggestions = []
    try:
        from app.services.llm_manager import get_llm_manager
        llm_manager = get_llm_manager()

        # Prepare FULL paper text for LLM - send everything!
        paper_text_for_llm = f"Title: {paper.get('title', '')}\n\n"
        paper_text_for_llm += f"Abstract: {paper.get('abstract', '')}\n\n"

        # Add FULL content - no truncation!
        if paper.get('content'):
            paper_text_for_llm += f"Full Paper Content:\n{paper['content']}"
            logger.info(f"Sending full paper content to LLM: {len(paper['content'])} characters")
        else:
            logger.warning(f"Paper {paper_id} has no content, using title and abstract only")

        # Get author names
        authors = paper.get('authors', '')
        if isinstance(authors, list):
            authors = ', '.join(authors)

        # Load prompts configuration
        import json
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        with open(os.path.join(backend_dir, 'prompts_config.json'), 'r') as f:
            prompts_config = json.load(f)

        # Get paper tag suggestion prompt
        tag_config = prompts_config.get('paper_tag_suggestion', {})
        system_prompt = tag_config.get('system', '')
        user_template = tag_config.get('user_template', '')
        max_tags = tag_config.get('max_tags', 30)

        # Replace placeholders
        user_prompt = user_template.replace('{author}', authors).replace('{text}', paper_text_for_llm).replace('{max_tags}', str(max_tags))

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        # Map frontend model selections to LiteLLM Router model_name (from litellm_config.yaml)
        # IMPORTANT: Values must match model_name in litellm_config.yaml, NOT the full litellm_params.model
        model_mapping = {
            # GPT models (model_name matches frontend value)
            "gpt-5": "gpt-5-2025-08-07",
            "gpt-5.1": "gpt-5.1",
            "gpt-5-mini": "gpt-5-mini",
            "gpt-5-nano": "gpt-5-nano",
            "gpt-4o": "gpt-4o",
            "gpt-4o-mini": "gpt-4o-mini",
            # Claude models
            "claude-sonnet-4.5": "claude-sonnet-4-5-20250929",
            "claude-opus-4.1": "claude-opus-4-1-20250805",
            "claude-haiku-4.5": "claude-haiku-4-5-20251001",
            "claude-3.5-sonnet": "claude-sonnet-4-20250514",
            # Gemini 3 models - map to model_name (without gemini/ prefix)
            "gemini-3-flash-preview": "gemini-3-flash-preview",
            "gemini/gemini-3-flash-preview": "gemini-3-flash-preview",
            "gemini-3-pro-preview": "gemini-3-pro-preview",
            "gemini/gemini-3-pro-preview": "gemini-3-pro-preview",
            # Gemini 2.5 models - map to model_name (without gemini/ prefix)
            "gemini-2.5-pro": "gemini-2.5-pro",
            "gemini/gemini-2.5-pro": "gemini-2.5-pro",
            "gemini-2.5-flash": "gemini-2.5-flash",
            "gemini/gemini-2.5-flash": "gemini-2.5-flash",
            "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
            "gemini/gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
            # Legacy Gemini model names
            "gemini-3.0-pro": "gemini-3-pro-preview",
        }

        # Prepare override parameters if user selected a model
        override_params = None
        if model and model in model_mapping:
            litellm_model = model_mapping[model]
            override_params = {'model': litellm_model}
            logger.info(f"Using user-selected model: {model} → {litellm_model}")
        elif model:
            # User selected a model but it's not in mapping - LOG WARNING
            logger.warning(f"Model '{model}' not found in model_mapping, falling back to task default")

        # Call LLM
        task_type = 'paper_tag_suggestion_gpt5' if not model else 'paper_tag_suggestion_deep'
        llm_response = await llm_manager.completion(
            task_type=task_type,
            messages=messages,
            user_id='default',
            override_params=override_params
        )

        result = llm_response.choices[0].message.content
        model_used = llm_response.model

        logger.info(f"LLM response from {model_used}: {len(result)} chars")
        logger.debug(f"Raw LLM response: {result[:500]}")

        # Parse JSON response - handle cases where LLM returns text before JSON
        import json
        import re
        try:
            llm_tags = json.loads(result)
            if not isinstance(llm_tags, list):
                logger.error(f"LLM returned non-list response: {type(llm_tags)}")
                llm_tags = []
        except json.JSONDecodeError as je:
            # Try to extract JSON array from response text
            logger.warning(f"Direct JSON parse failed, attempting extraction: {je}")
            json_match = re.search(r'\[[\s\S]*\]', result)
            if json_match:
                try:
                    llm_tags = json.loads(json_match.group())
                    logger.info(f"Successfully extracted JSON array from response")
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse extracted JSON: {result[:200]}")
                    llm_tags = []
            else:
                logger.error(f"No JSON array found in response: {result[:200]}")
                llm_tags = []

        # Filter out tags that already exist or are already tagged
        already_tagged_names = {t.lower() for t in already_tagged}
        existing_suggestion_names = {s['display_name'].lower() for s in existing_suggestions}

        for tag in llm_tags:
            tag_lower = tag.lower()
            if tag_lower not in already_tagged_names and tag_lower not in existing_suggestion_names:
                # It's a genuinely new suggestion from LLM
                new_suggestions.append({
                    'display_name': tag,
                    'slug': tag.lower().replace(' ', '-'),
                    'is_new': True
                })

        logger.info(f"Generated {len(new_suggestions)} new tag suggestions for paper {paper_id}")

    except Exception as e:
        logger.error(f"Failed to generate LLM tag suggestions: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Continue without LLM suggestions
    
    return {
        "existing_suggestions": existing_suggestions,
        "new_suggestions": new_suggestions,
        "already_tagged": already_tagged
    }

@router.post("/{paper_id}/tags/suggest")
async def suggest_tags_for_paper(paper_id: str, request: dict = Body({})):
    """Get AI-powered concept suggestions for a paper (POST endpoint with model selection)"""
    # Extract model from request body
    model = request.get('model', None)
    logger.info(f"Tag suggestion requested for paper {paper_id} with model: {model}")
    return await get_tag_suggestions(paper_id, model=model)

@router.post("/{paper_id}/entities/extract")
def extract_paper_entities(paper_id: str, use_fast_model: bool = False, model_choice: str = None):
    """Extract entities from paper content using AI"""
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get content from paper - try content field first, then sections
    content_text = paper.get('content', '')
    
    # If no content, try to extract from sections
    if not content_text and paper.get('sections'):
        sections_content = []
        for section in paper['sections']:
            if section.get('content'):
                sections_content.append(f"## {section.get('title', 'Section')}\n{section['content']}")
        content_text = '\n\n'.join(sections_content)
    
    if not content_text:
        raise HTTPException(status_code=400, detail="Paper has no content to analyze")
    
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from app.services.entity_extraction_service import EntityExtractionService
        
        # Initialize service with model choice
        service = EntityExtractionService(use_fast_model=use_fast_model, model_choice=model_choice)
        
        # Prepare full paper content for analysis
        paper_text = f"""
Title: {paper.get('title', 'Unknown')}

Abstract: {paper.get('abstract', 'No abstract available')}

Authors: {paper.get('authors', 'Unknown')}

Full Paper Content:
{content_text}
"""
        
        logger.info(f"Extracting entities from paper {paper_id} with {len(paper_text)} characters")
        
        # Extract entities using full paper content
        entities = service.extract_entities(text=paper_text, article_id=None)
        
        # Convert to response format
        entity_suggestions = [
            {
                "id": entity.id,
                "text": entity.text,
                "type": entity.entity_type,
                "confidence": entity.confidence,
                "context": entity.context,
                "normalized": entity.normalized,
                "metadata": entity.metadata
            }
            for entity in entities
        ]
        
        # Calculate statistics
        stats = {
            "total_entities": len(entities),
            "entity_types": {},
            "confidence_distribution": {
                "high": 0,
                "medium": 0, 
                "low": 0
            }
        }
        
        for entity in entities:
            # Count by type
            if entity.entity_type not in stats["entity_types"]:
                stats["entity_types"][entity.entity_type] = 0
            stats["entity_types"][entity.entity_type] += 1
            
            # Count by confidence level
            if entity.confidence >= 0.8:
                stats["confidence_distribution"]["high"] += 1
            elif entity.confidence >= 0.6:
                stats["confidence_distribution"]["medium"] += 1
            else:
                stats["confidence_distribution"]["low"] += 1
        
        return {
            "entities": entity_suggestions,
            "stats": stats,
            "model": service.model_name,
            "paper_title": paper.get('title', f'Paper {paper_id}'),
            "paper_id": paper_id
        }
        
    except Exception as e:
        logger.error(f"Error extracting entities from paper {paper_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entities/schema")  
def get_entities_schema():
    """Get entity extraction schema from the entity extraction service"""
    try:
        from app.services.entity_extraction_service import EntityExtractionService
        
        # Initialize service to get schema
        service = EntityExtractionService(use_fast_model=False)
        
        # Get entity types from service configuration
        entity_types = {}
        for entity_type, config in service.valid_entity_types.items():
            entity_types[entity_type] = {
                "description": config['display_name'],
                "color": config['color'],
                "icon": config.get('icon', '🏷️'),
                "slug": config['slug'],
                "parent_category": config['parent_category'],
                "validation_rules": config.get('validation_rules', {}),
                "extraction_hints": config.get('extraction_hints', [])
            }
        
        return {
            "entity_types": entity_types,
            "confidence_levels": ["high", "medium", "low"],
            "model": service.model_name,
            "extraction_config": service.extraction_config
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting entities schema: {e}")
        
        # Fallback to basic schema
        return {
            "entity_types": {
                "PERSON": {"description": "Person names", "color": "#ff6b6b", "icon": "👤"},
                "ORG": {"description": "Organizations", "color": "#4ecdc4", "icon": "🏢"},
                "TECH": {"description": "Technologies", "color": "#45b7d1", "icon": "⚙️"},
                "CONCEPT": {"description": "Concepts", "color": "#96ceb4", "icon": "💡"}
            },
            "confidence_levels": ["high", "medium", "low"],
            "model": "fallback",
            "error": str(e)
        }

@router.post("/{paper_id}/extract-affiliations")
def extract_paper_affiliations(paper_id: str):
    """Extract author affiliations from paper header using LLM"""
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get existing authors - handle both string and array formats
    authors_raw = paper.get('authors', [])
    if not authors_raw:
        raise HTTPException(status_code=400, detail="Paper has no authors to extract affiliations for")
    
    # Parse authors if they're a string
    if isinstance(authors_raw, str):
        # Split by comma and clean up
        authors = [{'name': name.strip()} for name in authors_raw.split(',') if name.strip()]
    elif isinstance(authors_raw, list):
        # Already in list format
        authors = authors_raw
    else:
        authors = []
    
    # Get paper header text (title to abstract)
    title = paper.get('title', '')
    abstract = paper.get('abstract', '')
    
    # Try to get the beginning of the content if available
    header_text = f"Title: {title}\n\n"
    
    # Look for the first section or content before abstract
    if paper.get('sections'):
        # Get content from the first few sections (likely contains author info)
        for section in paper['sections'][:3]:  # Check first 3 sections
            section_content = section.get('content', '')
            if section_content:
                header_text += f"{section.get('title', '')}\n{section_content[:2000]}\n\n"
                break
    elif paper.get('content'):
        # Get first 2000 characters of content
        header_text += paper['content'][:2000] + "\n\n"
    
    header_text += f"Abstract: {abstract}"
    
    # Prepare authors list for the prompt
    authors_list = []
    for i, author in enumerate(authors):
        if isinstance(author, dict):
            name = author.get('name', f'Author {i+1}')
            current_affiliation = author.get('affiliation', 'Not specified')
            authors_list.append(f"{i+1}. {name} (Current affiliation: {current_affiliation})")
        else:
            authors_list.append(f"{i+1}. {author} (Current affiliation: Not specified)")
    
    authors_text = '\n'.join(authors_list)
    
    try:
        from app.services.llm_service import LLMService
        import json
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Initialize LLM service
        llm_service = LLMService()
        
        # Use the paper_affiliation_extraction prompt from prompts_config.json
        # The generate_with_model method is async, but we can use generate_completion directly
        # First, get the prompt configuration
        prompt_config = llm_service.prompts.get('paper_affiliation_extraction')
        if not prompt_config:
            raise ValueError("paper_affiliation_extraction prompt not found in prompts_config.json")
        
        # Get model config
        model_config = llm_service.llm_config['models'].get('paper_affiliation_extraction')
        if not model_config:
            raise ValueError("paper_affiliation_extraction model not found in llm.json")
        
        # Format the prompt
        system_prompt = prompt_config.get('system', '')
        user_template = prompt_config.get('user_template', '')
        
        # Format user prompt with context
        user_prompt = user_template.format(
            authors_list=authors_text,
            header_text=header_text
        )
        
        # Combine system and user prompts
        full_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
        
        # Generate response using the configured model
        prompt_response = llm_service.generate_completion(
            prompt=full_prompt,
            model=model_config.get('model'),
            temperature=model_config.get('temperature', 0.1),
            max_tokens=model_config.get('max_tokens', 2000)
        )
        
        logger.info(f"LLM response for affiliation extraction: {prompt_response}")
        
        # Parse the JSON response
        try:
            affiliations_data = json.loads(prompt_response)
        except json.JSONDecodeError:
            # Try to extract JSON from the response if it's wrapped in text
            import re
            json_match = re.search(r'\{.*\}', prompt_response, re.DOTALL)
            if json_match:
                affiliations_data = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse LLM response as JSON")
        
        # Format the response for the UI
        suggestions = []
        for affiliation in affiliations_data.get('affiliations', []):
            author_index = affiliation.get('author_index', 0) - 1  # Convert to 0-based index
            if 0 <= author_index < len(authors):
                author_name = authors[author_index].get('name', authors[author_index]) if isinstance(authors[author_index], dict) else authors[author_index]
                suggestions.append({
                    'author_index': author_index,
                    'author_name': author_name,
                    'suggested_affiliation': affiliation.get('affiliation', ''),
                    'confidence': affiliation.get('confidence', 'medium'),
                    'current_affiliation': authors[author_index].get('affiliation', '') if isinstance(authors[author_index], dict) else ''
                })
        
        return {
            'paper_id': paper_id,
            'paper_title': title,
            'suggestions': suggestions,
            'model_used': model_config  # Return the model config directly
        }
        
    except Exception as e:
        logger.error(f"Error extracting affiliations for paper {paper_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{paper_id}/apply-affiliations")
def apply_paper_affiliations(paper_id: str, affiliations_data: dict):
    """Apply selected affiliations to paper authors"""
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get affiliations to apply
    affiliations_to_apply = affiliations_data.get('affiliations', [])
    
    # Get existing authors and convert to list format if needed
    authors_raw = paper.get('authors', [])
    
    # Parse authors if they're a string
    if isinstance(authors_raw, str):
        # Split by comma and convert to dict format
        authors = [{'name': name.strip()} for name in authors_raw.split(',') if name.strip()]
    elif isinstance(authors_raw, list):
        # Already in list format, ensure they're dicts
        authors = []
        for author in authors_raw:
            if isinstance(author, dict):
                authors.append(author)
            else:
                authors.append({'name': str(author)})
    else:
        authors = []
    updated_count = 0
    
    for affiliation in affiliations_to_apply:
        author_index = affiliation.get('author_index')
        new_affiliation = affiliation.get('affiliation')
        
        if author_index is not None and 0 <= author_index < len(authors):
            if isinstance(authors[author_index], dict):
                authors[author_index]['affiliation'] = new_affiliation
            else:
                # Convert string author to dict format
                authors[author_index] = {
                    'name': authors[author_index],
                    'affiliation': new_affiliation
                }
            updated_count += 1
    
    # Update the paper in the database
    if len(paper_id) == 24:
        db.papers.update_one(
            {'_id': ObjectId(paper_id)},
            {'$set': {'authors': authors}}
        )
    else:
        db.papers.update_one(
            {'old_sqlite_id': int(paper_id)},
            {'$set': {'authors': authors}}
        )
    
    return {
        'paper_id': paper_id,
        'updated_count': updated_count,
        'authors': authors
    }

@router.post("/{paper_id}/entities/bulk-action")
def bulk_action_entities(paper_id: str, action_data: dict):
    """Perform bulk actions on entities (accept_all or reject_all)"""
    try:
        entity_ids = action_data.get('entity_ids', [])
        action = action_data.get('action', 'accept_all')
        entities = action_data.get('entities', [])
        
        if not entity_ids:
            raise HTTPException(status_code=400, detail="No entity IDs provided")
            
        processed_entities = []
        
        if action == 'accept_all':
            # Process accepted entities - add them to the concept hierarchy
            from app.services.concept_only_tag_service import ConceptOnlyTagService
            concept_service = ConceptOnlyTagService()
            
            for entity in entities:
                entity_name = entity.get('text', '')
                entity_type = entity.get('type', '')
                
                if entity_name and entity_type:
                    try:
                        # Find the appropriate parent concept for this entity type
                        parent_concept_id = f"c_et_{entity_type.replace('-', '_')}"
                        
                        # Add as a new concept under the appropriate entity type
                        concept_id = concept_service.add_concept(
                            display_name=entity_name,
                            description=f"Extracted {entity_type} from paper {paper_id}",
                            parent_ids=[parent_concept_id] if parent_concept_id else [],
                            entity_type=entity_type
                        )
                        
                        processed_entities.append({
                            'entity_name': entity_name,
                            'entity_type': entity_type,
                            'concept_id': concept_id,
                            'status': 'accepted'
                        })
                        
                    except Exception as e:
                        processed_entities.append({
                            'entity_name': entity_name,
                            'entity_type': entity_type,
                            'error': str(e),
                            'status': 'failed'
                        })
                        
        elif action == 'reject_all':
            # Process rejected entities - store for future improvement
            for entity in entities:
                processed_entities.append({
                    'entity_name': entity.get('text', ''),
                    'entity_type': entity.get('type', ''),
                    'status': 'rejected'
                })
                
            # TODO: Store rejected entities in a collection for ML improvement
            
        return {
            "message": f"Bulk {action} completed",
            "processed_count": len(processed_entities),
            "successful": len([e for e in processed_entities if e.get('status') in ['accepted', 'rejected']]),
            "failed": len([e for e in processed_entities if e.get('status') == 'failed']),
            "entities": processed_entities
        }
        
    except Exception as e:
        logger.error(f"Error performing bulk action on entities for paper {paper_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/entities/extract")
async def extract_entities_from_text(data: Dict[str, Any] = Body(...)):
    """Extract entities from any text using LLM with concept model"""
    import json
    from pathlib import Path
    from app.services.llm_service import LLMService
    
    try:
        # Debug logging to understand the data format
        logger.info(f"Received data keys: {list(data.keys())}")
        logger.info(f"Data type: {type(data)}")
        
        text = data.get('text', '')
        content_type = data.get('content_type', 'general')
        
        if not text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        # Load prompts from configuration
        prompts_path = Path(__file__).parent.parent.parent / 'prompts_config.json'
        if prompts_path.exists():
            with open(prompts_path, 'r') as f:
                prompts_config = json.load(f)
                entity_prompts = prompts_config.get('entity_extraction', {})
        else:
            entity_prompts = {}
        
        # Get system and extraction prompts
        system_prompt = entity_prompts.get('system', """You are an expert at extracting named entities and concepts from text.
Extract all relevant entities including people, organizations, locations, technologies, concepts, and research topics.
Return the results as a JSON array where each item has: text, type, confidence (0-1), and context.""")
        
        extraction_prompt = entity_prompts.get('extraction_prompt', """Extract all named entities and key concepts from the following text.

Categories to identify:
- person: People's names
- organisation: Companies, institutions, research groups
- location: Places, countries, cities
- technology: Specific technologies, frameworks, models
- concept: Abstract concepts, theories, methodologies
- research_topic: Research areas and topics
- product: Products, tools, services
- event: Conferences, meetings, dates

Text to analyze:
{text}

Return a JSON array with extracted entities. Each entity should have:
- text: The entity text as it appears
- type: One of the categories above
- confidence: Confidence score between 0 and 1
- context: Brief context about the entity

Example format:
[
    {"text": "OpenAI", "type": "organisation", "confidence": 0.95, "context": "AI research company"},
    {"text": "GPT-4", "type": "technology", "confidence": 0.9, "context": "Large language model"}
]""")
        
        # Use LLMService with entity extraction model
        llm_service = LLMService()
        
        # Format the prompt - handle potential template errors
        try:
            prompt = extraction_prompt.format(text=text[:5000])  # Limit text length
        except KeyError:
            # Fallback if the prompt template has issues
            prompt = f"""Extract all named entities and key concepts from the following text.

Text to analyze:
{text[:5000]}

Return a JSON array with extracted entities. Each entity should have:
- text: The entity text as it appears
- type: One of: person, organisation, location, technology, concept, research_topic, product, event
- confidence: Confidence score between 0 and 1
- context: Brief context about the entity"""
        
        # Combine system and user prompts into a single prompt
        full_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Get LLM response - use model from llm.json if configured
        model = 'gpt-4o-mini'  # Default model
        llm_config_path = Path(__file__).parent.parent.parent / 'llm.json'
        if llm_config_path.exists():
            with open(llm_config_path, 'r') as f:
                llm_config = json.load(f)
                # Check for entity extraction model configuration
                if 'models' in llm_config and 'entity_extraction' in llm_config['models']:
                    model = llm_config['models']['entity_extraction'].get('model', model)
        
        response = llm_service.generate_completion(
            prompt=full_prompt,
            model=model,
            max_tokens=2000,
            temperature=0.1
        )
        
        # Parse the response
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                entities = json.loads(json_match.group())
            else:
                # Fallback: try parsing the entire response
                entities = json.loads(response)
        except:
            # If JSON parsing fails, return empty list
            logger.warning(f"Failed to parse entity extraction response as JSON")
            entities = []
        
        # Convert to concept model format
        concepts = []
        for entity in entities:
            # Create concept-compatible structure
            concept = {
                "id": hashlib.md5(f"{entity['text']}:{entity['type']}".encode()).hexdigest()[:12],
                "text": entity['text'],
                "type": entity['type'],
                "confidence": entity.get('confidence', 0.8),
                "context": entity.get('context', ''),
                "normalized": entity['text'].strip().replace(" ", "-").replace("_", "-"),
                "is_concept": True
            }
            concepts.append(concept)
        
        return {
            "success": True,
            "entities": concepts,
            "count": len(concepts),
            "model_used": model  # Use the model variable we already have
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Error extracting entities: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {str(e)}")

@router.post("/entities/review")
def review_entity(entity_data: dict):
    """Review and accept/reject entity suggestions"""
    try:
        entity_id = entity_data.get('entity_id')
        action = entity_data.get('action')  # 'accept' or 'reject'
        new_type = entity_data.get('new_type')  # optional type override
        
        if not entity_id or not action:
            raise HTTPException(status_code=400, detail="Missing entity_id or action")
        
        if action == 'accept':
            # For MongoDB, we could store accepted entities in a collection
            # For now, just return success - in a full implementation, 
            # we'd store this in a reviewed_entities collection
            
            # TODO: Store accepted entities in MongoDB collection for future reference
            return {
                "success": True,
                "message": f"Entity {entity_id} accepted",
                "action": action,
                "entity_id": entity_id,
                "new_type": new_type
            }
            
        elif action == 'reject':
            # Store rejected entities to improve future extractions
            return {
                "success": True, 
                "message": f"Entity {entity_id} rejected",
                "action": action,
                "entity_id": entity_id
            }
        else:
            raise HTTPException(status_code=400, detail="Action must be 'accept' or 'reject'")
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error reviewing entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{paper_id}")
def delete_paper(paper_id: str):
    """Delete a paper and all associated data"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    paper_id_str = str(paper['_id'])
    sqlite_id_str = str(paper.get('old_sqlite_id', ''))
    
    # Delete associated tag instances
    db.tag_instances.delete_many({
        'content_type': 'paper',
        '$or': [
            {'content_id': paper_id_str},
            {'content_id': sqlite_id_str}
        ]
    })
    
    # Delete the paper
    result = db.papers.delete_one({'_id': paper['_id']})
    
    if result.deleted_count > 0:
        logger.info(f"Deleted paper {paper_id_str}")
        return {"success": True, "message": "Paper deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete paper")

@router.get("/{paper_id}/snippets")
def get_paper_snippets(paper_id: str):
    """Get paper snippets from MongoDB"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Return snippets (if stored in MongoDB) with ObjectId conversion for safety
    snippets = paper.get('snippets', [])
    
    # Convert any ObjectIds to strings in snippets
    for snippet in snippets:
        if isinstance(snippet, dict):
            for key, value in snippet.items():
                if isinstance(value, ObjectId):
                    snippet[key] = str(value)
    
    return snippets

@router.get("/{paper_id}/sections")
def get_paper_sections(paper_id: str):
    """Get paper sections from MongoDB"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Return sections with ObjectId conversion for safety
    sections = paper.get('sections', [])
    
    # Convert any ObjectIds to strings in sections
    for section in sections:
        if isinstance(section, dict):
            for key, value in section.items():
                if isinstance(value, ObjectId):
                    section[key] = str(value)
    
    return sections

@router.put("/{paper_id}/sections/{section_id}")
def update_paper_section(paper_id: str, section_id: int, request: dict):
    """Update a paper section's title or content"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    sections = paper.get('sections', [])
    section_found = False
    
    # Update the specific section
    for i, section in enumerate(sections):
        if section.get('id') == section_id:
            if 'title' in request:
                # Clean up the title - remove leading numbers
                import re
                clean_title = re.sub(r'^\d+\.?\s*', '', request['title'])
                sections[i]['title'] = clean_title
            if 'content' in request:
                sections[i]['content'] = request['content']
            section_found = True
            break
    
    if not section_found:
        raise HTTPException(status_code=404, detail="Section not found")
    
    # Update the paper with the modified sections
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'sections': sections}}
    )
    
    return {"success": True, "message": "Section updated successfully"}

@router.get("/{paper_id}/references")
def get_paper_references(paper_id: str):
    """Get extracted references for a paper from MongoDB"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    references = paper.get('references', [])
    
    # Convert any ObjectIds to strings in references for safety
    for ref in references:
        if isinstance(ref, dict):
            for key, value in ref.items():
                if isinstance(value, ObjectId):
                    ref[key] = str(value)
    
    return {
        'paper_id': paper_id,
        'paper_title': paper.get('title', ''),
        'total_references': len(references),
        'references': references
    }

@router.get("/{paper_id}/tei")
def get_paper_tei_xml(paper_id: str):
    """Get the TEI XML for a paper from GROBID processing"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
            if paper:
                # For old SQLite IDs, look for TEI with the original ID
                paper_id = str(paper.get('old_sqlite_id', paper_id))
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check if TEI XML is stored in MongoDB
    if paper.get('tei_xml'):
        from fastapi.responses import Response
        return Response(
            content=paper['tei_xml'],
            media_type="application/xml",
            headers={
                "Content-Disposition": f"inline; filename=paper_{paper_id}_tei.xml"
            }
        )
    
    # Check if GROBID was attempted but failed
    if paper.get('grobid_processed') and not paper.get('tei_xml'):
        # Return a minimal TEI structure to prevent frontend errors
        from fastapi.responses import Response
        minimal_tei = f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc>
            <titleStmt>
                <title>{paper.get('title', 'Untitled')}</title>
            </titleStmt>
            <publicationStmt>
                <note>GROBID processing failed or incomplete. TEI XML not available.</note>
            </publicationStmt>
        </fileDesc>
    </teiHeader>
    <text>
        <body>
            <p>TEI content unavailable. The GROBID service may be temporarily unavailable.</p>
        </body>
    </text>
</TEI>"""
        return Response(
            content=minimal_tei,
            media_type="application/xml",
            headers={
                "Content-Disposition": f"inline; filename=paper_{paper_id}_tei_minimal.xml",
                "X-TEI-Status": "minimal"
            }
        )
    
    # Fall back to filesystem (legacy support)
    import os
    
    # Get the old SQLite ID for TEI file lookup
    old_id = paper.get('old_sqlite_id')
    if not old_id:
        # TEI XML is not available for papers without SQLite ID or tei_xml field
        # Return 204 No Content instead of 404 to prevent frontend errors
        from fastapi.responses import Response
        return Response(status_code=204)
    
    # Try different naming patterns
    tei_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'tei_xml')
    possible_files = [
        os.path.join(tei_dir, f"paper_{old_id}_tei.xml"),
        os.path.join(tei_dir, f"paper_{old_id}.xml"),
        os.path.join(tei_dir, f"{old_id}.xml")
    ]
    
    tei_path = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            tei_path = file_path
            break
    
    if not tei_path:
        raise HTTPException(
            status_code=404, 
            detail=f"TEI XML file not found for paper {old_id}. Tried: {', '.join(possible_files)}"
        )
    
    # Read and return TEI XML
    try:
        with open(tei_path, 'r', encoding='utf-8') as f:
            tei_xml = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading TEI XML: {e}")
    
    from fastapi.responses import Response
    return Response(
        content=tei_xml,
        media_type="application/xml",
        headers={
            "Content-Disposition": f"inline; filename=paper_{paper_id}.tei.xml"
        }
    )

@router.get("/{paper_id}/images/{image_path:path}")
def get_paper_image(
    paper_id: str,
    image_path: str
):
    """Serve an image for a specific paper"""
    from fastapi.responses import FileResponse
    import os
    from pathlib import Path
    
    logger.info(f"=== IMAGE REQUEST DEBUG ===")
    logger.info(f"Paper ID: {paper_id}")
    logger.info(f"Image path requested: {image_path}")
    
    # Get the paper to find its processor and image directory
    paper = None  # Initialize paper variable first
    try:
        # Try to convert to ObjectId if it's a valid format (24 hex chars)
        if len(paper_id) == 24:
            try:
                paper = db.papers.find_one({'_id': ObjectId(paper_id)})
                logger.info(f"Found paper by ObjectId: {paper is not None}")
            except:
                # Not a valid ObjectId, try as old SQLite ID
                paper = None
        
        # If not found by ObjectId, try as old SQLite ID (integer)
        if paper is None:
            try:
                paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
                logger.info(f"Found paper by SQLite ID {paper_id}: {paper is not None}")
            except:
                logger.warning(f"Could not parse {paper_id} as integer for SQLite ID")
                paper = None
        
        # If still not found, this might be a converted MongoDB ID (like 4245617128)
        # Search for papers where this could be the converted ID
        if paper is None and paper_id.isdigit():
            # This could be a paper where we converted the last 8 hex chars to int
            # We need to find papers where int(str(_id)[-8:], 16) == int(paper_id)
            # This is expensive, so we'll do a targeted search
            logger.info(f"Searching for paper with converted ID {paper_id}")
            
            # Get all papers and check their converted IDs
            for p in db.papers.find({}, {'_id': 1, 'title': 1, 'processor_used': 1}):
                mongo_id = str(p['_id'])
                converted_id = int(mongo_id[-8:], 16)
                if converted_id == int(paper_id):
                    logger.info(f"Found paper by converted ID! MongoDB ID: {mongo_id}, converted: {converted_id}")
                    paper = db.papers.find_one({'_id': p['_id']})
                    break
                    
    except Exception as e:
        logger.error(f"Error finding paper: {e}")
        paper = None
    
    if not paper:
        logger.error(f"Paper not found for ID: {paper_id}")
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Determine base path based on processor
    processor = paper.get('processor_used', 'marker')
    logger.info(f"Processor used: {processor}")
    logger.info(f"Paper title: {paper.get('title', 'N/A')}")
    
    # Check if this is an old paper with SQLite ID (needed for all processors)
    old_sqlite_id = paper.get('old_sqlite_id')
    logger.info(f"Old SQLite ID: {old_sqlite_id}")
    
    if processor == 'marker' or processor == 'marker_service':
        # Check if we have the marker session ID stored (for old papers)
        marker_metadata = paper.get('marker_metadata', {})
        logger.info(f"Marker metadata: {marker_metadata}")
        session_id = marker_metadata.get('session_id')
        logger.info(f"Session ID: {session_id}")
        
        # Determine which ID to use for ImageManager
        if old_sqlite_id is not None:
            # This is an old paper migrated from SQLite
            # Images are stored under the old SQLite ID
            paper_id_for_images = old_sqlite_id
            logger.info(f"Using old SQLite ID for images: {paper_id_for_images}")
        else:
            # This is a new paper created after MongoDB migration
            # Convert MongoDB ObjectId to integer for ImageManager
            if len(paper_id) == 24:
                # MongoDB ObjectId - convert to a stable integer
                # Use last 8 hex chars converted to int for uniqueness (same as when calling Marker)
                paper_id_for_images = int(paper_id[-8:], 16)
            else:
                paper_id_for_images = int(paper_id)
            logger.info(f"Using converted MongoDB ID for images: {paper_id_for_images}")
        
        # Check ImageManager's hierarchical structure
        id_str = str(paper_id_for_images).zfill(6)  # Pad to 6 digits
        image_manager_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "data" / "paper_images" / id_str[:2] / id_str[2:4] / id_str[4:]
        logger.info(f"Checking ImageManager path: {image_manager_path}")
        logger.info(f"ImageManager path exists: {image_manager_path.exists()}")
        
        if image_manager_path.exists():
            # Use ImageManager's location
            base_path = image_manager_path
            logger.info(f"Using ImageManager path: {base_path}")
        elif session_id:
            # Fall back to old session-based directory
            # Use the specific session directory
            marker_base = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "marker_service" / "debug_runs" / session_id
            logger.info(f"Marker base path: {marker_base}")
            logger.info(f"Marker base exists: {marker_base.exists()}")
            
            # Find the subdirectory containing the images
            if marker_base.exists():
                # Look for subdirectories
                subdirs = [d for d in marker_base.iterdir() if d.is_dir()]
                logger.info(f"Found {len(subdirs)} subdirectories: {[str(d.name) for d in subdirs]}")
                if subdirs:
                    # Use the first (and likely only) subdirectory
                    base_path = subdirs[0]
                    logger.info(f"Using subdirectory: {base_path}")
                else:
                    base_path = marker_base
                    logger.info(f"No subdirs, using marker base: {base_path}")
            else:
                # Fallback: try ImageManager path anyway
                base_path = image_manager_path
                logger.warning(f"Session directory not found, using ImageManager path")
        else:
            # No session ID stored, use ImageManager path
            base_path = image_manager_path
            logger.info(f"No session ID in metadata, using ImageManager path: {base_path}")
    elif processor == 'mineru' or processor == 'mineru_service':
        # MinerU uses ImageManager to save images in the same structure as Marker
        # Images are saved in data/paper_images/XX/YY/ZZZZZZ/ format
        logger.info(f"Processing MinerU image, original image_path: {image_path}")
        
        # First, check if this is a hierarchical path (e.g., "42/45/617126/figure_0_8dede0da.jpg")
        if "/" in image_path and image_path.count("/") >= 3:
            # This looks like a hierarchical path with the ID structure
            # Extract the hierarchical ID from the path
            path_parts = image_path.split("/")
            logger.info(f"Path parts: {path_parts}")
            
            if len(path_parts) >= 4:  # Should be XX/YY/ZZZZZZ/filename.ext
                hierarchical_id = "/".join(path_parts[:3])  # "42/45/617126"
                filename = "/".join(path_parts[3:])  # "figure_0_8dede0da.jpg"
                base_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "data" / "paper_images" / hierarchical_id
                # Update image_path to just the filename for later processing
                image_path = filename
                logger.info(f"Using MinerU hierarchical path: {base_path}")
                logger.info(f"Extracted filename: {filename}")
                logger.info(f"Updated image_path to: {image_path}")
            else:
                # Fallback to standard path
                base_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "data" / "paper_images"
                logger.info(f"Using MinerU standard path: {base_path}")
        else:
            # No hierarchy in path, use standard ImageManager location based on paper ID
            # Determine which ID to use for ImageManager
            if old_sqlite_id is not None:
                paper_id_for_images = old_sqlite_id
            else:
                # Convert MongoDB ObjectId to integer for ImageManager
                if len(paper_id) == 24:
                    paper_id_for_images = int(paper_id[-8:], 16)
                else:
                    paper_id_for_images = int(paper_id)
            
            # Check ImageManager's hierarchical structure
            id_str = str(paper_id_for_images).zfill(6)  # Pad to 6 digits
            base_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "data" / "paper_images" / id_str[:2] / id_str[2:4] / id_str[4:]
            logger.info(f"Using MinerU ImageManager path: {base_path}")
    else:
        # Fallback to old paper_images path
        base_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "data" / "paper_images"
        logger.info(f"Using fallback path: {base_path}")
    
    # Now construct the full image path
    # The base_path should already be set correctly above
    # and image_path should be the filename (or relative path within base_path)
    full_image_path = base_path / image_path
    logger.info(f"Trying path: {full_image_path}")
    logger.info(f"Path exists: {full_image_path.exists()}")
    
    # Get the filename for various fallback attempts
    filename = Path(image_path).name
    
    # If not found, try just the filename in the base directory
    if not full_image_path.exists():
        full_image_path = base_path / filename
        logger.info(f"Trying filename only: {full_image_path}")
        logger.info(f"Filename path exists: {full_image_path.exists()}")
    
    # If still not found, check for alternative naming patterns
    if not full_image_path.exists():
        # Try without leading underscore (Marker style names like _page_4_Figure_0.jpeg)
        if filename.startswith('_'):
            alt_filename = filename[1:]
            full_image_path = base_path / alt_filename
            logger.info(f"Trying without underscore: {full_image_path}")
            logger.info(f"Alt path exists: {full_image_path.exists()}")
    
    # For old papers, try the figure_X_hash.jpeg format
    if not full_image_path.exists() and old_sqlite_id is not None:
        # Old papers might have images like figure_0_1c48ce93.jpeg
        # Try to match by pattern
        import re
        # Extract the base name without extension
        base_name = Path(filename).stem
        # Try to find any matching file
        if base_path.exists():
            for file in base_path.iterdir():
                if file.is_file() and base_name in file.name:
                    full_image_path = file
                    logger.info(f"Found matching file by pattern: {full_image_path}")
                    break
    
    # List files in the directory to help debug
    if not full_image_path.exists() and base_path.exists():
        try:
            files_in_dir = list(base_path.glob("*.jpeg")) + list(base_path.glob("*.jpg")) + list(base_path.glob("*.png"))
            logger.info(f"Files in {base_path}: {[f.name for f in files_in_dir[:10]]}")
        except Exception as e:
            logger.error(f"Error listing directory: {e}")
    
    if not full_image_path.exists():
        logger.error(f"Image not found after all attempts: {image_path}")
        logger.error(f"Final path tried: {full_image_path}")
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")
    
    # Determine media type based on file extension
    suffix = full_image_path.suffix.lower()
    media_type_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp'
    }
    media_type = media_type_map.get(suffix, 'application/octet-stream')
    
    # Return the image file
    logger.info(f"=== SERVING IMAGE SUCCESSFULLY ===")
    logger.info(f"Image path: {full_image_path}")
    logger.info(f"Media type: {media_type}")
    logger.info(f"File size: {full_image_path.stat().st_size} bytes")
    
    return FileResponse(
        path=str(full_image_path),
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
        }
    )

@router.post("/{paper_id}/tags")
def add_tags_to_paper(paper_id: str, body: Dict[str, Any]):
    """Add tags to a paper (legacy endpoint, redirects to concepts)"""
    
    # Extract tag from body
    tag = body.get('tag', '')
    if not tag:
        raise HTTPException(status_code=400, detail="Tag is required")
    
    # Redirect to concepts endpoint
    return add_concept_to_paper(paper_id, text=tag)

@router.delete("/{paper_id}/tags/{tag}")
def remove_tag_from_paper(paper_id: str, tag: str):
    """Remove a tag from a paper (legacy endpoint)"""
    
    # For now, just return success
    # In a full implementation, this would map the tag to a concept_id
    return {"message": "Tag removed successfully"}

@router.get("/{paper_id}/pdf")
def get_paper_pdf(paper_id: str):
    """Serve PDF file for a paper"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get PDF path
    pdf_path = paper.get('pdf_path')
    if not pdf_path:
        raise HTTPException(status_code=404, detail="PDF not found for this paper")
    
    # Check if file exists
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        # Try relative to backend directory
        pdf_file = Path(__file__).parent.parent.parent.parent / pdf_path
        if not pdf_file.exists():
            raise HTTPException(status_code=404, detail=f"PDF file not found: {pdf_path}")
    
    # Return PDF file
    return FileResponse(
        path=str(pdf_file),
        media_type="application/pdf",
        filename=pdf_file.name
    )

@router.get("/{paper_id}/analyses/available")
def get_available_analyses(paper_id: str):
    """Get available analysis types for a paper - dynamically loaded from prompts_config.json"""
    
    import json
    import os
    
    # Load analysis types from prompts_config.json
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    with open(os.path.join(backend_dir, 'prompts_config.json'), 'r') as f:
        prompts_config = json.load(f)
    
    paper_analyses = prompts_config.get('paper_analyses', {})
    
    # Build available analyses list from prompts_config
    available_analyses = []
    
    # Icon mapping for different categories
    icon_map = {
        'summaries': '📝',
        'analysis': '💭',
        'review': '📋',
        'reference': '📖'
    }
    
    for analysis_id, config in paper_analyses.items():
        category = config.get('category', 'analysis')
        available_analyses.append({
            "id": analysis_id,
            "name": config.get('name', analysis_id.replace('_', ' ').title()),
            "description": config.get('description', ''),
            "icon": icon_map.get(category, '📊'),
            "category": category
        })
    
    # Sort analyses by category and name for better organization
    available_analyses.sort(key=lambda x: (x.get('category', ''), x.get('name', '')))
    
    # Group analyses by category for frontend
    by_category = {}
    for analysis in available_analyses:
        category = analysis.get('category', 'analysis')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(analysis)
    
    return {"analyses": available_analyses, "by_category": by_category}

@router.get("/{paper_id}/analyses/saved")
def get_saved_analyses(paper_id: str):
    """Get saved analyses for a paper from MongoDB"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get analyses from the paper document
    analyses = paper.get('analyses', [])
    
    # Convert array to object keyed by analysis type (frontend expects this format)
    analyses_dict = {}
    for analysis in analyses:
        # Get the analysis type (handle both field names)
        analysis_type = analysis.get('type') or analysis.get('analysis_type')
        if not analysis_type:
            continue
            
        # Format the analysis for frontend
        analyses_dict[analysis_type] = {
            "success": True,
            "content": analysis.get('content', ''),
            "model": analysis.get('model_used') or analysis.get('model', 'gpt-4o-mini'),
            "created_at": analysis.get('created_at') or analysis.get('generated_at'),
            "metadata": {
                "word_count": analysis.get('word_count'),
                "confidence_score": analysis.get('confidence_score'),
                "version": analysis.get('version')
            }
        }
    
    return {"analyses": analyses_dict}

@router.post("/{paper_id}/analyses")
async def create_analysis(paper_id: str, analysis_type: str = Body(...), regenerate: bool = Body(False), model: str = None):
    """Create a new analysis for a paper using prompts_config.json and llm.json"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check if analysis already exists and not regenerating
    existing_analyses = paper.get('analyses', [])
    existing = next((a for a in existing_analyses if (a.get('type') == analysis_type or a.get('analysis_type') == analysis_type)), None)
    
    if existing and not regenerate:
        return existing
    
    # Import required modules
    from app.services.llm_manager import get_llm_manager
    import json
    import os

    # Load configurations
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    with open(os.path.join(backend_dir, 'prompts_config.json'), 'r') as f:
        prompts_config = json.load(f)

    # Get paper content - use full content for better analysis
    paper_content = paper.get('content', '')
    if not paper_content or len(paper_content) < 100:
        paper_content = f"Title: {paper.get('title', '')}\n\nAbstract: {paper.get('abstract', '')}"

    # Get the appropriate prompt configuration from prompts_config.json
    paper_analyses = prompts_config.get('paper_analyses', {})

    # Get the analysis configuration directly from prompts_config
    # No mapping needed - analysis_type should match the key in prompts_config.json
    analysis_config = paper_analyses.get(analysis_type)

    if not analysis_config:
        # Fallback configuration
        analysis_config = {
            'system': 'You are an expert at analyzing research papers.',
            'user_template': 'Analyze this paper:\n\n{paper_content}'
        }

    # Prepare prompts
    system_prompt = analysis_config.get('system', '')
    user_template = analysis_config.get('user_template', '')
    user_prompt = user_template.replace('{paper_content}', paper_content)

    # Initialize LLM manager (uses LiteLLM)
    llm_manager = get_llm_manager()

    # Build messages in OpenAI format
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    # Determine task type for LiteLLM routing
    if analysis_type in ['review', 'sas_review', 'switt']:
        task_type = 'paper_analysis_deep'
    else:
        task_type = 'paper_analysis'

    # Map frontend model selections to LiteLLM Router model_name (from litellm_config.yaml)
    # IMPORTANT: Values must match model_name in litellm_config.yaml, NOT the full litellm_params.model
    model_mapping = {
        # GPT models (model_name matches frontend value)
        "gpt-5": "gpt-5-2025-08-07",
        "gpt-5.1": "gpt-5.1",
        "gpt-5-mini": "gpt-5-mini",
        "gpt-5-nano": "gpt-5-nano",
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        # Claude models
        "claude-sonnet-4.5": "claude-sonnet-4-5-20250929",
        "claude-opus-4.1": "claude-opus-4-1-20250805",
        "claude-haiku-4.5": "claude-haiku-4-5-20251001",
        "claude-3.5-sonnet": "claude-sonnet-4-20250514",
        # Gemini 3 models - map to model_name (without gemini/ prefix)
        "gemini-3-flash-preview": "gemini-3-flash-preview",
        "gemini/gemini-3-flash-preview": "gemini-3-flash-preview",
        "gemini-3-pro-preview": "gemini-3-pro-preview",
        "gemini/gemini-3-pro-preview": "gemini-3-pro-preview",
        # Gemini 2.5 models - map to model_name (without gemini/ prefix)
        "gemini-2.5-pro": "gemini-2.5-pro",
        "gemini/gemini-2.5-pro": "gemini-2.5-pro",
        "gemini-2.5-flash": "gemini-2.5-flash",
        "gemini/gemini-2.5-flash": "gemini-2.5-flash",
        "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
        "gemini/gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
        # Legacy Gemini model names
        "gemini-3.0-pro": "gemini-3-pro-preview",
    }

    # Prepare override parameters if user selected a specific model
    override_params = None
    if model and model in model_mapping:
        litellm_model = model_mapping[model]
        override_params = {'model': litellm_model}
        logger.info(f"User selected model: {model} → Router model_name: {litellm_model}")
    elif model:
        # User selected a model but it's not in mapping - LOG WARNING
        logger.warning(f"Model '{model}' not found in model_mapping, falling back to task default")

    # Generate the analysis using LiteLLM manager
    # If override_params is set, it will use the user's selected model
    # Otherwise, LiteLLM uses configured routing for the task_type
    try:
        llm_response = await llm_manager.completion(
            task_type=task_type,
            messages=messages,
            user_id='default',
            override_params=override_params
        )
    except Exception as e:
        # If user's selected model fails, fall back to default routing
        if override_params:
            logger.warning(f"User's selected model failed, using default routing: {e}")
            llm_response = await llm_manager.completion(
                task_type=task_type,
                messages=messages,
                user_id='default',
                override_params=None  # Let LiteLLM use default routing
            )
        else:
            raise  # Re-raise if it wasn't a model selection issue

    result = llm_response.choices[0].message.content
    model_name = llm_response.model  # Get actual model used by LiteLLM
    
    # Create analysis object
    analysis = {
        "type": analysis_type,
        "analysis_type": analysis_type,  # Keep both for backwards compatibility
        "content": result,
        "created_at": datetime.utcnow().isoformat(),
        "model": model_name,
        "model_used": model_name,
        "prompt_config": analysis_type  # Use analysis_type as the config key
        # Note: temperature and max_tokens are handled by LiteLLM config
    }
    
    # Update paper with new analysis
    if existing and regenerate:
        # Replace existing analysis
        existing_analyses = [a for a in existing_analyses if not (a.get('type') == analysis_type or a.get('analysis_type') == analysis_type)]
    
    existing_analyses.append(analysis)
    
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'analyses': existing_analyses}}
    )
    
    return analysis

@router.post("/{paper_id}/analyses/generate")
async def generate_analysis(paper_id: str, data: dict = Body(...)):
    """Generate a paper analysis (wrapper for frontend compatibility)"""
    # This is a wrapper endpoint for frontend compatibility
    # It calls the main create_analysis function
    analysis_type = data.get('analysis_type')
    regenerate = data.get('regenerate', False)  # Support regenerate flag from frontend
    model = data.get('model')  # Get model from frontend (LiteLLM handles model routing)

    try:
        analysis = await create_analysis(paper_id, analysis_type, regenerate=regenerate, model=model)
        
        # Wrap the response in the format the frontend expects
        return {
            "success": True,
            "analysis_type": analysis_type,
            "content": analysis.get("content", ""),
            "metadata": analysis.get("metadata", {}),
            "generated_at": analysis.get("generated_at"),
            "model_used": analysis.get("model_used") or analysis.get("model")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/{paper_id}/analyses/generate-multiple")
async def generate_multiple_analyses(paper_id: str, data: dict = Body(...)):
    """Generate multiple analyses for a paper at once"""
    analysis_types = data.get('analysis_types', [])
    model = data.get('model')  # Get model from frontend (LiteLLM handles model routing)

    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get paper content for context
    context = f"Title: {paper.get('title', '')}\n\n"
    if paper.get('abstract'):
        context += f"Abstract: {paper['abstract']}\n\n"
    if paper.get('content'):
        context += f"Content: {paper['content'][:5000]}..."  # Limit to 5000 chars
    
    results = {}
    existing_analyses = paper.get('analyses', [])
    
    # Import LLM service
    from app.services.llm_service import LLMService
    llm_service = LLMService()
    
    # Load configurations for proper prompt handling
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    with open(os.path.join(backend_dir, 'prompts_config.json'), 'r') as f:
        prompts_config = json.load(f)
    with open(os.path.join(backend_dir, 'llm.json'), 'r') as f:
        llm_config = json.load(f)
    
    for analysis_type in analysis_types:
        try:
            # Check if already exists
            existing = next((a for a in existing_analyses if (a.get('type') == analysis_type or a.get('analysis_type') == analysis_type)), None)
            if existing:
                results[analysis_type] = {
                    "success": True,
                    "content": existing.get('content', ''),
                    "model": existing.get('model_used') or existing.get('model', 'gpt-4o-mini'),
                    "created_at": existing.get('created_at') or existing.get('generated_at'),
                    "was_skipped": True
                }
                continue
            
            # Generate new analysis using configuration
            paper_analyses = prompts_config.get('paper_analyses', {})
            
            # Get the analysis configuration directly from prompts_config
            # No mapping needed - analysis_type should match the key in prompts_config.json
            analysis_config = paper_analyses.get(analysis_type, {
                'system': 'You are an expert at analyzing research papers.',
                'user_template': 'Analyze this paper:\\n\\n{paper_content}'
            })
            
            # Use full paper content if available
            paper_content = paper.get('content', '')
            if not paper_content or len(paper_content) < 100:
                paper_content = context
            
            # Prepare prompts
            system_prompt = analysis_config.get('system', '')
            user_template = analysis_config.get('user_template', '')
            user_prompt = user_template.replace('{paper_content}', paper_content)
            
            # Select model from llm.json or use frontend-provided model
            model_key = 'paper_analysis_deep' if analysis_type in ['review', 'sas_review', 'switt'] else 'paper_analysis'
            model_config = llm_config['models'].get(model_key, llm_config['models'].get('paper_analysis'))

            # Prefer frontend-provided model, fall back to config
            model_to_use = model if model else model_config.get('model')

            # Generate analysis
            full_prompt = f"{system_prompt}\\n\\n{user_prompt}" if system_prompt else user_prompt
            result = llm_service.generate_completion(
                prompt=full_prompt,
                max_tokens=model_config.get('max_tokens', 8000),
                temperature=model_config.get('temperature', 0.3),
                model=model_to_use
            )

            # Create analysis object
            analysis = {
                "type": analysis_type,
                "analysis_type": analysis_type,
                "content": result,
                "created_at": datetime.utcnow().isoformat(),
                "model": model_to_use,
                "model_used": model_to_use
            }
            
            existing_analyses.append(analysis)
            
            results[analysis_type] = {
                "success": True,
                "content": result,
                "model": model_config.get('model'),
                "created_at": analysis["created_at"],
                "was_skipped": False
            }
        except Exception as e:
            results[analysis_type] = {
                "success": False,
                "error": str(e)
            }
    
    # Update paper with all new analyses
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'analyses': existing_analyses}}
    )
    
    return {"analyses": results}

@router.post("/{paper_id}/analyses/async")
async def generate_multiple_analyses_async(
    paper_id: str,
    analysis_types: List[str] = Body(..., embed=True),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Start multiple analyses for a paper in background to prevent server blocking"""

    # Generate unique task ID
    task_id = str(uuid.uuid4())

    # Initialize task status
    analysis_tasks[task_id] = {
        "status": "started",
        "progress": 0,
        "results": {},
        "error": None,
        "started_at": datetime.utcnow().isoformat()
    }

    # Start background task
    background_tasks.add_task(run_analysis_in_background, task_id, paper_id, analysis_types)

    return {
        "task_id": task_id,
        "status": "started",
        "message": "Analysis started in background. Use task_id to check progress."
    }

@router.post("/{paper_id}/analyses/free")
async def create_free_analysis(
    paper_id: str,
    data: dict = Body(...)
):
    """Create a free-form analysis with custom user prompt"""
    prompt = data.get('prompt')
    regenerate = data.get('regenerate', False)
    model = data.get('model')  # Get model from frontend
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Import required modules
    from app.services.llm_service import LLMService
    import json
    import os
    from datetime import datetime
    import uuid
    
    # Get paper content
    paper_content = paper.get('content', '')
    if not paper_content or len(paper_content) < 100:
        paper_content = f"Title: {paper.get('title', '')}\n\nAbstract: {paper.get('abstract', '')}"
    
    # Generate a unique ID for this free analysis
    analysis_id = f"free_{uuid.uuid4().hex[:8]}"
    
    # Check if this exact prompt already exists and not regenerating
    free_analyses = paper.get('free_analyses', [])
    existing = next((a for a in free_analyses if a.get('prompt') == prompt), None)
    
    if existing and not regenerate:
        return existing
    
    # Load LLM configuration
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    with open(os.path.join(backend_dir, 'llm.json'), 'r') as f:
        llm_config = json.load(f)
    
    # Use the chat_general model for free-form analysis
    model_config = llm_config.get('models', {}).get('chat_general', {})

    # Prefer frontend-provided model, fall back to config
    model_to_use = model if model else model_config.get('model', 'gemini/gemini-2.5-pro')

    # Map frontend model selections to correct LiteLLM model names
    # Include both key formats (with and without gemini/ prefix) for compatibility
    model_mapping = {
        # Claude models
        "claude-3.5-sonnet": "claude-sonnet-4-20250514",
        "claude-sonnet-4": "claude-sonnet-4-20250514",
        # Gemini 3 models - CORRECT mappings (both key formats)
        "gemini-3-pro": "gemini/gemini-3-pro-preview",
        "gemini-3-flash": "gemini/gemini-3-flash-preview",
        "gemini-3-pro-preview": "gemini/gemini-3-pro-preview",
        "gemini/gemini-3-pro-preview": "gemini/gemini-3-pro-preview",
        "gemini-3-flash-preview": "gemini/gemini-3-flash-preview",
        "gemini/gemini-3-flash-preview": "gemini/gemini-3-flash-preview",
        # Gemini 2.5 models (both key formats)
        "gemini-2.5-pro": "gemini/gemini-2.5-pro",
        "gemini/gemini-2.5-pro": "gemini/gemini-2.5-pro",
        "gemini-2.5-flash": "gemini/gemini-2.5-flash",
        "gemini/gemini-2.5-flash": "gemini/gemini-2.5-flash",
        # GPT models
        "gpt-5.2-thinking": "openai/gpt-5.2",
        "gpt-5.2-pro": "openai/gpt-5.1",
        "gpt-5.2-codex": "openai/gpt-5-nano",
    }
    if model_to_use in model_mapping:
        logger.info(f"Mapped model {model_to_use} → {model_mapping[model_to_use]}")
        model_to_use = model_mapping[model_to_use]
    elif model:
        # User provided a model that's not in mapping - log for debugging
        logger.info(f"Using model directly (no mapping needed): {model_to_use}")

    # Initialize LLM service
    llm_service = LLMService()

    # Create the full prompt with system context
    system_context = "You are an expert at analyzing research papers. Provide detailed, insightful responses to user questions about the paper."
    full_prompt = f"{system_context}\n\nUser question: {prompt}\n\nPaper content:\n{paper_content}"

    # Generate the analysis
    try:
        response = llm_service.generate_completion(
            prompt=full_prompt,
            model=model_to_use,
            max_tokens=model_config.get('max_tokens', 8000),
            temperature=model_config.get('temperature', 0.5)
        )

        # Create the analysis object
        analysis = {
            "id": analysis_id,
            "prompt": prompt,
            "content": response,
            "created_at": datetime.utcnow().isoformat(),
            "model": model_to_use
        }
        
        # Update or add to free_analyses array
        if existing and regenerate:
            # Update existing
            for i, a in enumerate(free_analyses):
                if a.get('prompt') == prompt:
                    free_analyses[i] = analysis
                    break
        else:
            # Add new
            free_analyses.append(analysis)
        
        # Save to database
        db.papers.update_one(
            {'_id': paper['_id']},
            {'$set': {'free_analyses': free_analyses}}
        )
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis: {str(e)}")

@router.get("/{paper_id}/analyses/free")
async def get_free_analyses(paper_id: str):
    """Get all free-form analyses for a paper"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get free analyses and convert ObjectIds for safety
    free_analyses = paper.get('free_analyses', [])
    
    # Convert any ObjectIds to strings in analyses
    for analysis in free_analyses:
        if isinstance(analysis, dict):
            for key, value in analysis.items():
                if isinstance(value, ObjectId):
                    analysis[key] = str(value)
    
    return {"analyses": free_analyses}

@router.put("/{paper_id}/analyses/generated/{analysis_type}")
async def update_generated_analysis(
    paper_id: str,
    analysis_type: str,
    data: dict = Body(...)
):
    """Update the content of a generated analysis (like mollick_summary)"""
    
    content = data.get('content', '')
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get existing analyses - handle both dict and list formats
    analyses = paper.get('analyses', {})
    updated = False
    
    if isinstance(analyses, dict):
        # Dict format - used by the generation endpoint
        if analysis_type not in analyses:
            raise HTTPException(status_code=404, detail=f"Analysis type '{analysis_type}' not found")
        
        # Update the content while preserving other fields
        analyses[analysis_type]['content'] = content
        analyses[analysis_type]['updated_at'] = datetime.utcnow().isoformat()
        updated = True
        
    elif isinstance(analyses, list):
        # List format - handle legacy format
        for analysis in analyses:
            # Check both 'type' and 'analysis_type' fields
            if (analysis.get('type') == analysis_type or 
                analysis.get('analysis_type') == analysis_type):
                analysis['content'] = content
                analysis['updated_at'] = datetime.utcnow().isoformat()
                updated = True
                break
        
        if not updated:
            raise HTTPException(status_code=404, detail=f"Analysis type '{analysis_type}' not found")
    else:
        raise HTTPException(status_code=400, detail="Invalid analyses format")
    
    # Save to database
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'analyses': analyses}}
    )
    
    return {"success": True, "message": f"Analysis '{analysis_type}' updated"}

@router.put("/{paper_id}/analyses/free/{analysis_id}")
async def update_free_analysis(
    paper_id: str,
    analysis_id: str,
    content: str = Body(..., embed=True)
):
    """Update the content of a free-form analysis"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Find and update the analysis
    free_analyses = paper.get('free_analyses', [])
    updated = False
    
    for analysis in free_analyses:
        if analysis.get('id') == analysis_id:
            analysis['content'] = content
            analysis['updated_at'] = datetime.utcnow().isoformat()
            updated = True
            break
    
    if not updated:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Save to database
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'free_analyses': free_analyses}}
    )
    
    return {"success": True, "message": "Analysis updated"}

@router.delete("/{paper_id}/analyses/free/{analysis_id}")
async def delete_free_analysis(paper_id: str, analysis_id: str):
    """Delete a free-form analysis"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Filter out the analysis to delete
    free_analyses = paper.get('free_analyses', [])
    filtered_analyses = [a for a in free_analyses if a.get('id') != analysis_id]
    
    if len(filtered_analyses) == len(free_analyses):
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Save to database
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'free_analyses': filtered_analyses}}
    )
    
    return {"success": True, "message": "Analysis deleted"}

@router.get("/dblp/search")
async def search_dblp(
    title: str = Query(..., description="Paper title to search for"),
    max_results: int = Query(20, ge=1, le=50, description="Maximum number of results")
):
    """Search DBLP for papers by title"""
    from app.services.dblp_service import dblp_service
    
    try:
        if not title or len(title.strip()) < 3:
            raise HTTPException(status_code=400, detail="Title must be at least 3 characters long")
        
        # Search using DBLP service
        results = dblp_service.search_papers(title, max_results)
        
        # Format results for frontend - map dblp_key and dblp_url correctly
        formatted = []
        for result in results:
            formatted.append({
                "title": result.get("title"),
                "authors": result.get("authors", []),
                "author_string": result.get("author_string", ""),
                "year": result.get("year"),
                "venue": result.get("venue"),
                "dblp_key": result.get("dblp_key"),
                "dblp_url": result.get("dblp_url"),
                "pdf_url": result.get("pdf_url"),
                "doi": result.get("doi"),
                "type": result.get("type"),
                "citation_string": result.get("citation_string", "")
            })
        
        return {
            "query": title,
            "count": len(formatted),
            "results": formatted
        }
    except Exception as e:
        logger.error(f"DBLP search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{paper_id}/grobid/process")
async def process_with_grobid(paper_id: str):
    """Process paper with GROBID service"""
    try:
        # Get paper from MongoDB
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check if PDF exists
    pdf_path = paper.get('pdf_path')
    if not pdf_path:
        raise HTTPException(status_code=400, detail="Paper has no PDF file")
    
    # Import GROBID service
    from app.services.grobid_service import GROBIDService
    grobid_service = GROBIDService()
    
    try:
        # Process with GROBID (not async)
        result = grobid_service.process_pdf(pdf_path)
        
        # Extract TEI XML from the result
        tei_xml = None
        if result.get('success') and result.get('full_document', {}).get('tei_xml'):
            tei_xml = result['full_document']['tei_xml']
        
        # Store GROBID data in paper
        update_data = {
            'grobid_metadata': result,
            'grobid_processed': True,
            'grobid_processed_at': datetime.utcnow()
        }
        
        # Store TEI XML if available
        if tei_xml:
            update_data['tei_xml'] = tei_xml
        
        # Store BibTeX if available
        if result.get('metadata', {}).get('bibtex_raw'):
            update_data['bibtex'] = result['metadata']['bibtex_raw']
        
        # Store extracted authors if available
        if result.get('metadata', {}).get('authors'):
            authors = result['metadata']['authors']
            if isinstance(authors, list) and authors:
                # GROBID authors are stored as simple strings, not objects
                author_names = []
                for author in authors:
                    if isinstance(author, dict) and 'name' in author:
                        author_names.append(author['name'])
                    elif isinstance(author, str) and author.strip():
                        author_names.append(author.strip())
                
                if author_names:  # Only update if we have valid author names
                    update_data['authors'] = ', '.join(author_names)  # Store as comma-separated string for compatibility
                    update_data['authors_detailed'] = authors  # Store detailed structure separately
        
        # Store extracted references in dedicated field
        if result.get('references'):
            update_data['references'] = result['references']
        
        # Store extracted sections in dedicated field
        if result.get('sections'):
            update_data['sections'] = result['sections']
        
        # Store citation contexts in dedicated field
        if result.get('citation_contexts'):
            update_data['citation_contexts'] = result['citation_contexts']
        
        db.papers.update_one(
            {'_id': paper['_id']},
            {'$set': update_data}
        )
        
        # Format response for frontend
        response = {
            "success": True,
            "metadata": result,
            "metadata_extracted": bool(result.get('metadata')),
            "references_extracted": len(result.get('references', [])),
            "sections_extracted": len(result.get('sections', [])),
            "citations_extracted": len(result.get('citation_contexts', []))
        }
        
        return response
    except Exception as e:
        logger.error(f"GROBID processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{paper_id}/grobid/metadata")
def get_grobid_metadata(paper_id: str):
    """Get GROBID metadata for a paper"""
    try:
        # Get paper from MongoDB
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    grobid_metadata = paper.get('grobid_metadata')
    if not grobid_metadata:
        return {"success": False, "message": "No GROBID metadata available"}
    
    return {
        "success": True,
        "grobid_metadata": grobid_metadata,
        "metadata": grobid_metadata,
        "metadata_extracted": bool(grobid_metadata.get('metadata')),
        "references_extracted": len(grobid_metadata.get('references', [])),
        "sections_extracted": len(grobid_metadata.get('sections', [])),
        "citations_extracted": len(grobid_metadata.get('citation_contexts', [])),
        "processed_at": paper.get('grobid_processed_at')
    }

@router.put("/{paper_id}/metadata")
def update_paper_metadata(paper_id: str, metadata: dict):
    """Update paper metadata with selected fields"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Update only the provided fields
    update_data = {}
    
    # Handle each field that might be updated
    if 'title' in metadata:
        update_data['title'] = metadata['title']
    
    if 'authors' in metadata:
        # Handle both string array and object array formats
        if metadata['authors'] and isinstance(metadata['authors'][0], str):
            update_data['authors'] = metadata['authors']
        else:
            # Convert author objects to strings if needed
            update_data['authors'] = [
                author['name'] if isinstance(author, dict) else author
                for author in metadata['authors']
            ]
    
    if 'abstract' in metadata:
        update_data['abstract'] = metadata['abstract']
    
    if 'year' in metadata:
        update_data['year'] = int(metadata['year']) if metadata['year'] else None
    
    if 'publication_date' in metadata:
        update_data['publication_date'] = metadata['publication_date']
    
    if 'venue' in metadata:
        update_data['venue'] = metadata['venue']
    
    if 'journal' in metadata:
        update_data['venue'] = metadata['journal']  # Map journal to venue
    
    if 'doi' in metadata:
        update_data['doi'] = metadata['doi']
    
    if 'arxiv_id' in metadata:
        update_data['arxiv_id'] = metadata['arxiv_id']
    
    if 'volume' in metadata:
        update_data['volume'] = metadata['volume']
    
    if 'pages' in metadata:
        update_data['pages'] = metadata['pages']
    
    if 'bibtex' in metadata:
        update_data['bibtex'] = metadata['bibtex']
    
    # Also handle bibtex_raw from GROBID
    if 'bibtex_raw' in metadata:
        update_data['bibtex'] = metadata['bibtex_raw']
    
    # Update the paper
    if update_data:
        db.papers.update_one(
            {'_id': paper['_id']},
            {'$set': update_data}
        )
    
    return {"success": True, "updated_fields": list(update_data.keys())}

@router.patch("/{paper_id}")
def patch_paper_fields(paper_id: str, updates: dict):
    """
    Patch specific paper fields including import_url and import_source
    """
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Prepare update data - only update fields that are provided
    update_data = {}
    
    # Handle import-related fields
    if 'import_url' in updates:
        update_data['import_url'] = updates['import_url']
    
    if 'import_source' in updates:
        update_data['import_source'] = updates['import_source']
    
    # Add timestamp for tracking
    update_data['updated_at'] = datetime.utcnow()
    
    # Update the paper
    if update_data:
        db.papers.update_one(
            {'_id': paper['_id']},
            {'$set': update_data}
        )
        
        return {
            "success": True,
            "message": "Paper updated successfully",
            "updated_fields": list(update_data.keys())
        }
    
    return {
        "success": False,
        "message": "No fields to update"
    }

@router.delete("/{paper_id}/analyses/{analysis_type}")
def delete_analysis(paper_id: str, analysis_type: str):
    """Delete a saved analysis"""
    
    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except:
        paper = None
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Remove analysis from paper - check both type and analysis_type fields
    existing_analyses = paper.get('analyses', [])
    updated_analyses = [a for a in existing_analyses if not (a.get('type') == analysis_type or a.get('analysis_type') == analysis_type)]
    
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'analyses': updated_analyses}}
    )
    
    return {"message": "Analysis deleted successfully"}

@router.get("/stats/overview")
def get_statistics():
    """Get paper statistics from MongoDB"""
    
    # Count papers
    total_papers = db.papers.count_documents({})
    
    # Count papers with PDFs
    papers_with_pdf = db.papers.count_documents({'pdf_path': {'$ne': None}})
    
    # Count unique authors - handle both string and array formats
    all_authors = set()
    
    # Get all papers to process authors
    papers = db.papers.find({}, {'authors': 1, 'authors_detailed': 1})
    for paper in papers:
        # Try authors_detailed first (array of objects or strings)
        if paper.get('authors_detailed'):
            for author in paper['authors_detailed']:
                if isinstance(author, dict) and author.get('name'):
                    all_authors.add(author['name'].strip())
                elif isinstance(author, str) and author.strip():
                    all_authors.add(author.strip())
        # Fall back to authors field (might be string or array)
        elif paper.get('authors'):
            if isinstance(paper['authors'], str):
                # Split comma-separated string
                for author_name in paper['authors'].split(','):
                    all_authors.add(author_name.strip())
            elif isinstance(paper['authors'], list):
                # Handle array of strings or objects
                for author in paper['authors']:
                    if isinstance(author, str):
                        all_authors.add(author.strip())
                    elif isinstance(author, dict) and author.get('name'):
                        all_authors.add(author['name'].strip())
    
    unique_authors = len(all_authors)
    
    # Get date range
    oldest_paper = db.papers.find_one({}, sort=[('publication_date', ASCENDING)])
    newest_paper = db.papers.find_one({}, sort=[('publication_date', DESCENDING)])
    
    # Count concepts
    concepts = concept_service.get_all_concepts_with_counts(content_type='paper')
    
    # Count total snippets across all papers
    snippet_pipeline = [
        {'$unwind': '$snippets'},
        {'$count': 'total'}
    ]
    snippet_count_result = list(db.papers.aggregate(snippet_pipeline))
    total_snippets = snippet_count_result[0]['total'] if snippet_count_result else 0
    
    # Get top conferences
    top_conferences = list(db.papers.aggregate([
        {'$match': {'conference': {'$ne': None}}},
        {'$group': {
            '_id': '$conference',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}},
        {'$limit': 10}
    ]))
    
    return {
        "total_papers": total_papers,
        "papers_with_pdf": papers_with_pdf,
        "unique_authors": unique_authors,
        "total_authors": unique_authors,  # For frontend compatibility
        "total_concepts": len(concepts),
        "total_concept_tags": len(concepts),  # Updated naming
        "total_tags": len(concepts),  # For backwards compatibility
        "total_snippets": total_snippets,
        "date_range": {
            "oldest": oldest_paper.get('publication_date') if oldest_paper else None,
            "newest": newest_paper.get('publication_date') if newest_paper else None
        },
        "top_conferences": [
            {'name': conf['_id'], 'count': conf['count']} 
            for conf in top_conferences
        ],
        "top_concepts": concepts[:10] if concepts else []
    }


import hashlib
from pathlib import Path


@router.post("/upload")
async def upload_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process a PDF research paper (MongoDB version)"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Check file size (limit to 50MB)
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
    
    try:
        # Create unique filename to avoid conflicts
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(contents).hexdigest()[:8]
        safe_filename = file.filename.replace(' ', '_').replace('.pdf', '')
        new_filename = f"{timestamp}_{file_hash}_{safe_filename}.pdf"
        
        # Save the PDF file
        pdf_dir = Path("data/papers")
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_dir / new_filename
        
        with open(pdf_path, "wb") as f:
            f.write(contents)
        
        # Extract basic info from filename
        title = file.filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        
        # Create paper record immediately with basic info
        paper_doc = {
            "title": title,
            "authors": "",  # Will be filled when processed
            "authors_detailed": [],
            "abstract": "PDF uploaded. Click 'Use Marker' or 'Use MinerU' button to extract content.",
            "content": "",  # Will be filled by processing
            "sections": [],
            "pdf_path": str(pdf_path),
            "processed": False,
            "processing_status": "not_started",
            "processor_used": None,
            "processed_at": None,
            "created_at": datetime.utcnow(),
            "publication_date": None,
            "conference": "",
            "journal": "",
            "arxiv_id": "",
            "doi": ""
        }
        
        result = db.papers.insert_one(paper_doc)
        paper_id = str(result.inserted_id)
        
        logger.info(f"Paper uploaded successfully: {paper_id} - {title}")
        
        return {
            "id": paper_id,
            "title": title,
            "message": "Paper uploaded successfully. Use 'Use Marker' or 'Use MinerU' button to extract content.",
            "extracted_sections": 0,
            "extracted_authors": 0
        }
        
    except Exception as e:
        logger.error(f"Error uploading paper: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading paper: {str(e)}")


@router.post("/{paper_id}/extract-sections")
def extract_paper_sections(paper_id: str):
    """
    Extract Abstract, Introduction, and Conclusion sections from a paper using LLM.
    Uses Gemini 2.5 Pro with its 2M token context window to handle full papers.
    """
    try:
        # Get the paper
        paper = get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # Check if paper has markdown content
        markdown_content = paper.get('markdown_content') or paper.get('content')
        if not markdown_content:
            raise HTTPException(
                status_code=400, 
                detail="Paper has no content. Please process it with Marker or MinerU first."
            )
        
        # Import LLM service
        from app.services.llm_service import LLMService
        llm_service = LLMService()
        
        # Extract sections using LLM
        logger.info(f"Extracting sections for paper {paper_id}")
        
        # Call LLM with section extraction prompt
        extraction_result = llm_service.extract_paper_sections(markdown_content)
        
        if not extraction_result:
            raise HTTPException(status_code=500, detail="Failed to extract sections")
        
        # Parse the JSON response
        import json
        try:
            sections_data = json.loads(extraction_result) if isinstance(extraction_result, str) else extraction_result
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response: {extraction_result}")
            raise HTTPException(status_code=500, detail="Invalid response from LLM")
        
        # Update paper sections in database
        sections_to_save = []
        
        if sections_data.get('abstract'):
            sections_to_save.append({
                "id": -1,  # Special ID for abstract
                "title": "Abstract",
                "content": sections_data['abstract'],
                "type": "abstract",
                "position": 0
            })
        
        if sections_data.get('introduction'):
            sections_to_save.append({
                "id": 1,
                "title": "Introduction",
                "content": sections_data['introduction'],
                "type": "introduction",
                "position": 1
            })
        
        if sections_data.get('conclusion'):
            conclusion_title = sections_data.get('conclusion_title', 'Conclusion')
            sections_to_save.append({
                "id": 99,  # High ID for conclusion
                "title": conclusion_title,
                "content": sections_data['conclusion'],
                "type": "conclusion",
                "position": 99
            })
        
        # Update the paper with extracted sections
        update_result = db.papers.update_one(
            {'_id': ObjectId(paper_id)},
            {
                '$set': {
                    'sections': sections_to_save,
                    'sections_extracted': True,
                    'sections_extracted_at': datetime.utcnow(),
                    'abstract': sections_data.get('abstract', paper.get('abstract', ''))
                }
            }
        )
        
        if update_result.modified_count == 0:
            logger.warning(f"No changes made to paper {paper_id}")
        
        logger.info(f"Successfully extracted {len(sections_to_save)} sections for paper {paper_id}")
        
        return {
            "success": True,
            "sections_extracted": len(sections_to_save),
            "sections_found": sections_data.get('sections_found', {}),
            "conclusion_title": sections_data.get('conclusion_title'),
            "message": f"Successfully extracted {len(sections_to_save)} sections"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting sections for paper {paper_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error extracting sections: {str(e)}")
