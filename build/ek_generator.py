#!/usr/bin/env python3
"""
E-K (English-to-Klingon) Index Generator

Generates E-K lookup entries from YAML entry files using the ek_parts structure.
Each part becomes a lookup key that maps to the full Klingon entry.

Output formats:
- JSON: For use in apps
- Markdown: For print dictionary
"""

import os
import sys
import yaml
import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class EKEntry:
    """An English-to-Klingon lookup entry."""
    sort_key: str      # Lowercase sort key (e.g., "flap", "hostile")
    display: str       # Display text (e.g., "flap, flutter, wave")
    klingon: str       # Klingon word
    pos: str           # Part of speech
    pos_subtype: str   # POS subtype (for be-verb detection)
    slug: str          # Entry slug for reference


def get_sort_key(text: str, is_be_verb: bool = False) -> str:
    """Extract sort key from definition text."""
    text = text.strip()

    # Strip parentheticals for sort key
    text_no_parens = re.sub(r'\s*\([^)]*\)\s*', ' ', text).strip()

    # For be-verbs, strip "be " prefix
    if is_be_verb and text_no_parens.lower().startswith('be '):
        text_no_parens = text_no_parens[3:]

    # Get first word
    words = text_no_parens.split()
    if words:
        # Remove common articles and prepositions for sorting
        while words and words[0].lower() in ('a', 'an', 'the', 'to'):
            words = words[1:]
        if words:
            return words[0].lower()

    return text.lower()


def load_entries(data_dir: Path) -> List[Dict]:
    """Load all entries from YAML files."""
    entries = []
    entries_dir = data_dir / 'entries'

    for yaml_file in entries_dir.rglob('*.yaml'):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            try:
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

    return entries


def generate_ek_entries(entries: List[Dict]) -> List[EKEntry]:
    """Generate E-K entries from all YAML entries.

    Respects the following flags in definition structure:
    - no_permute: Don't generate permutations (guard cases)
    - dedup: Only generate one entry for similar parts (e.g., actor/actress)
    """
    ek_entries = []

    for entry in entries:
        definition = entry.get('definition', '')

        # Definition can be a string or a dict with 'text' and 'parts'
        if isinstance(definition, dict):
            definition_text = definition.get('text', '')
            ek_parts = definition.get('parts')
            global_paren = definition.get('global_parenthetical')
            no_permute = definition.get('no_permute', False)
            dedup = definition.get('dedup', False)
        else:
            definition_text = definition
            ek_parts = None
            global_paren = None
            no_permute = False
            dedup = False

        if not definition_text or definition_text.startswith('{'):
            # Skip empty definitions and pure references
            continue

        entry_name = entry.get('entry_name', '')
        pos = entry.get('pos', '')
        pos_subtype = entry.get('pos_subtype', '')
        slug = entry.get('slug', '')
        is_be_verb = pos_subtype == 'is'

        # Guard case: no_permute flag means treat as single entry
        if no_permute:
            sort_key = get_sort_key(definition_text, is_be_verb)
            ek_entries.append(EKEntry(
                sort_key=sort_key,
                display=definition_text,
                klingon=entry_name,
                pos=pos,
                pos_subtype=pos_subtype,
                slug=slug
            ))
            continue

        if ek_parts and len(ek_parts) > 1:
            # Multiple parts - generate permutations (unless dedup)
            seen_keys = set()

            for i, part_data in enumerate(ek_parts):
                part_text = part_data.get('text', '')
                sort_keyword = part_data.get('sort_keyword')

                if sort_keyword:
                    sort_key = sort_keyword.lower()
                else:
                    sort_key = get_sort_key(part_text, is_be_verb)

                if sort_key in seen_keys:
                    continue
                seen_keys.add(sort_key)

                # Build permuted display
                if is_be_verb:
                    # For be-verbs: "X, be X, be Y, be Z" format
                    # First the adjective (without "be"), then the full "be X", then other full forms
                    def strip_be(text):
                        t = text.strip()
                        if t.lower().startswith('be '):
                            return t[3:]
                        return t

                    adjective = strip_be(part_text)
                    other_parts = [p.get('text', '') for j, p in enumerate(ek_parts) if j != i]
                    display_parts = [adjective, part_text] + other_parts
                    display = ', '.join(display_parts)
                else:
                    # Standard format: current part first, then others
                    other_parts = [p.get('text', '') for j, p in enumerate(ek_parts) if j != i]
                    display_parts = [part_text] + other_parts
                    display = ', '.join(display_parts)

                if global_paren:
                    display += f' ({global_paren})'

                ek_entries.append(EKEntry(
                    sort_key=sort_key,
                    display=display,
                    klingon=entry_name,
                    pos=pos,
                    pos_subtype=pos_subtype,
                    slug=slug
                ))

                # Dedup: only generate one entry for similar parts
                if dedup:
                    break
        else:
            # Single part - one entry
            sort_key = get_sort_key(definition_text, is_be_verb)
            ek_entries.append(EKEntry(
                sort_key=sort_key,
                display=definition_text,
                klingon=entry_name,
                pos=pos,
                pos_subtype=pos_subtype,
                slug=slug
            ))

    return ek_entries


