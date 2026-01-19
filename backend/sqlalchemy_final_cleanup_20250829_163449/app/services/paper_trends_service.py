"""
Service for analyzing trends in research papers
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import Session
import numpy as np

from ..models import Paper, PaperTag, PaperAuthor, PaperReference, PaperSnippet
from ..models import Tweet, Tag, SubstackArticle


class PaperTrendsService:
    """Analyze trends and patterns in research papers"""
    
    def get_popular_papers(
        self, 
        db: Session, 
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most popular papers by various metrics"""
        
        # Get recent papers
        cutoff_date = datetime.now() - timedelta(days=days)
        
        papers = db.query(Paper).filter(
            Paper.created_at >= cutoff_date
        ).all()
        
        # Calculate popularity score
        popular_papers = []
        for paper in papers:
            # Count tags, snippets, references
            tag_count = db.query(func.count(PaperTag.id)).filter(
                PaperTag.paper_id == paper.id
            ).scalar()
            
            snippet_count = db.query(func.count(PaperSnippet.id)).filter(
                PaperSnippet.paper_id == paper.id
            ).scalar()
            
            # Calculate score (can be enhanced with citation data)
            score = (
                tag_count * 2 +  # Tags are important
                snippet_count * 3 +  # Snippets show engagement
                (paper.citation_count or 0) * 5  # Citations are most important
            )
            
            popular_papers.append({
                "id": paper.id,
                "title": paper.title,
                "abstract": paper.abstract[:200] if paper.abstract else None,
                "publication_date": paper.publication_date.isoformat() if paper.publication_date else None,
                "citation_count": paper.citation_count,
                "tag_count": tag_count,
                "snippet_count": snippet_count,
                "popularity_score": score,
                "authors": [
                    {"name": a.name, "affiliation": a.affiliation}
                    for a in paper.authors[:3]
                ]
            })
        
        # Sort by popularity score
        popular_papers.sort(key=lambda x: x["popularity_score"], reverse=True)
        
        return popular_papers[:limit]
    
    def identify_emerging_topics(
        self, 
        db: Session,
        days_window: int = 7,
        min_papers: int = 2
    ) -> List[Dict[str, Any]]:
        """Identify emerging research topics based on recent activity"""
        
        # Get recent papers
        recent_cutoff = datetime.now() - timedelta(days=days_window)
        older_cutoff = datetime.now() - timedelta(days=days_window * 4)
        
        # Count tags in recent period
        recent_tags = db.query(
            PaperTag.tag,
            func.count(PaperTag.id).label('count')
        ).join(Paper).filter(
            Paper.created_at >= recent_cutoff
        ).group_by(PaperTag.tag).all()
        
        # Count tags in older period
        older_tags = db.query(
            PaperTag.tag,
            func.count(PaperTag.id).label('count')
        ).join(Paper).filter(
            and_(
                Paper.created_at >= older_cutoff,
                Paper.created_at < recent_cutoff
            )
        ).group_by(PaperTag.tag).all()
        
        # Convert to dictionaries
        recent_dict = {tag: count for tag, count in recent_tags}
        older_dict = {tag: count for tag, count in older_tags}
        
        # Calculate growth rates
        emerging_topics = []
        for tag, recent_count in recent_dict.items():
            if recent_count >= min_papers:
                older_count = older_dict.get(tag, 0)
                
                # Calculate growth rate
                if older_count > 0:
                    growth_rate = (recent_count - older_count) / older_count
                else:
                    growth_rate = float('inf') if recent_count > 0 else 0
                
                # Get sample papers
                sample_papers = db.query(Paper).join(PaperTag).filter(
                    and_(
                        PaperTag.tag == tag,
                        Paper.created_at >= recent_cutoff
                    )
                ).limit(3).all()
                
                emerging_topics.append({
                    "tag": tag,
                    "recent_count": recent_count,
                    "older_count": older_count,
                    "growth_rate": min(growth_rate, 10.0),  # Cap at 10x growth
                    "is_new": older_count == 0,
                    "sample_papers": [
                        {"id": p.id, "title": p.title[:100]}
                        for p in sample_papers
                    ]
                })
        
        # Sort by growth rate
        emerging_topics.sort(key=lambda x: x["growth_rate"], reverse=True)
        
        return emerging_topics[:20]
    
    def analyze_author_activity(
        self, 
        db: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Analyze most active authors and their topics"""
        
        # Get author paper counts
        author_stats = db.query(
            PaperAuthor.name,
            func.count(PaperAuthor.paper_id).label('paper_count')
        ).group_by(PaperAuthor.name).having(
            func.count(PaperAuthor.paper_id) > 1
        ).order_by(desc('paper_count')).limit(limit).all()
        
        active_authors = []
        for author_name, paper_count in author_stats:
            # Get author's papers
            papers = db.query(Paper).join(PaperAuthor).filter(
                PaperAuthor.name == author_name
            ).all()
            
            # Get topics from papers
            tags = []
            for paper in papers:
                paper_tags = db.query(PaperTag.tag).filter(
                    PaperTag.paper_id == paper.id
                ).all()
                tags.extend([t[0] for t in paper_tags])
            
            # Count tag frequencies
            tag_counts = Counter(tags)
            top_topics = tag_counts.most_common(5)
            
            # Get affiliations
            affiliations = db.query(PaperAuthor.affiliation).filter(
                and_(
                    PaperAuthor.name == author_name,
                    PaperAuthor.affiliation.isnot(None)
                )
            ).distinct().all()
            
            active_authors.append({
                "name": author_name,
                "paper_count": paper_count,
                "affiliations": [a[0] for a in affiliations if a[0]],
                "top_topics": [
                    {"tag": tag, "count": count}
                    for tag, count in top_topics
                ],
                "recent_papers": [
                    {"id": p.id, "title": p.title[:100]}
                    for p in papers[:3]
                ]
            })
        
        return active_authors
    
    def find_cross_source_mentions(
        self, 
        db: Session,
        paper_id: int
    ) -> Dict[str, Any]:
        """Find mentions of a paper in tweets and articles"""
        
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return {}
        
        # Search patterns
        title_words = paper.title.lower().split()[:5]  # First 5 words
        arxiv_id = paper.arxiv_id
        doi = paper.doi
        
        # Search in tweets
        tweet_mentions = []
        
        # Search by title keywords
        for word in title_words:
            if len(word) > 4:  # Skip short words
                tweets = db.query(Tweet).filter(
                    Tweet.text.ilike(f'%{word}%')
                ).limit(10).all()
                tweet_mentions.extend(tweets)
        
        # Search by ArXiv ID
        if arxiv_id:
            tweets = db.query(Tweet).filter(
                or_(
                    Tweet.text.ilike(f'%{arxiv_id}%'),
                    Tweet.text.ilike(f'%arxiv.org%{arxiv_id}%')
                )
            ).all()
            tweet_mentions.extend(tweets)
        
        # Remove duplicates
        seen_tweet_ids = set()
        unique_tweets = []
        for tweet in tweet_mentions:
            if tweet.id not in seen_tweet_ids:
                seen_tweet_ids.add(tweet.id)
                unique_tweets.append({
                    "id": tweet.id,
                    "text": tweet.text[:200],
                    "author": tweet.author_username,
                    "created_at": tweet.created_at.isoformat() if tweet.created_at else None
                })
        
        # Search in Substack articles
        article_mentions = []
        
        # Search by title keywords
        for word in title_words:
            if len(word) > 4:
                articles = db.query(SubstackArticle).filter(
                    or_(
                        SubstackArticle.title.ilike(f'%{word}%'),
                        SubstackArticle.content.ilike(f'%{word}%')
                    )
                ).limit(5).all()
                article_mentions.extend(articles)
        
        # Remove duplicates
        seen_article_ids = set()
        unique_articles = []
        for article in article_mentions:
            if article.id not in seen_article_ids:
                seen_article_ids.add(article.id)
                unique_articles.append({
                    "id": article.id,
                    "title": article.title,
                    "author": article.author.name if article.author else None,
                    "published_date": article.published_date.isoformat() if article.published_date else None
                })
        
        return {
            "paper": {
                "id": paper.id,
                "title": paper.title,
                "arxiv_id": arxiv_id,
                "doi": doi
            },
            "tweet_mentions": unique_tweets[:10],
            "article_mentions": unique_articles[:5],
            "total_mentions": len(unique_tweets) + len(unique_articles)
        }
    
    def get_topic_evolution(
        self, 
        db: Session,
        tag: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """Track how a topic has evolved over time"""
        
        # Get papers with this tag over time
        papers = db.query(Paper).join(PaperTag).filter(
            PaperTag.tag == tag
        ).order_by(Paper.publication_date.desc()).all()
        
        # Group papers by month
        papers_by_month = defaultdict(list)
        for paper in papers:
            if paper.publication_date:
                month_key = paper.publication_date.strftime("%Y-%m")
                papers_by_month[month_key].append(paper)
        
        # Analyze evolution
        timeline = []
        for month, month_papers in sorted(papers_by_month.items()):
            # Get all tags from papers in this month
            all_tags = []
            for paper in month_papers:
                tags = db.query(PaperTag.tag).filter(
                    PaperTag.paper_id == paper.id
                ).all()
                all_tags.extend([t[0] for t in tags if t[0] != tag])
            
            # Count co-occurring tags
            co_tags = Counter(all_tags).most_common(5)
            
            timeline.append({
                "month": month,
                "paper_count": len(month_papers),
                "co_occurring_tags": [
                    {"tag": t, "count": c} for t, c in co_tags
                ],
                "sample_papers": [
                    {"id": p.id, "title": p.title[:100]}
                    for p in month_papers[:3]
                ]
            })
        
        # Get related topics (tags that frequently co-occur)
        all_co_tags = []
        for paper in papers:
            tags = db.query(PaperTag.tag).filter(
                and_(
                    PaperTag.paper_id == paper.id,
                    PaperTag.tag != tag
                )
            ).all()
            all_co_tags.extend([t[0] for t in tags])
        
        related_topics = Counter(all_co_tags).most_common(10)
        
        return {
            "tag": tag,
            "total_papers": len(papers),
            "timeline": timeline,
            "related_topics": [
                {"tag": t, "co_occurrence_count": c}
                for t, c in related_topics
            ],
            "first_seen": papers[-1].publication_date.isoformat() if papers and papers[-1].publication_date else None,
            "last_seen": papers[0].publication_date.isoformat() if papers and papers[0].publication_date else None
        }
    
    def get_citation_network(
        self, 
        db: Session,
        paper_id: int,
        depth: int = 2
    ) -> Dict[str, Any]:
        """Build a citation network around a paper"""
        
        def get_paper_info(p):
            if not p:
                return None
            return {
                "id": p.id,
                "title": p.title[:100],
                "year": p.publication_date.year if p.publication_date else None,
                "citation_count": p.citation_count
            }
        
        # Get the root paper
        root_paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not root_paper:
            return {}
        
        network = {
            "root": get_paper_info(root_paper),
            "references": [],
            "citations": [],
            "connections": []
        }
        
        # Get papers this paper references
        references = db.query(PaperReference).filter(
            PaperReference.paper_id == paper_id
        ).all()
        
        for ref in references:
            # Try to find the referenced paper in our database
            cited_paper = None
            if ref.cited_paper_id:
                cited_paper = db.query(Paper).filter(
                    Paper.id == ref.cited_paper_id
                ).first()
            
            ref_info = {
                "title": ref.title or ref.raw_citation,
                "year": ref.year,
                "in_database": cited_paper is not None
            }
            
            if cited_paper:
                ref_info.update(get_paper_info(cited_paper))
            
            network["references"].append(ref_info)
            network["connections"].append({
                "source": paper_id,
                "target": ref.cited_paper_id or f"external_{ref.id}",
                "type": "references"
            })
        
        # Get papers that cite this paper
        citations = db.query(PaperReference).filter(
            PaperReference.cited_paper_id == paper_id
        ).all()
        
        for citation in citations:
            citing_paper = db.query(Paper).filter(
                Paper.id == citation.paper_id
            ).first()
            
            if citing_paper:
                network["citations"].append(get_paper_info(citing_paper))
                network["connections"].append({
                    "source": citing_paper.id,
                    "target": paper_id,
                    "type": "cites"
                })
        
        # Calculate network statistics
        network["statistics"] = {
            "total_references": len(network["references"]),
            "total_citations": len(network["citations"]),
            "references_in_database": sum(1 for r in network["references"] if r.get("in_database")),
            "network_size": 1 + len(network["references"]) + len(network["citations"])
        }
        
        return network