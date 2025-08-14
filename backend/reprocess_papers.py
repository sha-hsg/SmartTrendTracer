#!/usr/bin/env python3
"""
Reprocess existing papers to extract better metadata
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, Paper, PaperAuthor, PaperSection, PaperReference
from app.services.paper_service import PaperService
from sqlalchemy import func
import PyPDF2
import re
from datetime import datetime
import json

def extract_enhanced_metadata(pdf_path):
    """Extract enhanced metadata from PDF"""
    metadata = {
        'authors': [],
        'abstract': None,
        'sections': [],
        'references': [],
        'keywords': [],
        'publication_info': {}
    }
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Get document info
            if pdf_reader.metadata:
                doc_info = pdf_reader.metadata
                if '/Author' in doc_info:
                    # Parse authors from metadata
                    author_str = doc_info['/Author']
                    if author_str:
                        # Split by common separators
                        authors = re.split(r'[,;&]|\sand\s', str(author_str))
                        metadata['authors'] = [a.strip() for a in authors if a.strip()]
                
                if '/Keywords' in doc_info:
                    keywords_str = doc_info['/Keywords']
                    if keywords_str:
                        metadata['keywords'] = [k.strip() for k in str(keywords_str).split(',')]
            
            # Extract text from first few pages for better parsing
            full_text = ""
            for page_num in range(min(10, len(pdf_reader.pages))):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                full_text += page_text + "\n"
            
            # Enhanced author extraction from text
            if not metadata['authors'] or len(metadata['authors']) < 2:
                # Look for author patterns in first page
                first_page = pdf_reader.pages[0].extract_text()
                
                # Pattern 1: Names before Abstract
                abstract_pos = first_page.lower().find('abstract')
                if abstract_pos > 0:
                    before_abstract = first_page[:abstract_pos]
                    # Look for lines with multiple capital letters (likely names)
                    lines = before_abstract.split('\n')
                    for line in lines[:20]:  # Check first 20 lines
                        # Match lines with 2+ capitalized words
                        if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', line.strip()):
                            # Could be an author name
                            names = re.findall(r'[A-Z][a-z]+(?: [A-Z][a-z]+)+', line)
                            metadata['authors'].extend(names)
                
                # Pattern 2: Look for author affiliations
                affiliation_patterns = [
                    r'([A-Z][a-z]+ [A-Z][a-z]+)[\s,]*\d*[\s,]*(?:University|Institute|Lab|Department)',
                    r'([A-Z][a-z]+ [A-Z][a-z]+)[\s,]*\{[\w@.]+\}',  # Email in braces
                    r'([A-Z][a-z]+ [A-Z][a-z]+)[\s,]*<[\w@.]+>',   # Email in angles
                ]
                
                for pattern in affiliation_patterns:
                    matches = re.findall(pattern, first_page)
                    for match in matches:
                        if match not in metadata['authors']:
                            metadata['authors'].append(match)
            
            # Extract abstract
            abstract_patterns = [
                r'Abstract[:\s]*(.+?)(?:1\s*Introduction|Keywords|1\.|I\.\s*INTRODUCTION)',
                r'ABSTRACT[:\s]*(.+?)(?:Categories|Keywords|1\s*Introduction)',
                r'Summary[:\s]*(.+?)(?:1\s*Introduction|Keywords)',
            ]
            
            for pattern in abstract_patterns:
                match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
                if match:
                    abstract = match.group(1).strip()
                    # Clean up the abstract
                    abstract = re.sub(r'\s+', ' ', abstract)
                    abstract = abstract.replace('- ', '')
                    if len(abstract) > 100:  # Ensure it's substantial
                        metadata['abstract'] = abstract[:1500]  # Limit length
                        break
            
            # Extract sections
            section_patterns = [
                r'(\d+\.?\s+[A-Z][A-Za-z\s]+)\n',  # 1. Introduction
                r'([IVX]+\.?\s+[A-Z][A-Za-z\s]+)\n',  # I. Introduction
                r'(\d+\s+[A-Z][A-Za-z\s]+)\n',  # 1 Introduction
            ]
            
            for pattern in section_patterns:
                sections = re.findall(pattern, full_text)
                if sections:
                    metadata['sections'] = sections[:20]  # Limit to 20 sections
                    break
            
            # Extract references (looking for common patterns)
            ref_section = None
            ref_patterns = [
                r'References\s*\n(.+)',
                r'REFERENCES\s*\n(.+)',
                r'Bibliography\s*\n(.+)',
            ]
            
            for pattern in ref_patterns:
                match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
                if match:
                    ref_section = match.group(1)
                    break
            
            if ref_section:
                # Parse individual references
                ref_lines = ref_section.split('\n')
                current_ref = ""
                
                for line in ref_lines[:100]:  # Limit to 100 lines
                    # Check if this starts a new reference (usually numbered or starts with [)
                    if re.match(r'^\[\d+\]|\d+\.', line.strip()):
                        if current_ref:
                            metadata['references'].append(current_ref.strip())
                        current_ref = line
                    else:
                        current_ref += " " + line
                
                if current_ref:
                    metadata['references'].append(current_ref.strip())
            
            # Extract publication info (conference, year, etc.)
            # Look for patterns like "Proceedings of", "Conference on", etc.
            conf_patterns = [
                r'(?:Proceedings of|In|Proc\.) ([A-Z][A-Za-z\s]+(?:Conference|Workshop|Symposium)[^,\n]*)',
                r'([A-Z]+\s*\d{4})',  # ICML 2024, NeurIPS 2023, etc.
                r'(?:Conference on|Workshop on) ([A-Za-z\s]+)',
            ]
            
            for pattern in conf_patterns:
                match = re.search(pattern, full_text[:5000])  # Check first part
                if match:
                    metadata['publication_info']['venue'] = match.group(1).strip()
                    break
            
            # Extract year
            year_match = re.search(r'20[1-2]\d', full_text[:2000])
            if year_match:
                metadata['publication_info']['year'] = int(year_match.group())
            
            # Page count
            metadata['page_count'] = len(pdf_reader.pages)
            
    except Exception as e:
        print(f"Error extracting metadata: {e}")
    
    return metadata

def reprocess_paper(db, paper_id):
    """Reprocess a single paper"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        print(f"Paper {paper_id} not found")
        return
    
    print(f"\nReprocessing: {paper.title}")
    print(f"PDF Path: {paper.pdf_path}")
    
    # Extract enhanced metadata
    # PDFs are in the root directory
    full_pdf_path = paper.pdf_path
    if not os.path.exists(full_pdf_path):
        print(f"  ❌ PDF file not found: {full_pdf_path}")
        return
    
    metadata = extract_enhanced_metadata(full_pdf_path)
    
    # Update paper metadata
    if metadata['abstract'] and not paper.abstract:
        paper.abstract = metadata['abstract']
        print(f"  ✅ Added abstract ({len(metadata['abstract'])} chars)")
    
    if metadata['page_count']:
        paper.page_count = metadata['page_count']
        print(f"  ✅ Set page count: {metadata['page_count']}")
    
    if metadata['publication_info'].get('venue'):
        if 'Conference' in metadata['publication_info']['venue']:
            paper.conference = metadata['publication_info']['venue']
            print(f"  ✅ Set conference: {paper.conference}")
        else:
            paper.journal = metadata['publication_info']['venue']
            print(f"  ✅ Set journal: {paper.journal}")
    
    if metadata['publication_info'].get('year'):
        year = metadata['publication_info']['year']
        paper.publication_date = datetime(year, 1, 1).date()
        print(f"  ✅ Set publication year: {year}")
    
    # Clear and re-add authors
    db.query(PaperAuthor).filter(PaperAuthor.paper_id == paper_id).delete()
    
    if metadata['authors']:
        print(f"  ✅ Found {len(metadata['authors'])} authors:")
        for idx, author_name in enumerate(metadata['authors'][:10]):  # Limit to 10 authors
            # Clean author name
            author_name = re.sub(r'\d+', '', author_name).strip()  # Remove numbers
            author_name = re.sub(r'[^\w\s-]', '', author_name).strip()  # Remove special chars
            
            if len(author_name) > 3:  # Ensure it's a real name
                author = PaperAuthor(
                    paper_id=paper_id,
                    name=author_name,
                    position=idx,
                    is_corresponding=(idx == 0)  # First author as corresponding
                )
                db.add(author)
                print(f"    - {author_name}")
    
    # Clear and re-add sections
    db.query(PaperSection).filter(PaperSection.paper_id == paper_id).delete()
    
    if metadata['sections']:
        print(f"  ✅ Found {len(metadata['sections'])} sections:")
        for idx, section_title in enumerate(metadata['sections'][:15]):  # Limit to 15 sections
            # Clean section title
            section_title = re.sub(r'^\d+\.?\s*', '', section_title).strip()
            section_title = re.sub(r'^[IVX]+\.?\s*', '', section_title).strip()
            
            # Determine section type
            section_type = 'other'
            title_lower = section_title.lower()
            if 'introduction' in title_lower:
                section_type = 'introduction'
            elif 'method' in title_lower or 'approach' in title_lower:
                section_type = 'methods'
            elif 'result' in title_lower or 'experiment' in title_lower:
                section_type = 'results'
            elif 'discussion' in title_lower:
                section_type = 'discussion'
            elif 'conclusion' in title_lower:
                section_type = 'conclusion'
            elif 'related' in title_lower:
                section_type = 'related_work'
            elif 'abstract' in title_lower:
                section_type = 'abstract'
            
            section = PaperSection(
                paper_id=paper_id,
                section_type=section_type,
                title=section_title,
                position=idx
            )
            db.add(section)
            print(f"    - {section_title} ({section_type})")
    
    # Clear and re-add references
    db.query(PaperReference).filter(PaperReference.paper_id == paper_id).delete()
    
    if metadata['references']:
        print(f"  ✅ Found {len(metadata['references'])} references")
        for ref_text in metadata['references'][:30]:  # Limit to 30 refs
            # Try to parse the reference
            ref = PaperReference(
                paper_id=paper_id,
                raw_citation=ref_text[:500]  # Limit length
            )
            
            # Try to extract title (usually in quotes or after year)
            title_match = re.search(r'"([^"]+)"', ref_text) or \
                         re.search(r'"([^"]+)"', ref_text) or \
                         re.search(r'\d{4}\.\s+([^.]+)\.', ref_text)
            if title_match:
                ref.title = title_match.group(1).strip()
            
            # Extract year
            year_match = re.search(r'(?:19|20)\d{2}', ref_text)
            if year_match:
                ref.year = int(year_match.group())
            
            # Extract first author
            author_match = re.match(r'^(?:\[\d+\]\s*)?([A-Z][a-z]+(?:,\s*[A-Z]\.?)?)', ref_text)
            if author_match:
                ref.authors = author_match.group(1)
            
            db.add(ref)
    
    # Mark as processed
    paper.processed = True
    paper.updated_at = datetime.utcnow()
    
    db.commit()
    print(f"  ✅ Paper reprocessed successfully!")