def group_by_sort_key(ek_entries: List[EKEntry]) -> Dict[str, List[EKEntry]]:
    """Group E-K entries by sort key."""
    groups = defaultdict(list)
    for entry in ek_entries:
        groups[entry.sort_key].append(entry)
    return dict(groups)


def generate_json_output(ek_entries: List[EKEntry]) -> Dict:
    """Generate JSON output for app use."""
    # Group by sort key for efficient lookup
    groups = group_by_sort_key(ek_entries)

    output = {
        'format_version': '1',
        'entry_count': len(ek_entries),
        'entries': {}
    }

    for key in sorted(groups.keys()):
        entries = groups[key]
        output['entries'][key] = [
            {
                'display': e.display,
                'klingon': e.klingon,
                'pos': e.pos,
                'slug': e.slug
            }
            for e in entries
        ]

    return output


def generate_markdown_output(ek_entries: List[EKEntry]) -> str:
    """Generate Markdown output for print dictionary."""
    lines = []
    lines.append("# English-Klingon Dictionary")
    lines.append("")
    lines.append("_Generated from boQwI' database_")
    lines.append("")

    # Group by first letter
    by_letter = defaultdict(list)
    for entry in ek_entries:
        letter = entry.sort_key[0].upper() if entry.sort_key else '?'
        by_letter[letter].append(entry)

    for letter in sorted(by_letter.keys()):
        lines.append(f"## {letter}")
        lines.append("")

        # Sort entries within letter
        entries = sorted(by_letter[letter], key=lambda e: e.sort_key)

        for entry in entries:
            # Format: _display_ — **klingon** (pos)
            # Following TKD convention: English italicized, Klingon bold
            pos_display = entry.pos
            if entry.pos_subtype:
                pos_display += f":{entry.pos_subtype}"
            lines.append(f"_{entry.display}_ — **{entry.klingon}** ({pos_display})")

        lines.append("")

    return '\n'.join(lines)


def main():
    # Get data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent

    print(f"Loading entries from {data_dir}/entries/...", file=sys.stderr)

    # Load entries
    entries = load_entries(data_dir)
    print(f"Loaded {len(entries)} entries", file=sys.stderr)

    # Generate E-K entries
    ek_entries = generate_ek_entries(entries)
    print(f"Generated {len(ek_entries)} E-K lookup entries", file=sys.stderr)

    # Count entries with various flags
    def get_def_field(e, field, default=None):
        defn = e.get('definition', {})
        if isinstance(defn, dict):
            return defn.get(field, default)
        return default

    multi_part = sum(1 for e in entries if isinstance(e.get('definition'), dict)
                     and e.get('definition', {}).get('parts')
                     and len(e.get('definition', {}).get('parts', [])) > 1)
    no_permute = sum(1 for e in entries if get_def_field(e, 'no_permute', False))
    dedup_count = sum(1 for e in entries if get_def_field(e, 'dedup', False))
    print(f"Entries with multiple parts: {multi_part}", file=sys.stderr)
    print(f"Guard cases (no_permute): {no_permute}", file=sys.stderr)
    print(f"Dedup cases: {dedup_count}", file=sys.stderr)

    # Generate outputs
    json_output = generate_json_output(ek_entries)
    md_output = generate_markdown_output(ek_entries)

    # Write JSON
    json_file = data_dir / 'build' / 'ek_index.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, ensure_ascii=False, indent=2)
    print(f"Wrote {json_file}", file=sys.stderr)

    # Write Markdown
    md_file = data_dir / 'build' / 'ek_dictionary.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_output)
    print(f"Wrote {md_file}", file=sys.stderr)

    # Print statistics
    groups = group_by_sort_key(ek_entries)
    print(f"\nStatistics:", file=sys.stderr)
    print(f"  Unique sort keys: {len(groups)}", file=sys.stderr)
    print(f"  Average entries per key: {len(ek_entries) / len(groups):.2f}", file=sys.stderr)

    # Show sample
    print(f"\nSample E-K entries:", file=sys.stderr)
    for entry in sorted(ek_entries, key=lambda e: e.sort_key)[:10]:
        print(f"  {entry.sort_key}: {entry.display} → {entry.klingon}", file=sys.stderr)


if __name__ == '__main__':
    main()
