"""
Pluggable summarization strategies.

Built-in strategies:
    - quick:  One-shot LLM prompt, fast summary (~30s)
    - deep:   Multi-phase deep research (research → write → review)

To create your own strategy, subclass `BaseStrategy` and register it here.
See `examples/custom_strategy.py` for a template.
"""

from .base import BaseStrategy
from .quick import QuickStrategy
from .deep import DeepStrategy

# Registry: strategy name → strategy class
BUILTIN_STRATEGIES: dict[str, type[BaseStrategy]] = {
    'quick': QuickStrategy,
    'deep': DeepStrategy,
}


def get_strategy(name: str) -> BaseStrategy:
    """
    Get a strategy instance by name.

    Supports built-in strategies and custom strategy files.
    To add a custom strategy file, set env var:
        BILI_SUMMARIZE_STRATEGY=/path/to/my_strategy.py
    The file must export a class named 'CustomStrategy' that subclasses BaseStrategy.
    """
    import os
    import importlib.util

    if name in BUILTIN_STRATEGIES:
        return BUILTIN_STRATEGIES[name]()

    # Try loading a custom strategy from file
    custom_path = os.environ.get('BILI_SUMMARIZE_STRATEGY', '')
    if custom_path and os.path.isfile(custom_path):
        spec = importlib.util.spec_from_file_location(
            'custom_strategy', custom_path
        )
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, 'CustomStrategy'):
                return mod.CustomStrategy()

    raise ValueError(
        f"Unknown strategy '{name}'. "
        f"Available: {list(BUILTIN_STRATEGIES.keys())}. "
        f"Or set BILI_SUMMARIZE_STRATEGY env var to a custom strategy file."
    )
