#!/usr/bin/env python3
"""
YAML to SQL converter: Generate SQLite database from YAML entry files.

This script reads YAML entry files and produces SQL output identical to
the original xml2sql.pl pipeline for backward compatibility.
"""

import os
import sys
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


# ==============================================================================
# Constants - Must match xml2sql.pl exactly
# ==============================================================================

# Column order from xml2sql.pl lines 74-119
COLUMN_ORDER = [
    '_id', 'entry_name', 'part_of_speech', 'definition',
    'synonyms', 'antonyms', 'see_also', 'notes', 'hidden_notes',
    'components', 'examples', 'search_tags', 'source',
    'definition_de', 'notes_de', 'examples_de', 'search_tags_de',
    'definition_fa', 'notes_fa', 'examples_fa', 'search_tags_fa',
    'definition_sv', 'notes_sv', 'examples_sv', 'search_tags_sv',
    'definition_ru', 'notes_ru', 'examples_ru', 'search_tags_ru',
    'definition_zh_HK', 'notes_zh_HK', 'examples_zh_HK', 'search_tags_zh_HK',
    'definition_pt', 'notes_pt', 'examples_pt', 'search_tags_pt',
    'definition_fi', 'notes_fi', 'examples_fi', 'search_tags_fi',
    'definition_fr', 'notes_fr', 'examples_fr', 'search_tags_fr',
]

LANGUAGES = ['de', 'fa', 'sv', 'ru', 'zh_HK', 'pt', 'fi', 'fr']


# ==============================================================================
# YAML Loading
# ==============================================================================

def load_all_entries(data_dir: Path) -> List[Dict]:
    """Load all entries from YAML files."""
    entries = []
    entries_dir = data_dir / 'entries'

    # Walk through all YAML files
    for yaml_file in entries_dir.rglob('*.yaml'):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            try:
                content = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"Error loading {yaml_file}: {e}", file=sys.stderr)
                continue

        if not content:
            continue

        # Handle single entry or multiple entries
        if 'entry' in content:
            entries.append(content['entry'])
        elif 'entries' in content:
            entries.extend(content['entries'])

    # Sort by _original_id
    entries.sort(key=lambda e: e.get('_original_id', 0))

    return entries


# ==============================================================================
# Reconstruction Functions
# ==============================================================================

def reconstruct_part_of_speech(entry: Dict) -> str:
    """Reconstruct part_of_speech string from structured fields."""
    pos = entry.get('pos', '')
    if not pos:
        return ''

    modifiers = []

    # Add homophone number
    if entry.get('homophone'):
        modifiers.append(str(entry['homophone']))

    # Add subtype
    if entry.get('pos_subtype'):
        modifiers.append(entry['pos_subtype'])

    # Add categories
    for cat in entry.get('categories', []):
        modifiers.append(cat)

    # Add metadata tags
    for tag in entry.get('metadata_tags', []):
        modifiers.append(tag)

    if modifiers:
        return f"{pos}:{','.join(modifiers)}"
    return pos


def escape_sql(value: str) -> str:
    """Escape single quotes for SQL."""
    if value is None:
        return ''
    return str(value).replace("'", "''")


def entry_to_columns(entry: Dict) -> Dict[str, str]:
    """Convert entry to column values dictionary."""
    columns = {}

    # Core fields
    columns['_id'] = entry.get('_original_id', '')
    columns['entry_name'] = entry.get('entry_name', '')
    # Use original part_of_speech string if available, otherwise reconstruct
    columns['part_of_speech'] = entry.get('part_of_speech', '') or reconstruct_part_of_speech(entry)
    # Definition can be a string or a dict with 'text' field
    definition = entry.get('definition', '')
    if isinstance(definition, dict):
        columns['definition'] = definition.get('text', '')
    else:
        columns['definition'] = definition
    columns['synonyms'] = entry.get('synonyms', '')
    columns['antonyms'] = entry.get('antonyms', '')
    columns['see_also'] = entry.get('see_also', '')
    columns['notes'] = entry.get('notes', '')
    columns['hidden_notes'] = entry.get('hidden_notes', '')
    columns['components'] = entry.get('components', '')
    columns['examples'] = entry.get('examples', '')
    columns['search_tags'] = entry.get('search_tags', '')
    # Source can be a string or a dict with 'raw' field
    sources = entry.get('sources', entry.get('source', ''))
    if isinstance(sources, dict):
        columns['source'] = sources.get('raw', '')
    else:
        columns['source'] = sources

    # Translation fields
    translations = entry.get('translations', {})
    for lang in LANGUAGES:
        trans = translations.get(lang, {})
        columns[f'definition_{lang}'] = trans.get('definition', '')
        columns[f'notes_{lang}'] = trans.get('notes', '')
        columns[f'examples_{lang}'] = trans.get('examples', '')
        columns[f'search_tags_{lang}'] = trans.get('search_tags', '')

    return columns


