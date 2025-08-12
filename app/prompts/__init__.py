"""
Prompts package for StanceLLM.

This package contains system prompts and prompt templates
for stance detection tasks.
"""

# app/prompts/__init__.py
from .system_prompts import (
    STANCE_DETECTION_SYSTEM_PROMPT,
    STANCE_DETECTION_BRIEF_PROMPT,
    MULTILINGUAL_STANCE_PROMPT
)
from .prompt_templates import (
    create_stance_prompt,
    create_batch_stance_prompt,
    create_comparative_stance_prompt,
    create_contextual_stance_prompt,
    create_domain_specific_prompt,
    create_confidence_aware_prompt,
    create_explanation_focused_prompt,
    validate_prompt_inputs,
    get_prompt_template
)

__all__ = [
    'STANCE_DETECTION_SYSTEM_PROMPT',
    'STANCE_DETECTION_BRIEF_PROMPT', 
    'MULTILINGUAL_STANCE_PROMPT',
    'create_stance_prompt',
    'create_batch_stance_prompt',
    'create_comparative_stance_prompt',
    'create_contextual_stance_prompt',
    'create_domain_specific_prompt',
    'create_confidence_aware_prompt',
    'create_explanation_focused_prompt',
    'validate_prompt_inputs',
    'get_prompt_template'
]