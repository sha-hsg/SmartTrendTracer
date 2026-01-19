"""
Test the complete OpenReview import with all fields
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.openreview_service import OpenReviewService
from pprint import pprint

def test_openreview_import():
    """Test importing a paper from OpenReview"""
    
    service = OpenReviewService()
    
    # Test URL from user
    test_url = "https://openreview.net/forum?id=ZZ4tcxJvux"
    
    print(f"Testing OpenReview import for: {test_url}")
    print("=" * 60)
    
    # Extract forum ID
    forum_id = service.extract_forum_id_from_url(test_url)
    print(f"Extracted Forum ID: {forum_id}")
    
    # Fetch metadata
    metadata = service.fetch_paper_metadata(forum_id)
    
    if metadata:
        print("\n✅ Successfully fetched metadata!")
        print("\nExtracted fields:")
        print(f"  Title: {metadata.get('title', 'N/A')}")
        print(f"  Authors: {', '.join(metadata.get('authors', [])) if metadata.get('authors') else 'N/A'}")
        print(f"  Venue: {metadata.get('venue', 'N/A')}")
        print(f"  Year: {metadata.get('year', 'N/A')}")
        print(f"  Keywords: {', '.join(metadata.get('keywords', [])) if metadata.get('keywords') else 'N/A'}")
        print(f"  TL;DR: {metadata.get('tldr', 'N/A')[:100]}..." if metadata.get('tldr') else "  TL;DR: N/A")
        print(f"  Abstract: {metadata.get('abstract', 'N/A')[:100]}..." if metadata.get('abstract') else "  Abstract: N/A")
        print(f"  PDF URL: {metadata.get('pdf_url', 'N/A')}")
        print(f"  OpenReview URL: {metadata.get('openreview_url', 'N/A')}")
        print(f"  Publication Date: {metadata.get('publication_date', 'N/A')}")
        
        # Check supplementary materials
        if metadata.get('supplementary'):
            print(f"\n  Supplementary Materials:")
            for supp in metadata['supplementary']:
                print(f"    - {supp['type']}: {supp['url']}")
        
        # Check BibTeX
        if metadata.get('bibtex'):
            print(f"\n  BibTeX (first 200 chars):")
            print(f"    {metadata['bibtex'][:200]}...")
        else:
            # Generate BibTeX if not provided
            bibtex = service.generate_bibtex(metadata)
            print(f"\n  Generated BibTeX (first 200 chars):")
            print(f"    {bibtex[:200]}...")
    else:
        print("\n❌ Failed to fetch metadata")
    
    # Test another paper (if you want)
    print("\n" + "=" * 60)
    print("Testing with another paper (ICLR 2024)...")
    print("=" * 60)
    
    test_url2 = "https://openreview.net/forum?id=2Hw2bPOPjp"
    forum_id2 = service.extract_forum_id_from_url(test_url2)
    metadata2 = service.fetch_paper_metadata(forum_id2)
    
    if metadata2:
        print(f"\n✅ Paper 2: {metadata2.get('title', 'N/A')}")
        print(f"  Authors: {', '.join(metadata2.get('authors', [])) if metadata2.get('authors') else 'N/A'}")
        print(f"  Venue: {metadata2.get('venue', 'N/A')}")
    else:
        print("\n❌ Failed to fetch metadata for paper 2")

if __name__ == "__main__":
    test_openreview_import()