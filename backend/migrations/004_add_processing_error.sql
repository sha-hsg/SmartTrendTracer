-- Add processing_error column to papers table
-- This column stores error messages when PDF processing fails or is cancelled

ALTER TABLE papers ADD COLUMN processing_error TEXT;