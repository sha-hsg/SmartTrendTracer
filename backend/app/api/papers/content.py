"""
Paper content route handlers.

Covers: snippets, sections, references, TEI XML, PDF serving,
and LLM-based section extraction.

Image serving is in content_media.py.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from bson import ObjectId
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import FileResponse, Response

from .utils import (
    db,
    logger,
    get_paper_by_id,
)

router = APIRouter()


@router.get("/{paper_id}/snippets")
def get_paper_snippets(paper_id: str) -> List[Dict[str, Any]]:
    """Get paper snippets from MongoDB"""

    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
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

@router.post("/{paper_id}/snippets")
def add_paper_snippet(paper_id: str, snippet: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Add a snippet to a paper (analog to the article snippet endpoint)"""

    try:
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        paper = None

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Create snippet document matching the structure the GET endpoint returns
    # and the frontend expects (usePaperActions.ts: content/annotation/category/page_number)
    new_snippet = {
        'id': str(ObjectId()),
        'content': snippet.get('content', ''),
        'annotation': snippet.get('annotation', ''),
        'category': snippet.get('category', ''),
        'page_number': snippet.get('page_number'),
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    db.papers.update_one(
        {'_id': paper['_id']},
        {'$push': {'snippets': new_snippet}}
    )

    # Frontend appends the response body directly to its snippet list
    return new_snippet

@router.delete("/{paper_id}/snippets/{snippet_id}")
def remove_paper_snippet(paper_id: str, snippet_id: str) -> Dict[str, str]:
    """Remove a snippet from a paper"""

    try:
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        paper = None

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    db.papers.update_one(
        {'_id': paper['_id']},
        {'$pull': {'snippets': {'id': snippet_id}}}
    )

    return {"message": "Snippet removed successfully"}

@router.get("/{paper_id}/sections")
def get_paper_sections(paper_id: str) -> List[Dict[str, Any]]:
    """Get paper sections from MongoDB"""

    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
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
def update_paper_section(paper_id: str, section_id: int, request: Dict[str, Any]) -> Dict[str, Any]:
    """Update a paper section's title or content"""

    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
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
def get_paper_references(paper_id: str) -> Dict[str, Any]:
    """Get extracted references for a paper from MongoDB"""

    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
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
def get_paper_tei_xml(paper_id: str) -> Response:
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
    except Exception:
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
    tei_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data', 'tei_xml')
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

@router.get("/{paper_id}/pdf")
def get_paper_pdf(paper_id: str) -> FileResponse:
    """Serve PDF file for a paper"""

    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
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

@router.post("/{paper_id}/extract-sections")
def extract_paper_sections(paper_id: str) -> Dict[str, Any]:
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

        from app.services.llm_service import LLMService
        llm_service = LLMService()

        logger.info(f"Extracting sections for paper {paper_id}")

        prompt_config = llm_service.prompts.get('paper_section_extraction')
        if not prompt_config:
            raise HTTPException(status_code=500, detail="paper_section_extraction prompt not configured")

        model_config = llm_service.llm_config['models'].get('paper_section_extraction')
        if not model_config:
            raise HTTPException(status_code=500, detail="paper_section_extraction model not configured")

        system_prompt = prompt_config.get('system', '')
        user_prompt = prompt_config['user_template'].replace('{paper_content}', markdown_content)
        full_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt

        extraction_result = llm_service.generate_completion(
            prompt=full_prompt,
            model=model_config.get('model'),
            temperature=model_config.get('temperature', 0.1),
            max_tokens=model_config.get('max_tokens', 20000),
        )

        if not extraction_result:
            raise HTTPException(status_code=500, detail="Failed to extract sections")

        try:
            sections_data = json.loads(extraction_result)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', extraction_result, re.DOTALL)
            if not json_match:
                logger.error(f"Failed to parse LLM response: {extraction_result[:500]}")
                raise HTTPException(status_code=500, detail="Invalid JSON response from LLM")
            sections_data = json.loads(json_match.group())

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
                    'sections_extracted_at': datetime.now(timezone.utc),
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
