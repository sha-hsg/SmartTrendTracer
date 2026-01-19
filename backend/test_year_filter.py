#!/usr/bin/env python3
from pymongo import MongoClient

db = MongoClient().smarttrendtracer

# Test the year filter pipeline
year = 2025

# Build base query with year filter
base_query = {
    '$expr': {
        '$eq': [
            {
                '$cond': {
                    'if': {
                        '$and': [
                            {'$ne': ['$publication_date', None]},
                            {'$ne': ['$publication_date', '']},
                            {'$eq': [{'$type': '$publication_date'}, 'string']},
                            {'$gt': [{'$strLenCP': '$publication_date'}, 4]}
                        ]
                    },
                    'then': {'$year': {'$dateFromString': {'dateString': '$publication_date', 'onError': None}}},
                    'else': {'$year': '$created_at'}
                }
            },
            year
        ]
    }
}

# Test year pipeline
year_pipeline = [
    {'$match': base_query},
    {
        '$addFields': {
            'year': {
                '$cond': {
                    'if': {
                        '$and': [
                            {'$ne': ['$publication_date', None]},
                            {'$ne': ['$publication_date', '']},
                            {'$eq': [{'$type': '$publication_date'}, 'string']},
                            {'$gt': [{'$strLenCP': '$publication_date'}, 4]}
                        ]
                    },
                    'then': {'$year': {'$dateFromString': {'dateString': '$publication_date', 'onError': None}}},
                    'else': {'$year': '$created_at'}
                }
            }
        }
    },
    {'$match': {'year': {'$ne': None}}},  # Filter out null years
    {'$group': {
        '_id': '$year',
        'count': {'$sum': 1}
    }},
    {'$sort': {'_id': -1}},
    {'$limit': 20}
]

try:
    print("Testing year aggregation pipeline...")
    result = list(db.papers.aggregate(year_pipeline))
    print(f"Success! Found {len(result)} year groups")
    for r in result:
        print(f"  Year {r['_id']}: {r['count']} papers")
except Exception as e:
    print(f"Error: {e}")

# Test without base match
print("\nTesting without base match filter...")
year_pipeline_no_filter = [
    {
        '$addFields': {
            'year': {
                '$cond': {
                    'if': {
                        '$and': [
                            {'$ne': ['$publication_date', None]},
                            {'$ne': ['$publication_date', '']},
                            {'$eq': [{'$type': '$publication_date'}, 'string']},
                            {'$gte': [{'$strLenCP': '$publication_date'}, 4]}
                        ]
                    },
                    'then': {
                        '$year': {
                            '$dateFromString': {
                                'dateString': '$publication_date',
                                'onError': {'$year': '$created_at'}
                            }
                        }
                    },
                    'else': {'$year': '$created_at'}
                }
            }
        }
    },
    {'$match': {'year': {'$ne': None}}},
    {'$group': {
        '_id': '$year',
        'count': {'$sum': 1}
    }},
    {'$sort': {'_id': -1}}
]

try:
    result = list(db.papers.aggregate(year_pipeline_no_filter))
    print(f"Success! Found {len(result)} year groups")
    for r in result[:5]:
        print(f"  Year {r['_id']}: {r['count']} papers")
except Exception as e:
    print(f"Error: {e}")