"""
Advanced services for research papers - Phase 5
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
import logging
import re
import requests
from urllib.parse import quote

from .llm_service import LLMService
from .paper_rag_service import PaperRAGService

logger = logging.getLogger(__name__)

class PaperAdvancedService:
    """Advanced analytics and AI features for papers"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.rag_service = PaperRAGService()
    
    def get_paper_recommendations(
        self, 
        db: Session, 
        paper_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Recommend similar papers based on content and citations"""
        
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return []
        
        # Get paper tags
        paper_tags = db.query(PaperTag.tag).filter(
            PaperTag.paper_id == paper_id
        ).all()
        paper_tag_set = set([t[0] for t in paper_tags])
        
        # Find papers with similar tags
        similar_papers = []
        all_papers = db.query(Paper).filter(Paper.id != paper_id).all()
        
        for candidate in all_papers:
            # Get candidate tags
            candidate_tags = db.query(PaperTag.tag).filter(
                PaperTag.paper_id == candidate.id
            ).all()
            candidate_tag_set = set([t[0] for t in candidate_tags])
            
            # Calculate Jaccard similarity
            if paper_tag_set and candidate_tag_set:
                intersection = len(paper_tag_set & candidate_tag_set)
                union = len(paper_tag_set | candidate_tag_set)
                similarity = intersection / union if union > 0 else 0
                
                if similarity > 0.2:  # Threshold for similarity
                    similar_papers.append({
                        "paper": candidate,
                        "similarity": similarity,
                        "common_tags": list(paper_tag_set & candidate_tag_set)
                    })
        
        # Sort by similarity
        similar_papers.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Format recommendations
        recommendations = []
        for item in similar_papers[:limit]:
            p = item["paper"]
            recommendations.append({
                "id": p.id,
                "title": p.title,
                "abstract": p.abstract[:200] if p.abstract else None,
                "similarity_score": round(item["similarity"], 3),
                "common_tags": item["common_tags"],
                "publication_date": p.publication_date.isoformat() if p.publication_date else None,
                "authors": [
                    {"name": a.name, "affiliation": a.affiliation}
                    for a in p.authors[:3]
                ],
                "reason": f"Shares {len(item['common_tags'])} research topics"
            })
        
        return recommendations
    
    def generate_paper_summary(
        self, 
        db: Session, 
        paper_id: int
    ) -> Dict[str, Any]:
        """Generate AI-powered summary of a paper"""
        
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return {"error": "Paper not found"}
        
        # Prepare content for summarization
        content_parts = []
        
        # Add title and abstract
        content_parts.append(f"Title: {paper.title}")
        if paper.abstract:
            content_parts.append(f"Abstract: {paper.abstract}")
        
        # Add section titles and snippets
        sections = db.query(PaperSection).filter(
            PaperSection.paper_id == paper_id
        ).order_by(PaperSection.position).all()
        
        for section in sections[:5]:  # Limit to first 5 sections
            if section.title:
                content_parts.append(f"\nSection: {section.title}")
                if section.content:
                    # Take first 500 chars of section
                    content_parts.append(section.content[:500])
        
        # Get paper tags for context
        tags = db.query(PaperTag.tag).filter(
            PaperTag.paper_id == paper_id
        ).all()
        tag_list = [t[0] for t in tags]
        
        if tag_list:
            content_parts.append(f"\nResearch Topics: {', '.join(tag_list)}")
        
        # Generate summary using LLM
        full_content = "\n".join(content_parts)
        
        prompt = """Provide a comprehensive summary of this research paper in the following structure:

1. **Main Contribution** (1-2 sentences)
2. **Key Methods/Approach** (2-3 bullet points)
3. **Important Findings** (2-3 bullet points)
4. **Potential Applications** (1-2 bullet points)
5. **Limitations/Future Work** (if mentioned)

Paper content:
{content}"""
        
        try:
            summary_text = self.llm_service.generate_completion(
                prompt.format(content=full_content[:3000]),  # Limit content length
                max_tokens=500,
                temperature=0.3
            )
            
            # Also extract key insights
            insights_prompt = """Extract 3-5 key insights from this paper that would be valuable for AI researchers:

{content}

Format as bullet points starting with "•"."""
            
            insights_text = self.llm_service.generate_completion(
                insights_prompt.format(content=full_content[:2000]),
                max_tokens=300,
                temperature=0.3
            )
            
            return {
                "paper_id": paper_id,
                "title": paper.title,
                "summary": summary_text,
                "key_insights": insights_text,
                "tags": tag_list,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return {
                "paper_id": paper_id,
                "title": paper.title,
                "error": "Failed to generate summary",
                "fallback_abstract": paper.abstract[:500] if paper.abstract else None
            }
    
    def build_knowledge_graph(
        self, 
        db: Session,
        center_paper_id: Optional[int] = None,
        depth: int = 2
    ) -> Dict[str, Any]:
        """Build a knowledge graph of paper relationships"""
        
        nodes = []
        edges = []
        node_ids = set()
        
        def add_paper_node(paper, node_type="paper"):
            if paper.id not in node_ids:
                node_ids.add(paper.id)
                
                # Get paper stats
                tag_count = db.query(func.count(PaperTag.id)).filter(
                    PaperTag.paper_id == paper.id
                ).scalar()
                
                nodes.append({
                    "id": f"paper_{paper.id}",
                    "label": paper.title[:50] + "..." if len(paper.title) > 50 else paper.title,
                    "type": node_type,
                    "data": {
                        "full_title": paper.title,
                        "year": paper.publication_date.year if paper.publication_date else None,
                        "citations": paper.citation_count or 0,
                        "tags": tag_count,
                        "arxiv_id": paper.arxiv_id
                    }
                })
        
        if center_paper_id:
            # Build graph around specific paper
            center_paper = db.query(Paper).filter(Paper.id == center_paper_id).first()
            if center_paper:
                add_paper_node(center_paper, "center")
                
                # Add references
                refs = db.query(PaperReference).filter(
                    PaperReference.paper_id == center_paper_id
                ).limit(10).all()
                
                for ref in refs:
                    if ref.cited_paper_id:
                        cited_paper = db.query(Paper).filter(
                            Paper.id == ref.cited_paper_id
                        ).first()
                        if cited_paper:
                            add_paper_node(cited_paper, "reference")
                            edges.append({
                                "source": f"paper_{center_paper_id}",
                                "target": f"paper_{cited_paper.id}",
                                "type": "cites"
                            })
                
                # Add papers citing this one
                citations = db.query(PaperReference).filter(
                    PaperReference.cited_paper_id == center_paper_id
                ).limit(10).all()
                
                for citation in citations:
                    citing_paper = db.query(Paper).filter(
                        Paper.id == citation.paper_id
                    ).first()
                    if citing_paper:
                        add_paper_node(citing_paper, "citation")
                        edges.append({
                            "source": f"paper_{citing_paper.id}",
                            "target": f"paper_{center_paper_id}",
                            "type": "cites"
                        })
                
                # Add papers with similar tags
                paper_tags = db.query(PaperTag.tag).filter(
                    PaperTag.paper_id == center_paper_id
                ).all()
                
                if paper_tags:
                    tag_list = [t[0] for t in paper_tags]
                    
                    # Find papers with same tags
                    similar_papers = db.query(Paper).join(PaperTag).filter(
                        and_(
                            PaperTag.tag.in_(tag_list),
                            Paper.id != center_paper_id
                        )
                    ).distinct().limit(5).all()
                    
                    for similar in similar_papers:
                        add_paper_node(similar, "related")
                        edges.append({
                            "source": f"paper_{center_paper_id}",
                            "target": f"paper_{similar.id}",
                            "type": "similar"
                        })
        else:
            # Build general graph of recent papers
            recent_papers = db.query(Paper).order_by(
                Paper.created_at.desc()
            ).limit(20).all()
            
            for paper in recent_papers:
                add_paper_node(paper)
            
            # Add citation relationships
            for paper in recent_papers:
                refs = db.query(PaperReference).filter(
                    and_(
                        PaperReference.paper_id == paper.id,
                        PaperReference.cited_paper_id.in_([p.id for p in recent_papers])
                    )
                ).all()
                
                for ref in refs:
                    edges.append({
                        "source": f"paper_{paper.id}",
                        "target": f"paper_{ref.cited_paper_id}",
                        "type": "cites"
                    })
        
        # Add author nodes and relationships
        author_papers = defaultdict(list)
        for node in nodes:
            if node["type"] in ["paper", "center"]:
                paper_id = int(node["id"].replace("paper_", ""))
                authors = db.query(PaperAuthor).filter(
                    PaperAuthor.paper_id == paper_id
                ).limit(3).all()
                
                for author in authors:
                    author_papers[author.name].append(paper_id)
        
        # Add author nodes for authors with multiple papers
        for author_name, papers in author_papers.items():
            if len(papers) > 1:
                author_id = f"author_{hash(author_name) % 10000}"
                nodes.append({
                    "id": author_id,
                    "label": author_name,
                    "type": "author",
                    "data": {
                        "paper_count": len(papers)
                    }
                })
                
                for paper_id in papers:
                    edges.append({
                        "source": author_id,
                        "target": f"paper_{paper_id}",
                        "type": "authored"
                    })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "paper_nodes": len([n for n in nodes if n["type"] in ["paper", "center", "reference", "citation", "related"]]),
                "author_nodes": len([n for n in nodes if n["type"] == "author"]),
                "citation_edges": len([e for e in edges if e["type"] == "cites"]),
                "authorship_edges": len([e for e in edges if e["type"] == "authored"])
            }
        }
    
    def import_from_arxiv(
        self, 
        db: Session,
        arxiv_id: str
    ) -> Dict[str, Any]:
        """Import a paper from ArXiv"""
        
        # Clean ArXiv ID
        arxiv_id = arxiv_id.replace("arxiv:", "").replace("https://arxiv.org/abs/", "")
        
        # Check if already exists
        existing = db.query(Paper).filter(Paper.arxiv_id == arxiv_id).first()
        if existing:
            return {
                "status": "exists",
                "paper_id": existing.id,
                "message": "Paper already in database"
            }
        
        try:
            # Fetch from ArXiv API
            api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            # Parse XML response (simplified - in production use proper XML parser)
            content = response.text
            
            # Extract basic info using regex (simplified)
            title_match = re.search(r'<title>(.*?)</title>', content, re.DOTALL)
            abstract_match = re.search(r'<summary>(.*?)</summary>', content, re.DOTALL)
            authors_match = re.findall(r'<name>(.*?)</name>', content)
            published_match = re.search(r'<published>(.*?)</published>', content)
            
            if not title_match:
                return {
                    "status": "error",
                    "message": "Could not parse ArXiv response"
                }
            
            # Clean extracted data
            title = title_match.group(1).strip().replace('\n', ' ')
            abstract = abstract_match.group(1).strip() if abstract_match else None
            
            # Parse publication date
            pub_date = None
            if published_match:
                try:
                    pub_date = datetime.strptime(published_match.group(1)[:10], "%Y-%m-%d").date()
                except:
                    pass
            
            # Create paper record
            paper = Paper(
                title=title,
                abstract=abstract,
                arxiv_id=arxiv_id,
                publication_date=pub_date,
                processed=True
            )
            db.add(paper)
            db.flush()
            
            # Add authors
            for idx, author_name in enumerate(authors_match[:10]):  # Limit to 10 authors
                author = PaperAuthor(
                    paper_id=paper.id,
                    name=author_name.strip(),
                    position=idx
                )
                db.add(author)
            
            db.commit()
            
            # Generate tags using LLM
            try:
                from .paper_tag_service import PaperTagService
                tag_service = PaperTagService()
                tags = tag_service.suggest_tags_for_paper(db, paper.id)
                
                # Apply top 5 tags
                for tag in tags.get("suggestions", [])[:5]:
                    paper_tag = PaperTag(
                        paper_id=paper.id,
                        tag=tag["tag"],
                        tag_type="auto"
                    )
                    db.add(paper_tag)
                db.commit()
            except Exception as e:
                logger.warning(f"Failed to generate tags: {e}")
            
            return {
                "status": "success",
                "paper_id": paper.id,
                "title": title,
                "authors": authors_match,
                "message": "Paper imported successfully from ArXiv"
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch from ArXiv: {e}")
            return {
                "status": "error",
                "message": f"Failed to fetch from ArXiv: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Failed to import from ArXiv: {e}")
            return {
                "status": "error",
                "message": f"Import failed: {str(e)}"
            }
    
    def extract_github_links(
        self, 
        db: Session,
        paper_id: int
    ) -> List[str]:
        """Extract GitHub repository links from paper content"""
        
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return []
        
        github_links = set()
        
        # Regex pattern for GitHub URLs
        github_pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w\-]+/[\w\-\.]+'
        
        # Search in abstract
        if paper.abstract:
            matches = re.findall(github_pattern, paper.abstract, re.IGNORECASE)
            github_links.update(matches)
        
        # Search in content
        if paper.content:
            matches = re.findall(github_pattern, paper.content[:10000], re.IGNORECASE)  # Limit search
            github_links.update(matches)
        
        # Search in sections
        sections = db.query(PaperSection).filter(
            PaperSection.paper_id == paper_id
        ).all()
        
        for section in sections:
            if section.content:
                matches = re.findall(github_pattern, section.content, re.IGNORECASE)
                github_links.update(matches)
        
        # Clean and normalize URLs
        cleaned_links = []
        for link in github_links:
            if not link.startswith('http'):
                link = 'https://' + link
            # Remove trailing dots or commas
            link = link.rstrip('.,')
            cleaned_links.append(link)
        
        return list(set(cleaned_links))
    
    def get_author_collaboration_network(
        self, 
        db: Session,
        min_papers: int = 2
    ) -> Dict[str, Any]:
        """Build author collaboration network"""
        
        # Get all paper-author relationships
        author_papers = defaultdict(set)
        paper_authors = defaultdict(set)
        
        all_authorships = db.query(PaperAuthor).all()
        
        for authorship in all_authorships:
            author_papers[authorship.name].add(authorship.paper_id)
            paper_authors[authorship.paper_id].add(authorship.name)
        
        # Filter authors with minimum papers
        active_authors = {
            author: papers 
            for author, papers in author_papers.items() 
            if len(papers) >= min_papers
        }
        
        # Build collaboration edges
        collaborations = defaultdict(int)
        
        for paper_id, authors in paper_authors.items():
            author_list = list(authors)
            for i in range(len(author_list)):
                for j in range(i + 1, len(author_list)):
                    if author_list[i] in active_authors and author_list[j] in active_authors:
                        key = tuple(sorted([author_list[i], author_list[j]]))
                        collaborations[key] += 1
        
        # Build network structure
        nodes = []
        edges = []
        
        for author, papers in active_authors.items():
            # Get author's affiliations
            affiliations = db.query(PaperAuthor.affiliation).filter(
                and_(
                    PaperAuthor.name == author,
                    PaperAuthor.affiliation.isnot(None)
                )
            ).distinct().all()
            
            nodes.append({
                "id": author,
                "label": author,
                "size": len(papers),
                "affiliations": [a[0] for a in affiliations if a[0]],
                "paper_count": len(papers)
            })
        
        for (author1, author2), count in collaborations.items():
            edges.append({
                "source": author1,
                "target": author2,
                "weight": count,
                "label": f"{count} papers"
            })
        
        # Calculate network statistics
        total_collaborations = sum(collaborations.values())
        avg_collaborations = total_collaborations / len(active_authors) if active_authors else 0
        
        # Find most collaborative authors
        author_collab_count = defaultdict(int)
        for (author1, author2), count in collaborations.items():
            author_collab_count[author1] += count
            author_collab_count[author2] += count
        
        top_collaborators = sorted(
            author_collab_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return {
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "total_authors": len(nodes),
                "total_collaborations": len(edges),
                "total_collaboration_instances": total_collaborations,
                "average_collaborations_per_author": round(avg_collaborations, 2),
                "top_collaborators": [
                    {"name": name, "collaboration_count": count}
                    for name, count in top_collaborators
                ]
            }
        }