#!/usr/bin/env python3
"""
Migration script: Convert XML lexicon entries to YAML format.

This script:
1. Parses all mem-*.xml files
2. Extracts and structures sources into sources.yaml
3. Parses part_of_speech fields into structured format
4. Identifies and extracts shared notes
5. Groups entries by homophones and derived forms
6. Generates YAML files in the new directory structure
"""

import os
import re
import sys
import html
import yaml
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import xml.etree.ElementTree as ET

# Add build directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from definition_parser import parse_definition, DefinitionPart
from source_parser import SourceCitation, citations_to_yaml

# Ensure proper YAML output
yaml.SafeDumper.ignore_aliases = lambda *args: True

# ==============================================================================
# Data Classes
# ==============================================================================

@dataclass
class POSInfo:
    """Parsed part of speech information."""
    pos: str = ""
    pos_subtype: Optional[str] = None
    homophone: Optional[int] = None
    categories: List[str] = field(default_factory=list)
    metadata_tags: List[str] = field(default_factory=list)
    raw: str = ""  # Original string for reconstruction

@dataclass
class DefinitionPart:
    """A single part of a definition."""
    text: str
    sort_keyword: Optional[str] = None
    sources: List[SourceCitation] = field(default_factory=list)

@dataclass
class DefinitionInfo:
    """Structured definition with parts and global parenthetical."""
    parts: List[DefinitionPart] = field(default_factory=list)
    global_parenthetical: Optional[str] = None
    raw: str = ""  # Original string for reconstruction

@dataclass
class Entry:
    """A lexicon entry."""
    id: int
    entry_name: str
    part_of_speech: str
    pos_info: POSInfo = None
    definition: str = ""
    definition_info: DefinitionInfo = None
    synonyms: str = ""
    antonyms: str = ""
    see_also: str = ""
    notes: str = ""
    hidden_notes: str = ""
    components: str = ""
    examples: str = ""
    search_tags: str = ""
    source: str = ""
    sources: List[SourceCitation] = field(default_factory=list)
    # Translations
    translations: Dict[str, Dict[str, str]] = field(default_factory=dict)
    # Derived entries (nested)
    derived: List['Entry'] = field(default_factory=list)
    # File path (computed)
    file_path: str = ""
    slug: str = ""
    # Section (main/extra/examples) based on source XML file
    section: str = "main"
    # Original XML filename for exact round-trip
    _original_file: str = ""

# ==============================================================================
# Constants
# ==============================================================================

VERB_SUBTYPES = {'i', 't', 'is', 'ambi', 'i_c', 't_c', 'pref', 'suff'}
NOUN_SUBTYPES = {'name', 'num', 'pro', 'body', 'being', 'place',
                 'inhpl', 'inhps', 'plural', 'suff'}
SENTENCE_SUBTYPES = {'eu', 'idiom', 'mv', 'nt', 'phr', 'prov', 'Ql',
                     'rej', 'rp', 'sp', 'toast', 'lyr', 'bc'}
EXCL_SUBTYPES = {'epithet'}

CATEGORIES = {'anim', 'archaic', 'food', 'inv', 'slang', 'weap', 'reg'}
METADATA_TAGS = {'deriv', 'alt', 'fic', 'hyp', 'extcan', 'klcp1',
                 'terran', 'noanki', 'nodict', 'nolink'}

LANGUAGES = ['de', 'fa', 'sv', 'ru', 'zh_HK', 'pt', 'fi', 'fr']

# Source name to ID mapping
SOURCE_ID_MAP = {
    'TKD': 'tkd',
    'TKDA': 'tkda',
    'TKW': 'tkw',
    'KGT': 'kgt',
    'CK': 'ck',
    'PK': 'pk',
    'KCD': 'kcd',
    'TNK': 'tnk',
    'HQ': 'holqed',
    'BoP': 'bop',
    'FTG': 'ftg',
    's.k': 'startrek_klingon',
    's.e': 'startrek_expertforum',
    'msn': 'msn',
}

# POS to directory mapping
POS_DIRS = {
    'v': 'verbs',
    'n': 'nouns',
    'adv': 'adverbials',
    'conj': 'conjunctions',
    'ques': 'questions',
    'sen': 'sentences',
    'excl': 'exclamations',
    'src': 'sources'
}

