"""
Readability metrics calculation service for paper content.
"""

import re
from typing import Dict, Optional
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import syllables

# Try to download required NLTK data if not available
# Note: Modern NLTK versions require punkt_tab for sentence tokenization
for resource in ['punkt', 'punkt_tab']:
    try:
        nltk.data.find(f'tokenizers/{resource}')
    except LookupError:
        try:
            nltk.download(resource, quiet=True)
        except Exception:
            pass


class ReadabilityService:
    """Calculate various readability metrics for text content."""
    
    @staticmethod
    def calculate_flesch_reading_ease(text: str) -> Optional[float]:
        """
        Calculate Flesch Reading Ease score.
        
        Score interpretation:
        90-100: Very Easy (5th grade)
        80-89: Easy (6th grade)
        70-79: Fairly Easy (7th grade)
        60-69: Standard (8th-9th grade)
        50-59: Fairly Difficult (10th-12th grade)
        30-49: Difficult (College)
        0-29: Very Difficult (Graduate)
        
        Args:
            text: The text to analyze
            
        Returns:
            Flesch Reading Ease score or None if calculation fails
        """
        if not text or len(text.strip()) == 0:
            return None
            
        try:
            # Clean text
            text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
            text = re.sub(r'[^\w\s.!?]', '', text)  # Keep only words and sentence endings
            
            # Tokenize
            sentences = sent_tokenize(text)
            words = word_tokenize(text.lower())
            
            # Filter out non-words
            words = [w for w in words if w.isalpha()]
            
            if len(sentences) == 0 or len(words) == 0:
                return None
            
            # Count syllables
            total_syllables = sum(syllables.estimate(word) for word in words)
            
            # Calculate Flesch Reading Ease
            # Formula: 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)
            avg_sentence_length = len(words) / len(sentences)
            avg_syllables_per_word = total_syllables / len(words)
            
            score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
            
            # Bound the score between 0 and 100
            return max(0, min(100, round(score, 1)))
            
        except Exception as e:
            print(f"Error calculating Flesch Reading Ease: {e}")
            return None
    
    @staticmethod
    def calculate_flesch_kincaid_grade(text: str) -> Optional[float]:
        """
        Calculate Flesch-Kincaid Grade Level.
        
        Returns the U.S. school grade level required to understand the text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Grade level or None if calculation fails
        """
        if not text or len(text.strip()) == 0:
            return None
            
        try:
            # Clean text
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s.!?]', '', text)
            
            # Tokenize
            sentences = sent_tokenize(text)
            words = word_tokenize(text.lower())
            
            # Filter out non-words
            words = [w for w in words if w.isalpha()]
            
            if len(sentences) == 0 or len(words) == 0:
                return None
            
            # Count syllables
            total_syllables = sum(syllables.estimate(word) for word in words)
            
            # Calculate Flesch-Kincaid Grade Level
            # Formula: 0.39 * (total_words / total_sentences) + 11.8 * (total_syllables / total_words) - 15.59
            avg_sentence_length = len(words) / len(sentences)
            avg_syllables_per_word = total_syllables / len(words)
            
            grade = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
            
            return max(0, round(grade, 1))
            
        except Exception as e:
            print(f"Error calculating Flesch-Kincaid Grade: {e}")
            return None
    
    @staticmethod
    def get_readability_metrics(text: str) -> Dict:
        """
        Calculate all readability metrics for a text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with readability metrics
        """
        # Extract just the main content, skip references if present
        if "# References" in text:
            text = text.split("# References")[0]
        elif "## References" in text:
            text = text.split("## References")[0]
        
        flesch_score = ReadabilityService.calculate_flesch_reading_ease(text)
        grade_level = ReadabilityService.calculate_flesch_kincaid_grade(text)
        
        # Determine difficulty category
        difficulty = "Unknown"
        if flesch_score is not None:
            if flesch_score >= 90:
                difficulty = "Very Easy"
            elif flesch_score >= 80:
                difficulty = "Easy"
            elif flesch_score >= 70:
                difficulty = "Fairly Easy"
            elif flesch_score >= 60:
                difficulty = "Standard"
            elif flesch_score >= 50:
                difficulty = "Fairly Difficult"
            elif flesch_score >= 30:
                difficulty = "Difficult"
            else:
                difficulty = "Very Difficult"
        
        # Academic level interpretation
        academic_level = "Unknown"
        if grade_level is not None:
            if grade_level <= 6:
                academic_level = "Elementary"
            elif grade_level <= 8:
                academic_level = "Middle School"
            elif grade_level <= 12:
                academic_level = "High School"
            elif grade_level <= 16:
                academic_level = "Undergraduate"
            elif grade_level <= 20:
                academic_level = "Graduate"
            else:
                academic_level = "Post-Graduate"
        
        return {
            "flesch_reading_ease": flesch_score,
            "flesch_kincaid_grade": grade_level,
            "difficulty": difficulty,
            "academic_level": academic_level
        }
    
    @staticmethod
    def get_simple_readability_label(text: str) -> str:
        """
        Get a simple readability label for UI display.
        
        Args:
            text: The text to analyze
            
        Returns:
            A simple label like "Graduate Level" or "Undergraduate Level"
        """
        metrics = ReadabilityService.get_readability_metrics(text)
        
        # Prefer academic level for academic papers
        if metrics["academic_level"] != "Unknown":
            return f"{metrics['academic_level']} Level"
        
        # Fall back to difficulty
        if metrics["difficulty"] != "Unknown":
            return metrics["difficulty"]
        
        return "Readability Unknown"