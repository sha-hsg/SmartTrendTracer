"""
Analyze tag case variations in the database and identify proper capitalizations
"""
import sqlite3
from collections import defaultdict
import re

def analyze_tag_cases():
    # Connect to database
    conn = sqlite3.connect('data/tweets.db')
    cursor = conn.cursor()
    
    # Get all tags with their counts from tweets
    cursor.execute("""
        SELECT tag, COUNT(*) as count 
        FROM tags 
        GROUP BY tag 
        ORDER BY tag COLLATE NOCASE
    """)
    tweet_tags = cursor.fetchall()
    
    # Get all tags from articles
    cursor.execute("""
        SELECT tag, COUNT(*) as count 
        FROM article_tags 
        GROUP BY tag 
        ORDER BY tag COLLATE NOCASE
    """)
    article_tags = cursor.fetchall()
    
    # Combine all tags
    all_tags = {}
    for tag, count in tweet_tags:
        all_tags[tag] = {'tweet_count': count, 'article_count': 0}
    
    for tag, count in article_tags:
        if tag in all_tags:
            all_tags[tag]['article_count'] = count
        else:
            all_tags[tag] = {'tweet_count': 0, 'article_count': count}
    
    # Group tags by lowercase version
    tag_groups = defaultdict(list)
    for tag in all_tags:
        tag_lower = tag.lower()
        tag_groups[tag_lower].append({
            'tag': tag,
            'tweet_count': all_tags[tag]['tweet_count'],
            'article_count': all_tags[tag]['article_count'],
            'total_count': all_tags[tag]['tweet_count'] + all_tags[tag]['article_count']
        })
    
    # Analyze each group
    print("=" * 80)
    print("TAG CASE ANALYSIS")
    print("=" * 80)
    
    proper_forms = {}  # Will store the determined proper form for each tag group
    needs_sameas = []  # Tags that need sameAs relations
    
    for tag_lower, variants in tag_groups.items():
        if len(variants) > 1:
            # Multiple case variants exist
            print(f"\n{tag_lower}:")
            for v in sorted(variants, key=lambda x: -x['total_count']):
                print(f"  '{v['tag']}': {v['total_count']} uses (tweets: {v['tweet_count']}, articles: {v['article_count']})")
            
            # Determine the proper form
            proper = determine_proper_form(variants)
            if proper:
                proper_forms[tag_lower] = proper
                print(f"  → PROPER FORM: '{proper}'")
            else:
                needs_sameas.append(variants)
                print(f"  → UNCLEAR - needs sameAs relation")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total unique tags (case-sensitive): {len(all_tags)}")
    print(f"Total unique tags (case-insensitive): {len(tag_groups)}")
    print(f"Tags with multiple case variants: {sum(1 for v in tag_groups.values() if len(v) > 1)}")
    print(f"Tags with clear proper form: {len(proper_forms)}")
    print(f"Tags needing sameAs relations: {len(needs_sameas)}")
    
    conn.close()
    return proper_forms, needs_sameas, tag_groups