# ==============================================================================
# Parsing Functions
# ==============================================================================

def parse_part_of_speech(pos_string: str) -> POSInfo:
    """Parse part of speech string into structured format."""
    result = POSInfo(raw=pos_string)

    if ':' not in pos_string:
        result.pos = pos_string
        return result

    parts = pos_string.split(':', 1)
    result.pos = parts[0]

    modifiers = [m.strip() for m in parts[1].split(',')]

    # Determine subtype set based on POS
    if result.pos == 'v':
        subtype_set = VERB_SUBTYPES
    elif result.pos == 'n':
        subtype_set = NOUN_SUBTYPES
    elif result.pos == 'sen':
        subtype_set = SENTENCE_SUBTYPES
    elif result.pos == 'excl':
        subtype_set = EXCL_SUBTYPES
    else:
        subtype_set = set()

    for mod in modifiers:
        # Check for homophone number (e.g., "1", "2", "1h", "2h")
        # The 'h' suffix indicates a hidden homophone
        homophone_match = re.match(r'^(\d+)h?$', mod)
        if homophone_match:
            result.homophone = int(homophone_match.group(1))
        elif mod in subtype_set:
            if result.pos_subtype is None:
                result.pos_subtype = mod
            else:
                # Multiple subtypes - treat as category
                result.categories.append(mod)
        elif mod in CATEGORIES:
            result.categories.append(mod)
        elif mod in METADATA_TAGS:
            result.metadata_tags.append(mod)
        else:
            # Unknown modifier - treat as category to preserve
            result.categories.append(mod)

    return result


def parse_source_field(source_string: str) -> List[SourceCitation]:
    """Parse source field into list of citations."""
    if not source_string or not source_string.strip():
        return []

    citations = []

    # Pattern for source items: [N] {content:src} (optional reprint)
    # This handles complex cases like:
    # [1] {SkyBox S27:src} (reprinted in {HQ 5.3, p.15, Sep. 1996:src})
    pattern = r'\[(\d+)\]\s*\{([^}]+):src\}(?:\s*\(reprinted in \{([^}]+):src\}\))?'

    for match in re.finditer(pattern, source_string):
        index = int(match.group(1))
        source_content = match.group(2)
        reprint_content = match.group(3)

        citation = parse_source_content(source_content)
        citation.index = index
        citation.raw_text = match.group(0)

        if reprint_content:
            citation.reprinted_in = parse_source_content(reprint_content)

        citations.append(citation)

    return citations


