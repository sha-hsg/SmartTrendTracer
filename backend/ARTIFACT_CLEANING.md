# Substack Article Artifact Cleaning

## Overview
Comprehensive cleaning system that removes HTML-to-Markdown conversion artifacts while preserving actual content.

## Artifacts Removed

### 1. Pipe Prefixes
**Before:**
```
| | | [View in browser](link)
| | [Author Name](link)
| | ![Image](url)
```

**After:**
```
[View in browser](link)
[Author Name](link)
![Image](url)
```

### 2. Image Table Artifacts
**Before:**
```
| ![Article image](url)|
---|---|---
```

**After:**
```
![Article image](url)
```

### 3. Empty Table Structures
- Lines with just `|` or `| |` or `| | |`
- Table separators like `---|---|---`
- Standalone dash lines `---` (unless they're markdown horizontal rules)

### 4. Invisible Characters
- Unicode invisible characters (U+034F, U+200B, etc.)
- Zero-width spaces and joiners
- Non-breaking spaces that cause incorrect word counts

## Implementation

### Automatic Collection-Time Cleaning
The Gmail Substack collector (`python -m app.collectors.gmail_substack_collector`) automatically performs comprehensive artifact cleaning through the `_clean_markdown()` method:

1. **First pass**: Removes leading pipe prefixes while preserving content
2. **Second pass**: Cleans image tables (removes pipes and separators around images)
3. **Third pass**: Removes empty table artifacts and separators
4. Preserves legitimate markdown structures (images, links, horizontal rules)

This cleaning happens automatically during collection - no additional steps needed!

### Database Cleaning
Three cleaning passes on existing articles:
- Removed 860 lines with pipe prefixes
- Removed 448 empty table artifact lines  
- Removed 421 image table artifacts
- Cleaned invisible characters from 18 articles

## Results
- ✅ Clean, readable markdown without formatting artifacts
- ✅ Preserved all actual content (links, images, text)
- ✅ Accurate word counts without invisible character interference
- ✅ Automatic cleaning during email collection

## Examples

### Full Transformation
**Original (from email):**
```
| | | [View in browser](...)
---|---|---
| | ![Article image](...)
---
| | [Author Name](...)
| Aug 11| | | ∙| | Paid
---|---|---
```

**Cleaned:**
```
[View in browser](...)
![Article image](...)
[Author Name](...)
Aug 11 ∙ Paid
```

## Testing
To verify cleaning is working:
```bash
# Check for pipe prefixes
sqlite3 data/tweets.db "SELECT content_markdown FROM substack_articles LIMIT 1;" | grep "^|"

# Check for empty artifacts
sqlite3 data/tweets.db "SELECT content_markdown FROM substack_articles LIMIT 1;" | grep -E "^---|---|---$"
```

Both should return no results if cleaning is successful.