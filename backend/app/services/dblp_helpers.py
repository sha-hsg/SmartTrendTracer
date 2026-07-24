"""
Helper functions for DBLP service - XML/SPARQL parsing, BibTeX generation,
and data transformation utilities.
"""
import logging
import re
from typing import List, Dict, Optional, Any
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


def format_citation(title: str, authors: List[str], venue: str, year: str) -> str:
    """Format a human-readable citation string"""
    parts = []

    if authors:
        if len(authors) <= 3:
            parts.append(', '.join(authors))
        else:
            parts.append(f"{authors[0]} et al.")

    if year:
        parts.append(f"({year})")

    parts.append(f'"{title}"')

    if venue:
        parts.append(f"In: {venue}")

    return ' '.join(parts)


def clean_author_name(author_name: str) -> str:
    """
    Clean up DBLP author name by removing disambiguation suffixes.
    DBLP sometimes adds " (disambiguation)" or " 0001", " 0002" etc.
    """
    author_name = re.sub(r'\s*\(disambiguation\)\s*$', '', author_name)
    author_name = re.sub(r'\s+\d{4}$', '', author_name)  # Remove numeric suffixes like " 0001"
    return author_name.strip()


def parse_hit(hit: ET.Element) -> Optional[Dict[str, Any]]:
    """Parse a single search hit from DBLP XML"""
    try:
        info = hit.find('info')
        if info is None:
            return None

        # Extract all authors
        authors = []
        for author in info.findall('authors/author'):
            if author.text:
                authors.append(author.text)

        # Extract venue information
        venue = info.find('venue')
        venue_text = venue.text if venue is not None else None

        # Extract year
        year = info.find('year')
        year_text = year.text if year is not None else None

        # Extract type (article, inproceedings, etc.)
        type_elem = info.find('type')
        pub_type = type_elem.text if type_elem is not None else 'unknown'

        # Extract URLs
        url = info.find('url')
        dblp_url = url.text if url is not None else None

        # Extract electronic edition (PDF link if available)
        ee = info.find('ee')
        pdf_url = ee.text if ee is not None else None

        # Extract DOI if available
        doi = info.find('doi')
        doi_text = doi.text if doi is not None else None

        # Extract key (unique identifier)
        key = info.find('key')
        dblp_key = key.text if key is not None else None

        # Extract title
        title = info.find('title')
        title_text = title.text if title is not None else 'Unknown Title'

        return {
            'title': title_text,
            'authors': authors,
            'venue': venue_text,
            'year': year_text,
            'type': pub_type,
            'dblp_url': dblp_url,
            'pdf_url': pdf_url,
            'doi': doi_text,
            'dblp_key': dblp_key,
            'author_string': ', '.join(authors) if authors else '',
            'citation_string': format_citation(title_text, authors, venue_text, year_text)
        }

    except Exception as e:
        logger.error(f"Error parsing DBLP hit: {e}")
        return None