def parse_source_content(content: str) -> SourceCitation:
    """Parse individual source content string."""
    citation = SourceCitation(index=0, source_id="", raw_text=content)

    # Try HolQeD pattern: "HQ V.I, p.P-P, Mon. YYYY"
    hq_match = re.match(r'^HQ\s+(\d+)\.(\d+)(?:,\s*p\.(\d+)(?:-(\d+))?)?(?:,\s*([A-Za-z]+\.?\s*\d{4}))?$', content)
    if hq_match:
        citation.source_id = 'holqed'
        citation.volume = int(hq_match.group(1))
        citation.issue = int(hq_match.group(2))
        if hq_match.group(3):
            citation.page_start = int(hq_match.group(3))
            if hq_match.group(4):
                citation.page_end = int(hq_match.group(4))
        if hq_match.group(5):
            citation.date = hq_match.group(5)
        return citation

    # Try qep'a' pattern: "qep'a' N (YYYY)"
    qepa_match = re.match(r"^qep'a'\s+(\d+)\s*\((\d{4})\)$", content)
    if qepa_match:
        year = qepa_match.group(2)
        citation.source_id = f"qepa_{year}"
        citation.date = year
        return citation

    # Try qepHom'a' pattern: "Location qepHom'a' YYYY"
    qephom_match = re.match(r'^(.+?)\s+qepHom\'a\'\s+(\d{4})$', content)
    if qephom_match:
        year = qephom_match.group(2)
        citation.source_id = f"qephom_{year}"
        citation.date = year
        return citation

    # Try KLI mailing list: "KLI mailing list YYYY.MM.DD"
    kli_match = re.match(r'^KLI mailing list\s+(\d{4})\.(\d{2})\.(\d{2})$', content)
    if kli_match:
        citation.source_id = 'kli_mailing_list'
        citation.date = f"{kli_match.group(1)}-{kli_match.group(2)}-{kli_match.group(3)}"
        return citation

    # Try newsgroup: "s.k YYYY.MM.DD" or "msn YYYY.MM.DD"
    newsgroup_match = re.match(r'^(s\.k|s\.e|msn)\s+(\d{4})\.(\d{2})\.(\d{2})$', content)
    if newsgroup_match:
        citation.source_id = SOURCE_ID_MAP.get(newsgroup_match.group(1), newsgroup_match.group(1))
        citation.date = f"{newsgroup_match.group(2)}-{newsgroup_match.group(3)}-{newsgroup_match.group(4)}"
        return citation

    # Try paq'batlh with edition: "paq'batlh Ned p.N-M"
    paqbatlh_match = re.match(r"^paq'batlh\s+(\d+)ed(?:\s+p\.(\d+)(?:-(\d+))?)?$", content)
    if paqbatlh_match:
        citation.source_id = 'paqbatlh'
        if paqbatlh_match.group(2):
            citation.page_start = int(paqbatlh_match.group(2))
            if paqbatlh_match.group(3):
                citation.page_end = int(paqbatlh_match.group(3))
        return citation

    # Try book with page range: "BOOK p.N-M"
    book_page_match = re.match(r'^([A-Za-z]+(?:\s+\d+ed)?)\s+p\.(\d+)(?:-(\d+))?$', content)
    if book_page_match:
        book_name = book_page_match.group(1)
        citation.source_id = SOURCE_ID_MAP.get(book_name, book_name.lower())
        citation.page_start = int(book_page_match.group(2))
        if book_page_match.group(3):
            citation.page_end = int(book_page_match.group(3))
        return citation

    # Try book with section: "BOOK N.N"
    book_section_match = re.match(r'^([A-Z]+)\s+(\d+\.\d+)$', content)
    if book_section_match:
        book_name = book_section_match.group(1)
        citation.source_id = SOURCE_ID_MAP.get(book_name, book_name.lower())
        citation.section = book_section_match.group(2)
        return citation

    # Try SkyBox: "SkyBox SNN"
    skybox_match = re.match(r'^SkyBox\s+(S\d+|SP\d+)$', content)
    if skybox_match:
        citation.source_id = f"skybox_{skybox_match.group(1).lower()}"
        return citation

    # Fallback: Use content as source ID
    citation.source_id = normalize_source_id(content)
    return citation


def normalize_source_id(name: str) -> str:
    """Convert source name to canonical ID."""
    name = name.strip()
    if name in SOURCE_ID_MAP:
        return SOURCE_ID_MAP[name]
    # Generate slug-like ID
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


def generate_slug(entry_name: str, pos: str, homophone: Optional[int] = None,
                  pos_subtype: Optional[str] = None) -> str:
    """Generate deterministic slug from entry name and POS."""
    # Normalize entry name
    slug_base = entry_name.strip()

    # Remove sentence-final punctuation
    if slug_base.endswith(('.', '!', '?')):
        slug_base = slug_base[:-1]

    # Convert leading hyphen (suffix marker) to underscore
    if slug_base.startswith('-'):
        slug_base = '_' + slug_base[1:]

    # Convert spaces to underscores
    slug_base = slug_base.replace(' ', '_')

    # Get base POS
    base_pos = pos.split(':')[0] if ':' in pos else pos

    # Build slug
    slug = f"{slug_base}_{base_pos}"

    # Add homophone number if present
    if homophone is not None:
        slug = f"{slug}_{homophone}"

    # Add subtype for suffixes/prefixes
    if pos_subtype in ('suff', 'pref'):
        slug = f"{slug}_{pos_subtype}"

    return slug


