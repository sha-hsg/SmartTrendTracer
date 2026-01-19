"""
Test script to debug OpenReview API and understand the response structure
"""
import requests
import json
from pprint import pprint

def test_openreview_api(forum_id="ZZ4tcxJvux"):
    """Test OpenReview API endpoints to understand the data structure"""
    
    print(f"Testing OpenReview API for forum ID: {forum_id}")
    print("=" * 60)
    
    # Test 1: Notes API v2 (current)
    print("\n1. Testing Notes API v2...")
    api_url = f"https://api2.openreview.net/notes"
    params = {'id': forum_id}
    
    try:
        response = requests.get(api_url, params=params, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response type: {type(data)}")
            
            if 'notes' in data:
                notes = data['notes']
                if notes and len(notes) > 0:
                    note = notes[0]
                    print("\nNote structure keys:", list(note.keys()))
                    
                    # Check content structure
                    if 'content' in note:
                        content = note['content']
                        print("\nContent keys:", list(content.keys()))
                        
                        # Print each content field
                        for key, value in content.items():
                            if isinstance(value, dict) and 'value' in value:
                                print(f"\n{key}: {value['value'][:200] if isinstance(value['value'], str) else value['value']}")
                            else:
                                print(f"\n{key}: {value[:200] if isinstance(value, str) else value}")
    except Exception as e:
        print(f"Error with v2 API: {e}")
    
    # Test 2: Try the older API v1
    print("\n2. Testing Notes API v1...")
    api_url_v1 = f"https://api.openreview.net/notes"
    
    try:
        response = requests.get(api_url_v1, params=params, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'notes' in data and data['notes']:
                note = data['notes'][0]
                print("\nV1 Note structure keys:", list(note.keys()))
                if 'content' in note:
                    print("V1 Content keys:", list(note['content'].keys()))
    except Exception as e:
        print(f"Error with v1 API: {e}")
    
    # Test 3: Try the forum endpoint directly
    print("\n3. Testing Forum Details API...")
    forum_url = f"https://api2.openreview.net/notes?forum={forum_id}&details=original"
    
    try:
        response = requests.get(forum_url, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'notes' in data and data['notes']:
                note = data['notes'][0]
                
                # Look for invitation details which might have venue info
                if 'invitation' in note:
                    print(f"\nInvitation: {note['invitation']}")
                
                # Look for signatures (might have author info)
                if 'signatures' in note:
                    print(f"\nSignatures: {note['signatures']}")
                
                # Check for venue in content
                if 'content' in note:
                    content = note['content']
                    if 'venue' in content:
                        print(f"\nVenue: {content['venue']}")
                    if 'venueid' in content:
                        print(f"\nVenue ID: {content['venueid']}")
                        
    except Exception as e:
        print(f"Error with forum details API: {e}")
    
    # Test 4: Check if we need to make additional calls for full data
    print("\n4. Testing with details=replyCount,writable,signatures...")
    details_url = f"https://api2.openreview.net/notes?id={forum_id}&details=replyCount,invitation,original"
    
    try:
        response = requests.get(details_url, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # Save full response for analysis
            with open('openreview_response.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("\nFull response saved to openreview_response.json")
            
            if 'notes' in data and data['notes']:
                note = data['notes'][0]
                
                # Extract all the metadata we need
                content = note.get('content', {})
                
                # Title
                title = content.get('title', {})
                if isinstance(title, dict):
                    title = title.get('value', 'No title')
                print(f"\nTitle: {title}")
                
                # Authors
                authors = content.get('authors', {})
                if isinstance(authors, dict):
                    authors = authors.get('value', [])
                print(f"Authors: {authors}")
                
                # Abstract
                abstract = content.get('abstract', {})
                if isinstance(abstract, dict):
                    abstract = abstract.get('value', '')
                print(f"Abstract: {abstract[:200]}...")
                
                # Venue
                venue = content.get('venue', {})
                if isinstance(venue, dict):
                    venue = venue.get('value', '')
                print(f"Venue: {venue}")
                
                # Publication date from cdate
                if 'cdate' in note:
                    from datetime import datetime
                    cdate = datetime.fromtimestamp(note['cdate'] / 1000)
                    print(f"Creation Date: {cdate}")
                
                # Look for conference from invitation
                if 'invitation' in note:
                    invitation = note['invitation']
                    # Extract conference from invitation string
                    # e.g., "ICLR.cc/2024/Conference/-/Submission"
                    parts = invitation.split('/')
                    if len(parts) >= 3:
                        conference = f"{parts[0]} {parts[1]}"
                        print(f"Conference (from invitation): {conference}")
                        
    except Exception as e:
        print(f"Error with detailed API: {e}")

if __name__ == "__main__":
    # Test with the provided forum ID
    test_openreview_api("ZZ4tcxJvux")
    
    # Also test with another known paper
    print("\n" + "=" * 60)
    print("Testing with another paper...")
    print("=" * 60)
    test_openreview_api("HJxyAHggxE")  # Another random OpenReview paper