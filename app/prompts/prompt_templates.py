# app/prompts/prompt_templates.py

def create_stance_prompt(target: str, text: str) -> str:
    """
    Create a stance detection prompt with the given target and text.
    
    Args:
        target: The target entity for stance detection
        text: The text to analyze for stance
        
    Returns:
        Formatted prompt string
    """
    if not target:
        target = "the mentioned topic"
    
    if not text:
        text = "[No text provided]"
    
    return f"""Target: {target}
Text: "{text}"

Analyze the stance expressed in this text toward the target and classify it according to the guidelines above."""

def create_batch_stance_prompt(target: str, texts: list) -> str:
    """
    Create a prompt for analyzing multiple texts against the same target.
    
    Args:
        target: The target entity for stance detection
        texts: List of texts to analyze
        
    Returns:
        Formatted batch prompt string
    """
    if not target:
        target = "the mentioned topic"
    
    if not texts:
        return f"Target: {target}\nNo texts provided for analysis."
    
    prompt = f"Target: {target}\n\nAnalyze the stance in each of the following texts:\n\n"
    
    for i, text in enumerate(texts, 1):
        prompt += f"Text {i}: \"{text}\"\n"
    
    prompt += "\nProvide stance classification (FAVOR/AGAINST/NONE) and reasoning for each text."
    
    return prompt

def create_comparative_stance_prompt(targets: list, text: str) -> str:
    """
    Create a prompt for analyzing stance toward multiple targets in the same text.
    
    Args:
        targets: List of target entities
        text: The text to analyze
        
    Returns:
        Formatted comparative prompt string
    """
    if not targets:
        targets = ["the mentioned topics"]
    
    if not text:
        text = "[No text provided]"
    
    targets_str = ", ".join(targets)
    
    return f"""Text: "{text}"

Analyze the stance expressed in this text toward each of the following targets: {targets_str}

For each target, provide:
Target: [target name]
STANCE: [FAVOR/AGAINST/NONE]
Reasoning: [explanation]"""

def create_contextual_stance_prompt(target: str, text: str, context: str = None) -> str:
    """
    Create a stance detection prompt with additional context.
    
    Args:
        target: The target entity for stance detection
        text: The text to analyze for stance
        context: Additional context information (optional)
        
    Returns:
        Formatted prompt string with context
    """
    base_prompt = create_stance_prompt(target, text)
    
    if context:
        return f"Context: {context}\n\n{base_prompt}\n\nConsider the provided context when analyzing the stance."
    
    return base_prompt

def create_domain_specific_prompt(target: str, text: str, domain: str) -> str:
    """
    Create a domain-specific stance detection prompt.
    
    Args:
        target: The target entity for stance detection
        text: The text to analyze for stance
        domain: The domain context (e.g., 'political', 'healthcare', 'technology')
        
    Returns:
        Formatted domain-specific prompt string
    """
    domain_guidelines = {
        'political': "Consider political rhetoric, policy positions, and partisan language patterns.",
        'healthcare': "Focus on medical policy, treatment approaches, and healthcare system perspectives.",
        'technology': "Consider technological adoption, innovation impacts, and digital transformation views.",
        'environmental': "Analyze environmental policy, sustainability practices, and climate-related positions.",
        'economic': "Focus on economic policies, market perspectives, and financial implications.",
        'social': "Consider social issues, cultural perspectives, and community impact views."
    }
    
    domain_context = domain_guidelines.get(domain.lower(), f"Consider {domain}-specific perspectives and terminology.")
    
    return f"""Domain: {domain.title()}
{domain_context}

{create_stance_prompt(target, text)}

Apply domain-specific understanding while maintaining consistent stance classification standards."""

def create_confidence_aware_prompt(target: str, text: str) -> str:
    """
    Create a prompt that asks for confidence levels in stance detection.
    
    Args:
        target: The target entity for stance detection
        text: The text to analyze for stance
        
    Returns:
        Formatted prompt string requesting confidence
    """
    base_prompt = create_stance_prompt(target, text)
    
    return f"""{base_prompt}

Additionally, provide a confidence level for your classification:
Confidence: [High/Medium/Low]

High: Clear, unambiguous stance with strong textual evidence
Medium: Reasonably clear stance with adequate evidence
Low: Uncertain or ambiguous stance with limited evidence"""

def create_explanation_focused_prompt(target: str, text: str) -> str:
    """
    Create a prompt that emphasizes detailed explanation of reasoning.
    
    Args:
        target: The target entity for stance detection
        text: The text to analyze for stance
        
    Returns:
        Formatted prompt string emphasizing explanation
    """
    return f"""{create_stance_prompt(target, text)}

Provide a detailed analysis including:
1. Key phrases or words that indicate stance
2. Implicit meanings or implications
3. Overall context and tone
4. Any ambiguities or conflicting signals
5. Final stance decision with confidence level

Be thorough in your reasoning and cite specific textual evidence."""

def validate_prompt_inputs(target: str, text: str) -> tuple:
    """
    Validate and clean prompt inputs.
    
    Args:
        target: Target entity
        text: Text to analyze
        
    Returns:
        Tuple of (cleaned_target, cleaned_text, is_valid)
    """
    # Clean and validate target
    if not target or not isinstance(target, str):
        cleaned_target = "the mentioned topic"
    else:
        cleaned_target = target.strip()
        if len(cleaned_target) > 200:
            cleaned_target = cleaned_target[:200] + "..."
    
    # Clean and validate text
    if not text or not isinstance(text, str):
        return cleaned_target, "[No text provided]", False
    
    cleaned_text = text.strip()
    
    # Check text length
    if len(cleaned_text) == 0:
        return cleaned_target, "[Empty text]", False
    
    if len(cleaned_text) > 5000:
        cleaned_text = cleaned_text[:5000] + "..."
    
    return cleaned_target, cleaned_text, True

def get_prompt_template(template_type: str = "default") -> str:
    """
    Get a specific prompt template by type.
    
    Args:
        template_type: Type of template to retrieve
        
    Returns:
        Template string
    """
    templates = {
        "default": create_stance_prompt,
        "brief": lambda target, text: f"Target: {target}\nText: \"{text}\"\n\nStance (FAVOR/AGAINST/NONE):",
        "detailed": create_explanation_focused_prompt,
        "confidence": create_confidence_aware_prompt,
        "comparative": create_comparative_stance_prompt,
        "contextual": create_contextual_stance_prompt,
        "domain": create_domain_specific_prompt
    }
    
    return templates.get(template_type, create_stance_prompt)

# Example usage and testing functions
def test_prompt_templates():
    """Test function for prompt templates"""
    
    # Test basic prompt
    basic_prompt = create_stance_prompt("Climate Change", "Global warming is a serious threat to humanity.")
    print("Basic Prompt:")
    print(basic_prompt)
    print("\n" + "="*50 + "\n")
    
    # Test batch prompt
    texts = [
        "I support renewable energy initiatives.",
        "Coal power plants should be shut down immediately.",
        "The weather is nice today."
    ]
    batch_prompt = create_batch_stance_prompt("Environmental Policy", texts)
    print("Batch Prompt:")
    print(batch_prompt)
    print("\n" + "="*50 + "\n")
    
    # Test comparative prompt
    targets = ["Donald Trump", "Joe Biden"]
    comparative_prompt = create_comparative_stance_prompt(targets, "Both candidates have their strengths and weaknesses.")
    print("Comparative Prompt:")
    print(comparative_prompt)
    
if __name__ == "__main__":
    test_prompt_templates()