def main():
    """Reprocess all papers"""
    db = next(get_db())
    
    # Get all papers
    papers = db.query(Paper).all()
    print(f"Found {len(papers)} papers to reprocess")
    
    for paper in papers:
        try:
            reprocess_paper(db, paper.id)
        except Exception as e:
            print(f"Error reprocessing paper {paper.id}: {e}")
            db.rollback()
    
    # Show final statistics
    print("\n" + "="*50)
    print("Reprocessing Complete!")
    print("="*50)
    
    for paper in db.query(Paper).all():
        print(f"\n📄 {paper.title}")
        
        author_count = db.query(func.count(PaperAuthor.id)).filter(
            PaperAuthor.paper_id == paper.id
        ).scalar()
        
        section_count = db.query(func.count(PaperSection.id)).filter(
            PaperSection.paper_id == paper.id
        ).scalar()
        
        ref_count = db.query(func.count(PaperReference.id)).filter(
            PaperReference.paper_id == paper.id
        ).scalar()
        
        print(f"   - Authors: {author_count}")
        print(f"   - Sections: {section_count}")
        print(f"   - References: {ref_count}")
        print(f"   - Pages: {paper.page_count}")
        print(f"   - Abstract: {'Yes' if paper.abstract else 'No'} ({len(paper.abstract) if paper.abstract else 0} chars)")
        print(f"   - Conference: {paper.conference or 'N/A'}")
        print(f"   - Journal: {paper.journal or 'N/A'}")
        print(f"   - Publication Date: {paper.publication_date or 'N/A'}")

if __name__ == "__main__":
    main()