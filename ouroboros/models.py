"""
Ouroboros — Model definitions and static pricing.
"""

from typing import Dict, Tuple

# Pricing from OpenRouter API (2026-02-17). Update periodically.
# Format: (input_1m, cached_input_1m, output_1m) in USD.
MODEL_PRICING_STATIC: Dict[str, Tuple[float, float, float]] = {
    'anthropic/claude-opus-4.6': (5.0, 0.5, 25.0),
    'anthropic/claude-opus-4': (15.0, 1.5, 75.0),
    'anthropic/claude-sonnet-4': (3.0, 0.30, 15.0),
    'anthropic/claude-sonnet-4.6': (3.0, 0.30, 15.0),
    'anthropic/claude-sonnet-4.5': (3.0, 0.30, 15.0),
    'openai/o3': (2.0, 0.50, 8.0),
    'openai/o3-pro': (20.0, 1.0, 80.0),
    'openai/o4-mini': (1.10, 0.275, 4.40),
    'openai/gpt-4.1': (2.0, 0.50, 8.0),
    'openai/gpt-5.2': (1.75, 0.175, 14.0),
    'openai/gpt-5.2-codex': (1.75, 0.175, 14.0),
    'google/gemini-2.5-pro-preview': (1.25, 0.125, 10.0),
    'google/gemini-3.1-pro-preview': (2.0, 0.20, 12.0),
    'google/gemini-3-pro-preview': (2.0, 0.20, 12.0),
    'google/gemini-3-flash-preview': (0.15, 0.015, 0.60),
    'x-ai/grok-3-mini': (0.30, 0.03, 0.50),
    'qwen/qwen3.5-plus-02-15': (0.40, 0.04, 2.40),
}
