#!/usr/bin/env python3
"""
YAML to JSON converter: Generate JSON output from YAML entry files.

This script reads YAML entry files and produces JSON output identical to
the original xml2json.py pipeline for backward compatibility.
"""

import os
import sys
import yaml
import json
import re
import unicodedata
from pathlib import Path
from collections import OrderedDict
from typing import Dict, List, Any


# ==============================================================================
# Constants - Must match xml2json.py exactly
# ==============================================================================

LANGUAGES = ['de', 'fa', 'sv', 'ru', 'zh_HK', 'pt', 'fi', 'fr']

LOCALES = OrderedDict([
    ('de', 'Deutsch'),
    ('en', 'English'),
    ('fa', 'فارسى'),
    ('ru', 'Русский язык'),
    ('sv', 'Svenska'),
    ('zh_HK', '中文 (香港)'),
    ('pt', 'Português'),
    ('fi', 'Suomi'),
    ('fr', 'Français'),
])

SUPPORTED_LOCALES = ['de', 'en', 'sv']


# ==============================================================================
# YAML Loading
# ==============================================================================

def load_all_entries(data_dir: Path, show_progress: bool = True) -> List[Dict]:
    """Load all entries from YAML files."""
    entries = []
    entries_dir = data_dir / 'entries'

    # Collect all YAML files first for progress reporting
    yaml_files = list(entries_dir.rglob('*.yaml'))
    total_files = len(yaml_files)

    # Walk through all YAML files
    for i, yaml_file in enumerate(yaml_files):
        if show_progress and (i + 1) % 500 == 0:
            print(f"  Loading file {i + 1}/{total_files}...", file=sys.stderr)

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
    if show_progress:
        print(f"  Sorting {len(entries)} entries...", file=sys.stderr)
    entries.sort(key=lambda e: e.get('_original_id', 0))

    return entries


# ==============================================================================
# Search Name Normalization
# ==============================================================================

def normalize_search_name(entry_name: str, part_of_speech: str) -> str:
    """Normalize entry name and POS into search name."""
    # Split part of speech into separate fields
    pos_split = part_of_speech.split(':')
    pos = pos_split[0]

    # If there is a second field, it contains comma-separated tags
    if len(pos_split) > 1:
        flags = pos_split[1]
    else:
        flags = ''

    homophone = ''
    # Look for a homophone number in the flags. Ignore an 'h' which is used
    # to indicate a hidden homophone number.
    for flag in flags.split(','):
        flag = flag.rstrip('h')
        if flag.isdigit():
            homophone = ':' + flag
            break

    return entry_name + ':' + pos + homophone


# ==============================================================================
# Entry Conversion
# ==============================================================================

def entry_to_json_dict(entry: Dict) -> Dict[str, Any]:
    """Convert YAML entry to JSON format.

    Fields are output in the same order as they appear in the XML,
    which is the order the original xml2json.py produces.
    """
    result = OrderedDict()
    translations = entry.get('translations', {})

    # Core fields (note: _id is omitted from JSON output)
    result['entry_name'] = entry.get('entry_name', '')
    result['part_of_speech'] = entry.get('part_of_speech', '')

    # Definition - localized field
    # Definition can be a string or a dict with 'text' field
    definition = OrderedDict()
    entry_def = entry.get('definition', '')
    if isinstance(entry_def, dict):
        entry_def_text = entry_def.get('text', '')
    else:
        entry_def_text = entry_def
    if entry_def_text:
        definition['en'] = unicodedata.normalize('NFKD', entry_def_text)
    for lang in LANGUAGES:
        trans = translations.get(lang, {})
        if trans.get('definition'):
            definition[lang] = unicodedata.normalize('NFKD', trans['definition'])
    if definition:
        result['definition'] = definition

    # Simple fields in XML column order: synonyms, antonyms, see_also
    for field in ['synonyms', 'antonyms', 'see_also']:
        if entry.get(field):
            result[field] = unicodedata.normalize('NFKD', entry[field])

    # Notes - localized field (comes after see_also in XML)
    notes = OrderedDict()
    if entry.get('notes'):
        notes['en'] = unicodedata.normalize('NFKD', entry['notes'])
    for lang in LANGUAGES:
        trans = translations.get(lang, {})
        if trans.get('notes'):
            notes[lang] = unicodedata.normalize('NFKD', trans['notes'])
    if notes:
        result['notes'] = notes

    # hidden_notes (comes after notes in XML)
    if entry.get('hidden_notes'):
        result['hidden_notes'] = unicodedata.normalize('NFKD', entry['hidden_notes'])

    # components (comes after hidden_notes in XML)
    if entry.get('components'):
        result['components'] = unicodedata.normalize('NFKD', entry['components'])

    # Examples - localized field (comes after components in XML)
    examples = OrderedDict()
    if entry.get('examples'):
        examples['en'] = unicodedata.normalize('NFKD', entry['examples'])
    for lang in LANGUAGES:
        trans = translations.get(lang, {})
        if trans.get('examples'):
            examples[lang] = unicodedata.normalize('NFKD', trans['examples'])
    if examples:
        result['examples'] = examples

    # Search tags - localized field (comes after examples in XML)
    search_tags = OrderedDict()
    if entry.get('search_tags'):
        tags_str = unicodedata.normalize('NFKD', entry['search_tags'])
        search_tags['en'] = re.split(', *', tags_str)
    for lang in LANGUAGES:
        trans = translations.get(lang, {})
        if trans.get('search_tags'):
            tags_str = unicodedata.normalize('NFKD', trans['search_tags'])
            search_tags[lang] = re.split(', *', tags_str)
    if search_tags:
        result['search_tags'] = search_tags

    # source (last column in XML)
    # Sources can be a string or a dict with 'raw' field
    sources = entry.get('sources', entry.get('source', ''))
    if isinstance(sources, dict):
        source_raw = sources.get('raw', '')
    else:
        source_raw = sources
    if source_raw:
        result['source'] = unicodedata.normalize('NFKD', source_raw)

    return result


