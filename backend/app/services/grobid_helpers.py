"""
GROBID TEI/XML and BibTeX parsing helpers.

Extracted from grobid_service.py to keep each module under 600 LOC.
All functions are pure: they accept strings and return data structures,
with no network or filesystem side-effects.
"""
import re
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# TEI namespace used throughout GROBID XML output
TEI_NS = {'tei': 'http://www.tei-c.org/ns/1.0'}


def parse_bibtex(bibtex_str: str) -> Dict[str, Any]:
    """Parse BibTeX format metadata from GROBID"""
    metadata = {}

    # Extract entry type and key
    entry_match = re.match(r'@(\w+)\{([^,]+),', bibtex_str)
    if entry_match:
        metadata['entry_type'] = entry_match.group(1).lower()
        metadata['bibtex_key'] = entry_match.group(2)

    # Common BibTeX fields
    patterns = {
        'author': r'author\s*=\s*\{([^}]+)\}',
        'title': r'title\s*=\s*\{([^}]+)\}',
        'year': r'year\s*=\s*\{([^}]+)\}',
        'month': r'month\s*=\s*\{([^}]+)\}',
        'day': r'day\s*=\s*\{([^}]+)\}',
        'date': r'date\s*=\s*\{([^}]+)\}',
        'abstract': r'abstract\s*=\s*\{([^}]+)\}',
        'eprint': r'eprint\s*=\s*\{([^}]+)\}',
        'journal': r'journal\s*=\s*\{([^}]+)\}',
        'volume': r'volume\s*=\s*\{([^}]+)\}',
        'number': r'number\s*=\s*\{([^}]+)\}',
        'pages': r'pages\s*=\s*\{([^}]+)\}',
        'doi': r'doi\s*=\s*\{([^}]+)\}',
        'url': r'url\s*=\s*\{([^}]+)\}',
        'publisher': r'publisher\s*=\s*\{([^}]+)\}',
        'booktitle': r'booktitle\s*=\s*\{([^}]+)\}'
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, bibtex_str, re.IGNORECASE | re.DOTALL)
        if match:
            value = match.group(1).strip()
            # Clean up whitespace and newlines
            value = ' '.join(value.split())
            metadata[field] = value

    # Parse authors into a list and convert from "Lastname, Firstname" to "Firstname Lastname"
    if 'author' in metadata:
        authors = metadata['author'].split(' and ')
        formatted_authors = []
        for author in authors:
            author = author.strip()
            # Check if author is in "Lastname, Firstname" format
            if ', ' in author:
                parts = author.split(', ', 1)
                # Convert to "Firstname Lastname" format
                formatted_authors.append(f"{parts[1]} {parts[0]}")
            else:
                # Keep as is if not in expected format
                formatted_authors.append(author)
        metadata['authors'] = formatted_authors

    # Create a formatted date if available
    if 'date' in metadata:
        metadata['publication_date'] = metadata['date']
    elif all(k in metadata for k in ['year', 'month', 'day']):
        metadata['publication_date'] = f"{metadata['year']}-{metadata['month']:0>2}-{metadata['day']:0>2}"
    elif 'year' in metadata:
        metadata['publication_date'] = metadata['year']

    # Add raw BibTeX for reference
    metadata['bibtex_raw'] = bibtex_str

    return metadata