def get_sort_letter(name: str) -> str:
    """Get the first Klingon letter for sorting/directory placement."""
    name_lower = name.lower()

    # Handle leading underscore from suffix normalization
    if name_lower.startswith('_'):
        name_lower = name_lower[1:]

    # Check for digraphs first
    if name_lower.startswith("ch"):
        return "ch"
    if name_lower.startswith("gh"):
        return "gh"
    if name_lower.startswith("ng"):
        return "ng"
    if name_lower.startswith("tlh"):
        return "tlh"

    # Handle apostrophe (qaghwI')
    if name_lower.startswith("'"):
        return "'"

    # Otherwise, first character
    return name_lower[0] if name_lower else "_"


def get_file_path(entry: Entry) -> str:
    """Determine file path for an entry."""
    pos_info = entry.pos_info
    base_pos = pos_info.pos

    # Handle suffixes
    if pos_info.pos_subtype in ('suff', 'pref'):
        parent_pos = 'verb' if base_pos == 'v' else 'noun'
        base_dir = f"entries/suffixes/{parent_pos}"
    else:
        base_dir = f"entries/{POS_DIRS.get(base_pos, 'other')}"

    # Get first letter
    first_letter = get_sort_letter(entry.entry_name)

    # Build filename from entry name (without homophone number)
    filename_base = entry.entry_name
    if filename_base.endswith(('.', '!', '?')):
        filename_base = filename_base[:-1]
    if filename_base.startswith('-'):
        filename_base = '_' + filename_base[1:]
    filename_base = filename_base.replace(' ', '_')

    return f"{base_dir}/{first_letter}/{filename_base}.yaml"


# ==============================================================================
# XML Parsing
# ==============================================================================

def get_section_for_file(filename: str) -> str:
    """Determine section based on source XML file."""
    if 'mem-27-extra' in filename:
        return 'extra'
    elif 'mem-28-examples' in filename:
        return 'examples'
    else:
        return 'main'


def parse_xml_files(data_dir: Path) -> List[Entry]:
    """Parse all mem-*.xml files and return list of entries."""
    entries = []
    next_id = 10000  # Start ID at 10000 like renumber.py

    # Get all mem-*.xml files in order (same order as renumber.py)
    xml_files = sorted(data_dir.glob("mem-*.xml"))

    for xml_file in xml_files:
        # Skip header and footer
        if 'header' in xml_file.name or 'footer' in xml_file.name:
            continue

        print(f"Parsing {xml_file.name}...")

        # Determine section for entries in this file
        section = get_section_for_file(xml_file.name)

        # Read file content
        content = xml_file.read_text(encoding='utf-8')

        # Parse tables
        for table_match in re.finditer(r'<table name="mem">(.*?)</table>', content, re.DOTALL):
            table_content = table_match.group(1)
            entry = parse_entry(table_content, next_id, section, xml_file.name)
            if entry:
                entries.append(entry)
                next_id += 1

    print(f"Parsed {len(entries)} entries")
    return entries


def parse_entry(table_content: str, assigned_id: int, section: str = 'main', source_file: str = '') -> Optional[Entry]:
    """Parse a single entry from table content."""
    columns = {}

    for col_match in re.finditer(r'<column name="([^"]+)">(.*?)</column>', table_content, re.DOTALL):
        col_name = col_match.group(1)
        col_value = html.unescape(col_match.group(2))  # Decode XML entities
        columns[col_name] = col_value

    if 'entry_name' not in columns:
        return None

    # Use assigned ID (XML _id may be empty)
    entry = Entry(
        id=assigned_id,
        entry_name=columns.get('entry_name', ''),
        part_of_speech=columns.get('part_of_speech', ''),
        definition=columns.get('definition', ''),
        synonyms=columns.get('synonyms', ''),
        antonyms=columns.get('antonyms', ''),
        see_also=columns.get('see_also', ''),
        notes=columns.get('notes', ''),
        hidden_notes=columns.get('hidden_notes', ''),
        components=columns.get('components', ''),
        examples=columns.get('examples', ''),
        search_tags=columns.get('search_tags', ''),
        source=columns.get('source', ''),
        section=section,
        _original_file=source_file,
    )

    # Parse structured fields
    entry.pos_info = parse_part_of_speech(entry.part_of_speech)
    entry.sources = parse_source_field(entry.source)
    entry.slug = generate_slug(
        entry.entry_name,
        entry.pos_info.pos,
        entry.pos_info.homophone,
        entry.pos_info.pos_subtype
    )
    entry.file_path = get_file_path(entry)

    # Parse translations
    for lang in LANGUAGES:
        trans = {}
        if columns.get(f'definition_{lang}'):
            trans['definition'] = columns[f'definition_{lang}']
        if columns.get(f'notes_{lang}'):
            trans['notes'] = columns[f'notes_{lang}']
        if columns.get(f'examples_{lang}'):
            trans['examples'] = columns[f'examples_{lang}']
        if columns.get(f'search_tags_{lang}'):
            trans['search_tags'] = columns[f'search_tags_{lang}']
        if trans:
            entry.translations[lang] = trans

    return entry