def parse_sparql_binding(binding: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Parse a single SPARQL result binding"""
    try:
        # Extract URI and convert to DBLP key
        pub_uri = binding.get('pub', {}).get('value', '')
        dblp_key = pub_uri.replace('https://dblp.org/rec/', '').replace('.html', '') if pub_uri else None

        # Build paper info
        paper_info = {
            'title': binding.get('title', {}).get('value', 'Unknown Title'),
            'authors': [],  # Would need separate query for authors
            'venue': binding.get('venue', {}).get('value', None),
            'year': binding.get('year', {}).get('value', None),
            'type': binding.get('type', {}).get('value', 'unknown'),
            'dblp_url': pub_uri if pub_uri else None,
            'pdf_url': binding.get('ee', {}).get('value', None),
            'doi': binding.get('doi', {}).get('value', None),
            'dblp_key': dblp_key,
            'author_string': '',  # Would need separate query
            'citation_string': ''
        }

        # Format citation string
        paper_info['citation_string'] = format_citation(
            paper_info['title'],
            [],
            paper_info['venue'],
            paper_info['year']
        )

        return paper_info

    except Exception as e:
        logger.error(f"Error parsing SPARQL binding: {e}")
        return None


def parse_pub_type(pub_type_uri: str) -> str:
    """Determine publication type from SPARQL type URI"""
    if 'Article' in pub_type_uri:
        return 'article'
    elif 'Inproceedings' in pub_type_uri:
        return 'inproceedings'
    elif 'Book' in pub_type_uri:
        return 'book'
    elif 'Incollection' in pub_type_uri:
        return 'incollection'
    elif 'Proceedings' in pub_type_uri:
        return 'proceedings'
    elif 'Phdthesis' in pub_type_uri:
        return 'phdthesis'
    elif 'Mastersthesis' in pub_type_uri:
        return 'mastersthesis'
    else:
        return 'misc'


def parse_venue_from_bibtex(bibtex: str) -> str:
    """Extract venue (booktitle or journal) from a BibTeX string"""
    booktitle_match = re.search(r'booktitle\s*=\s*\{([^}]+)\}', bibtex)
    journal_match = re.search(r'journal\s*=\s*\{([^}]+)\}', bibtex)

    if booktitle_match:
        return booktitle_match.group(1).strip()
    elif journal_match:
        return journal_match.group(1).strip()
    return ''


def parse_authors_from_bibtex(bibtex: str) -> List[Dict[str, str]]:
    """Extract and clean author list from a BibTeX string"""
    author_match = re.search(r'author\s*=\s*\{([^}]+)\}', bibtex)
    if not author_match:
        return []

    author_string = author_match.group(1)
    author_parts = author_string.split(' and ')
    authors = []
    for author_part in author_parts:
        # Clean up whitespace and newlines
        author_name = ' '.join(author_part.strip().split())
        author_name = clean_author_name(author_name)
        if author_name:
            authors.append({'name': author_name})
    return authors


def generate_bibtex_from_metadata(metadata: Dict[str, Any]) -> str:
    """
    Generate BibTeX entry from metadata

    Args:
        metadata: Dictionary containing paper metadata

    Returns:
        BibTeX string
    """
    try:
        # If we have official BibTeX from DBLP, prefer that
        if metadata.get('official_bibtex'):
            return metadata['official_bibtex']
        # Determine entry type
        entry_type = metadata.get('type', 'misc')
        key = metadata.get('dblp_key', 'unknown').replace('/', '_')

        # Start BibTeX entry
        bibtex = f"@{entry_type}{{{key},\n"

        # Add authors
        if metadata.get('authors'):
            author_names = [author.get('name', '') for author in metadata['authors']]
            author_str = ' and '.join(author_names)
            bibtex += f"  author = {{{author_str}}},\n"

        # Add title
        if metadata.get('title'):
            bibtex += f"  title = {{{metadata['title']}}},\n"

        # Add venue-specific fields
        if entry_type == 'article':
            if metadata.get('venue'):
                bibtex += f"  journal = {{{metadata['venue']}}},\n"
            if metadata.get('volume'):
                bibtex += f"  volume = {{{metadata['volume']}}},\n"
            if metadata.get('number'):
                bibtex += f"  number = {{{metadata['number']}}},\n"
            if metadata.get('pages'):
                bibtex += f"  pages = {{{metadata['pages']}}},\n"
        elif entry_type == 'inproceedings':
            if metadata.get('venue'):
                bibtex += f"  booktitle = {{{metadata['venue']}}},\n"
            if metadata.get('pages'):
                bibtex += f"  pages = {{{metadata['pages']}}},\n"
            if metadata.get('series'):
                bibtex += f"  series = {{{metadata['series']}}},\n"
            if metadata.get('volume'):
                bibtex += f"  volume = {{{metadata['volume']}}},\n"
        elif entry_type == 'book':
            if metadata.get('publisher'):
                bibtex += f"  publisher = {{{metadata['publisher']}}},\n"
            if metadata.get('isbn'):
                bibtex += f"  isbn = {{{metadata['isbn']}}},\n"

        # Add year
        if metadata.get('year'):
            bibtex += f"  year = {{{metadata['year']}}},\n"

        # Add month if available
        if metadata.get('month') and metadata['month'] not in ['', '1']:
            bibtex += f"  month = {{{metadata['month']}}},\n"

        # Add DOI
        if metadata.get('doi'):
            bibtex += f"  doi = {{{metadata['doi']}}},\n"

        # Add URL (electronic edition)
        if metadata.get('ee'):
            bibtex += f"  url = {{{metadata['ee']}}},\n"

        # Remove last comma and close
        bibtex = bibtex.rstrip(',\n') + '\n}'

        return bibtex

    except Exception as e:
        logger.error(f"Error generating BibTeX: {e}")
        return ""
