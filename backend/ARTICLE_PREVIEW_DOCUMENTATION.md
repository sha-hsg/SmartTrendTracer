# Article Preview System Documentation

## Overview
Article previews are short text snippets displayed in the faceted article browser. They provide users with a quick summary of article content without HTML formatting, images, or markdown syntax.

## How Previews Are Generated

### Initial Generation (During Import)
When articles are imported via `url_article_importer.py` or the Gmail collector, previews are automatically generated from the markdown content:

1. **Source**: Generated from `content_markdown` field
2. **Length**: Default 300-500 characters
3. **Process**:
   - Remove all markdown formatting (headers, bold, italics, links, code)
   - Convert multiple newlines to spaces
   - Truncate to specified length at word boundary
   - Add "..." if truncated

### Preview Generation Function
Located in `app/services/url_article_importer.py`:
```python
def _generate_preview(self, markdown: str, length: int = 300) -> str:
    preview = re.sub(r'#+ ', '', markdown)  # Headers
    preview = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'\1', preview)  # Bold/italic
    preview = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', preview)  # Links
    preview = re.sub(r'`([^`]+)`', r'\1', preview)  # Code
    preview = re.sub(r'\n+', ' ', preview)  # Newlines to spaces
    
    if len(preview) > length:
        preview = preview[:length].rsplit(' ', 1)[0] + '...'
    
    return preview.strip()
```

## Common Issues with Previews

### 1. CDN Image References
**Problem**: Previews may contain broken Substack CDN or S3 image URLs that return 404 errors.

**Example**:
```
![](https://substackcdn.com/image/fetch/...)
<img src="https://s3.amazonaws.com/...">
```

**Solution**: Run the cleanup scripts or regenerate previews.

### 2. HTML Artifacts
**Problem**: Some previews contain HTML tags or entities.

**Example**:
```html
&nbsp;&lt;div&gt;Some text&lt;/div&gt;
```

**Solution**: Regenerate previews with enhanced cleaning.

### 3. Truncation Issues
**Problem**: Previews cut off mid-word or mid-sentence.

**Solution**: Regenerate with better sentence boundary detection.

## Regenerating Previews

### Using the Regeneration Script

The `regenerate_article_previews.py` script provides flexible preview regeneration:

#### Regenerate All Previews
```bash
cd backend
python regenerate_article_previews.py
```

#### Dry Run (Preview Changes)
```bash
python regenerate_article_previews.py --dry-run
```

#### Custom Length
```bash
python regenerate_article_previews.py --length 400
```

#### Specific Article
```bash
python regenerate_article_previews.py --article-id 65abc123def456789
```

#### Limit Processing
```bash
python regenerate_article_previews.py --limit 10
```

### What the Script Does

1. **Fetches articles** from MongoDB
2. **Extracts markdown content** from `content_markdown` field
3. **Removes unwanted content**:
   - CDN image URLs (substackcdn.com, s3.amazonaws.com)
   - Local image references (/api/articles/...)
   - All markdown formatting
   - HTML tags and entities
4. **Intelligently truncates**:
   - Tries to cut at sentence boundaries
   - Falls back to word boundaries
   - Adds ellipsis when truncated
5. **Updates database** with clean previews

### Enhanced Features

The regeneration script includes improvements over the original:
- Better CDN URL removal (multiple patterns)
- HTML entity decoding
- Sentence-aware truncation
- Verification of results
- Dry-run mode for testing

## Maintenance Scripts

### Check for CDN Images
```bash
python check_remaining_cdn_images.py
```
Shows which articles have CDN URLs in their preview fields.

### Clean CDN References
```bash
python clean_remaining_cdn_previews.py
```
Removes all CDN URLs from preview fields without regenerating entire preview.

### Update to Local Images
```bash
python update_preview_images.py
```
Attempts to replace CDN URLs with local image paths where available.

## Best Practices

1. **Regular Regeneration**: Run preview regeneration after bulk imports or when formatting issues are noticed.

2. **Verify After Updates**: Always check for remaining CDN URLs after regeneration:
   ```bash
   python regenerate_article_previews.py --dry-run --limit 5
   ```

3. **Consistent Length**: Use 500 characters for better content representation while keeping load times fast.

4. **Monitor Quality**: Check the faceted browser regularly for preview quality issues.

## Database Fields

Articles in MongoDB have these relevant fields:
- `content`: Original HTML content
- `content_markdown`: Markdown version of content
- `preview`: Text preview (300-500 chars)
- `images`: Array of image metadata with local paths

## API Endpoints

Previews are included in:
- `GET /api/articles` - List view includes preview field
- `GET /api/articles/{id}` - Full article includes preview

## Troubleshooting

### Preview Shows "[object Object]" or Similar
**Cause**: JavaScript object accidentally stored as preview
**Fix**: Regenerate preview from markdown content

### Preview is Empty
**Cause**: No markdown content available
**Fix**: Check if `content_markdown` field exists and has content

### Preview Has Broken Characters
**Cause**: Encoding issues or special Unicode characters
**Fix**: Regenerate with proper UTF-8 handling

### Images Still Showing as Broken
**Cause**: Preview contains image markdown/HTML
**Fix**: Run `regenerate_article_previews.py` to strip all image references

## Future Improvements

1. **Smart Summarization**: Use AI to generate actual summaries instead of truncation
2. **Keyword Extraction**: Include key topics in preview
3. **Dynamic Length**: Adjust preview length based on viewport
4. **Rich Previews**: Support formatted previews with basic styling
5. **Caching**: Cache generated previews for performance