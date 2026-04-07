from enum import StrEnum


class PaperVersionType(StrEnum):
    ARXIV = "arxiv"
    CONFERENCE = "conference"
    JOURNAL = "journal"
    CAMERA_READY = "camera_ready"
    UNKNOWN = "unknown"


class SectionType(StrEnum):
    ABSTRACT = "abstract"
    INTRO = "intro"
    METHOD = "method"
    EXPERIMENT = "experiment"
    CONCLUSION = "conclusion"
    REFERENCES = "references"
    OTHER = "other"


class CitationContextType(StrEnum):
    BACKGROUND = "background"
    COMPARISON = "comparison"
    EXTENSION = "extension"
    CRITIQUE = "critique"
    UNKNOWN = "unknown"


class PaperEdgeType(StrEnum):
    CITES = "cites"
    EXTENDS = "extends"
    COMPARES = "compares"
    CONTRADICTS = "contradicts"
    REPRODUCES = "reproduces"
    USES_DATASET = "uses_dataset"
    PROPOSES_METHOD = "proposes_method"
    REPORTS_RESULT_AGAINST = "reports_result_against"
