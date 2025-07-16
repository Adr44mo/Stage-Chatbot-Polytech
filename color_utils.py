"""
Global color utilities - Easy import for the entire project
Usage: from color_utils import cp, log_intent_analysis, log_performance

This provides a consistent way to access color printing across the entire project.
"""

from shared_utils.color_print import (
    ColorPrint, cp, COLORAMA_AVAILABLE,
    log_intent_analysis, log_document_retrieval, 
    log_token_cost, log_performance, log_api_call
)

# Re-export everything for convenience
__all__ = [
    'ColorPrint', 'cp', 'COLORAMA_AVAILABLE',
    'log_intent_analysis', 'log_document_retrieval', 
    'log_token_cost', 'log_performance', 'log_api_call'
]
