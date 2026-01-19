#!/usr/bin/env python3
from pymongo import MongoClient

db = MongoClient().smarttrendtracer

# Check papers with concepts
papers_with_concepts = db.papers.count_documents({
    'concept_ids': {'$exists': True, '$ne': [], '$ne': None}
})
print(f'Papers with concepts: {papers_with_concepts}')

# Check total papers
total_papers = db.papers.count_documents({})
print(f'Total papers: {total_papers}')

# Sample a paper with concepts
sample = db.papers.find_one({'concept_ids': {'$exists': True, '$ne': [], '$ne': None}})
if sample:
    print(f"\nSample paper: {sample.get('title')}")
    print(f"Concept IDs: {sample.get('concept_ids')}")