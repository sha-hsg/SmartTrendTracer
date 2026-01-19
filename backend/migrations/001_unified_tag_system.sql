-- Migration 001: Unified Tag System
-- This migration creates the new unified tag architecture
-- Run this BEFORE the data migration script

-- Step 1: Create enum types (for PostgreSQL)
-- For SQLite, these will be CHECK constraints instead

-- Step 2: Create the tag_instances table
CREATE TABLE IF NOT EXISTS tag_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Content reference
    content_type VARCHAR(20) NOT NULL CHECK(content_type IN ('tweet', 'article', 'paper', 'snippet')),
    content_id VARCHAR(255) NOT NULL,
    
    -- Link to concept (the key improvement)
    concept_id INTEGER NOT NULL,
    
    -- Original tag as entered
    raw_tag VARCHAR(255) NOT NULL,
    
    -- Tag metadata
    tag_type VARCHAR(20) DEFAULT 'manual' CHECK(tag_type IN ('manual', 'ai_suggested', 'auto', 'system')),
    confidence REAL DEFAULT 1.0,
    
    -- User tracking
    created_by VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Soft delete
    deleted BOOLEAN DEFAULT 0,
    deleted_at TIMESTAMP,
    
    -- Foreign key to tag_concepts
    FOREIGN KEY (concept_id) REFERENCES tag_concepts(id) ON DELETE CASCADE
);

-- Step 3: Create indexes for performance
CREATE INDEX idx_tag_instances_content ON tag_instances(content_type, content_id);
CREATE INDEX idx_tag_instances_concept ON tag_instances(concept_id);
CREATE INDEX idx_tag_instances_raw_tag ON tag_instances(raw_tag);
CREATE INDEX idx_tag_instances_created_at ON tag_instances(created_at);
CREATE INDEX idx_tag_instances_deleted ON tag_instances(deleted);

-- Step 4: Create unique constraint for content-concept pairs
-- SQLite doesn't support partial indexes in the same way, so we'll enforce in application
CREATE UNIQUE INDEX uq_tag_instances_content_concept 
ON tag_instances(content_type, content_id, concept_id) 
WHERE deleted = 0;

-- Step 5: Create extended concept info table
CREATE TABLE IF NOT EXISTS tag_concept_extended (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id INTEGER UNIQUE NOT NULL,
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    
    -- Quality metrics
    quality_score REAL DEFAULT 1.0,
    
    -- Metadata
    auto_created BOOLEAN DEFAULT 0,
    verified BOOLEAN DEFAULT 0,
    
    -- Configuration
    allow_auto_tagging BOOLEAN DEFAULT 1,
    min_confidence REAL DEFAULT 0.5,
    
    -- Rich description
    description TEXT,
    external_url VARCHAR(500),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (concept_id) REFERENCES tag_concepts(id) ON DELETE CASCADE
);

-- Step 6: Create migration log table
CREATE TABLE IF NOT EXISTS tag_migration_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- What was migrated
    source_table VARCHAR(50) NOT NULL,
    source_id INTEGER,
    
    -- Original data
    original_tag VARCHAR(255) NOT NULL,
    original_content_id VARCHAR(255) NOT NULL,
    
    -- New data
    tag_instance_id INTEGER,
    concept_id INTEGER,
    
    -- Migration metadata
    migration_status VARCHAR(20),
    migration_notes TEXT,
    
    -- Timestamp
    migrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (tag_instance_id) REFERENCES tag_instances(id),
    FOREIGN KEY (concept_id) REFERENCES tag_concepts(id)
);

-- Step 7: Create indexes for migration log
CREATE INDEX idx_migration_log_source ON tag_migration_log(source_table, source_id);
CREATE INDEX idx_migration_log_status ON tag_migration_log(migration_status);