# ==============================================================================
# Link Validation
# ==============================================================================

def validate_links(root: Dict, node: Any) -> None:
    """Validate links in the database."""
    if isinstance(node, dict):
        for subnode in node:
            validate_links(root, node[subnode])
    elif isinstance(node, list):
        for item in node:
            validate_links(root, item)
    else:
        # Find all text in {curly braces}
        remaining = str(node)
        while remaining.find('{') != -1:
            remaining = remaining[remaining.find('{')+1:]
            tag = remaining[0:remaining.find('}')]

            # For {sentences with components@@sentences, with, components},
            # check the individual components.
            if tag.find('@@') != -1:
                for term in tag.split('@@')[1].split(','):
                    validate_links(root, '{' + term.strip(' ') + '}')
                continue

            tagsplit = tag.split(':')

            if len(tagsplit) > 1:
                # The second field identifies the text type: don't bother
                # validating url links or src attributions.
                if tagsplit[1] == 'url' or tagsplit[1] == 'src':
                    continue
                # Check the flags in the third field and ignore text tagged
                # with the "nolink" flag.
                if len(tagsplit) > 2 and 'nolink' in tagsplit[2].split(','):
                    continue

                # Normalize the search name and check if an entry exists
                normalized = normalize_search_name(tagsplit[0], ':'.join(tagsplit[1:]))
                if normalized not in root:
                    hom = ''

                    # Check if the failure to resolve was due to an ambiguous
                    # homophone
                    if normalized + ':1' in root:
                        hom = ' (homophone exists)'
                    # A homophone number of 0 explicitly indicates that the
                    # link is supposed to lead to all homophones
                    elif normalized[-2:] == ':0':
                        if normalized[:-2] + ':1' in root:
                            continue

                    sys.stderr.write('no entry for {' + tag + '}' + hom + '.\n')


# ==============================================================================
# Main
# ==============================================================================

def main():
    # Get data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent

    print(f"Loading entries from {data_dir}/entries/...", file=sys.stderr)

    # Load all entries
    entries = load_all_entries(data_dir)
    print(f"Loaded {len(entries)} entries", file=sys.stderr)

    # Read version
    version_file = data_dir / 'VERSION'
    if version_file.exists():
        version = version_file.read_text().strip()
    else:
        version = '0'

    # NOTE: [[VERSION]] substitution is NOT done here to match xml2json.py behavior.
    # The version substitution happens later in the build process (generate_db.sh).
    # The version variable is kept for the top-level 'version' field only.

    # Build qawHaq dictionary
    print("Building dictionary...", file=sys.stderr)
    qawHaq = OrderedDict()
    overwritten = 0
    total_entries = len(entries)

    for i, entry in enumerate(entries):
        if (i + 1) % 1000 == 0:
            print(f"  Processing entry {i + 1}/{total_entries}...", file=sys.stderr)

        entry_name = entry.get('entry_name', '')
        part_of_speech = entry.get('part_of_speech', '')
        search_name = normalize_search_name(entry_name, part_of_speech)

        if search_name in qawHaq:
            sys.stderr.write(search_name + ' overwrites an existing entry\n')
            overwritten += 1

        # Every entry should have a definition
        if entry.get('definition'):
            qawHaq[search_name] = entry_to_json_dict(entry)
        else:
            sys.stderr.write('no definition for entry ' + search_name + '\n')

    # Validate links
    print("Validating links...", file=sys.stderr)
    validate_links(qawHaq, qawHaq)

    # Build output structure
    print("Building output...", file=sys.stderr)
    ret = OrderedDict()
    ret['format_version'] = '1'
    ret['version'] = version
    ret['locales'] = LOCALES
    ret['supported_locales'] = SUPPORTED_LOCALES
    ret['qawHaq'] = qawHaq

    # Dump as JSON
    print(json.dumps(ret))

    print(f"Generated JSON for {len(entries)} entries", file=sys.stderr)

    if overwritten:
        sys.stderr.write('\n*** yIqImqu\' jay\'! ***\n\n')
        sys.stderr.write(str(overwritten) + ' entries overwritten by duplicates!\n')
        sys.exit(1)


if __name__ == '__main__':
    main()