def parse_header_xml(tei_xml: str) -> Dict[str, Any]:
    """Parse TEI header XML or BibTeX to extract metadata"""
    try:
        if not tei_xml:
            return {}

        # Check if it's BibTeX format (from HuggingFace GROBID)
        if tei_xml.strip().startswith('@'):
            return parse_bibtex(tei_xml)

        # Check if it's actually XML (not an error message)
        if not tei_xml.strip().startswith('<?xml') and not tei_xml.strip().startswith('<TEI'):
            logger.warning(f"Header response is not XML or BibTeX: {tei_xml[:100]}")
            return {}

        # Parse XML
        root = ET.fromstring(tei_xml)
        ns = TEI_NS

        metadata = {}

        # Extract title
        title_elem = root.find('.//tei:titleStmt/tei:title', ns)
        if title_elem is not None and title_elem.text:
            metadata['title'] = title_elem.text.strip()

        # Extract authors
        authors = []
        for author in root.findall('.//tei:sourceDesc//tei:author', ns):
            author_info = {}

            # Extract person name
            persname = author.find('.//tei:persName', ns)
            if persname is not None:
                forename = persname.find('.//tei:forename', ns)
                surname = persname.find('.//tei:surname', ns)

                if forename is not None and surname is not None:
                    author_info['name'] = f"{forename.text} {surname.text}"

                # Email
                email = author.find('.//tei:email', ns)
                if email is not None and email.text:
                    author_info['email'] = email.text

            # Affiliation
            affiliation = author.find('.//tei:affiliation', ns)
            if affiliation is not None:
                org_names = []
                for orgname in affiliation.findall('.//tei:orgName', ns):
                    if orgname.text:
                        org_names.append(orgname.text)
                if org_names:
                    author_info['affiliation'] = ', '.join(org_names)

                # Department
                dept = affiliation.find(".//tei:orgName[@type='department']", ns)
                if dept is not None and dept.text:
                    author_info['department'] = dept.text

            if author_info:
                authors.append(author_info)

        if authors:
            metadata['authors'] = authors

        # Extract abstract
        abstract = root.find('.//tei:abstract', ns)
        if abstract is not None:
            abstract_text = ' '.join(abstract.itertext()).strip()
            if abstract_text:
                metadata['abstract'] = abstract_text

        # Extract keywords
        keywords = []
        for term in root.findall('.//tei:keywords/tei:term', ns):
            if term.text:
                keywords.append(term.text)
        if keywords:
            metadata['keywords'] = keywords

        # Extract publication info
        pub_date = root.find('.//tei:publicationStmt/tei:date', ns)
        if pub_date is not None:
            if pub_date.get('when'):
                metadata['publication_date'] = pub_date.get('when')

        # DOI
        idno_doi = root.find(".//tei:idno[@type='DOI']", ns)
        if idno_doi is not None and idno_doi.text:
            metadata['doi'] = idno_doi.text

        # ArXiv ID - clean it to remove category suffix like [cs.CL]
        idno_arxiv = root.find(".//tei:idno[@type='arXiv']", ns)
        if idno_arxiv is not None and idno_arxiv.text:
            # Remove category suffix like [cs.CL] from "2507.18103v1[cs.CL]"
            arxiv_id = idno_arxiv.text
            # Remove the category in brackets at the end
            arxiv_id = re.sub(r'\[.*?\]$', '', arxiv_id)
            metadata['arxiv_id'] = arxiv_id.strip()

        return metadata

    except ET.ParseError as e:
        logger.error(f"Error parsing header XML: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error parsing header: {e}")
        return {}


def extract_references(tei_xml: str) -> List[Dict[str, Any]]:
    """Extract references from TEI XML"""
    try:
        if not tei_xml:
            return []

        root = ET.fromstring(tei_xml)
        ns = TEI_NS

        references = []

        # Find all biblStruct elements in the back matter
        for bibl in root.findall('.//tei:back//tei:biblStruct', ns):
            ref = {}

            # Extract title
            title = bibl.find('.//tei:title', ns)
            if title is not None and title.text:
                ref['title'] = title.text.strip()

            # Extract authors
            authors = []
            for author in bibl.findall('.//tei:author', ns):
                persname = author.find('.//tei:persName', ns)
                if persname is not None:
                    forename = persname.find('.//tei:forename', ns)
                    surname = persname.find('.//tei:surname', ns)
                    if forename is not None and surname is not None:
                        authors.append(f"{forename.text} {surname.text}")
            if authors:
                ref['authors'] = authors

            # Extract year
            date = bibl.find('.//tei:date', ns)
            if date is not None:
                if date.get('when'):
                    ref['year'] = date.get('when')[:4]
                elif date.text:
                    ref['year'] = date.text

            # Extract venue (journal/conference)
            meeting = bibl.find('.//tei:meeting', ns)
            if meeting is not None and meeting.text:
                ref['venue'] = meeting.text
            else:
                journal = bibl.find('.//tei:title[@level="j"]', ns)
                if journal is not None and journal.text:
                    ref['venue'] = journal.text

            # Extract DOI
            idno_doi = bibl.find(".//tei:idno[@type='DOI']", ns)
            if idno_doi is not None and idno_doi.text:
                ref['doi'] = idno_doi.text

            # Extract arXiv
            idno_arxiv = bibl.find(".//tei:idno[@type='arXiv']", ns)
            if idno_arxiv is not None and idno_arxiv.text:
                ref['arxiv'] = idno_arxiv.text

            # Extract pages
            biblscope_pages = bibl.find(".//tei:biblScope[@unit='page']", ns)
            if biblscope_pages is not None:
                from_page = biblscope_pages.get('from')
                to_page = biblscope_pages.get('to')
                if from_page and to_page:
                    ref['pages'] = f"{from_page}-{to_page}"

            # Get the reference ID if available
            if bibl.get('{http://www.w3.org/XML/1998/namespace}id'):
                ref['id'] = bibl.get('{http://www.w3.org/XML/1998/namespace}id')

            if ref:
                references.append(ref)

        return references

    except ET.ParseError as e:
        logger.error(f"Error parsing references XML: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error extracting references: {e}")
        return []