# ==============================================================================
# Source Registry Generation
# ==============================================================================

def extract_sources(entries: List[Entry]) -> Dict[str, Dict]:
    """Extract all unique sources from entries."""
    sources = {}

    for entry in entries:
        for citation in entry.sources:
            source_id = citation.source_id
            if source_id and source_id not in sources:
                sources[source_id] = infer_source_metadata(citation)

            # Also check reprints
            if citation.reprinted_in:
                reprint_id = citation.reprinted_in.source_id
                if reprint_id and reprint_id not in sources:
                    sources[reprint_id] = infer_source_metadata(citation.reprinted_in)

    return sources


def infer_source_metadata(citation: SourceCitation) -> Dict:
    """Infer source metadata from citation."""
    source_id = citation.source_id

    # Known sources
    known_sources = {
        'tkd': {'name': 'The Klingon Dictionary', 'short_name': 'TKD', 'type': 'book'},
        'tkda': {'name': 'The Klingon Dictionary Addendum', 'short_name': 'TKDA', 'type': 'book'},
        'tkw': {'name': 'The Klingon Way', 'short_name': 'TKW', 'type': 'book'},
        'kgt': {'name': 'Klingon for the Galactic Traveler', 'short_name': 'KGT', 'type': 'book'},
        'ck': {'name': 'Conversational Klingon', 'short_name': 'CK', 'type': 'audio'},
        'pk': {'name': 'Power Klingon', 'short_name': 'PK', 'type': 'audio'},
        'kcd': {'name': 'Star Trek: Klingon (CD game)', 'short_name': 'KCD', 'type': 'game'},
        'tnk': {'name': "Talk Now! Klingon", 'short_name': 'TNK', 'type': 'software'},
        'holqed': {'name': 'HolQeD', 'short_name': 'HQ', 'type': 'journal'},
        'bop': {'name': 'Bird of Prey poster', 'short_name': 'BoP', 'type': 'media'},
        'ftg': {'name': 'Federation Travel Guide', 'short_name': 'FTG', 'type': 'book'},
        'paqbatlh': {'name': "paq'batlh", 'short_name': "paq'batlh", 'type': 'book'},
        'kli_mailing_list': {'name': 'KLI mailing list', 'short_name': 'KLI mailing list', 'type': 'mailing_list'},
        'startrek_klingon': {'name': 'startrek.klingon newsgroup', 'short_name': 's.k', 'type': 'newsgroup'},
        'startrek_expertforum': {'name': 'startrek.expertforum', 'short_name': 's.e', 'type': 'newsgroup'},
        'msn': {'name': 'MSN expert forum', 'short_name': 'msn', 'type': 'newsgroup'},
    }

    if source_id in known_sources:
        return known_sources[source_id]

    # Try to infer from ID pattern
    if source_id.startswith('qepa_'):
        year = source_id.split('_')[1]
        return {'name': f"qep'a' ({year})", 'short_name': f"qep'a' {year}", 'type': 'event', 'year': int(year)}

    if source_id.startswith('qephom_'):
        year = source_id.split('_')[1]
        return {'name': f"qepHom'a' ({year})", 'short_name': f"qepHom'a' {year}", 'type': 'event', 'year': int(year)}

    if source_id.startswith('skybox_'):
        item_id = source_id.replace('skybox_', '').upper()
        return {'name': f'SkyBox {item_id}', 'short_name': f'SkyBox {item_id}', 'type': 'media'}

    # Unknown source
    return {'name': source_id, 'short_name': source_id, 'type': 'unknown'}


