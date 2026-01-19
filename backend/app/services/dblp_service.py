"""
DBLP (dblp.org) integration service for searching papers and retrieving BibTeX citations
Supports both REST API and SPARQL endpoint
"""
import logging
import re
from typing import List, Dict, Optional, Any, Tuple
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote, unquote
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class DBLPService:
    """Service for interacting with DBLP API and SPARQL endpoint"""
    
    BASE_URL = "https://dblp.org"
    SEARCH_API = f"{BASE_URL}/search/publ/api"
    SPARQL_ENDPOINT = "https://sparql.dblp.org/sparql"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SmartTrendTracer/1.0 (Academic Research Tool)'
        })
    
    def search_papers(self, title: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for papers on DBLP by title
        
        Args:
            title: Paper title to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of paper matches with metadata
        """
        try:
            # Clean and prepare the search query - keep some punctuation for better matching
            # But remove problematic characters like colons that might break the search
            query = re.sub(r'[:\'\"]', ' ', title)  # Remove colons and quotes
            query = re.sub(r'\s+', ' ', query)  # Normalize whitespace
            query = query.strip()
            
            params = {
                'q': query,
                'format': 'xml',
                'h': max_results,  # hits per page
                'c': 0  # complete search results
            }
            
            logger.info(f"Searching DBLP for: {query}")
            response = self.session.get(self.SEARCH_API, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            papers = []
            for hit in root.findall('.//hit'):
                paper_info = self._parse_hit(hit)
                if paper_info:
                    papers.append(paper_info)
            
            logger.info(f"Found {len(papers)} results on DBLP")
            return papers
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching DBLP: {e}")
            return []
        except ET.ParseError as e:
            logger.error(f"Error parsing DBLP XML response: {e}")
            return []
    
    def _parse_hit(self, hit: ET.Element) -> Optional[Dict[str, Any]]:
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
                'citation_string': self._format_citation(title_text, authors, venue_text, year_text)
            }
            
        except Exception as e:
            logger.error(f"Error parsing DBLP hit: {e}")
            return None
    
    def _format_citation(self, title: str, authors: List[str], venue: str, year: str) -> str:
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
    
    def get_bibtex(self, dblp_key: str) -> Optional[str]:
        """
        Fetch BibTeX entry for a specific DBLP record
        
        Args:
            dblp_key: DBLP key identifier (e.g., 'conf/icml/Smith20')
            
        Returns:
            BibTeX string or None if not found
        """
        try:
            # DBLP BibTeX URL pattern
            bibtex_url = f"{self.BASE_URL}/rec/{dblp_key}.bib"
            
            logger.info(f"Fetching BibTeX from: {bibtex_url}")
            response = self.session.get(bibtex_url, timeout=10)
            
            if response.status_code == 200:
                # Clean up the BibTeX
                bibtex = response.text.strip()
                
                # DBLP sometimes includes HTML, so we need to extract just the BibTeX
                if '<pre>' in bibtex:
                    # Extract content between <pre> tags
                    import re
                    match = re.search(r'<pre[^>]*>(.*?)</pre>', bibtex, re.DOTALL)
                    if match:
                        bibtex = match.group(1).strip()
                
                return bibtex
            else:
                logger.warning(f"BibTeX not found for key: {dblp_key}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching BibTeX: {e}")
            return None
    
    def search_papers_sparql(self, title: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for papers using DBLP SPARQL endpoint for more precise results
        
        Args:
            title: Paper title to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of paper matches with metadata
        """
        try:
            # Construct SPARQL query
            # Clean title for SPARQL FILTER - escape special characters properly
            # Remove colons, quotes, and other special chars that break SPARQL
            clean_title = re.sub(r'[:\"\'\(\)\[\]\{\}\\/@#$%^&*+=|<>?`~]', ' ', title)
            clean_title = re.sub(r'\s+', ' ', clean_title.lower()).strip()
            
            sparql_query = f"""
            PREFIX dblp: <https://dblp.org/rdf/schema#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?pub ?title ?year ?venue ?type ?ee ?doi
            WHERE {{
                ?pub rdf:type ?pubType .
                ?pub dblp:title ?title .
                OPTIONAL {{ ?pub dblp:year ?year }}
                OPTIONAL {{ ?pub dblp:publishedIn ?venue }}
                OPTIONAL {{ ?pub dblp:ee ?ee }}
                OPTIONAL {{ ?pub dblp:doi ?doi }}
                
                FILTER(CONTAINS(LCASE(?title), "{clean_title}"))
                FILTER(?pubType IN (dblp:Article, dblp:Inproceedings, dblp:Proceedings, 
                                   dblp:Book, dblp:Incollection, dblp:Phdthesis, dblp:Mastersthesis))
                
                BIND(
                    IF(?pubType = dblp:Article, "article",
                    IF(?pubType = dblp:Inproceedings, "inproceedings",
                    IF(?pubType = dblp:Proceedings, "proceedings",
                    IF(?pubType = dblp:Book, "book",
                    IF(?pubType = dblp:Incollection, "incollection",
                    IF(?pubType = dblp:Phdthesis, "phdthesis",
                    IF(?pubType = dblp:Mastersthesis, "mastersthesis", "other")))))))
                    AS ?type
                )
            }}
            ORDER BY DESC(?year)
            LIMIT {max_results}
            """
            
            params = {
                'query': sparql_query,
                'format': 'json'
            }
            
            logger.info(f"Executing SPARQL query for: {title}")
            response = self.session.get(self.SPARQL_ENDPOINT, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            for binding in data.get('results', {}).get('bindings', []):
                paper_info = self._parse_sparql_binding(binding)
                if paper_info:
                    papers.append(paper_info)
            
            logger.info(f"Found {len(papers)} results via SPARQL")
            return papers
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying DBLP SPARQL: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing SPARQL JSON response: {e}")
            return []
    
    def _parse_sparql_binding(self, binding: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
            paper_info['citation_string'] = self._format_citation(
                paper_info['title'], 
                [], 
                paper_info['venue'], 
                paper_info['year']
            )
            
            return paper_info
            
        except Exception as e:
            logger.error(f"Error parsing SPARQL binding: {e}")
            return None
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Wrapper method for search functionality
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of search results with dblp_key and dblp_url populated
        """
        # Use the primary search method
        return self.search_papers(query, max_results=limit)
    
    
    def get_bibtex_from_url(self, dblp_url: str) -> Optional[str]:
        """
        Fetch BibTeX entry from a DBLP URL
        
        Args:
            dblp_url: Full DBLP URL (e.g., 'https://dblp.org/rec/conf/icml/Smith20.html')
            
        Returns:
            BibTeX string or None if not found
        """
        try:
            # Remove .html if present and add .bib
            if dblp_url.endswith('.html'):
                bibtex_url = dblp_url[:-5] + '.bib'
            elif dblp_url.endswith('/'):
                bibtex_url = dblp_url[:-1] + '.bib'
            else:
                bibtex_url = dblp_url + '.bib'
            
            logger.info(f"Fetching BibTeX from: {bibtex_url}")
            response = self.session.get(bibtex_url, timeout=15)
            
            if response.status_code == 200:
                return response.text.strip()
            else:
                logger.warning(f"BibTeX not found at: {bibtex_url}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching BibTeX: {e}")
            return None
    
    def get_complete_metadata(self, dblp_key: str) -> Dict[str, Any]:
        """
        Fetch complete metadata for a paper using SPARQL
        
        Args:
            dblp_key: DBLP key identifier (e.g., 'conf/icml/Smith20')
            
        Returns:
            Dictionary with complete metadata including authors, venue, dates, etc.
        """
        try:
            # Convert key to URI
            dblp_uri = f"https://dblp.org/rec/{dblp_key}"
            
            # First, let's try to get the official BibTeX directly - it's more reliable
            official_bibtex = self.get_bibtex(dblp_key)
            
            # SPARQL query for additional metadata using proper DBLP schema
            sparql_query = f"""
            PREFIX dblp: <https://dblp.org/rdf/schema#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX datacite: <http://purl.org/spar/datacite/>
            PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
            PREFIX dblp2: <https://dblp.org/rdf/schema>
            
            SELECT DISTINCT ?title ?year ?doi ?ee ?pages ?volume ?number ?month ?pubType
                           (GROUP_CONCAT(DISTINCT ?venueFull; SEPARATOR="; ") AS ?venues)
                           (GROUP_CONCAT(DISTINCT ?seriesName; SEPARATOR="; ") AS ?series)
            WHERE {{
                <{dblp_uri}> rdfs:label ?title .
                
                OPTIONAL {{ <{dblp_uri}> dblp:yearOfPublication ?year }}
                OPTIONAL {{ <{dblp_uri}> dblp:monthOfPublication ?month }}
                OPTIONAL {{ <{dblp_uri}> dblp:pagination ?pages }}
                OPTIONAL {{ <{dblp_uri}> dblp:volume ?volume }}
                OPTIONAL {{ <{dblp_uri}> dblp:number ?number }}
                OPTIONAL {{ <{dblp_uri}> datacite:doi ?doi }}
                OPTIONAL {{ <{dblp_uri}> bibtex:hasURL ?ee }}
                OPTIONAL {{ <{dblp_uri}> rdf:type ?pubType }}
                
                # Try multiple ways to get venue information
                OPTIONAL {{
                    <{dblp_uri}> dblp:publishedIn ?venueEntity .
                    ?venueEntity rdfs:label ?venueFull .
                }}
                
                OPTIONAL {{
                    <{dblp_uri}> dblp:publishedInSeries ?seriesEntity .
                    ?seriesEntity rdfs:label ?seriesName .
                }}
            }}
            GROUP BY ?title ?year ?doi ?ee ?pages ?volume ?number ?month ?pubType
            LIMIT 1
            """
            
            # Get basic metadata
            params = {'query': sparql_query, 'format': 'json'}
            response = self.session.get(self.SPARQL_ENDPOINT, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            bindings = data.get('results', {}).get('bindings', [])
            
            if not bindings:
                logger.warning(f"No metadata found for key: {dblp_key}")
                return {}
            
            binding = bindings[0]
            
            # Start with data from official BibTeX if available
            metadata = {
                'dblp_key': dblp_key,
                'dblp_url': dblp_uri,
                'official_bibtex': official_bibtex if official_bibtex else None
            }
            
            # Parse venue from official BibTeX first (it's more accurate)
            venue_from_bibtex = ''
            if official_bibtex:
                import re
                # Try to extract booktitle or journal from BibTeX
                booktitle_match = re.search(r'booktitle\s*=\s*\{([^}]+)\}', official_bibtex)
                journal_match = re.search(r'journal\s*=\s*\{([^}]+)\}', official_bibtex)
                
                if booktitle_match:
                    venue_from_bibtex = booktitle_match.group(1).strip()
                elif journal_match:
                    venue_from_bibtex = journal_match.group(1).strip()
            
            # Extract metadata from SPARQL, using BibTeX venue as fallback
            metadata.update({
                'title': binding.get('title', {}).get('value', ''),
                'year': binding.get('year', {}).get('value', ''),
                'month': binding.get('month', {}).get('value', ''),
                'venue': binding.get('venues', {}).get('value', '') or venue_from_bibtex,
                'volume': binding.get('volume', {}).get('value', ''),
                'number': binding.get('number', {}).get('value', ''),
                'pages': binding.get('pages', {}).get('value', ''),
                'doi': binding.get('doi', {}).get('value', ''),
                'ee': binding.get('ee', {}).get('value', ''),
                'series': binding.get('series', {}).get('value', ''),
            })
            
            # Determine publication type
            pub_type_uri = binding.get('pubType', {}).get('value', '')
            if 'Article' in pub_type_uri:
                metadata['type'] = 'article'
            elif 'Inproceedings' in pub_type_uri:
                metadata['type'] = 'inproceedings'
            elif 'Book' in pub_type_uri:
                metadata['type'] = 'book'
            elif 'Incollection' in pub_type_uri:
                metadata['type'] = 'incollection'
            elif 'Proceedings' in pub_type_uri:
                metadata['type'] = 'proceedings'
            elif 'Phdthesis' in pub_type_uri:
                metadata['type'] = 'phdthesis'
            elif 'Mastersthesis' in pub_type_uri:
                metadata['type'] = 'mastersthesis'
            else:
                metadata['type'] = 'misc'
            
            # Get authors separately
            metadata['authors'] = self._get_authors_sparql(dblp_uri)
            
            # Parse publication date
            if metadata['year']:
                month = metadata.get('month', '1')
                try:
                    month_num = {
                        'January': 1, 'February': 2, 'March': 3, 'April': 4,
                        'May': 5, 'June': 6, 'July': 7, 'August': 8,
                        'September': 9, 'October': 10, 'November': 11, 'December': 12
                    }.get(month, month)
                    metadata['publication_date'] = f"{metadata['year']}-{str(month_num).zfill(2)}-01"
                except:
                    metadata['publication_date'] = f"{metadata['year']}-01-01"
            
            # If we're missing authors, try to parse from official BibTeX
            if not metadata['authors'] and official_bibtex:
                logger.info(f"Parsing authors from official BibTeX for {dblp_key}")
                import re
                author_match = re.search(r'author\s*=\s*\{([^}]+)\}', official_bibtex)
                if author_match:
                    author_string = author_match.group(1)
                    # Split by 'and' and clean up, handling various author formats
                    author_parts = author_string.split(' and ')
                    authors = []
                    for author_part in author_parts:
                        # Clean up whitespace and newlines
                        author_name = ' '.join(author_part.strip().split())
                        # Also clean disambiguation from BibTeX authors
                        author_name = re.sub(r'\s*\(disambiguation\)\s*$', '', author_name)
                        author_name = re.sub(r'\s+\d{4}$', '', author_name)  # Remove numeric suffixes
                        if author_name:
                            authors.append({'name': author_name.strip()})
                    metadata['authors'] = authors
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error fetching complete metadata: {e}")
            return {}
    
    def _get_authors_sparql(self, dblp_uri: str) -> List[Dict[str, str]]:
        """Get author information for a paper"""
        try:
            sparql_query = f"""
            PREFIX dblp: <https://dblp.org/rdf/schema#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX datacite: <http://purl.org/spar/datacite/>
            
            SELECT ?authorEntity ?authorName ?orcid
            WHERE {{
                <{dblp_uri}> dblp:authoredBy ?authorEntity .
                ?authorEntity rdfs:label ?authorName .
                OPTIONAL {{ ?authorEntity datacite:orcid ?orcid }}
            }}
            ORDER BY ?authorName
            """
            
            params = {'query': sparql_query, 'format': 'json'}
            response = self.session.get(self.SPARQL_ENDPOINT, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            authors = []
            
            for binding in data.get('results', {}).get('bindings', []):
                author_name = binding.get('authorName', {}).get('value', '')
                
                # Clean up author name - remove disambiguation suffixes
                # DBLP sometimes adds " (disambiguation)" or " 0001", " 0002" etc.
                import re
                # Remove disambiguation patterns
                author_name = re.sub(r'\s*\(disambiguation\)\s*$', '', author_name)
                author_name = re.sub(r'\s+\d{4}$', '', author_name)  # Remove numeric suffixes like " 0001"
                
                author_info = {
                    'name': author_name.strip(),
                    'dblp_url': binding.get('authorEntity', {}).get('value', ''),
                    'orcid': binding.get('orcid', {}).get('value', '') if 'orcid' in binding else ''
                }
                authors.append(author_info)
            
            return authors
            
        except Exception as e:
            logger.error(f"Error fetching authors: {e}")
            return []
    
    def generate_bibtex_from_metadata(self, metadata: Dict[str, Any]) -> str:
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


# Singleton instance
dblp_service = DBLPService()