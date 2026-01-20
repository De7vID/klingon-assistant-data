#!/usr/bin/env python3
"""
Source Parser: Parse source strings into structured citations.

Converts source strings like:
  "[1] {TKD:src}, [2] {KGT p.56:src}"
  "[1] {HQ 13.1, p.8-10, Mar. 2004:src}"
  "[1] {SkyBox S27:src} (reprinted in {HQ 5.3, p.15, Sep. 1996:src})"

Into structured citations with source IDs, page numbers, etc.
"""

import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SourceCitation:
    """A structured source citation."""
    index: int              # Citation index [1], [2], etc.
    source_id: str          # Reference to sources.yaml key
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    section: Optional[str] = None
    volume: Optional[int] = None
    issue: Optional[float] = None
    date: Optional[str] = None
    reprinted_in: Optional['SourceCitation'] = None
    raw_text: str = ""      # Original text for reconstruction

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML output."""
        result = {'source': self.source_id}
        if self.page_start:
            result['page_start'] = self.page_start
        if self.page_end:
            result['page_end'] = self.page_end
        if self.section:
            result['section'] = self.section
        if self.volume:
            result['volume'] = self.volume
        if self.issue:
            result['issue'] = self.issue
        if self.date:
            result['date'] = self.date
        if self.reprinted_in:
            result['reprinted_in'] = self.reprinted_in.to_dict()
        return result


# Mapping from short names to source IDs
SOURCE_ID_MAP = {
    'TKD': 'tkd',
    'KGT': 'kgt',
    'TKDA': 'tkda',
    'HQ': 'holqed',
    'CK': 'ck',
    'PK': 'pk',
    'TNK': 'tnk',
    'BoP': 'bop',
    "paq'batlh": 'paqbatlh',
    "paq'batlh 2ed": 'paqbatlh_2ed',
}


def normalize_source_id(text: str) -> str:
    """Normalize a source short name to source ID."""
    text = text.strip()

    # Check explicit mapping
    if text in SOURCE_ID_MAP:
        return SOURCE_ID_MAP[text]

    # Handle common patterns
    # qep'a' NN (YYYY) -> qepa_YYYY
    match = re.match(r"qep'a'\s*(?:\d+\s*)?\((\d{4})\)", text)
    if match:
        return f"qepa_{match.group(1)}"

    # qepHom'a' YYYY -> qephom_YYYY
    match = re.match(r"(?:Saarbrücken\s+)?qepHom'a'\s*(\d{4})", text)
    if match:
        return f"qephom_{match.group(1)}"

    # KLI mailing list YYYY.MM.DD -> kli_mailing_list
    if 'KLI mailing list' in text:
        return 'kli_mailing_list'

    # SkyBox SNN -> skybox_sNN
    match = re.match(r"SkyBox\s*S(\d+)", text)
    if match:
        return f"skybox_s{match.group(1)}"

    # startrek.klingon -> startrek_klingon
    if 'startrek.klingon' in text or 's.k' in text:
        return 'startrek_klingon'

    # HQ -> holqed
    if text.startswith('HQ'):
        return 'holqed'

    # Generic: lowercase and replace spaces/special chars with underscore
    source_id = re.sub(r'[^\w]', '_', text.lower())
    source_id = re.sub(r'_+', '_', source_id)
    source_id = source_id.strip('_')
    return source_id


def parse_source_text(text: str) -> Optional[SourceCitation]:
    """Parse a single source text like 'TKD p.56' or 'HQ 13.1, p.8-10, Mar. 2004'."""
    if not text:
        return None

    text = text.strip()

    # Extract page numbers
    page_start = None
    page_end = None
    page_match = re.search(r'p\.?\s*(\d+)(?:\s*-\s*(\d+))?', text)
    if page_match:
        page_start = int(page_match.group(1))
        if page_match.group(2):
            page_end = int(page_match.group(2))
        # Remove page from text
        text = text[:page_match.start()] + text[page_match.end():]

    # Extract section (like "6.6")
    section = None
    section_match = re.search(r'\s+(\d+\.\d+)\s*', text)
    if section_match:
        section = section_match.group(1)
        text = text[:section_match.start()] + text[section_match.end():]

    # Extract volume/issue for journals (like "13.1")
    volume = None
    issue = None
    vol_match = re.search(r'\s+(\d+)\.(\d+)', text)
    if vol_match:
        volume = int(vol_match.group(1))
        issue = float(vol_match.group(2))
        text = text[:vol_match.start()] + text[vol_match.end():]

    # Extract date (like "Mar. 2004")
    date = None
    date_match = re.search(r',?\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{4})', text)
    if date_match:
        date = date_match.group(1)
        text = text[:date_match.start()] + text[date_match.end():]

    # Clean up remaining text to get source name
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.rstrip(',').strip()

    source_id = normalize_source_id(text)

    return SourceCitation(
        index=0,
        source_id=source_id,
        page_start=page_start,
        page_end=page_end,
        section=section,
        volume=volume,
        issue=issue,
        date=date,
        raw_text=text
    )


def parse_source_field(source_str: str) -> List[SourceCitation]:
    """Parse a full source field string into list of citations."""
    if not source_str or not source_str.strip():
        return []

    citations = []

    # Split on numbered citations [1], [2], etc.
    # Pattern: [N] {source_text:src} (optional: reprinted in {...})
    pattern = r'\[(\d+)\]\s*\{([^}]+):src\}(?:\s*\(reprinted in \{([^}]+):src\}\))?'

    for match in re.finditer(pattern, source_str):
        index = int(match.group(1))
        source_text = match.group(2)
        reprinted_text = match.group(3)

        citation = parse_source_text(source_text)
        if citation:
            citation.index = index

            # Handle reprinted in
            if reprinted_text:
                reprint_citation = parse_source_text(reprinted_text)
                if reprint_citation:
                    citation.reprinted_in = reprint_citation

            citations.append(citation)

    return citations


def citations_to_yaml(citations: List[SourceCitation]) -> List[Dict]:
    """Convert list of citations to YAML-friendly format."""
    return [c.to_dict() for c in citations]


def reconstruct_source_text(citations: List[SourceCitation], sources_db: Dict[str, Dict]) -> str:
    """Reconstruct the original source text from structured citations."""
    parts = []
    for i, c in enumerate(citations, 1):
        # Get the source info
        source_info = sources_db.get(c.source_id, {})
        short_name = source_info.get('short_name', c.raw_text)

        text = short_name
        if c.section:
            text += f' {c.section}'
        if c.volume:
            text += f' {c.volume}'
            if c.issue:
                text += f'.{int(c.issue)}'
        if c.page_start:
            text += f', p.{c.page_start}'
            if c.page_end:
                text += f'-{c.page_end}'
        if c.date:
            text += f', {c.date}'

        part = f'[{i}] {{{text}:src}}'

        if c.reprinted_in:
            r = c.reprinted_in
            r_info = sources_db.get(r.source_id, {})
            r_name = r_info.get('short_name', r.raw_text)
            r_text = r_name
            if r.volume:
                r_text += f' {r.volume}'
                if r.issue:
                    r_text += f'.{int(r.issue)}'
            if r.page_start:
                r_text += f', p.{r.page_start}'
            if r.date:
                r_text += f', {r.date}'
            part += f' (reprinted in {{{r_text}:src}})'

        parts.append(part)

    return ', '.join(parts)


# Test cases
if __name__ == '__main__':
    test_cases = [
        "[1] {TKD:src}",
        "[1] {TKD:src}, [2] {KGT p.56:src}",
        "[1] {TKD 6.6:src}, [2] {KGT p.178-9:src}",
        "[1] {HQ 13.1, p.8-10, Mar. 2004:src}",
        "[1] {SkyBox S27:src} (reprinted in {HQ 5.3, p.15, Sep. 1996:src})",
        "[1] {qep'a' 25 (2018):src}",
        "[1] {Saarbrücken qepHom'a' 2023:src}",
        "[1] {KLI mailing list 2009.07.27:src}",
    ]

    for source_str in test_cases:
        print(f"\nInput: {source_str}")
        citations = parse_source_field(source_str)
        for c in citations:
            print(f"  [{c.index}] {c.source_id}", end='')
            if c.page_start:
                print(f" p.{c.page_start}", end='')
                if c.page_end:
                    print(f"-{c.page_end}", end='')
            if c.section:
                print(f" sec.{c.section}", end='')
            if c.volume:
                print(f" vol.{c.volume}", end='')
            if c.issue:
                print(f" iss.{c.issue}", end='')
            if c.date:
                print(f" {c.date}", end='')
            if c.reprinted_in:
                print(f" (reprinted in {c.reprinted_in.source_id})", end='')
            print()
        print(f"  YAML: {citations_to_yaml(citations)}")
