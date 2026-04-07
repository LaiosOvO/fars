from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from fars.models import ParsedPaper


class PaperParser(ABC):
    @abstractmethod
    async def parse_pdf(self, pdf_path: str | Path) -> ParsedPaper:
        raise NotImplementedError
