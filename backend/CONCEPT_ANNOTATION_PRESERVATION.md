# Concept-to-Annotation Connection Preservation

## Overview
The SmartTrendTracer system maintains connections between concepts and content annotations through the `tag_instances` collection. This document explains how these connections are preserved during concept reorganization.

## Data Structure

### 1. Tag Instances Collection (`tag_instances`)
Each annotation is stored as a document with:
```javascript
{
  _id: ObjectId('...'),
  content_type: 'tweet|paper|article',  // Type of content
  content_id: '...',                    // ID of the content item
  concept_id: '...',                     // Links to tag_concepts_v2._id
  tag_type: 'auto|manual',              // How tag was created
  confidence: 0.0-1.0,                  // Confidence score
  created_at: '...',                    // Timestamp
}
```

### 2. Current Statistics
- **Total annotations**: 3,259
  - Tweets: 1,477
  - Papers: 1,304
  - Articles: 478
- **Orphaned annotations**: 0 (all linked to concepts)

## How Connections Are Preserved

### During Concept Merging

When duplicate concepts are merged, the system preserves annotations by:

1. **Updating concept_id references**: All `tag_instances` pointing to the merged concept are updated to point to the target concept:
```python
# From send_concepts_in_batches_to_gpt5.py
result = db.tag_instances.update_many(
    {'concept_id': source_concept_id},
    {'$set': {'concept_id': target_concept_id}}
)
```

2. **Example**: When merging duplicate "Applications" concepts:
   - Source: `68aa2d04857c1e09148ea8bd` (Applications and Tasks)
   - Target: `68af78566b4944766c2e6f08` (Applications & Domains)
   - All annotations pointing to source are updated to point to target

### During Tag Reorganization

The GPT-5 reorganizer preserves annotations through:

1. **MongoDB ID Preservation**: Each concept includes its MongoDB ID when sent to GPT-5:
```python
concept_data = {
    'mongodb_id': str(concept['_id']),  # Preserved for mapping
    'slug': concept.get('slug', ''),
    'display_name': concept.get('display_name', ''),
    # ... other fields
}
```

2. **Merge Proposals**: When GPT-5 suggests merging concepts, the system:
   - Updates all `tag_instances` to point to the target concept
   - Marks the source concept as "merged"
   - Preserves the merge history

3. **Alias Mapping**: When concepts become aliases:
   - Original annotations remain linked to the canonical concept
   - New annotations can use either the canonical name or aliases

### During Apply Operations

The `tag_reorganization_apply.py` endpoint preserves annotations by:

1. **Maintaining ID Mappings**:
```python
concept_id_map = {}  # Maps GPT-5 IDs to MongoDB ObjectIds
for concept_data in concepts:
    # Preserve existing concept IDs
    existing = concept_service.tag_concepts.find_one({"slug": concept["slug"]})
    if existing:
        concept_id_map[concept_data.get("id")] = str(existing["_id"])
```

2. **Mapping Orphan Tags**: Finds and links any orphaned annotations:
```python
orphan_tags = list(concept_service.tag_instances.find({"concept_id": None}))
for tag in orphan_tags:
    # Match to concept or alias
    if matched_concept_id:
        concept_service.tag_instances.update_one(
            {"_id": tag["_id"]},
            {"$set": {"concept_id": ObjectId(matched_concept_id)}}
        )
```

## Safety Mechanisms

### 1. No Deletion Policy
- Concepts are never deleted, only marked as "merged" or "inactive"
- Ensures annotations are never orphaned

### 2. Audit Trail
- Merge operations record:
  - Source concept ID
  - Target concept ID
  - Timestamp
  - Reason for merge

### 3. Validation Checks
Before applying reorganization:
```python
# Check that all annotations will remain linked
orphan_check = db.tag_instances.count_documents({
    'concept_id': {'$in': concepts_to_merge}
})
```

## Query Examples

### Find all annotations for a concept (including merged)
```javascript
// In MongoDB shell
db.tag_instances.find({
    concept_id: "68af78566b4944766c2e6f08"
})
```

### Find annotations by content type
```javascript
db.tag_instances.aggregate([
    {$match: {concept_id: "68af78566b4944766c2e6f08"}},
    {$group: {_id: "$content_type", count: {$sum: 1}}}
])
```

### Track concept usage over time
```javascript
db.tag_instances.aggregate([
    {$match: {concept_id: "68af78566b4944766c2e6f08"}},
    {$group: {
        _id: {$dateToString: {format: "%Y-%m-%d", date: "$created_at"}},
        count: {$sum: 1}
    }},
    {$sort: {_id: 1}}
])
```

## Best Practices

### 1. Before Reorganization
- Backup the database
- Count total annotations: `db.tag_instances.count()`
- Verify no orphans: `db.tag_instances.count({concept_id: null})`

### 2. During Reorganization
- Always preserve MongoDB IDs
- Use batch updates for efficiency
- Log all merge operations

### 3. After Reorganization
- Verify annotation count unchanged
- Check for new orphans
- Test content retrieval by concept

## Recovery Procedures

### If Annotations Get Orphaned
```python
# Find orphaned annotations
orphans = db.tag_instances.find({concept_id: null})

# Match by original tag text (if preserved)
for orphan in orphans:
    tag_text = orphan.get('original_tag', '').lower()
    
    # Try to find concept or alias
    concept = db.tag_concepts_v2.find_one({slug: tag_text})
    if not concept:
        alias = db.tag_aliases_v2.find_one({alias_text: tag_text})
        if alias:
            concept_id = alias['concept_id']
    
    # Relink if found
    if concept_id:
        db.tag_instances.update_one(
            {_id: orphan['_id']},
            {$set: {concept_id: concept_id}}
        )
```

### Restore from Backup
```bash
# If reorganization fails
mongorestore --db smarttrendtracer backup/smarttrendtracer
```

## Summary

The concept-to-annotation connection is preserved through:
1. **Unique MongoDB IDs** that persist across reorganizations
2. **Update operations** that relink annotations when concepts merge
3. **Alias systems** that maintain backward compatibility
4. **No-deletion policy** that prevents orphaning
5. **Validation checks** at each step

This ensures that all 3,259 annotations remain accessible and properly categorized regardless of how the concept hierarchy is reorganized.