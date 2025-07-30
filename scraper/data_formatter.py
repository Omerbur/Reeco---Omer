"""
Data formatting utilities for the Sysco scraper
Handles cleaning and organizing product descriptions and other text fields
"""

import re
from typing import Dict, List


class DataFormatter:
    """Handles formatting and cleaning of scraped data"""
    
    def format_description(self, raw_description: str) -> str:
        """
        Format and organize product description into readable sections
        
        Args:
            raw_description: Raw description text from the website
            
        Returns:
            Formatted description with organized sections
        """
        if not raw_description or not raw_description.strip():
            return ""
        
        # Clean the raw text
        cleaned_text = self._clean_raw_text(raw_description)
        
        # Organize into sections
        sections = self._organize_into_sections(cleaned_text)
        
        # Format the final output
        return self._format_sections(sections)
    
    def _clean_raw_text(self, text: str) -> str:
        """Clean raw text by removing unwanted characters and formatting"""
        # Remove excessive whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        
        # Remove bullet points and list markers
        text = re.sub(r'[•·▪▫◦‣⁃]\s*', '', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{2,}', '.', text)
        text = re.sub(r'[-]{2,}', '-', text)
        
        # Clean up spacing around punctuation
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        text = re.sub(r'([,.!?;:])\s+', r'\1 ', text)
        
        return text.strip()
    
    def _organize_into_sections(self, text: str) -> Dict[str, str]:
        """Organize text into logical sections"""
        sections = {
            'PRODUCT': '',
            'SPECIFICATIONS': '',
            'FEATURES': '',
            'COOKING_INSTRUCTIONS': ''
        }
        
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Categorize sentences based on keywords
            if any(keyword in sentence_lower for keyword in [
                'cook', 'bake', 'fry', 'grill', 'heat', 'temperature', 
                'oven', 'microwave', 'preparation', 'serve'
            ]):
                sections['COOKING_INSTRUCTIONS'] += sentence + '. '
                
            elif any(keyword in sentence_lower for keyword in [
                'weight', 'size', 'count', 'piece', 'lb', 'oz', 'gram',
                'dimension', 'pack', 'case', 'unit'
            ]):
                sections['SPECIFICATIONS'] += sentence + '. '
                
            elif any(keyword in sentence_lower for keyword in [
                'feature', 'benefit', 'quality', 'fresh', 'premium',
                'natural', 'organic', 'grade', 'cut', 'style'
            ]):
                sections['FEATURES'] += sentence + '. '
                
            else:
                # Default to product description
                sections['PRODUCT'] += sentence + '. '
        
        # Clean up sections
        for key in sections:
            sections[key] = sections[key].strip()
        
        return sections
    
    def _format_sections(self, sections: Dict[str, str]) -> str:
        """Format sections into final description"""
        formatted_parts = []
        
        # Add sections in order of importance
        section_order = ['PRODUCT', 'SPECIFICATIONS', 'FEATURES', 'COOKING_INSTRUCTIONS']
        section_labels = {
            'PRODUCT': 'PRODUCT',
            'SPECIFICATIONS': 'SPECIFICATIONS', 
            'FEATURES': 'FEATURES',
            'COOKING_INSTRUCTIONS': 'COOKING INSTRUCTIONS'
        }
        
        for section_key in section_order:
            content = sections.get(section_key, '').strip()
            if content:
                # Limit section length for readability
                content = self._limit_section_length(content, 200)
                label = section_labels[section_key]
                formatted_parts.append(f"{label}: {content}")
        
        return ' | '.join(formatted_parts) if formatted_parts else sections.get('PRODUCT', '')
    
    def _limit_section_length(self, text: str, max_length: int) -> str:
        """Limit section length while preserving sentence boundaries"""
        if len(text) <= max_length:
            return text
        
        # Find the last complete sentence within the limit
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        
        if last_period > max_length * 0.7:  # If we can keep most of the text
            return text[:last_period + 1]
        else:
            return truncated.rstrip() + '...'
    
    def clean_price(self, price_text: str) -> str:
        """Clean and format price text"""
        if not price_text:
            return ""
        
        # Remove extra whitespace
        price_text = re.sub(r'\s+', ' ', price_text.strip())
        
        # Extract price pattern (e.g., "$12.99", "$1,234.56")
        price_match = re.search(r'\$[\d,]+\.?\d*', price_text)
        if price_match:
            return price_match.group()
        
        return price_text
    
    def clean_text_field(self, text: str) -> str:
        """General text field cleaning"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted characters
        # Allow common characters, including unicode letters for different languages
        text = re.sub(r'[^\w\s\-.,!?()&/$€£¥°À-ÖØ-öø-ÿ]', '', text, flags=re.UNICODE)
        
        return text