def write_sources_yaml(sources: Dict[str, Dict], output_path: Path):
    """Write sources.yaml file."""
    output = {'sources': sources}

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(output, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"Wrote {len(sources)} sources to {output_path}")


# ==============================================================================
# Entry Grouping
# ==============================================================================

def group_entries(entries: List[Entry]) -> Dict[str, List[Entry]]:
    """Group entries by file path."""
    groups = defaultdict(list)

    for entry in entries:
        groups[entry.file_path].append(entry)

    # Sort entries within each group
    for file_path, group in groups.items():
        groups[file_path] = sorted(group, key=lambda e: (
            'deriv' in e.pos_info.metadata_tags,  # Non-derived first
            e.pos_info.homophone or 0,  # By homophone number
            e.entry_name  # Alphabetically
        ))

    return dict(groups)


# ==============================================================================
# YAML Generation
# ==============================================================================

def entry_to_yaml_dict(entry: Entry) -> Dict:
    """Convert entry to YAML-compatible dictionary."""
    result = {
        'entry_name': entry.entry_name,
        'slug': entry.slug,
    }

    # POS info - store original for exact reconstruction
    result['part_of_speech'] = entry.part_of_speech  # Original string

    # Also store parsed components for new schema usage
    result['pos'] = entry.pos_info.pos
    if entry.pos_info.pos_subtype:
        result['pos_subtype'] = entry.pos_info.pos_subtype
    if entry.pos_info.homophone:
        result['homophone'] = entry.pos_info.homophone
    if entry.pos_info.categories:
        result['categories'] = entry.pos_info.categories
    if entry.pos_info.metadata_tags:
        result['metadata_tags'] = entry.pos_info.metadata_tags

    # Status (provenance - derive from tags)
    if 'hyp' in entry.pos_info.metadata_tags:
        result['status'] = 'hypothetical'
    elif 'extcan' in entry.pos_info.metadata_tags:
        result['status'] = 'extended_canon'
    else:
        result['status'] = 'canonical'

    # Nodict flag (separate from status - can co-occur with any status)
    if 'nodict' in entry.pos_info.metadata_tags:
        result['nodict'] = True

    # Section (editorial placement - based on source XML file)
    result['section'] = entry.section

    # Definition - structured format per REDESIGN.md
    if entry.definition and not entry.definition.startswith('{'):
        is_be_verb = entry.pos_info.pos_subtype == 'is'
        parsed = parse_definition(entry.definition, entry.pos_info.pos_subtype)

        # Check if we need structured output (multiple parts, flags, or global paren)
        needs_structure = (
            len(parsed.parts) > 1 or
            parsed.global_parenthetical or
            parsed.no_permute or
            parsed.dedup or
            parsed.etc_suffix
        )

        if needs_structure:
            # Structured definition with parts and/or flags
            definition_struct = {
                'text': entry.definition,  # Raw text for backward compat
            }
            if len(parsed.parts) > 1 or parsed.global_parenthetical:
                definition_struct['parts'] = []
                for part in parsed.parts:
                    part_dict = {'text': part.text}
                    if part.sort_keyword:
                        part_dict['sort_keyword'] = part.sort_keyword
                    definition_struct['parts'].append(part_dict)
                if parsed.global_parenthetical:
                    definition_struct['global_parenthetical'] = parsed.global_parenthetical
            # Add E-K generation flags
            if parsed.no_permute:
                definition_struct['no_permute'] = True
            if parsed.dedup:
                definition_struct['dedup'] = True
            if parsed.etc_suffix:
                definition_struct['etc_suffix'] = True
            result['definition'] = definition_struct
        else:
            # Simple definition - just the text
            result['definition'] = entry.definition
    else:
        # Reference or empty definition
        result['definition'] = entry.definition

    # Relations
    if entry.synonyms:
        result['synonyms'] = entry.synonyms
    if entry.antonyms:
        result['antonyms'] = entry.antonyms
    if entry.see_also:
        result['see_also'] = entry.see_also

    # Notes
    if entry.notes:
        result['notes'] = entry.notes
    if entry.hidden_notes:
        result['hidden_notes'] = entry.hidden_notes

    # Components
    if entry.components:
        result['components'] = entry.components

    # Examples
    if entry.examples:
        result['examples'] = entry.examples

    # Search tags
    if entry.search_tags:
        result['search_tags'] = entry.search_tags

    # Sources - structured format per REDESIGN.md
    if entry.source:
        citations = parse_source_field(entry.source)
        if citations:
            result['sources'] = {
                'raw': entry.source,  # For backward compat
                'citations': citations_to_yaml(citations)
            }
        else:
            # Couldn't parse, keep raw text
            result['sources'] = {'raw': entry.source}

    # Translations
    if entry.translations:
        result['translations'] = entry.translations

    # Original metadata (for verification and round-trip)
    result['_original_id'] = entry.id
    result['_original_file'] = entry._original_file

    return result


