"""
PDF Export Service for Substack Articles
"""
import os
import io
from typing import List, Optional, Dict, Any
from datetime import datetime
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
from sqlalchemy.orm import Session
from PIL import Image as PILImage
import requests
from io import BytesIO

from app.models import SubstackArticle, SubstackAuthor, ArticleSnippet


class PDFExportService:
    """Service for exporting articles to PDF"""
    
    def __init__(self, db: Session):
        """Initialize PDF export service"""
        self.db = db
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
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        ))
        
        # Author and date style
        self.styles.add(ParagraphStyle(
            name='AuthorDate',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#888888'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Article body style
        self.styles.add(ParagraphStyle(
            name='ArticleBody',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        ))
        
        # Quote style
        self.styles.add(ParagraphStyle(
            name='Quote',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=16,
            leftIndent=30,
            rightIndent=30,
            textColor=colors.HexColor('#555555'),
            fontName='Helvetica-Oblique',
            spaceAfter=12
        ))
        
        # Code style
        self.styles.add(ParagraphStyle(
            name='CodeBlock',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Courier',
            backColor=colors.HexColor('#f5f5f5'),
            borderColor=colors.HexColor('#dddddd'),
            borderWidth=1,
            borderPadding=10,
            spaceAfter=12
        ))
        
        # Snippet style
        self.styles.add(ParagraphStyle(
            name='Snippet',
            parent=self.styles['Normal'],
            fontSize=10,
            leftIndent=20,
            rightIndent=20,
            backColor=colors.HexColor('#fff9e6'),
            borderColor=colors.HexColor('#ffd700'),
            borderWidth=1,
            borderPadding=10,
            spaceAfter=12
        ))
    
    def _markdown_to_reportlab(self, markdown_text: str) -> List:
        """Convert markdown text to ReportLab flowables with image support"""
        if not markdown_text:
            return []
        
        flowables = []
        
        # First, let's handle images in markdown format ![alt](url)
        lines = markdown_text.split('\n')
        current_paragraph = []
        
        for line in lines:
            # Check for markdown image syntax
            img_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
            img_matches = re.findall(img_pattern, line)
            
            if img_matches:
                # First, add any accumulated paragraph text
                if current_paragraph:
                    para_text = ' '.join(current_paragraph).strip()
                    if para_text:
                        para_text = self._clean_html_for_reportlab(para_text)
                        if para_text:
                            flowables.append(Paragraph(para_text, self.styles['ArticleBody']))
                            flowables.append(Spacer(1, 0.1 * inch))
                    current_paragraph = []
                
                # Process each image
                for alt_text, img_url in img_matches:
                    img_flowable = self._create_image_flowable(img_url, alt_text)
                    if img_flowable:
                        flowables.append(img_flowable)
                        flowables.append(Spacer(1, 0.2 * inch))
                        
                        # Add caption if alt text exists
                        if alt_text:
                            caption = Paragraph(f"<i>{alt_text}</i>", self.styles['Normal'])
                            flowables.append(caption)
                            flowables.append(Spacer(1, 0.2 * inch))
            
            # Check for HTML img tags
            elif '<img' in line:
                # Extract image URL from HTML
                img_src_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
                src_matches = re.findall(img_src_pattern, line)
                
                if src_matches:
                    # Add accumulated text
                    if current_paragraph:
                        para_text = ' '.join(current_paragraph).strip()
                        if para_text:
                            flowables.append(Paragraph(para_text, self.styles['ArticleBody']))
                            flowables.append(Spacer(1, 0.1 * inch))
                        current_paragraph = []
                    
                    for img_url in src_matches:
                        img_flowable = self._create_image_flowable(img_url, "")
                        if img_flowable:
                            flowables.append(img_flowable)
                            flowables.append(Spacer(1, 0.2 * inch))
            
            # Handle headings
            elif line.startswith('#'):
                # Add accumulated text first
                if current_paragraph:
                    para_text = ' '.join(current_paragraph).strip()
                    if para_text:
                        para_text = self._clean_html_for_reportlab(para_text)
                        if para_text:
                            flowables.append(Paragraph(para_text, self.styles['ArticleBody']))
                            flowables.append(Spacer(1, 0.1 * inch))
                    current_paragraph = []
                
                # Process heading
                heading_level = len(line) - len(line.lstrip('#'))
                heading_text = line.lstrip('#').strip()
                
                if heading_level == 1:
                    style = self.styles['Heading1']
                elif heading_level == 2:
                    style = self.styles['Heading2']
                elif heading_level == 3:
                    style = self.styles['Heading3']
                else:
                    style = self.styles['Heading4']
                
                flowables.append(Paragraph(heading_text, style))
                flowables.append(Spacer(1, 0.15 * inch))
            
            # Handle blockquotes
            elif line.startswith('>'):
                # Add accumulated text first
                if current_paragraph:
                    para_text = ' '.join(current_paragraph).strip()
                    if para_text:
                        para_text = self._clean_html_for_reportlab(para_text)
                        if para_text:
                            flowables.append(Paragraph(para_text, self.styles['ArticleBody']))
                            flowables.append(Spacer(1, 0.1 * inch))
                    current_paragraph = []
                
                quote_text = line.lstrip('>').strip()
                flowables.append(Paragraph(quote_text, self.styles['Quote']))
                flowables.append(Spacer(1, 0.1 * inch))
            
            # Handle code blocks
            elif line.startswith('```'):
                # This is a code fence, accumulate until closing fence
                if current_paragraph:
                    para_text = ' '.join(current_paragraph).strip()
                    if para_text:
                        para_text = self._clean_html_for_reportlab(para_text)
                        if para_text:
                            flowables.append(Paragraph(para_text, self.styles['ArticleBody']))
                            flowables.append(Spacer(1, 0.1 * inch))
                    current_paragraph = []
            
            # Empty line - end current paragraph
            elif not line.strip():
                if current_paragraph:
                    para_text = ' '.join(current_paragraph).strip()
                    if para_text:
                        para_text = self._clean_html_for_reportlab(para_text)
                        if para_text:
                            flowables.append(Paragraph(para_text, self.styles['ArticleBody']))
                            flowables.append(Spacer(1, 0.1 * inch))
                    current_paragraph = []
            
            # Regular text line
            else:
                current_paragraph.append(line)
        
        # Add any remaining paragraph
        if current_paragraph:
            para_text = ' '.join(current_paragraph).strip()
            if para_text:
                # Clean up HTML - remove all tags and their attributes
                para_text = self._clean_html_for_reportlab(para_text)
                if para_text:
                    flowables.append(Paragraph(para_text, self.styles['ArticleBody']))
                    flowables.append(Spacer(1, 0.1 * inch))
        
        return flowables
    
    def _clean_html_for_reportlab(self, text: str) -> str:
        """Clean HTML tags and attributes that ReportLab doesn't support"""
        # First remove script and style content
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove all HTML tags with their attributes
        text = re.sub(r'<[^>]+>', '', text)
        
        # Unescape HTML entities
        text = unescape(text)
        
        # Remove any remaining XML/HTML artifacts
        text = text.replace('<para>', '').replace('</para>', '')
        text = text.replace('<span>', '').replace('</span>', '')
        
        # Clean up problematic characters for ReportLab
        text = text.replace('\x00', '')  # Null bytes
        text = text.replace('\r', '')    # Carriage returns
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        # Escape XML special characters for ReportLab
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        
        return text.strip()
    
    def _create_image_flowable(self, img_url: str, alt_text: str = ""):
        """Create an image flowable from URL"""
        try:
            # Skip tracking pixels and tiny images
            if any(tracker in img_url.lower() for tracker in ['pixel', 'track', '1x1', 'spacer']):
                return None
            
            # Handle relative URLs (shouldn't happen with Substack but just in case)
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                return None  # Can't handle relative paths without base URL
            
            print(f"Attempting to fetch image: {img_url[:100]}...")
            
            # Download image
            response = requests.get(img_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; PDFExporter/1.0)'
            })
            response.raise_for_status()
            
            # Load image into PIL
            img_data = BytesIO(response.content)
            pil_img = PILImage.open(img_data)
            
            # Convert RGBA to RGB if necessary (PDF doesn't support transparency well)
            if pil_img.mode == 'RGBA':
                # Create a white background
                background = PILImage.new('RGB', pil_img.size, (255, 255, 255))
                background.paste(pil_img, mask=pil_img.split()[3])  # Use alpha channel as mask
                pil_img = background
            elif pil_img.mode not in ('RGB', 'L'):
                pil_img = pil_img.convert('RGB')
            
            # Get image dimensions
            img_width, img_height = pil_img.size
            
            # Calculate scaling to fit page width (max 6 inches wide)
            max_width = 6 * inch
            max_height = 8 * inch
            
            # Calculate aspect ratio
            aspect = img_height / float(img_width)
            
            # Determine final dimensions
            if img_width > max_width:
                display_width = max_width
                display_height = max_width * aspect
            else:
                display_width = img_width
                display_height = img_height
            
            # Further scale if height is too large
            if display_height > max_height:
                display_height = max_height
                display_width = max_height / aspect
            
            # Save PIL image to bytes for ReportLab
            img_buffer = BytesIO()
            pil_img.save(img_buffer, format='PNG' if pil_img.mode == 'L' else 'JPEG', quality=85)
            img_buffer.seek(0)
            
            # Create ReportLab Image
            from reportlab.platypus import Image as RLImage
            rl_image = RLImage(img_buffer, width=display_width, height=display_height)
            
            print(f"Successfully loaded image: {img_width}x{img_height} -> {display_width/inch:.1f}x{display_height/inch:.1f} inches")
            return rl_image
            
        except Exception as e:
            print(f"Failed to load image {img_url[:100]}: {str(e)}")
            # Return a text placeholder for failed images
            return Paragraph(f"[Image unavailable: {alt_text or 'No description'}]", self.styles['Normal'])
    
    def export_article_to_pdf(self, article_id: int) -> bytes:
        """Export a single article to PDF"""
        # Get article from database
        article = self.db.query(SubstackArticle).filter(
            SubstackArticle.id == article_id
        ).first()
        
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
        if article.title:
            story.append(Paragraph(article.title, self.styles['CustomTitle']))
        
        # Add subtitle
        if article.subtitle:
            story.append(Paragraph(article.subtitle, self.styles['Subtitle']))
        
        # Add author and date
        author_text = []
        if article.author:
            author_text.append(f"By {article.author.name}")
        if article.published_at:
            author_text.append(article.published_at.strftime("%B %d, %Y"))
        if author_text:
            story.append(Paragraph(" • ".join(author_text), self.styles['AuthorDate']))
        
        story.append(Spacer(1, 0.5 * inch))
        
        # Add article content
        if article.content_markdown:
            try:
                content_flowables = self._markdown_to_reportlab(article.content_markdown)
                story.extend(content_flowables)
            except Exception as e:
                print(f"Error processing markdown content: {e}")
                # Fallback to simple text
                clean_text = self._clean_html_for_reportlab(article.content_markdown[:5000])
                if clean_text:
                    story.append(Paragraph(clean_text, self.styles['ArticleBody']))
        elif article.preview:
            clean_preview = self._clean_html_for_reportlab(article.preview)
            if clean_preview:
                story.append(Paragraph(clean_preview, self.styles['ArticleBody']))
        
        # Add snippets if any
        snippets = self.db.query(ArticleSnippet).filter(
            ArticleSnippet.article_id == article_id
        ).order_by(ArticleSnippet.created_at).all()
        
        if snippets:
            story.append(PageBreak())
            story.append(Paragraph("Highlighted Snippets & Annotations", self.styles['Heading2']))
            story.append(Spacer(1, 0.2 * inch))
            
            for snippet in snippets:
                # Add snippet text
                story.append(Paragraph(f'"{snippet.text}"', self.styles['Snippet']))
                
                # Add annotation if exists
                if snippet.annotation:
                    annotation_text = f"<i>Note: {snippet.annotation}</i>"
                    story.append(Paragraph(annotation_text, self.styles['Normal']))
                
                story.append(Spacer(1, 0.2 * inch))
        
        # Add metadata footer
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("―" * 50, self.styles['Normal']))
        
        metadata = []
        if article.word_count:
            metadata.append(f"Word count: {article.word_count}")
        if article.reading_time_minutes:
            metadata.append(f"Reading time: {article.reading_time_minutes} minutes")
        if article.url:
            metadata.append(f"Source: {article.url}")
        
        if metadata:
            story.append(Paragraph(" • ".join(metadata), self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def export_multiple_articles_to_pdf(
        self, 
        article_ids: List[int], 
        title: str = "Article Collection",
        include_toc: bool = True
    ) -> bytes:
        """Export multiple articles to a single PDF"""
        # Get articles from database
        articles = self.db.query(SubstackArticle).filter(
            SubstackArticle.id.in_(article_ids)
        ).order_by(SubstackArticle.published_at.desc()).all()
        
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
            f"Generated on {datetime.now().strftime('%B %d, %Y')}",
            self.styles['AuthorDate']
        ))
        story.append(PageBreak())
        
        # Add table of contents if requested
        if include_toc and len(articles) > 1:
            story.append(Paragraph("Table of Contents", self.styles['Heading1']))
            story.append(Spacer(1, 0.3 * inch))
            
            toc_data = []
            for i, article in enumerate(articles, 1):
                toc_data.append([
                    str(i),
                    article.title[:60] + "..." if len(article.title) > 60 else article.title,
                    article.author.name if article.author else "Unknown",
                    article.published_at.strftime("%m/%d/%Y") if article.published_at else ""
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
            if article.title:
                story.append(Paragraph(article.title, self.styles['CustomTitle']))
            
            # Add subtitle
            if article.subtitle:
                story.append(Paragraph(article.subtitle, self.styles['Subtitle']))
            
            # Add author and date
            author_text = []
            if article.author:
                author_text.append(f"By {article.author.name}")
            if article.published_at:
                author_text.append(article.published_at.strftime("%B %d, %Y"))
            if author_text:
                story.append(Paragraph(" • ".join(author_text), self.styles['AuthorDate']))
            
            story.append(Spacer(1, 0.5 * inch))
            
            # Add article content
            if article.content_markdown:
                content_flowables = self._markdown_to_reportlab(article.content_markdown)
                story.extend(content_flowables)
            elif article.preview:
                story.append(Paragraph(article.preview, self.styles['ArticleBody']))
            
            # Add page break between articles
            if i < len(articles) - 1:
                story.append(PageBreak())
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def export_author_articles_to_pdf(self, author_id: int) -> bytes:
        """Export all articles from a specific author to PDF"""
        # Get author
        author = self.db.query(SubstackAuthor).filter(
            SubstackAuthor.id == author_id
        ).first()
        
        if not author:
            raise ValueError(f"Author with ID {author_id} not found")
        
        # Get all articles from this author
        articles = self.db.query(SubstackArticle).filter(
            SubstackArticle.author_id == author_id
        ).order_by(SubstackArticle.published_at.desc()).all()
        
        if not articles:
            raise ValueError(f"No articles found for author {author.name}")
        
        # Export to PDF with custom title
        article_ids = [article.id for article in articles]
        title = f"{author.name} - Article Collection"
        
        return self.export_multiple_articles_to_pdf(article_ids, title)