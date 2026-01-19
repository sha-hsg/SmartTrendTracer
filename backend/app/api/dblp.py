"""
DBLP API endpoints for paper search and BibTeX retrieval
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from app.services.dblp_service import dblp_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/search")
async def search_dblp_papers(
    title: str = Query(..., description="Paper title to search for"),
    max_results: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    use_sparql: bool = Query(False, description="Use SPARQL endpoint for search")
) -> Dict[str, Any]:
    """
    Search for papers on DBLP by title
    
    Returns multiple versions/venues if the paper appears in different places
    Uses REST API by default, can optionally use SPARQL endpoint
    """
    try:
        if not title or len(title.strip()) < 3:
            raise HTTPException(status_code=400, detail="Title must be at least 3 characters long")
        
        # Try REST API first, fallback to SPARQL if needed
        if use_sparql:
            results = dblp_service.search_papers_sparql(title, max_results)
        else:
            results = dblp_service.search_papers(title, max_results)
            
            # If REST API returns no results, try SPARQL
            if not results:
                logger.info("No results from REST API, trying SPARQL...")
                results = dblp_service.search_papers_sparql(title, max_results)
        
        return {
            "query": title,
            "count": len(results),
            "results": results,
            "search_method": "sparql" if use_sparql or (not results and use_sparql) else "rest_api"
        }
        
    except Exception as e:
        logger.error(f"Error searching DBLP: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching DBLP: {str(e)}")

@router.get("/bibtex")
async def get_bibtex(
    dblp_key: Optional[str] = Query(None, description="DBLP key identifier"),
    dblp_url: Optional[str] = Query(None, description="Full DBLP URL")
) -> Dict[str, Any]:
    """
    Get BibTeX citation for a specific DBLP entry
    
    Provide either dblp_key or dblp_url
    """
    try:
        if not dblp_key and not dblp_url:
            raise HTTPException(
                status_code=400, 
                detail="Either dblp_key or dblp_url must be provided"
            )
        
        bibtex = None
        
        if dblp_key:
            bibtex = dblp_service.get_bibtex(dblp_key)
        elif dblp_url:
            bibtex = dblp_service.get_bibtex_from_url(dblp_url)
        
        if not bibtex:
            raise HTTPException(status_code=404, detail="BibTeX not found")
        
        return {
            "bibtex": bibtex,
            "dblp_key": dblp_key,
            "dblp_url": dblp_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching BibTeX: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching BibTeX: {str(e)}")

@router.get("/metadata/{dblp_key:path}")
async def get_complete_metadata(dblp_key: str) -> Dict[str, Any]:
    """
    Get complete metadata for a DBLP entry using SPARQL
    
    Returns comprehensive metadata including authors, venue, dates, etc.
    """
    try:
        metadata = dblp_service.get_complete_metadata(dblp_key)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Metadata not found")
        
        # Generate BibTeX from metadata
        metadata['bibtex'] = dblp_service.generate_bibtex_from_metadata(metadata)
        
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching metadata: {str(e)}")

@router.post("/attach-metadata/{paper_id}")
async def attach_dblp_metadata(
    paper_id: int,
    dblp_key: str = Query(..., description="DBLP key identifier"),
    overwrite: bool = Query(False, description="Overwrite existing metadata"),
) -> Dict[str, Any]:
    """
    Attach DBLP metadata to an existing paper in SmartTrendTracer
    
    Updates the paper with:
    - Complete author information
    - Publication venue and date
    - DOI and other identifiers
    - Conference/journal information
    
    By default, only updates empty fields unless overwrite=True
    """
    try:
        # Get the paper
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # Fetch DBLP metadata
        metadata = dblp_service.get_complete_metadata(dblp_key)
        if not metadata:
            raise HTTPException(status_code=404, detail="DBLP metadata not found")
        
        # Track what was updated
        updated_fields = []
        skipped_fields = []
        
        # Update paper with DBLP metadata - smart update logic
        # Title - usually don't overwrite as user's title might be cleaner
        if metadata.get('title'):
            if not paper.title or paper.title.strip() == "":
                paper.title = metadata['title']
                updated_fields.append('title')
            elif overwrite:
                paper.title = metadata['title']
                updated_fields.append('title (overwritten)')
            else:
                skipped_fields.append(f'title (existing: "{paper.title[:50]}...")')
        
        # Authors - always update if empty, otherwise check if different
        if metadata.get('authors'):
            author_names = [author.get('name', '') for author in metadata['authors']]
            new_authors = ', '.join(author_names)
            
            # Check if current authors field is effectively empty
            current_authors_empty = not paper.authors or paper.authors.strip() == "" or paper.authors.strip().lower() == "none"
            
            if current_authors_empty:
                paper.authors = new_authors
                updated_fields.append('authors')
                logger.info(f"Updated authors for paper {paper_id}: {new_authors}")
                # Also create PaperAuthor records
                # First remove any existing PaperAuthor records
                db.query(PaperAuthor).filter(PaperAuthor.paper_id == paper_id).delete()
                # Create new PaperAuthor records
                for i, author_name in enumerate(author_names):
                    if author_name:
                        author_record = PaperAuthor(
                            paper_id=paper_id,
                            name=author_name,
                            position=i
                        )
                        db.add(author_record)
                logger.info(f"Created {len(author_names)} PaperAuthor records for paper {paper_id}")
            elif overwrite:
                # Only overwrite if DBLP has authors and user explicitly wants to overwrite
                old_authors = paper.authors
                paper.authors = new_authors
                updated_fields.append('authors (overwritten)')
                logger.info(f"Overwrote authors for paper {paper_id}: '{old_authors}' -> '{new_authors}'")
                # Update PaperAuthor records
                db.query(PaperAuthor).filter(PaperAuthor.paper_id == paper_id).delete()
                for i, author_name in enumerate(author_names):
                    if author_name:
                        author_record = PaperAuthor(
                            paper_id=paper_id,
                            name=author_name,
                            position=i
                        )
                        db.add(author_record)
                logger.info(f"Updated {len(author_names)} PaperAuthor records for paper {paper_id}")
            elif paper.authors != new_authors:
                # Authors are different but not empty - check if DBLP version is cleaner
                # Don't overwrite if existing authors don't have disambiguation markers
                if '(disambiguation)' not in paper.authors and '(disambiguation)' in new_authors:
                    skipped_fields.append(f'authors (kept cleaner existing: {len(paper.authors.split(","))} authors)')
                    logger.info(f"Skipped DBLP authors with disambiguation markers for paper {paper_id}")
                else:
                    skipped_fields.append(f'authors (existing: {len(paper.authors.split(","))} authors, DBLP: {len(author_names)} authors)')
        
        # Venue (conference/journal)
        if metadata.get('venue'):
            venue = metadata['venue']
            # Clean up venue - remove truncation artifacts
            if venue.endswith(', {'):
                venue = venue[:-3].strip()
            
            if metadata['type'] == 'article':
                if not paper.journal or paper.journal.strip() == "":
                    paper.journal = venue
                    updated_fields.append('journal')
                elif overwrite:
                    paper.journal = venue
                    updated_fields.append('journal (overwritten)')
                else:
                    skipped_fields.append(f'journal (existing: "{paper.journal[:30]}...")')
            else:
                if not paper.conference or paper.conference.strip() == "":
                    paper.conference = venue
                    updated_fields.append('conference')
                elif overwrite:
                    paper.conference = venue
                    updated_fields.append('conference (overwritten)')
                else:
                    skipped_fields.append(f'conference (existing: "{paper.conference[:30]}...")')
        
        # DOI - prefer DBLP's DOI if we don't have one
        if metadata.get('doi'):
            if not paper.doi or paper.doi.strip() == "":
                paper.doi = metadata['doi']
                updated_fields.append('doi')
            elif overwrite:
                paper.doi = metadata['doi']
                updated_fields.append('doi (overwritten)')
        
        # Publication date - update if empty
        if metadata.get('publication_date'):
            if not paper.publication_date:
                try:
                    # Handle partial dates (year only, year-month, etc)
                    date_str = metadata['publication_date']
                    if date_str.endswith('-00-01'):
                        # Year only, use January 1st
                        paper.publication_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        paper.publication_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    updated_fields.append('publication_date')
                except Exception as e:
                    logger.warning(f"Could not parse date {metadata['publication_date']}: {e}")
            elif overwrite:
                try:
                    paper.publication_date = datetime.strptime(metadata['publication_date'], '%Y-%m-%d').date()
                    updated_fields.append('publication_date (overwritten)')
                except:
                    pass
        
        # Store DBLP key and URL
        # Try to set these fields - they may not exist in older databases
        try:
            paper.dblp_key = dblp_key
            updated_fields.append('dblp_key')
        except AttributeError:
            logger.warning("dblp_key column not available - run add_dblp_columns.py migration")
        
        try:
            if metadata.get('dblp_url'):
                paper.dblp_url = metadata['dblp_url']
                updated_fields.append('dblp_url')
        except AttributeError:
            logger.warning("dblp_url column not available - run add_dblp_columns.py migration")
        
        try:
            if metadata.get('official_bibtex'):
                paper.bibtex = metadata['official_bibtex']
                updated_fields.append('bibtex')
        except AttributeError:
            logger.warning("bibtex column not available - run add_dblp_columns.py migration")
        
        db.commit()
        db.refresh(paper)
        
        # Generate BibTeX
        bibtex = dblp_service.generate_bibtex_from_metadata(metadata)
        
        # Build detailed message
        message = "DBLP metadata processed."
        if updated_fields:
            message += f" Updated: {', '.join(updated_fields)}."
        if skipped_fields:
            message += f" Skipped (non-empty): {', '.join(skipped_fields)}."
        if not updated_fields and not skipped_fields:
            message = "No fields were updated (all fields already had values)."
        
        return {
            "success": True,
            "message": message,
            "paper_id": paper_id,
            "dblp_key": dblp_key,
            "metadata": metadata,
            "bibtex": bibtex,
            "updated_fields": updated_fields,
            "skipped_fields": skipped_fields
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error attaching metadata: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error attaching metadata: {str(e)}")

@router.get("/generate-bibtex/{paper_id}")
async def generate_bibtex_for_paper(
    paper_id: int,
) -> Dict[str, Any]:
    """
    Generate BibTeX entry for a paper using its stored metadata
    """
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # Build metadata dict from paper
        metadata = {
            'title': paper.title,
            'authors': [{'name': name.strip()} for name in paper.authors.split(',')] if paper.authors else [],
            'year': str(paper.publication_date.year) if paper.publication_date else '',
            'venue': paper.conference or paper.journal or '',
            'doi': paper.doi or '',
            'type': 'article' if paper.journal else 'inproceedings' if paper.conference else 'misc',
            'dblp_key': f"paper_{paper_id}"  # Generate a key if no DBLP key
        }
        
        # Generate BibTeX
        bibtex = dblp_service.generate_bibtex_from_metadata(metadata)
        
        return {
            "paper_id": paper_id,
            "title": paper.title,
            "bibtex": bibtex
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating BibTeX: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating BibTeX: {str(e)}")