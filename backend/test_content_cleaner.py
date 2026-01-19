#!/usr/bin/env python3
"""
Test the content cleaner utility
"""
from app.utils.content_cleaner import clean_markdown_content

# Test content with problematic tags
test_content = """
# Research Paper Analysis

<answer>
The transformer architecture introduced in this paper revolutionized NLP.
</answer>

## Key Findings

<solution>
The attention mechanism allows for parallel processing.
</solution>

Here's a normal paragraph with no tags.

<question>What is the computational complexity?</question>

The complexity is O(n²) for self-attention.

<example>
This is an example of how transformers work.
</example>
"""

print("ORIGINAL CONTENT:")
print("=" * 60)
print(test_content)

cleaned = clean_markdown_content(test_content)

print("\nCLEANED CONTENT:")
print("=" * 60)
print(cleaned)

print("\nVERIFICATION:")
print("-" * 60)

# Check that problematic tags are removed
tags_to_check = ['<answer>', '</answer>', '<solution>', '</solution>', 
                 '<question>', '</question>', '<example>', '</example>']

for tag in tags_to_check:
    if tag in cleaned:
        print(f"❌ Tag still present: {tag}")
    else:
        print(f"✅ Tag removed: {tag}")

# Check that content is preserved
important_content = [
    "transformer architecture",
    "attention mechanism", 
    "normal paragraph",
    "computational complexity",
    "O(n²)"
]

print("\nContent preservation:")
for content in important_content:
    if content in cleaned:
        print(f"✅ Content preserved: {content}")
    else:
        print(f"❌ Content lost: {content}")