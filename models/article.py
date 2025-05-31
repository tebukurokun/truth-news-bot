from dataclasses import dataclass
from typing import Optional

from .media import Media


@dataclass
class Article:
    title: str
    link: str
    media: Optional[Media] = None
