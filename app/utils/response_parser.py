# app/utils/response_parser.py
import re
import logging
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)

class StanceResponseParser:
    """Parse and validate LLM responses for stance detection"""
    
    # Valid stance labels
    VALID_STANCES = {"FAVOR", "AGAINST", "NONE"}
    
    # Regex patterns for extracting stance and reasoning
    STANCE_PATTERNS = [
        r'STANCE:\s*(FAVOR|AGAINST|NONE)',
        r'stance:\s*(favor|against|none)',
        r'classification:\s*(FAVOR|AGAINST|NONE)',
        r'result:\s*(FAVOR|AGAINST|NONE)',
        r'answer:\s*(FAVOR|AGAINST|NONE)',
        r'\b(FAVOR|AGAINST|NONE)\b'
    ]
    
    REASONING_PATTERNS = [
        r'(?:reasoning|explanation|because|rationale):\s*(.*?)(?:\n|$)',
        r'(?:this is because|the reason is):\s*(.*?)(?:\n|$)',
        r'(?:justification|support):\s*(.*?)(?:\n|$)',
        r'(?:analysis|assessment):\s*(.*?)(?:\n|$)'
    ]
    
    CONFIDENCE_PATTERNS = [
        r'confidence:\s*([0-9]*\.?[0-9]+)',
        r'certainty:\s*([0-9]*\.?[0-9]+)',
        r'score:\s*([0-9]*\.?[0-9]+)'
    ]
    
    @classmethod
    def parse_stance_response(cls, response: str) -> Tuple[str, str, Optional[float]]:
        """
        Parse LLM response to extract stance, reasoning, and confidence.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            Tuple of (stance, reasoning, confidence)
        """
        if not response or not isinstance(response, str):
            logger.warning("Empty or invalid response received")
            return "NONE", "No valid response provided", None
        
        response = response.strip()
        
        # Extract stance
        stance = cls._extract_stance(response)
        
        # Extract reasoning
        reasoning = cls._extract_reasoning(response)
        
        # Extract confidence (optional)
        confidence = cls._extract_confidence(response)
        
        # Validate and clean up
        stance = cls._validate_stance(stance)
        reasoning = cls._clean_reasoning(reasoning)
        
        logger.debug(f"Parsed response - Stance: {stance}, Reasoning: {reasoning[:50]}...")
        
        return stance, reasoning, confidence
    
    @classmethod
    def _extract_stance(cls, response: str) -> str:
        """Extract stance from response using multiple patterns"""
        response_upper = response.upper()
        
        # Try each pattern in order of preference
        for pattern in cls.STANCE_PATTERNS:
            match = re.search(pattern, response_upper, re.IGNORECASE | re.MULTILINE)
            if match:
                stance = match.group(1).upper()
                if stance in cls.VALID_STANCES:
                    return stance
        
        # Fallback: look for stance words in the response
        for stance in cls.VALID_STANCES:
            if stance in response_upper:
                return stance
        
        # Default fallback
        logger.warning(f"Could not extract valid stance from response: {response[:100]}...")
        return "NONE"
    
    @classmethod
    def _extract_reasoning(cls, response: str) -> str:
        """Extract reasoning from response"""
        # Try structured reasoning patterns first
        for pattern in cls.REASONING_PATTERNS:
            match = re.search(pattern, response, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                if len(reasoning) > 10:  # Ensure meaningful reasoning
                    return reasoning
        
        # Fallback: extract sentences that contain explanatory words
        explanatory_keywords = [
            "because", "since", "as", "due to", "given that", "considering",
            "indicates", "suggests", "shows", "demonstrates", "expresses",
            "support", "opposition", "favor", "against"
        ]
        
        sentences = re.split(r'[.!?]+', response)
        reasoning_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in explanatory_keywords):
                reasoning_sentences.append(sentence)
        
        if reasoning_sentences:
            return ". ".join(reasoning_sentences[:2])  # Take first 2 relevant sentences
        
        # Final fallback: use the entire response if it's not too long
        if len(response) < 200:
            return response
        
        return "No clear reasoning provided in the response."
    
    @classmethod
    def _extract_confidence(cls, response: str) -> Optional[float]:
        """Extract confidence score if available"""
        for pattern in cls.CONFIDENCE_PATTERNS:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    confidence = float(match.group(1))
                    # Normalize to 0-1 range if needed
                    if confidence > 1.0:
                        confidence = confidence / 100.0
                    return min(max(confidence, 0.0), 1.0)
                except ValueError:
                    continue
        return None
    
    @classmethod
    def _validate_stance(cls, stance: str) -> str:
        """Validate and normalize stance"""
        stance = stance.upper().strip()
        if stance in cls.VALID_STANCES:
            return stance
        
        # Handle common variations
        stance_mapping = {
            "POSITIVE": "FAVOR",
            "SUPPORT": "FAVOR",
            "FOR": "FAVOR",
            "PRO": "FAVOR",
            "NEGATIVE": "AGAINST",
            "OPPOSE": "AGAINST",
            "OPPOSED": "AGAINST",
            "ANTI": "AGAINST",
            "NEUTRAL": "NONE",
            "UNKNOWN": "NONE",
            "UNCLEAR": "NONE"
        }
        
        return stance_mapping.get(stance, "NONE")
    
    @classmethod
    def _clean_reasoning(cls, reasoning: str) -> str:
        """Clean and format reasoning text"""
        if not reasoning:
            return "No reasoning provided."
        
        # Remove common artifacts
        reasoning = re.sub(r'^(reasoning|explanation|because):\s*', '', reasoning, flags=re.IGNORECASE)
        reasoning = re.sub(r'\s+', ' ', reasoning)  # Normalize whitespace
        reasoning = reasoning.strip()
        
        # Ensure proper capitalization
        if reasoning and not reasoning[0].isupper():
            reasoning = reasoning[0].upper() + reasoning[1:]
        
        # Ensure proper ending punctuation
        if reasoning and reasoning[-1] not in '.!?':
            reasoning += '.'
        
        return reasoning[:500]  # Limit length
    
    @classmethod
    def validate_response_format(cls, response: str) -> Dict[str, Any]:
        """Validate and provide feedback on response format quality"""
        validation_result = {
            "is_valid": True,
            "issues": [],
            "suggestions": []
        }
        
        if not response:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Empty response")
            return validation_result
        
        # Check for stance presence
        stance = cls._extract_stance(response)
        if stance == "NONE" and "NONE" not in response.upper():
            validation_result["issues"].append("No clear stance detected")
            validation_result["suggestions"].append("Response should explicitly state FAVOR, AGAINST, or NONE")
        
        # Check for reasoning presence
        reasoning = cls._extract_reasoning(response)
        if len(reasoning) < 20:
            validation_result["issues"].append("Insufficient reasoning provided")
            validation_result["suggestions"].append("Response should include clear justification for the stance")
        
        # Check response length
        if len(response) < 50:
            validation_result["issues"].append("Response too short")
            validation_result["suggestions"].append("Response should provide more detailed analysis")
        elif len(response) > 1000:
            validation_result["issues"].append("Response too long")
            validation_result["suggestions"].append("Response should be more concise")
        
        if validation_result["issues"]:
            validation_result["is_valid"] = False
        
        return validation_result