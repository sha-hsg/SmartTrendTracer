"""
PDF Export Service for Substack Articles - MongoDB Version
NO SQLAlchemy - Pure MongoDB queries only!
"""
import os
import io
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import markdown
from html import unescape
import re
from PIL import Image as PILImage
import requests
from io import BytesIO
from bson import ObjectId

class PDFExportService:
    """Service for exporting articles to PDF - MongoDB version"""

    def __init__(self, db):
        """Initialize PDF export service with MongoDB database"""
        self.db = db  # MongoDB database instance
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for PDF"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            spaceAfter=8,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        ))

        # Author/Date style
        self.styles.add(ParagraphStyle(
            name='AuthorDate',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#888888'),
            spaceAfter=16,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))

        # Article body style
        self.styles.add(ParagraphStyle(
            name='ArticleBody',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=16,
            textColor=colors.HexColor('#333333'),
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))

        # Snippet style (for highlighted text)
        self.styles.add(ParagraphStyle(
            name='Snippet',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#444444'),
            leftIndent=20,
            rightIndent=20,
            spaceBefore=8,
            spaceAfter=4,
            fontName='Helvetica-Oblique',
            borderColor=colors.HexColor('#FFC107'),
            borderWidth=1,
            borderPadding=8,
            backColor=colors.HexColor('#FFF9E6')
        ))

        # Annotation style
        self.styles.add(ParagraphStyle(
            name='Annotation',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#555555'),
            leftIndent=20,
            spaceBefore=4,
            spaceAfter=12,
            fontName='Helvetica'
        ))

    def _clean_html_for_reportlab(self, text: str) -> str:
        """Clean HTML/markdown text for ReportLab"""
        if not text:
            return ""

        # Remove markdown image syntax
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)

        # Remove markdown links but keep text
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)

        # Remove markdown headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        text = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', text)

        # Remove extra whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)

        # Decode HTML entities
        text = unescape(text)

        # Escape special XML characters for ReportLab
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;').replace('>', '&gt;')

        # Restore the formatting tags we added
        text = text.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
        text = text.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
        text = text.replace('&lt;font', '<font').replace('&lt;/font&gt;', '</font>')

        return text.strip()

    def _markdown_to_reportlab(self, markdown_text: str) -> List:
        """Convert markdown to ReportLab flowables"""
        flowables = []

        # Split into paragraphs
        paragraphs = markdown_text.split('\n\n')

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Handle headers
            if para.startswith('#'):
                level = len(para) - len(para.lstrip('#'))
                text = para.lstrip('#').strip()
                if level == 1:
                    flowables.append(Paragraph(text, self.styles['Heading1']))
                elif level == 2:
                    flowables.append(Paragraph(text, self.styles['Heading2']))
                else:
                    flowables.append(Paragraph(text, self.styles['Heading3']))
                flowables.append(Spacer(1, 0.1 * inch))

            # Handle bullet points
            elif para.startswith('- ') or para.startswith('* '):
                lines = para.split('\n')
                for line in lines:
                    if line.startswith(('- ', '* ')):
                        text = line[2:].strip()
                        flowables.append(Paragraph(f"• {text}", self.styles['Normal']))

            # Handle code blocks
            elif para.startswith('```'):
                code = para.strip('`').strip()
                flowables.append(Paragraph(
                    f'<font face="Courier" size="9">{self._clean_html_for_reportlab(code)}</font>',
                    self.styles['Normal']
                ))
                flowables.append(Spacer(1, 0.1 * inch))

            # Regular paragraph
            else:
                clean_text = self._clean_html_for_reportlab(para)
                if clean_text:
                    flowables.append(Paragraph(clean_text, self.styles['ArticleBody']))
                    flowables.append(Spacer(1, 0.1 * inch))

        return flowables

    def _load_image_from_url(self, img_url: str, alt_text: str = "") -> Any:
        """Load image from URL for PDF"""
        try:
            response = requests.get(img_url, timeout=10)
            if response.status_code == 200:
                img_data = BytesIO(response.content)
                img = PILImage.open(img_data)

                # Resize if too large
                max_width = 400
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), PILImage.Resampling.LANCZOS)

                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Save to BytesIO
                img_buffer = BytesIO()
                img.save(img_buffer, format='JPEG')
                img_buffer.seek(0)

                return ImageReader(img_buffer)
            else:
                return Paragraph(f"[Image unavailable: {alt_text or 'No description'}]", self.styles['Normal'])
        except Exception as e:
            print(f"Failed to load image {img_url[:100]}: {str(e)}")
            return Paragraph(f"[Image unavailable: {alt_text or 'No description'}]", self.styles['Normal'])

    def export_article_to_pdf(self, article_id: str) -> bytes:
        """Export a single article to PDF"""
        # Get article from MongoDB
        try:
            if len(article_id) == 24:
                article = self.db.articles.find_one({'_id': ObjectId(article_id)})
            else:
                article = self.db.articles.find_one({'old_sqlite_id': int(article_id)})
        except Exception:
            article = None

        if not article:
            raise ValueError(f"Article with ID {article_id} not found")

        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Build content
        story = []

        # Add title
        if article.get('title'):
            story.append(Paragraph(article['title'], self.styles['CustomTitle']))

        # Add subtitle
        if article.get('subtitle'):
            story.append(Paragraph(article['subtitle'], self.styles['Subtitle']))

        # Add author and date
        author_text = []

        # Handle author - can be string, dict, or reference
        if article.get('author_name'):
            author_text.append(f"By {article['author_name']}")
        elif article.get('author'):
            if isinstance(article['author'], str):
                author_text.append(f"By {article['author']}")
            elif isinstance(article['author'], dict):
                author_text.append(f"By {article['author'].get('name', 'Unknown')}")

        if article.get('published_at'):
            pub_date = article['published_at']
            if isinstance(pub_date, datetime):
                author_text.append(pub_date.strftime("%B %d, %Y"))
            else:
                author_text.append(str(pub_date))

        if author_text:
            story.append(Paragraph(" • ".join(author_text), self.styles['AuthorDate']))

        story.append(Spacer(1, 0.5 * inch))

        # Add article content
        content = article.get('content') or article.get('content_markdown', '')
        if content:
            try:
                content_flowables = self._markdown_to_reportlab(content)
                story.extend(content_flowables)
            except Exception as e:
                print(f"Error processing markdown content: {e}")
                # Fallback to simple text
                clean_text = self._clean_html_for_reportlab(content[:5000])
                if clean_text:
                    story.append(Paragraph(clean_text, self.styles['ArticleBody']))
        elif article.get('preview'):
            clean_preview = self._clean_html_for_reportlab(article['preview'])
            if clean_preview:
                story.append(Paragraph(clean_preview, self.styles['ArticleBody']))

        # Add snippets if any
        snippets = list(self.db.article_snippets.find({
            'article_id': str(article['_id'])
        }).sort('created_at', 1))

        if snippets:
            story.append(PageBreak())
            story.append(Paragraph("Highlighted Snippets & Annotations", self.styles['Heading2']))
            story.append(Spacer(1, 0.2 * inch))

            for snippet in snippets:
                # Add snippet text
                story.append(Paragraph(f'"{snippet.get("text", "")}"', self.styles['Snippet']))

                # Add annotation if exists
                if snippet.get('annotation'):
                    story.append(Paragraph(
                        f"Note: {snippet['annotation']}",
                        self.styles['Annotation']
                    ))

                story.append(Spacer(1, 0.15 * inch))

        # Build PDF
        doc.build(story)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def export_multiple_articles_to_pdf(
        self,
        article_ids: List[str],
        title: str = "Article Collection",
        include_toc: bool = True
    ) -> bytes:
        """Export multiple articles to a single PDF"""
        # Get articles from MongoDB
        article_object_ids = []
        for aid in article_ids:
            try:
                if len(aid) == 24:
                    article_object_ids.append(ObjectId(aid))
                else:
                    # Find by old SQLite ID
                    article = self.db.articles.find_one({'old_sqlite_id': int(aid)})
                    if article:
                        article_object_ids.append(article['_id'])
            except Exception:
                continue

        articles = list(self.db.articles.find({
            '_id': {'$in': article_object_ids}
        }).sort('published_at', -1))

        if not articles:
            raise ValueError("No articles found with provided IDs")

        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Build content
        story = []

        # Add collection title page
        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph(
            f"Collection of {len(articles)} Articles",
            self.styles['Subtitle']
        ))
        story.append(Paragraph(
            f"Generated on {datetime.now(timezone.utc).strftime('%B %d, %Y')}",
            self.styles['AuthorDate']
        ))
        story.append(PageBreak())

        # Add table of contents if requested
        if include_toc and len(articles) > 1:
            story.append(Paragraph("Table of Contents", self.styles['Heading1']))
            story.append(Spacer(1, 0.3 * inch))

            toc_data = []
            for i, article in enumerate(articles, 1):
                # Get author name
                author_name = "Unknown"
                if article.get('author_name'):
                    author_name = article['author_name']
                elif article.get('author'):
                    if isinstance(article['author'], str):
                        author_name = article['author']
                    elif isinstance(article['author'], dict):
                        author_name = article['author'].get('name', 'Unknown')

                # Get published date
                pub_date = ""
                if article.get('published_at'):
                    if isinstance(article['published_at'], datetime):
                        pub_date = article['published_at'].strftime("%m/%d/%Y")
                    else:
                        pub_date = str(article['published_at'])

                title_text = article.get('title', 'Untitled')
                toc_data.append([
                    str(i),
                    title_text[:60] + "..." if len(title_text) > 60 else title_text,
                    author_name,
                    pub_date
                ])

            toc_table = Table(toc_data, colWidths=[0.5*inch, 3.5*inch, 1.5*inch, 1*inch])
            toc_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'LEFT'),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(toc_table)
            story.append(PageBreak())

        # Add each article
        for i, article in enumerate(articles):
            # Add article number if multiple articles
            if len(articles) > 1:
                story.append(Paragraph(
                    f"Article {i + 1} of {len(articles)}",
                    self.styles['Normal']
                ))
                story.append(Spacer(1, 0.2 * inch))

            # Add title
            if article.get('title'):
                story.append(Paragraph(article['title'], self.styles['CustomTitle']))

            # Add subtitle
            if article.get('subtitle'):
                story.append(Paragraph(article['subtitle'], self.styles['Subtitle']))

            # Add author and date
            author_text = []
            if article.get('author_name'):
                author_text.append(f"By {article['author_name']}")
            elif article.get('author'):
                if isinstance(article['author'], str):
                    author_text.append(f"By {article['author']}")
                elif isinstance(article['author'], dict):
                    author_text.append(f"By {article['author'].get('name', 'Unknown')}")

            if article.get('published_at'):
                if isinstance(article['published_at'], datetime):
                    author_text.append(article['published_at'].strftime("%B %d, %Y"))
                else:
                    author_text.append(str(article['published_at']))

            if author_text:
                story.append(Paragraph(" • ".join(author_text), self.styles['AuthorDate']))

            story.append(Spacer(1, 0.5 * inch))

            # Add article content
            content = article.get('content') or article.get('content_markdown', '')
            if content:
                content_flowables = self._markdown_to_reportlab(content)
                story.extend(content_flowables)
            elif article.get('preview'):
                story.append(Paragraph(article['preview'], self.styles['ArticleBody']))

            # Add page break between articles
            if i < len(articles) - 1:
                story.append(PageBreak())

        # Build PDF
        doc.build(story)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def export_author_articles_to_pdf(self, author_id: str) -> bytes:
        """Export all articles from a specific author to PDF"""
        # Get author from MongoDB
        try:
            if len(author_id) == 24:
                author = self.db.substack_authors.find_one({'_id': ObjectId(author_id)})
            else:
                author = self.db.substack_authors.find_one({'old_sqlite_id': int(author_id)})
        except Exception:
            author = None

        if not author:
            raise ValueError(f"Author with ID {author_id} not found")

        # Get all articles from this author
        articles = list(self.db.articles.find({
            'author_name': author.get('name')
        }).sort('published_at', -1))

        if not articles:
            raise ValueError(f"No articles found for author {author.get('name', 'Unknown')}")

        # Export to PDF with custom title
        article_ids = [str(article['_id']) for article in articles]
        title = f"{author.get('name', 'Unknown')} - Article Collection"

        return self.export_multiple_articles_to_pdf(article_ids, title)

    def export_recent_articles_to_pdf(self, days: int = 30, limit: int = 10) -> bytes:
        """Export recent articles from the last N days"""
        from datetime import timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Get recent articles
        articles = list(self.db.articles.find({
            'published_at': {'$gte': cutoff_date}
        }).sort('published_at', -1).limit(limit))

        if not articles:
            raise ValueError(f"No articles found from the last {days} days")

        # Export to PDF
        article_ids = [str(article['_id']) for article in articles]
        title = f"Recent Articles - Last {days} Days"

        return self.export_multiple_articles_to_pdf(article_ids, title)

    def export_tagged_articles_to_pdf(self, tag: str) -> bytes:
        """Export all articles with a specific tag"""
        # Get articles with this tag from tag_instances
        tag_instances = list(self.db.tag_instances.find({
            'content_type': 'article'
        }))

        # Get article IDs
        article_ids = [ti['content_id'] for ti in tag_instances]

        if not article_ids:
            raise ValueError(f"No articles found with tag '{tag}'")

        # Export to PDF
        title = f"Articles Tagged: {tag}"

        return self.export_multiple_articles_to_pdf(article_ids, title)