-- Step 8: Add columns to existing tag_concepts table if they don't exist
-- These help with the transition
-- Note: SQLite doesn't support IF NOT EXISTS for columns, so we'll handle errors in application
-- These columns may already exist, which is fine
-- ALTER TABLE tag_concepts ADD COLUMN migration_completed BOOLEAN DEFAULT 0;
-- ALTER TABLE tag_concepts ADD COLUMN old_tag_count INTEGER DEFAULT 0;

-- Step 9: Create views for backward compatibility during transition
-- These views help existing code work during migration

-- View for tweet tags (mimics old tags table structure)
CREATE VIEW IF NOT EXISTS tags_view AS
SELECT 
    ti.id,
    ti.content_id as tweet_id,
    COALESCE(tc.display_name, ti.raw_tag) as tag,
    ti.tag_type,
    ti.confidence,
    ti.created_at
FROM tag_instances ti
LEFT JOIN tag_concepts tc ON ti.concept_id = tc.id
WHERE ti.content_type = 'tweet' AND ti.deleted = 0;

-- View for article tags
CREATE VIEW IF NOT EXISTS article_tags_view AS
SELECT 
    ti.id,
    ti.content_id as article_id,
    COALESCE(tc.display_name, ti.raw_tag) as tag,
    ti.tag_type,
    ti.created_at
FROM tag_instances ti
LEFT JOIN tag_concepts tc ON ti.concept_id = tc.id
WHERE ti.content_type = 'article' AND ti.deleted = 0;

-- View for paper tags
CREATE VIEW IF NOT EXISTS paper_tags_view AS
SELECT 
    ti.id,
    ti.content_id as paper_id,
    COALESCE(tc.display_name, ti.raw_tag) as tag,
    ti.tag_type,
    ti.created_at
FROM tag_instances ti
LEFT JOIN tag_concepts tc ON ti.concept_id = tc.id
WHERE ti.content_type = 'paper' AND ti.deleted = 0;

-- Step 10: Create helper functions (as views in SQLite)
-- Get all tags for a piece of content
CREATE VIEW IF NOT EXISTS content_tags AS
SELECT 
    ti.content_type,
    ti.content_id,
    tc.id as concept_id,
    tc.tag as concept_tag,
    tc.display_name,
    ti.raw_tag,
    ti.tag_type,
    ti.confidence,
    ti.created_at
FROM tag_instances ti
JOIN tag_concepts tc ON ti.concept_id = tc.id
WHERE ti.deleted = 0
ORDER BY ti.created_at DESC;

-- Step 11: Create triggers for updated_at (SQLite specific)
CREATE TRIGGER IF NOT EXISTS update_tag_instances_updated_at 
AFTER UPDATE ON tag_instances
BEGIN
    UPDATE tag_instances SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_tag_concept_extended_updated_at 
AFTER UPDATE ON tag_concept_extended
BEGIN
    UPDATE tag_concept_extended SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Step 12: Create trigger to update usage counts
CREATE TRIGGER IF NOT EXISTS update_usage_count_on_insert
AFTER INSERT ON tag_instances
WHEN NEW.deleted = 0
BEGIN
    UPDATE tag_concept_extended 
    SET usage_count = usage_count + 1,
        last_used_at = CURRENT_TIMESTAMP
    WHERE concept_id = NEW.concept_id;
END;

CREATE TRIGGER IF NOT EXISTS update_usage_count_on_delete
AFTER UPDATE ON tag_instances
WHEN OLD.deleted = 0 AND NEW.deleted = 1
BEGIN
    UPDATE tag_concept_extended 
    SET usage_count = MAX(0, usage_count - 1)
    WHERE concept_id = NEW.concept_id;
END;

-- Step 13: Add migration version tracking
CREATE TABLE IF NOT EXISTS migration_version (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- Ensure only one row
    version INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR REPLACE INTO migration_version (id, version, name) 
VALUES (1, 1, '001_unified_tag_system');

-- Migration complete!
-- Next: Run the data migration script (002_migrate_existing_tags.py)