def write_entry_files(groups: Dict[str, List[Entry]], base_dir: Path):
    """Write YAML files for each entry group."""
    files_written = 0

    for file_path, entries in groups.items():
        full_path = base_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Build YAML content
        if len(entries) == 1:
            content = {'entry': entry_to_yaml_dict(entries[0])}
        else:
            content = {'entries': [entry_to_yaml_dict(e) for e in entries]}

        with open(full_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(content, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        files_written += 1

    print(f"Wrote {files_written} YAML files")
    return files_written


# ==============================================================================
# Shared Notes Detection
# ==============================================================================

def find_shared_notes(entries: List[Entry]) -> Dict[str, Dict]:
    """Find notes that appear in multiple entries."""
    note_occurrences = defaultdict(list)

    for entry in entries:
        if not entry.notes:
            continue

        # Normalize note text for comparison
        normalized = normalize_note_text(entry.notes)
        note_occurrences[normalized].append(entry.entry_name)

    # Filter to notes appearing in 2+ entries
    shared = {}
    for normalized, entry_names in note_occurrences.items():
        if len(entry_names) >= 2:
            note_id = generate_note_id(normalized)
            shared[note_id] = {
                'text': normalized,
                'used_by': entry_names,
                'count': len(entry_names)
            }

    return shared


def normalize_note_text(text: str) -> str:
    """Normalize note text for comparison."""
    # Remove inline source citations
    text = re.sub(r'\[\d+(?:,\s*p\.\d+(?:-\d+)?)?\]', '', text)
    # Normalize whitespace
    text = ' '.join(text.split())
    return text.strip()


def generate_note_id(text: str) -> str:
    """Generate ID for a note from its text."""
    # Known patterns
    if 'musical scale' in text.lower():
        return 'musical_scale'
    if 'refers to the sound' in text.lower():
        return 'consonant_sound'
    if 'inherent plural' in text.lower():
        return 'inherent_plural'

    # Generate from first words
    words = re.findall(r'\w+', text)[:4]
    return '_'.join(words).lower()


def write_shared_notes(shared_notes: Dict[str, Dict], output_dir: Path):
    """Write shared notes to files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for note_id, note_data in shared_notes.items():
        if note_data['count'] >= 3:  # Only write notes appearing 3+ times
            note_file = output_dir / f"{note_id}.yaml"
            content = {
                'note': {
                    'id': note_id,
                    'text': note_data['text'],
                    'used_by_count': note_data['count']
                }
            }
            with open(note_file, 'w', encoding='utf-8') as f:
                yaml.safe_dump(content, f, default_flow_style=False, allow_unicode=True)

    print(f"Wrote {len([n for n in shared_notes.values() if n['count'] >= 3])} shared note files")


# ==============================================================================
# Main
# ==============================================================================

def main():
    # Get data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent

    print(f"Data directory: {data_dir}")

    # Parse XML files
    entries = parse_xml_files(data_dir)

    # Extract and write sources
    sources = extract_sources(entries)
    write_sources_yaml(sources, data_dir / 'sources.yaml')

    # Find shared notes
    shared_notes = find_shared_notes(entries)
    print(f"Found {len(shared_notes)} shared notes")
    write_shared_notes(shared_notes, data_dir / 'notes')

    # Group entries
    groups = group_entries(entries)
    print(f"Grouped into {len(groups)} files")

    # Write entry files
    write_entry_files(groups, data_dir)

    print("Migration complete!")


if __name__ == '__main__':
    main()