def determine_proper_form(variants):
    """
    Determine the proper capitalized form of a tag based on patterns
    """
    # Sort by usage count
    variants_sorted = sorted(variants, key=lambda x: -x['total_count'])
    
    # Extract just the tag names
    tags = [v['tag'] for v in variants_sorted]
    
    # Rules for determining proper form:
    
    # 1. Known acronyms and proper nouns
    acronyms = ['AI', 'ML', 'NLP', 'LLM', 'AGI', 'API', 'GPU', 'CPU', 'USA', 'UK', 'EU', 'R&D', 
                'CEO', 'CTO', 'PhD', 'MIT', 'NASA', 'IBM', 'AWS', 'GCP', 'IoT', 'VR', 'AR', 
                'NFT', 'DAO', 'DeFi', 'SaaS', 'PaaS', 'IaaS', 'B2B', 'B2C', 'UI', 'UX',
                'SDK', 'IDE', 'CI/CD', 'DevOps', 'MLOps', 'RAG', 'RLHF', 'PEFT', 'LoRA']
    
    for tag in tags:
        # Check if it's a known acronym
        tag_upper = tag.upper()
        for acronym in acronyms:
            if tag_upper == acronym or tag_upper.replace('-', '') == acronym:
                return tag if tag.upper() == tag else None  # Return if already uppercase
        
        # Check for acronym pattern (2-5 uppercase letters)
        if re.match(r'^[A-Z]{2,5}$', tag.replace('-', '').replace('&', '')):
            return tag
    
    # 2. Company/Product names (check for specific capitalizations)
    proper_names = {
        'openai': 'OpenAI',
        'deepmind': 'DeepMind',
        'anthropic': 'Anthropic',
        'chatgpt': 'ChatGPT',
        'gpt-4': 'GPT-4',
        'gpt-3': 'GPT-3',
        'gpt-4o': 'GPT-4o',
        'claude': 'Claude',
        'gemini': 'Gemini',
        'llama': 'LLaMA',
        'mistral': 'Mistral',
        'huggingface': 'HuggingFace',
        'tensorflow': 'TensorFlow',
        'pytorch': 'PyTorch',
        'javascript': 'JavaScript',
        'typescript': 'TypeScript',
        'github': 'GitHub',
        'gitlab': 'GitLab',
        'linkedin': 'LinkedIn',
        'youtube': 'YouTube',
        'iphone': 'iPhone',
        'ipad': 'iPad',
        'macos': 'macOS',
        'ios': 'iOS',
        'microsoft': 'Microsoft',
        'google': 'Google',
        'amazon': 'Amazon',
        'facebook': 'Facebook',
        'meta': 'Meta',
        'tesla': 'Tesla',
        'spacex': 'SpaceX',
        'nvidia': 'NVIDIA',
        'amd': 'AMD',
        'intel': 'Intel'
    }
    
    for tag in tags:
        tag_lower = tag.lower().replace('-', '').replace('_', '')
        if tag_lower in proper_names:
            # Check if any variant matches the proper form
            proper = proper_names[tag_lower]
            for variant in tags:
                if variant.replace('-', '').replace('_', '') == proper:
                    return variant
    
    # 3. If one variant is significantly more used (>70% of total uses)
    total_uses = sum(v['total_count'] for v in variants_sorted)
    if variants_sorted[0]['total_count'] > 0.7 * total_uses:
        return variants_sorted[0]['tag']
    
    # 4. Prefer Title Case for multi-word tags
    for tag in tags:
        if '-' in tag or '_' in tag or ' ' in tag:
            # Check if it's in title case
            words = re.split(r'[-_ ]', tag)
            if all(w[0].isupper() and w[1:].islower() for w in words if len(w) > 0):
                # It's in proper title case
                if variants_sorted[0]['tag'] == tag:  # And it's the most used
                    return tag
    
    # 5. For single words, prefer lowercase unless it's clearly a proper noun
    if len(tags) == 2:
        lower_variant = None
        other_variant = None
        for tag in tags:
            if tag.islower():
                lower_variant = tag
            else:
                other_variant = tag
        
        if lower_variant and other_variant:
            # Check if the capitalized version starts with uppercase (proper noun pattern)
            if other_variant[0].isupper() and other_variant[1:].islower():
                # Could be a proper noun, check usage ratio
                lower_count = next(v['total_count'] for v in variants_sorted if v['tag'] == lower_variant)
                other_count = next(v['total_count'] for v in variants_sorted if v['tag'] == other_variant)
                
                # If the capitalized version is used more, it's likely correct
                if other_count > lower_count:
                    return other_variant
                else:
                    return lower_variant
    
    # Can't determine - return None to indicate sameAs relation needed
    return None

if __name__ == "__main__":
    proper_forms, needs_sameas, tag_groups = analyze_tag_cases()
    
    # Save results for migration script
    import json
    results = {
        'proper_forms': proper_forms,
        'needs_sameas': [[v['tag'] for v in group] for group in needs_sameas],
        'total_groups': len(tag_groups)
    }
    
    with open('tag_normalization_plan.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to tag_normalization_plan.json")