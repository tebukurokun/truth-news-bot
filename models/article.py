from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .media import Media


@dataclass
class Article:
    title: str
    link: str
    media: Optional[Media] = None
    # RSS の配信日時（UTC aware）。取れないフィードもあるので Optional。
    published_at: Optional[datetime] = None
