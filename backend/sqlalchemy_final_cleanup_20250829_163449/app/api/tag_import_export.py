"""
API endpoints for importing and exporting tag ontology
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models import get_db
from app.services.tag_service_v2 import get_tag_service_v2

logger = logging.getLogger(__name__)
router = APIRouter()

class ExportRequest(BaseModel):
    """Request for exporting tag data"""
    include_instances: bool = False
    include_proposals: bool = False
    format: str = "json"  # json, csv (future)

class ImportRequest(BaseModel):
    """Request for importing tag data"""
    merge_mode: str = "replace"  # replace, merge, skip_existing
    validate_before_import: bool = True
    backup_existing: bool = True

class ImportResult(BaseModel):
    """Result of import operation"""
    success: bool
    concepts_imported: int
    aliases_imported: int
    relations_imported: int
    instances_imported: int
    errors: List[str]
    warnings: List[str]

@router.get("/export")
async def export_tag_ontology(
    include_instances: bool = False,
    include_proposals: bool = False,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Export the complete tag ontology structure as JSON
    """
    try:
        service = get_tag_service_v2(db)
        export_data = service.export_ontology(include_instances, include_proposals)
        return export_data
        
    except Exception as e:
        logger.error(f"Error exporting tag ontology: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/file")
async def export_tag_ontology_file(
    include_instances: bool = False,
    include_proposals: bool = False,
    db: Session = Depends(get_db)
):
    """
    Export the tag ontology as a downloadable JSON file
    """
    try:
        # Get the export data
        export_data = await export_tag_ontology(include_instances, include_proposals, db)
        
        # Save to temporary file
        import tempfile
        import os
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"tag_ontology_export_{timestamp}.json"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
            temp_path = f.name
        
        # Return as file download
        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type='application/json',
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting tag ontology file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_tag_ontology(
    file: UploadFile = File(...),
    merge_mode: str = "replace",
    validate_before_import: bool = True,
    backup_existing: bool = True,
    db: Session = Depends(get_db)
) -> ImportResult:
    """
    Import tag ontology from JSON file
    """
    try:
        # Read the uploaded file
        contents = await file.read()
        import_data = json.loads(contents)
        
        # Validate structure
        errors = []
        warnings = []
        
        if validate_before_import:
            errors, warnings = validate_import_data(import_data)
            if errors:
                return ImportResult(
                    success=False,
                    concepts_imported=0,
                    aliases_imported=0,
                    relations_imported=0,
                    instances_imported=0,
                    errors=errors,
                    warnings=warnings
                )
        
        service = get_tag_service_v2(db)
        
        # Import the data
        stats = service.import_ontology(import_data, merge_mode, backup_existing)
        
        logger.info(f"Imported {stats['concepts_imported']} concepts, "
                   f"{stats['aliases_imported']} aliases, "
                   f"{stats['relations_imported']} relations")
        
        return ImportResult(
            success=True,
            concepts_imported=stats.get("concepts_imported", 0),
            aliases_imported=stats.get("aliases_imported", 0),
            relations_imported=stats.get("relations_imported", 0),
            instances_imported=stats.get("instances_imported", 0),
            errors=[],
            warnings=warnings
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in import file: {e}")
        return ImportResult(
            success=False,
            concepts_imported=0,
            aliases_imported=0,
            relations_imported=0,
            instances_imported=0,
            errors=[f"Invalid JSON format: {str(e)}"],
            warnings=[]
        )
    except Exception as e:
        logger.error(f"Error importing tag ontology: {e}")
        return ImportResult(
            success=False,
            concepts_imported=0,
            aliases_imported=0,
            relations_imported=0,
            instances_imported=0,
            errors=[str(e)],
            warnings=[]
        )

@router.get("/validate")
async def validate_current_ontology(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Validate the current tag ontology for consistency
    """
    try:
        service = get_tag_service_v2(db)
        return service.validate_ontology()
        
    except Exception as e:
        logger.error(f"Error validating ontology: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

def validate_import_data(data: Dict[str, Any]) -> tuple[List[str], List[str]]:
    """Validate import data structure"""
    errors = []
    warnings = []
    
    # Check required fields
    if 'version' not in data:
        warnings.append("No version field in import data")
    
    if 'concepts' not in data:
        errors.append("No concepts array in import data")
    
    if 'aliases' not in data:
        warnings.append("No aliases array in import data")
    
    # Validate concepts
    if 'concepts' in data:
        concept_ids = set()
        for i, concept in enumerate(data['concepts']):
            if 'id' not in concept:
                errors.append(f"Concept at index {i} missing 'id' field")
            elif concept['id'] in concept_ids:
                errors.append(f"Duplicate concept ID: {concept['id']}")
            else:
                concept_ids.add(concept['id'])
            
            if 'slug' not in concept:
                errors.append(f"Concept {concept.get('id', i)} missing 'slug' field")
            
            if 'display_name' not in concept:
                errors.append(f"Concept {concept.get('id', i)} missing 'display_name' field")
    
    # Validate aliases
    if 'aliases' in data:
        for i, alias in enumerate(data['aliases']):
            if 'alias_text' not in alias:
                errors.append(f"Alias at index {i} missing 'alias_text' field")
            
            if 'concept_id' not in alias:
                errors.append(f"Alias at index {i} missing 'concept_id' field")
    
    return errors, warnings

def has_circular_dependency(concept_id: str, all_concepts: List[Dict], visited: set = None) -> bool:
    """Check if a concept has circular parent-child relationships"""
    if visited is None:
        visited = set()
    
    if concept_id in visited:
        return True
    
    visited.add(concept_id)
    
    concept = next((c for c in all_concepts if c['id'] == concept_id), None)
    if not concept:
        return False
    
    for parent_id in concept.get('parents', []):
        if has_circular_dependency(parent_id, all_concepts, visited.copy()):
            return True
    
    return False

