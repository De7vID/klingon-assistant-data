#!/usr/bin/env python3
"""
yaml2xml.py - Reverse migration: Convert YAML entries back to XML format.

This script reads YAML entry files and generates XML output compatible
with the original mem-*.xml format. It uses the section field to output
entries to the correct files.

Usage:
    python3 yaml2xml.py [--output-dir DIR]

If --output-dir is not specified, outputs to current directory.
"""

import argparse
import html
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict


# ==============================================================================
# Constants
# ==============================================================================

# Languages in XML column order
LANGUAGES = ['de', 'fa', 'sv', 'ru', 'zh_HK', 'pt', 'fi', 'fr']

# Klingon letter to file mapping
LETTER_TO_FILE = {
    'b': 'mem-01-b.xml',
    'ch': 'mem-02-ch.xml',
    'D': 'mem-03-D.xml',
    'gh': 'mem-04-gh.xml',
    'H': 'mem-05-H.xml',
    'j': 'mem-06-j.xml',
    'l': 'mem-07-l.xml',
    'm': 'mem-08-m.xml',
    'n': 'mem-09-n.xml',
    'ng': 'mem-10-ng.xml',
    'p': 'mem-11-p.xml',
    'q': 'mem-12-q.xml',
    'Q': 'mem-13-Q.xml',
    'r': 'mem-14-r.xml',
    'S': 'mem-15-S.xml',
    't': 'mem-16-t.xml',
    'tlh': 'mem-17-tlh.xml',
    'v': 'mem-18-v.xml',
    'w': 'mem-19-w.xml',
    'y': 'mem-20-y.xml',
    'a': 'mem-21-a.xml',
    'e': 'mem-22-e.xml',
    'I': 'mem-23-I.xml',
    'o': 'mem-24-o.xml',
    'u': 'mem-25-u.xml',
}

# Suffixes file
SUFFIXES_FILE = 'mem-26-suffixes.xml'

# Section to file mapping
SECTION_TO_FILE = {
    'extra': 'mem-27-extra.xml',
    'examples': 'mem-28-examples.xml',
}


# ==============================================================================
# YAML Loading
# ==============================================================================

def load_yaml_entries(data_dir: Path) -> List[Dict]:
    """Load all YAML entries from the entries directory."""
    entries = []
    entries_dir = data_dir / 'entries'

    for yaml_file in entries_dir.rglob('*.yaml'):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error loading {yaml_file}: {e}", file=sys.stderr)
            continue

        if not content:
            continue

        if 'entry' in content:
            entries.append(content['entry'])
        elif 'entries' in content:
            entries.extend(content['entries'])

    # Sort by original ID to maintain order
    entries.sort(key=lambda e: e.get('_original_id', 0))

    return entries


# ==============================================================================
# XML Generation
# ==============================================================================

def escape_xml(text: str) -> str:
    """Escape special characters for XML."""
    if not text:
        return ''
    # Use html.escape but preserve already-escaped entities
    # Only escape &, <, > (not quotes since we use them in attributes only)
    result = text.replace('&', '&amp;')
    result = result.replace('<', '&lt;')
    result = result.replace('>', '&gt;')
    return result


def get_definition_text(entry: Dict) -> str:
    """Extract definition text from entry (handles both string and structured)."""
    definition = entry.get('definition', '')
    if isinstance(definition, dict):
        return definition.get('text', '')
    return definition


def get_source_text(entry: Dict) -> str:
    """Extract source text from entry (handles both string and structured)."""
    sources = entry.get('sources', entry.get('source', ''))
    if isinstance(sources, dict):
        return sources.get('raw', '')
    return sources


def entry_to_xml(entry: Dict) -> str:
    """Convert a single entry to XML table format."""
    lines = ['    <table name="mem">']

    # Get translations
    translations = entry.get('translations', {})

    # Build columns in the exact order of the original XML
    columns = []

    # Core fields
    columns.append(('_id', ''))  # Empty - renumber.py fills this
    columns.append(('entry_name', entry.get('entry_name', '')))
    columns.append(('part_of_speech', entry.get('part_of_speech', '')))

    # Definition (English + translations)
    columns.append(('definition', get_definition_text(entry)))
    for lang in LANGUAGES:
        trans = translations.get(lang, {})
        columns.append((f'definition_{lang}', trans.get('definition', '')))

    # Simple fields
    columns.append(('synonyms', entry.get('synonyms', '')))
    columns.append(('antonyms', entry.get('antonyms', '')))
    columns.append(('see_also', entry.get('see_also', '')))

    # Notes (English + translations)
    columns.append(('notes', entry.get('notes', '')))
    for lang in LANGUAGES:
        trans = translations.get(lang, {})
        columns.append((f'notes_{lang}', trans.get('notes', '')))

    # Hidden notes
    columns.append(('hidden_notes', entry.get('hidden_notes', '')))

    # Components
    columns.append(('components', entry.get('components', '')))

    # Examples (English + translations)
    columns.append(('examples', entry.get('examples', '')))
    for lang in LANGUAGES:
        trans = translations.get(lang, {})
        columns.append((f'examples_{lang}', trans.get('examples', '')))

    # Search tags (English + translations)
    columns.append(('search_tags', entry.get('search_tags', '')))
    for lang in LANGUAGES:
        trans = translations.get(lang, {})
        columns.append((f'search_tags_{lang}', trans.get('search_tags', '')))

    # Source
    columns.append(('source', get_source_text(entry)))

    # Generate XML lines
    for name, value in columns:
        escaped_value = escape_xml(str(value) if value else '')
        lines.append(f'      <column name="{name}">{escaped_value}</column>')

    lines.append('    </table>')
    return '\n'.join(lines)


