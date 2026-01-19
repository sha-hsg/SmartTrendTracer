"""
Export service for articles and annotations
Supports multiple formats: JSON, Markdown, CSV, HTML
"""
import json
import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd

class ExportService:
    """Service for exporting articles and annotations in various formats"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def export_articles_json(self, article_ids: Optional[List[int]] = None) -> str:
        """Export articles with all related data as JSON"""
        query = self.db.query(SubstackArticle)
        
        if article_ids:
            query = query.filter(SubstackArticle.id.in_(article_ids))
        
        articles = query.all()
        
        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "total_articles": len(articles),
            "articles": []
        }
        
        for article in articles:
            article_data = {
                "id": article.id,
                "title": article.title,
                "subtitle": article.subtitle,
                "author": {
                    "name": article.author.name,
                    "subdomain": article.author.subdomain,
                    "url": article.author.url
                },
                "url": article.url,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "collected_at": article.collected_at.isoformat() if article.collected_at else None,
                "word_count": article.word_count,
                "reading_time_minutes": article.reading_time_minutes,
                "summary": article.summary,
                "key_points": article.key_points,
                "content_markdown": article.content_markdown,
                "tags": [
                    {
                        "tag": tag.tag,
                        "type": tag.tag_type,
                        "confidence": tag.confidence
                    }
                    for tag in article.tags
                ],
                "snippets": [
                    {
                        "text": snippet.text,
                        "annotation": snippet.annotation,
                        "category": snippet.category,
                        "importance": snippet.importance,
                        "created_at": snippet.created_at.isoformat()
                    }
                    for snippet in article.snippets
                ]
            }
            export_data["articles"].append(article_data)
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def export_articles_markdown(self, article_ids: Optional[List[int]] = None) -> str:
        """Export articles as a single Markdown document"""
        query = self.db.query(SubstackArticle)
        
        if article_ids:
            query = query.filter(SubstackArticle.id.in_(article_ids))
        
        articles = query.order_by(SubstackArticle.published_at.desc()).all()
        
        markdown = f"# Substack Articles Export\n\n"
        markdown += f"*Exported on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*\n\n"
        markdown += f"**Total Articles:** {len(articles)}\n\n"
        markdown += "---\n\n"
        
        for article in articles:
            # Article header
            markdown += f"## {article.title}\n\n"
            
            if article.subtitle:
                markdown += f"*{article.subtitle}*\n\n"
            
            # Metadata
            markdown += f"**Author:** {article.author.name}  \n"
            markdown += f"**Published:** {article.published_at.strftime('%Y-%m-%d') if article.published_at else 'Unknown'}  \n"
            markdown += f"**Reading Time:** {article.reading_time_minutes} minutes  \n"
            
            if article.url:
                markdown += f"**Original:** [{article.url}]({article.url})  \n"
            
            markdown += "\n"
            
            # Tags
            if article.tags:
                markdown += "**Tags:** "
                markdown += ", ".join([f"`{tag.tag}`" for tag in article.tags])
                markdown += "\n\n"
            
            # Summary
            if article.summary:
                markdown += f"### Summary\n\n{article.summary}\n\n"
            
            # Key Points
            if article.key_points:
                markdown += "### Key Points\n\n"
                for point in article.key_points:
                    markdown += f"- {point}\n"
                markdown += "\n"
            
            # Highlights/Snippets
            if article.snippets:
                markdown += "### Highlights & Annotations\n\n"
                for snippet in article.snippets:
                    markdown += f"> {snippet.text}\n"
                    if snippet.annotation:
                        markdown += f"> \n"
                        markdown += f"> **Note:** {snippet.annotation}\n"
                    if snippet.category:
                        markdown += f"> *Category: {snippet.category}*\n"
                    markdown += "\n"
            
            # Content
            markdown += "### Full Content\n\n"
            markdown += article.content_markdown or "*(No content available)*"
            markdown += "\n\n---\n\n"
        
        return markdown
    
    def export_snippets_csv(self, article_ids: Optional[List[int]] = None) -> str:
        """Export all snippets/highlights as CSV"""
        query = self.db.query(ArticleSnippet).join(SubstackArticle)
        
        if article_ids:
            query = query.filter(SubstackArticle.id.in_(article_ids))
        
        snippets = query.all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Article Title",
            "Author",
            "Published Date",
            "Snippet Text",
            "Annotation",
            "Category",
            "Importance",
            "Created At",
            "Article URL"
        ])
        
        # Data rows
        for snippet in snippets:
            writer.writerow([
                snippet.article.title,
                snippet.article.author.name,
                snippet.article.published_at.strftime('%Y-%m-%d') if snippet.article.published_at else '',
                snippet.text,
                snippet.annotation or '',
                snippet.category or '',
                snippet.importance,
                snippet.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                snippet.article.url or ''
            ])
        
        return output.getvalue()
    
    def export_articles_html(self, article_ids: Optional[List[int]] = None) -> str:
        """Export articles as a formatted HTML document"""
        query = self.db.query(SubstackArticle)
        
        if article_ids:
            query = query.filter(SubstackArticle.id.in_(article_ids))
        
        articles = query.order_by(SubstackArticle.published_at.desc()).all()
        
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Substack Articles Export</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .article {
            background: white;
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { color: #333; border-bottom: 3px solid #1da1f2; padding-bottom: 10px; }
        h2 { color: #1da1f2; margin-top: 0; }
        h3 { color: #666; margin-top: 25px; }
        .metadata {
            color: #666;
            font-size: 14px;
            margin: 15px 0;
            padding: 10px;
            background: #f8f8f8;
            border-radius: 5px;
        }
        .tag {
            display: inline-block;
            padding: 3px 10px;
            background: #e3f2fd;
            color: #1976d2;
            border-radius: 15px;
            font-size: 12px;
            margin-right: 5px;
        }
        .snippet {
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            background: #fffbf0;
            border-radius: 4px;
        }
        .snippet-text {
            font-style: italic;
            margin-bottom: 10px;
        }
        .annotation {
            color: #666;
            font-size: 14px;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e0e0e0;
        }
        .content {
            margin-top: 30px;
            line-height: 1.8;
        }
        .export-info {
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-bottom: 30px;
        }
        blockquote {
            border-left: 4px solid #ddd;
            padding-left: 20px;
            color: #666;
            margin: 20px 0;
        }
        pre {
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        a { color: #1da1f2; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>📚 Substack Articles Export</h1>
    <div class="export-info">
        Exported on {export_date} • {total_articles} articles
    </div>
"""
        
        html = html.replace("{export_date}", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))
        html = html.replace("{total_articles}", str(len(articles)))
        
        for article in articles:
            html += '<div class="article">\n'
            
            # Title and subtitle
            html += f'<h2>{article.title}</h2>\n'
            if article.subtitle:
                html += f'<p style="color: #666; font-style: italic;">{article.subtitle}</p>\n'
            
            # Metadata
            html += '<div class="metadata">\n'
            html += f'<strong>Author:</strong> {article.author.name}<br>\n'
            html += f'<strong>Published:</strong> {article.published_at.strftime("%Y-%m-%d") if article.published_at else "Unknown"}<br>\n'
            html += f'<strong>Reading Time:</strong> {article.reading_time_minutes} minutes<br>\n'
            if article.url:
                html += f'<strong>Original:</strong> <a href="{article.url}" target="_blank">{article.url}</a>\n'
            html += '</div>\n'
            
            # Tags
            if article.tags:
                html += '<div style="margin: 15px 0;">\n'
                for tag in article.tags:
                    html += f'<span class="tag">{tag.tag}</span>\n'
                html += '</div>\n'
            
            # Summary
            if article.summary:
                html += '<h3>Summary</h3>\n'
                html += f'<p>{article.summary}</p>\n'
            
            # Key Points
            if article.key_points:
                html += '<h3>Key Points</h3>\n<ul>\n'
                for point in article.key_points:
                    html += f'<li>{point}</li>\n'
                html += '</ul>\n'
            
            # Snippets
            if article.snippets:
                html += '<h3>Highlights & Annotations</h3>\n'
                for snippet in article.snippets:
                    html += '<div class="snippet">\n'
                    html += f'<div class="snippet-text">"{snippet.text}"</div>\n'
                    if snippet.annotation:
                        html += f'<div class="annotation"><strong>Note:</strong> {snippet.annotation}</div>\n'
                    if snippet.category:
                        html += f'<div style="font-size: 12px; color: #999;">Category: {snippet.category}</div>\n'
                    html += '</div>\n'
            
            # Content (convert markdown to basic HTML)
            if article.content_markdown:
                html += '<h3>Full Content</h3>\n'
                html += '<div class="content">\n'
                # Basic markdown to HTML conversion
                content = article.content_markdown
                content = content.replace('\n\n', '</p><p>')
                content = f'<p>{content}</p>'
                html += content
                html += '</div>\n'
            
            html += '</div>\n'
        
        html += """
</body>
</html>
"""
        
        return html
    
    def export_reading_list(self, article_ids: Optional[List[int]] = None) -> str:
        """Export a simple reading list with links"""
        query = self.db.query(SubstackArticle)
        
        if article_ids:
            query = query.filter(SubstackArticle.id.in_(article_ids))
        
        articles = query.order_by(SubstackArticle.published_at.desc()).all()
        
        reading_list = f"# Reading List\n\n"
        reading_list += f"Generated on {datetime.utcnow().strftime('%Y-%m-%d')}\n\n"
        
        # Group by author
        by_author = {}
        for article in articles:
            author_name = article.author.name
            if author_name not in by_author:
                by_author[author_name] = []
            by_author[author_name].append(article)
        
        for author, author_articles in by_author.items():
            reading_list += f"## {author}\n\n"
            for article in author_articles:
                date_str = article.published_at.strftime('%Y-%m-%d') if article.published_at else 'Unknown'
                reading_list += f"- [{article.title}]({article.url or '#'}) ({date_str})"
                if article.reading_time_minutes:
                    reading_list += f" • {article.reading_time_minutes} min read"
                reading_list += "\n"
            reading_list += "\n"
        
        return reading_list