def extract_sections(tei_xml: str) -> List[Dict[str, Any]]:
    """Extract document sections from TEI XML"""
    try:
        if not tei_xml:
            return []

        root = ET.fromstring(tei_xml)
        ns = TEI_NS

        sections = []

        # Find all div elements in the body
        for div in root.findall('.//tei:body//tei:div', ns):
            section = {}

            # Get section number and title from head
            head = div.find('tei:head', ns)
            if head is not None:
                # Extract section number if present
                n_attr = head.get('n')
                if n_attr:
                    section['number'] = n_attr

                # Extract title
                if head.text:
                    section['title'] = head.text.strip()

            # Extract section content (first 500 chars as preview)
            content_parts = []
            for p in div.findall('tei:p', ns):
                if p.text:
                    content_parts.append(p.text.strip())

            if content_parts:
                full_content = ' '.join(content_parts)
                section['content_preview'] = full_content[:500] + ('...' if len(full_content) > 500 else '')
                section['content_length'] = len(full_content)

            if section:
                sections.append(section)

        return sections

    except ET.ParseError as e:
        logger.error(f"Error parsing sections XML: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error extracting sections: {e}")
        return []


def parse_citations(tei_xml: str) -> List[Dict[str, Any]]:
    """Parse citation contexts from TEI XML"""
    try:
        if not tei_xml:
            return []

        root = ET.fromstring(tei_xml)
        ns = TEI_NS

        citations = []

        # Extract each biblStruct as a citation
        for bibl in root.findall('.//tei:biblStruct', ns):
            citation = {}

            # Extract basic citation info
            title = bibl.find('.//tei:title', ns)
            if title is not None and title.text:
                citation['title'] = title.text.strip()

            # Get raw citation text if available
            note = bibl.find('.//tei:note[@type="raw_reference"]', ns)
            if note is not None and note.text:
                citation['raw_text'] = note.text.strip()

            if citation:
                citations.append(citation)

        return citations

    except ET.ParseError as e:
        logger.error(f"Error parsing citations XML: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error parsing citations: {e}")
        return []


def extract_conclusion(tei_xml: str) -> Optional[Dict[str, str]]:
    """
    Extract conclusion section from TEI XML

    Args:
        tei_xml: TEI XML content

    Returns:
        Dict with title and content of conclusion, or None if not found
    """
    try:
        if not tei_xml:
            return None

        root = ET.fromstring(tei_xml)
        ns = TEI_NS

        # Look for conclusion section in the body
        # GROBID typically marks sections with <div> and <head> tags
        for div in root.findall('.//tei:body//tei:div', ns):
            head = div.find('tei:head', ns)
            if head is not None and head.text:
                # Check if this is a conclusion section
                title = head.text.strip().lower()
                if 'conclusion' in title or 'summary' in title or 'concluding' in title:
                    # Extract all text from this section
                    content_parts = []
                    for elem in div:
                        if elem.tag.endswith('head'):
                            continue  # Skip the heading itself
                        # Get all text including nested elements
                        text = ' '.join(elem.itertext()).strip()
                        if text:
                            content_parts.append(text)

                    if content_parts:
                        return {
                            'title': head.text.strip(),
                            'content': '\n\n'.join(content_parts)
                        }

        # Alternative: Look for conclusion in specific section types
        for div in root.findall(".//tei:div[@type='conclusion']", ns):
            head = div.find('tei:head', ns)
            title = head.text.strip() if head is not None and head.text else 'Conclusion'

            content_parts = []
            for elem in div:
                if elem.tag.endswith('head'):
                    continue
                text = ' '.join(elem.itertext()).strip()
                if text:
                    content_parts.append(text)

            if content_parts:
                return {
                    'title': title,
                    'content': '\n\n'.join(content_parts)
                }

        return None

    except ET.ParseError as e:
        logger.error(f"Error parsing TEI XML for conclusion: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error extracting conclusion: {e}")
        return None