# ==============================================================================
# SQL Generation
# ==============================================================================

def generate_sql_header() -> str:
    """Generate SQL file header."""
    return (
        "PRAGMA foreign_keys=OFF;\n"
        "BEGIN TRANSACTION;\n"
        "CREATE TABLE IF NOT EXISTS \"android_metadata\" (\"locale\" TEXT DEFAULT 'en_US');\n"
        "INSERT INTO android_metadata VALUES('en_US');\n"
        "CREATE TABLE IF NOT EXISTS \"mem\" ("
        "\"_id\" INTEGER PRIMARY KEY,"
        "\"entry_name\" TEXT,"
        "\"part_of_speech\" TEXT,"
        "\"definition\" TEXT,"
        "\"synonyms\" TEXT,"
        "\"antonyms\" TEXT,"
        "\"see_also\" TEXT,"
        "\"notes\" TEXT,"
        "\"hidden_notes\" TEXT,"
        "\"components\" TEXT,"
        "\"examples\" TEXT,"
        "\"search_tags\" TEXT,"
        "\"source\" TEXT,"
        "\"definition_de\" TEXT,"
        "\"notes_de\" TEXT,"
        "\"examples_de\" TEXT,"
        "\"search_tags_de\" TEXT,"
        "\"definition_fa\" TEXT,"
        "\"notes_fa\" TEXT,"
        "\"examples_fa\" TEXT,"
        "\"search_tags_fa\" TEXT,"
        "\"definition_sv\" TEXT,"
        "\"notes_sv\" TEXT,"
        "\"examples_sv\" TEXT,"
        "\"search_tags_sv\" TEXT,"
        "\"definition_ru\" TEXT,"
        "\"notes_ru\" TEXT,"
        "\"examples_ru\" TEXT,"
        "\"search_tags_ru\" TEXT,"
        "\"definition_zh_HK\" TEXT,"
        "\"notes_zh_HK\" TEXT,"
        "\"examples_zh_HK\" TEXT,"
        "\"search_tags_zh_HK\" TEXT,"
        "\"definition_pt\" TEXT,"
        "\"notes_pt\" TEXT,"
        "\"examples_pt\" TEXT,"
        "\"search_tags_pt\" TEXT,"
        "\"definition_fi\" TEXT,"
        "\"notes_fi\" TEXT,"
        "\"examples_fi\" TEXT,"
        "\"search_tags_fi\" TEXT,"
        "\"definition_fr\" TEXT,"
        "\"notes_fr\" TEXT,"
        "\"examples_fr\" TEXT,"
        "\"search_tags_fr\" TEXT"
        ");\n"
    )


def generate_sql_row(entry: Dict) -> str:
    """Generate INSERT statement for an entry."""
    columns = entry_to_columns(entry)

    values = []
    for col in COLUMN_ORDER:
        if col == '_id':
            # _id is an integer, convert to string for joining
            values.append(str(columns[col]) if columns[col] else 'NULL')
        else:
            values.append(f"'{escape_sql(columns.get(col, ''))}'")

    # Match original format: quotes around table name
    return f"INSERT INTO \"mem\" VALUES({','.join(values)});\n"


def generate_sql_footer() -> str:
    """Generate SQL file footer."""
    return "COMMIT;\n"


# ==============================================================================
# Main
# ==============================================================================

def substitute_version(text: str, version: str) -> str:
    """Replace [[VERSION]] placeholder with actual version."""
    if text and '[[VERSION]]' in text:
        return text.replace('[[VERSION]]', version)
    return text


def main():
    # Get data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent

    print(f"Loading entries from {data_dir}/entries/...", file=sys.stderr)

    # Read version
    version_file = data_dir / 'VERSION'
    if version_file.exists():
        version = version_file.read_text().strip()
    else:
        version = '0'

    # Load all entries
    entries = load_all_entries(data_dir)
    print(f"Loaded {len(entries)} entries", file=sys.stderr)

    # NOTE: [[VERSION]] substitution is NOT done here to match xml2sql.pl behavior.
    # The version substitution happens later in the build process (write_db.sh).
    # The version variable is kept for potential future use.

    # Generate SQL
    print(generate_sql_header(), end='')

    for entry in entries:
        print(generate_sql_row(entry), end='')

    print(generate_sql_footer(), end='')

    print(f"Generated SQL for {len(entries)} entries", file=sys.stderr)


if __name__ == '__main__':
    main()
