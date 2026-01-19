#!/usr/bin/env python3
"""
Script to manually add a Substack article to the database
"""

import sys
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import get_db
from app.models.substack import SubstackAuthor, SubstackArticle

def add_article():
    """Add the Mathematics for ML roadmap article"""
    
    db = next(get_db())
    
    try:
        # Check if author exists, create if not
        author = db.query(SubstackAuthor).filter(
            SubstackAuthor.subdomain == "thepalindrome"
        ).first()
        
        if not author:
            author = SubstackAuthor(
                email="tivadar@thepalindrome.org",  # Placeholder
                name="Tivadar Danka",
                subdomain="thepalindrome",
                url="https://thepalindrome.org"
            )
            db.add(author)
            db.commit()
            print(f"Created author: {author.name}")
        else:
            print(f"Found existing author: {author.name}")
        
        # Check if article already exists
        existing = db.query(SubstackArticle).filter(
            SubstackArticle.url == "https://thepalindrome.org/p/the-roadmap-of-mathematics-for-machine-learning"
        ).first()
        
        if existing:
            print(f"Article already exists: {existing.title}")
            return
        
        # Create the article
        article_content = """# The Roadmap of Mathematics for Machine Learning

A complete guide to linear algebra, calculus, and probability theory

## Introduction

Understanding the mathematical foundations of machine learning is crucial for moving beyond baseline performance. This roadmap provides a structured approach for engineers and researchers to develop deep mathematical understanding of ML algorithms.

## 1. Linear Algebra

Linear algebra forms the backbone of machine learning, providing the language and tools to work with high-dimensional data.

### Key Concepts:
- **Vector Spaces**: Understanding abstract spaces where data lives
- **Norms and Inner Products**: Measuring distances and angles in high dimensions
- **Linear Transformations**: How data is transformed and manipulated
- **Matrices**: Computational representation of linear transformations
- **Eigenvalues and Eigenvectors**: Finding principal directions in data
- **Matrix Decompositions**: SVD, QR, and other factorizations

### Learning Path:
1. Start with geometric intuition of vectors and operations
2. Move to abstract vector spaces and linear independence
3. Study matrix operations and special matrix types
4. Master eigenvalue problems and spectral theory
5. Learn decomposition techniques and their applications

## 2. Calculus

Calculus enables optimization, the heart of training machine learning models.

### Single Variable Calculus:
- **Differentiation**: Rate of change and tangent lines
- **Integration**: Areas and accumulation
- **Taylor Series**: Function approximation

### Multivariable Calculus:
- **Partial Derivatives**: Change with respect to individual variables
- **Gradients**: Direction of steepest ascent
- **Chain Rule**: Backpropagation foundation
- **Optimization**: Finding minima and maxima

### Key Applications:
- Gradient descent and its variants
- Backpropagation in neural networks
- Loss function optimization
- Regularization techniques

## 3. Probability Theory

Probability theory provides the framework for uncertainty quantification and statistical learning.

### Fundamentals:
- **Probability Spaces**: Sample spaces, events, and measures
- **Random Variables**: Discrete and continuous distributions
- **Expected Value and Variance**: Central tendencies and spread
- **Joint and Conditional Probability**: Relationships between events

### Advanced Topics:
- **Bayes' Theorem**: Foundation of Bayesian inference
- **Entropy and Information Theory**: Measuring uncertainty
- **Concentration Inequalities**: Bounds on random variables
- **Central Limit Theorem**: Convergence to normality

### Machine Learning Applications:
- Maximum likelihood estimation
- Bayesian networks and inference
- Probabilistic graphical models
- Uncertainty quantification in predictions

## Recommended Resources

### Linear Algebra:
- **Book**: "Linear Algebra Done Right" by Sheldon Axler
- **Course**: MIT 18.06 Linear Algebra (Gilbert Strang)
- **Online**: 3Blue1Brown's Essence of Linear Algebra

### Calculus:
- **Book**: "Calculus" by Michael Spivak
- **Course**: MIT 18.01 Single Variable Calculus
- **Online**: Khan Academy Calculus sequence

### Probability:
- **Book**: "Probability Theory: The Logic of Science" by E.T. Jaynes
- **Course**: MIT 6.041 Probabilistic Systems Analysis
- **Online**: Stat 110 from Harvard (Joe Blitzstein)

## Learning Strategy

1. **Build Intuition First**: Start with visual and geometric understanding
2. **Practice Computation**: Work through problems by hand before using tools
3. **Connect to ML**: Always relate concepts back to ML applications
4. **Implement in Code**: Program the algorithms to solidify understanding
5. **Iterate and Review**: Mathematics requires multiple passes for mastery

## Conclusion

The mathematical foundations of machine learning are deep but accessible with structured study. This roadmap provides a path from fundamentals to advanced topics, enabling practitioners to understand not just how ML algorithms work, but why they work.

Remember: The goal isn't to become a mathematician, but to gain sufficient mathematical maturity to read papers, implement algorithms, and innovate in the field of machine learning."""
        
        article = SubstackArticle(
            author_id=author.id,
            title="The Roadmap of Mathematics for Machine Learning",
            subtitle="A complete guide to linear algebra, calculus, and probability theory",
            substack_id=f"manual_import_{datetime.now().isoformat()}",
            slug="the-roadmap-of-mathematics-for-machine-learning",
            url="https://thepalindrome.org/p/the-roadmap-of-mathematics-for-machine-learning",
            content_markdown=article_content,
            content_html="",  # Not needed for markdown rendering
            preview="Understanding the mathematical foundations of machine learning is crucial for moving beyond baseline performance. This roadmap covers linear algebra, calculus, and probability theory.",
            published_at=datetime(2025, 8, 6),  # Aug 06, 2025
            word_count=len(article_content.split()),
            reading_time_minutes=max(1, len(article_content.split()) // 200),
            processed=True,
            deleted=False
        )
        
        db.add(article)
        db.commit()
        print(f"Successfully added article: {article.title}")
        print(f"Article ID: {article.id}")
        print(f"Word count: {article.word_count}")
        print(f"Reading time: {article.reading_time_minutes} minutes")
        
    except Exception as e:
        print(f"Error adding article: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_article()