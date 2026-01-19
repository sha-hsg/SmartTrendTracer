"""
Unified Image Management Service for PDF Processing
Handles image extraction, storage, and serving for all PDF processors
"""

import os
import hashlib
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image
import io
import base64
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class ImageManager:
    """
    Scalable image management for PDF processing
    Stores images in a hierarchical structure for efficient access
    """
    
    def __init__(self, base_path: str = "data/paper_images"):
        """
        Initialize the image manager
        
        Args:
            base_path: Root directory for image storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        self.temp_path = self.base_path / "temp"
        self.temp_path.mkdir(exist_ok=True)
        
        logger.info(f"ImageManager initialized with base path: {self.base_path}")
    
    def get_paper_image_dir(self, paper_id: int) -> Path:
        """
        Get the image directory for a specific paper
        Uses hierarchical structure for scalability (e.g., 1234 -> 12/34/)
        
        Args:
            paper_id: The paper ID
            
        Returns:
            Path to the paper's image directory
        """
        # Create hierarchical structure for scalability
        # E.g., paper_id 12345 -> 12/34/5/
        id_str = str(paper_id).zfill(6)  # Pad to 6 digits
        dir_path = self.base_path / id_str[:2] / id_str[2:4] / id_str[4:]
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    def save_image(self, 
                   paper_id: int, 
                   image_data: bytes, 
                   image_name: Optional[str] = None,
                   page_num: Optional[int] = None,
                   image_type: str = "extracted") -> str:
        """
        Save an image for a paper
        
        Args:
            paper_id: The paper ID
            image_data: Raw image bytes
            image_name: Optional name for the image
            page_num: Optional page number where image appears
            image_type: Type of image (extracted, figure, equation, table)
            
        Returns:
            Relative path to the saved image
        """
        # Generate unique filename if not provided
        if not image_name:
            # Use content hash for deduplication
            content_hash = hashlib.md5(image_data).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_name = f"{image_type}_{page_num or 0}_{content_hash}.png"
        
        # Get paper directory
        paper_dir = self.get_paper_image_dir(paper_id)
        image_path = paper_dir / image_name
        
        logger.debug(f"save_image: Saving to {image_path} ({len(image_data)} bytes)")
        
        # Save image
        with open(image_path, 'wb') as f:
            f.write(image_data)
        
        # Return relative path from base
        rel_path = image_path.relative_to(self.base_path)
        logger.info(f"✅ Saved image for paper {paper_id}: {rel_path}")
        
        return str(rel_path)
    
    def save_image_from_file(self,
                            paper_id: int,
                            source_path: str,
                            image_name: Optional[str] = None,
                            page_num: Optional[int] = None,
                            image_type: str = "extracted") -> str:
        """
        Save an image from a file path
        
        Args:
            paper_id: The paper ID
            source_path: Path to the source image file
            image_name: Optional name for the image
            page_num: Optional page number
            image_type: Type of image
            
        Returns:
            Relative path to the saved image
        """
        logger.debug(f"save_image_from_file: Reading from {source_path}")
        with open(source_path, 'rb') as f:
            image_data = f.read()
        
        logger.debug(f"save_image_from_file: Read {len(image_data)} bytes")
        
        # Determine extension from source if no name provided
        if not image_name:
            ext = Path(source_path).suffix or '.png'
            content_hash = hashlib.md5(image_data).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_name = f"{image_type}_{page_num or 0}_{content_hash}{ext}"
        
        result = self.save_image(paper_id, image_data, image_name, page_num, image_type)
        if result:
            logger.info(f"✅ Saved image to: data/paper_images/{paper_id}/{result}")
        else:
            logger.error(f"❌ Failed to save image from {source_path}")
        return result
    
    def process_markdown_images(self, 
                              paper_id: int, 
                              markdown: str, 
                              image_files: Dict[str, str] = None,
                              processor: str = "unknown") -> Tuple[str, List[Dict]]:
        """
        Process markdown to update image references and extract/save images
        
        Args:
            paper_id: The paper ID
            markdown: The markdown content
            image_files: Optional dict mapping image references to file paths
            processor: Name of the processor (marker, mineru, etc.)
            
        Returns:
            Tuple of (updated_markdown, image_metadata_list)
        """
        image_metadata = []
        updated_markdown = markdown
        
        # Pattern to find image references in markdown
        # Matches: ![alt text](path) or ![alt text][ref]
        img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        ref_pattern = r'!\[([^\]]*)\]\[([^\]]+)\]'
        
        # Also look for reference definitions
        ref_def_pattern = r'^\[([^\]]+)\]:\s*(.+)$'
        
        # Extract reference definitions
        references = {}
        for match in re.finditer(ref_def_pattern, markdown, re.MULTILINE):
            ref_id = match.group(1)
            ref_url = match.group(2)
            references[ref_id] = ref_url
        
        # Process direct image links
        for match in re.finditer(img_pattern, markdown):
            alt_text = match.group(1)
            img_path = match.group(2)
            
            # Process the image
            new_path = self._process_single_image(
                paper_id, img_path, alt_text, image_files, processor
            )
            
            if new_path:
                # Update markdown with new path
                old_ref = match.group(0)
                new_ref = f"![{alt_text}](/api/papers/{paper_id}/images/{new_path})"
                updated_markdown = updated_markdown.replace(old_ref, new_ref)
                
                image_metadata.append({
                    "paper_id": paper_id,
                    "path": new_path,
                    "alt_text": alt_text,
                    "processor": processor
                })
        
        # Process reference-style images
        for match in re.finditer(ref_pattern, markdown):
            alt_text = match.group(1)
            ref_id = match.group(2)
            
            if ref_id in references:
                img_path = references[ref_id]
                
                # Process the image
                new_path = self._process_single_image(
                    paper_id, img_path, alt_text, image_files, processor
                )
                
                if new_path:
                    # Update markdown with direct link
                    old_ref = match.group(0)
                    new_ref = f"![{alt_text}](/api/papers/{paper_id}/images/{new_path})"
                    updated_markdown = updated_markdown.replace(old_ref, new_ref)
                    
                    image_metadata.append({
                        "paper_id": paper_id,
                        "path": new_path,
                        "alt_text": alt_text,
                        "processor": processor
                    })
        
        return updated_markdown, image_metadata
    
    def _process_single_image(self,
                            paper_id: int,
                            img_path: str,
                            alt_text: str,
                            image_files: Dict[str, str],
                            processor: str) -> Optional[str]:
        """
        Process a single image reference
        
        Args:
            paper_id: The paper ID
            img_path: Path or reference to the image
            alt_text: Alt text for the image
            image_files: Dict mapping references to actual file paths
            processor: Name of the processor
            
        Returns:
            New relative path to the saved image, or None if failed
        """
        try:
            # Determine image type from alt text
            image_type = "figure"
            if "equation" in alt_text.lower() or "formula" in alt_text.lower():
                image_type = "equation"
            elif "table" in alt_text.lower():
                image_type = "table"
            elif "diagram" in alt_text.lower() or "chart" in alt_text.lower():
                image_type = "diagram"
            
            # Check if it's a base64 encoded image
            if img_path.startswith("data:image"):
                # Extract base64 data
                header, data = img_path.split(",", 1)
                image_data = base64.b64decode(data)
                
                # Determine extension from header
                if "png" in header:
                    ext = ".png"
                elif "jpeg" in header or "jpg" in header:
                    ext = ".jpg"
                else:
                    ext = ".png"
                
                # Generate filename
                content_hash = hashlib.md5(image_data).hexdigest()[:8]
                image_name = f"{processor}_{image_type}_{content_hash}{ext}"
                
                return self.save_image(paper_id, image_data, image_name, image_type=image_type)
            
            # Check if it's a file path that exists
            elif image_files and img_path in image_files:
                source_path = image_files[img_path]
                logger.info(f"Found image mapping: '{img_path}' -> '{source_path}'")
                
                # Check if the value is a data URL
                if isinstance(source_path, str) and source_path.startswith("data:image"):
                    # Extract base64 data
                    header, data = source_path.split(",", 1)
                    image_data = base64.b64decode(data)
                    
                    # Determine extension from header
                    if "png" in header:
                        ext = ".png"
                    elif "jpeg" in header or "jpg" in header:
                        ext = ".jpg"
                    else:
                        ext = ".png"
                    
                    # Use the original img_path as part of the filename
                    image_name = os.path.basename(img_path) if img_path else f"{processor}_{image_type}_{hashlib.md5(image_data).hexdigest()[:8]}{ext}"
                    
                    result = self.save_image(paper_id, image_data, image_name, image_type=image_type)
                    if result:
                        logger.info(f"Successfully saved base64 image as: {result}")
                    return result
                
                # Otherwise treat as file path
                elif os.path.exists(source_path):
                    logger.info(f"Found image file at: {source_path}")
                    result = self.save_image_from_file(
                        paper_id, source_path, image_type=image_type
                    )
                    if result:
                        logger.info(f"Successfully saved image file as: {result}")
                    return result
                else:
                    logger.warning(f"Image file not found at mapped path: {source_path}")
            
            # Check if it's a direct file path
            elif os.path.exists(img_path):
                logger.info(f"Found image at direct path: {img_path}")
                result = self.save_image_from_file(
                    paper_id, img_path, image_type=image_type
                )
                if result:
                    logger.info(f"Successfully saved direct path image as: {result}")
                return result
            
            # Check if it's a relative path that needs resolution
            elif image_files:
                logger.debug(f"Trying to resolve relative path: {img_path}")
                # Try to find a matching file
                for ref, path in image_files.items():
                    if ref in img_path or img_path in ref:
                        if os.path.exists(path):
                            logger.info(f"Resolved '{img_path}' to '{path}'")
                            result = self.save_image_from_file(
                                paper_id, path, image_type=image_type
                            )
                            if result:
                                logger.info(f"Successfully saved resolved image as: {result}")
                            return result
            
            logger.warning(f"Could not process image: {img_path} (not found in {len(image_files) if image_files else 0} mappings)")
            return None
            
        except Exception as e:
            logger.error(f"Error processing image {img_path}: {e}")
            return None
    
    def get_image_path(self, paper_id: int, image_name: str) -> Optional[Path]:
        """
        Get the full path to an image
        
        Args:
            paper_id: The paper ID
            image_name: The image filename or relative path
            
        Returns:
            Full path to the image, or None if not found
        """
        # Handle full relative paths
        if "/" in image_name:
            full_path = self.base_path / image_name
            if full_path.exists():
                return full_path
        
        # Try paper directory
        paper_dir = self.get_paper_image_dir(paper_id)
        image_path = paper_dir / image_name
        
        if image_path.exists():
            return image_path
        
        return None
    
    def delete_paper_images(self, paper_id: int) -> bool:
        """
        Delete all images for a paper
        
        Args:
            paper_id: The paper ID
            
        Returns:
            True if successful
        """
        try:
            paper_dir = self.get_paper_image_dir(paper_id)
            if paper_dir.exists():
                shutil.rmtree(paper_dir)
                logger.info(f"Deleted images for paper {paper_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting images for paper {paper_id}: {e}")
            return False
    
    def get_paper_image_stats(self, paper_id: int) -> Dict:
        """
        Get statistics about images for a paper
        
        Args:
            paper_id: The paper ID
            
        Returns:
            Dict with image statistics
        """
        paper_dir = self.get_paper_image_dir(paper_id)
        
        if not paper_dir.exists():
            return {
                "total_images": 0,
                "total_size_bytes": 0,
                "image_types": {}
            }
        
        total_images = 0
        total_size = 0
        image_types = {}
        
        for img_file in paper_dir.glob("*"):
            if img_file.is_file():
                total_images += 1
                total_size += img_file.stat().st_size
                
                # Categorize by type (based on filename pattern)
                if "equation" in img_file.name:
                    image_types["equations"] = image_types.get("equations", 0) + 1
                elif "table" in img_file.name:
                    image_types["tables"] = image_types.get("tables", 0) + 1
                elif "figure" in img_file.name or "diagram" in img_file.name:
                    image_types["figures"] = image_types.get("figures", 0) + 1
                else:
                    image_types["other"] = image_types.get("other", 0) + 1
        
        return {
            "total_images": total_images,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "image_types": image_types
        }

# Global instance
_image_manager = None

def get_image_manager() -> ImageManager:
    """Get or create the global image manager instance"""
    global _image_manager
    if _image_manager is None:
        _image_manager = ImageManager()
    return _image_manager