def get_klingon_first_letter(entry_name: str) -> str:
    """Get the first Klingon letter of an entry name.

    In Klingon, words beginning with vowels are written with a leading
    apostrophe (glottal stop). For file assignment purposes, the vowel
    determines the file (e.g., 'eb -> e -> mem-22-e.xml).
    """
    if not entry_name:
        return ''

    # Handle special prefixes
    name = entry_name.lstrip('-')  # Remove suffix indicator

    # Check for multi-character letters first
    if name.startswith('tlh'):
        return 'tlh'
    elif name.startswith('ch'):
        return 'ch'
    elif name.startswith('gh'):
        return 'gh'
    elif name.startswith('ng'):
        return 'ng'
    elif name.startswith("'"):
        # Entries starting with apostrophe: use the vowel that follows
        # e.g., 'eb -> e, 'Iw -> I, 'oH -> o
        if len(name) > 1 and name[1] in 'aeIou':
            return name[1]
        return 'a'  # Fallback for bare apostrophe
    elif name and name[0] in LETTER_TO_FILE:
        return name[0]

    # Default to first character
    return name[0] if name else ''


def is_suffix(entry: Dict) -> bool:
    """Check if entry is a suffix."""
    pos = entry.get('pos', entry.get('part_of_speech', ''))
    if ':suff' in pos or pos.endswith(':suff'):
        return True
    # Also check entry_name
    entry_name = entry.get('entry_name', '')
    return entry_name.startswith('-')


def get_file_for_entry(entry: Dict) -> str:
    """Determine which XML file an entry belongs to.

    Uses _original_file if available for exact round-trip fidelity.
    Otherwise, infers the file based on section, suffix status, and first letter.
    """
    # Use original file if available (for exact round-trip)
    original_file = entry.get('_original_file', '')
    if original_file:
        return original_file

    section = entry.get('section', 'main')

    # Extra and examples sections have dedicated files
    if section in SECTION_TO_FILE:
        return SECTION_TO_FILE[section]

    # Suffixes go to mem-26-suffixes.xml
    if is_suffix(entry):
        return SUFFIXES_FILE

    # Main entries go to letter-based files
    entry_name = entry.get('entry_name', '')
    first_letter = get_klingon_first_letter(entry_name)

    return LETTER_TO_FILE.get(first_letter, 'mem-21-a.xml')


def group_entries_by_file(entries: List[Dict]) -> Dict[str, List[Dict]]:
    """Group entries by their target XML file."""
    groups = defaultdict(list)

    for entry in entries:
        filename = get_file_for_entry(entry)
        groups[filename].append(entry)

    return dict(groups)


def write_xml_file(entries: List[Dict], output_path: Path):
    """Write entries to an XML file."""
    # Sort entries by _original_id within the file
    entries_sorted = sorted(entries, key=lambda e: e.get('_original_id', 0))

    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in entries_sorted:
            f.write(entry_to_xml(entry))
            f.write('\n')


# ==============================================================================
# Main
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Convert YAML entries back to XML format'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('.'),
        help='Output directory for XML files (default: current directory)'
    )
    args = parser.parse_args()

    # Get data directory (parent of build/)
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent

    print(f"Loading entries from {data_dir}/entries/...", file=sys.stderr)

    # Load all entries
    entries = load_yaml_entries(data_dir)
    print(f"Loaded {len(entries)} entries", file=sys.stderr)

    # Group by target file
    groups = group_entries_by_file(entries)
    print(f"Grouped into {len(groups)} files", file=sys.stderr)

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Write each file
    for filename, file_entries in sorted(groups.items()):
        output_path = args.output_dir / filename
        write_xml_file(file_entries, output_path)
        print(f"Wrote {len(file_entries)} entries to {filename}", file=sys.stderr)

    print(f"Done! Generated {len(groups)} XML files", file=sys.stderr)


if __name__ == '__main__':
    main()
