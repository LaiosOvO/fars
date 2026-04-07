from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

import httpx

from fars_kg.parsers.base import ParseResult, ParsedCitation, ParsedSection

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}


class GrobidParser:
    provider_name = "grobid"

    def __init__(self, base_url: str, timeout_seconds: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def parse_version(self, version: object) -> ParseResult:
        local_pdf_path = getattr(version, "local_pdf_path", None)
        if not local_pdf_path:
            raise ValueError("Paper version has no local_pdf_path for GROBID parsing")
        pdf_path = Path(local_pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        with pdf_path.open("rb") as handle:
            response = httpx.post(
                f"{self.base_url}/api/processFulltextDocument",
                files={"input": (pdf_path.name, handle, "application/pdf")},
                timeout=self.timeout_seconds,
            )
        response.raise_for_status()
        xml = response.text
        return ParseResult(
            raw_tei_xml=xml,
            sections=self._extract_sections(xml),
            citations=self._extract_citations(xml),
        )

    def _extract_sections(self, xml: str) -> list[ParsedSection]:
        root = ET.fromstring(xml)
        sections: list[ParsedSection] = []
        body_divs = root.findall(".//tei:text/tei:body//tei:div", TEI_NS)
        for div in body_divs:
            heading = self._join_text(div.find("tei:head", TEI_NS))
            paragraphs = [self._join_text(p) for p in div.findall("tei:p", TEI_NS)]
            paragraphs = [paragraph for paragraph in paragraphs if paragraph]
            if heading or paragraphs:
                sections.append(ParsedSection(section_type="body", heading=heading, paragraphs=paragraphs))
        if not sections:
            abstract = self._join_text(root.find(".//tei:abstract", TEI_NS))
            if abstract:
                sections.append(ParsedSection(section_type="abstract", heading="Abstract", paragraphs=[abstract]))
        return sections

    def _extract_citations(self, xml: str) -> list[ParsedCitation]:
        root = ET.fromstring(xml)
        citations: list[ParsedCitation] = []
        for bibl in root.findall(".//tei:listBibl/tei:biblStruct", TEI_NS):
            raw_reference = self._join_text(bibl)
            if raw_reference:
                citations.append(ParsedCitation(raw_reference=raw_reference))
        return citations

    @staticmethod
    def _join_text(node: ET.Element | None) -> str | None:
        if node is None:
            return None
        text = " ".join(part.strip() for part in node.itertext() if part.strip())
        return text or None
