"""
Base strategy class.

To create a custom summarization strategy:
  1. Subclass BaseStrategy
  2. Override `summarize()` — the only required method
  3. Optionally override `name` and `description`

See `examples/custom_strategy.py` for a complete example.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class VideoContext:
    """All the information gathered about a video before summarization."""

    bvid: str
    url: str = ""
    title: str = ""
    author: str = ""
    duration: int = 0          # seconds
    views: int = 0
    description: str = ""
    subtitle_text: str = ""    # Plain text of the subtitle
    subtitle_lang: str = ""    # e.g. "中文（简体）"
    subtitle_type: str = ""    # "human" | "ai" | "whisper" | "none"


@dataclass
class SummaryResult:
    """The output of a summarization strategy."""

    markdown: str              # The generated note content
    metadata: dict = field(default_factory=dict)  # Extra info (tokens used, etc.)


class BaseStrategy(ABC):
    """
    Abstract base for summarization strategies.

    Subclass this and override `summarize()` to define your own strategy.
    """

    name: str = "base"
    description: str = "Base strategy (does nothing)"

    @abstractmethod
    def summarize(self, ctx: VideoContext) -> SummaryResult:
        """
        Generate a summary/note from the video context.

        Args:
            ctx: VideoContext with all gathered information.

        Returns:
            SummaryResult with the generated markdown note.
        """
        ...
