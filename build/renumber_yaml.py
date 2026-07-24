#!/usr/bin/env python3
"""Maintain entries/_index.yaml.

Analogue of ``renumber.py`` for the YAML pipeline. The index is an
ordered list of ``{slug, file}`` items; position N (0-indexed) fixes the
SQL ``_id`` as ``BASE_ID + N`` and controls XML row order.

Running this script:

* Preserves the position of every slug already in the index (no churn).
* Inserts new slugs (present on disk but not in the index) at the sorted
  position within their target XML file, using the same sort key as
  ``migrate_xml.py``: non-derived first, then by homophone number, then
  Klingon-alphabetical entry name.
* Removes slugs that are no longer on disk (with a warning per slug).

Run this whenever entry YAML files are added, removed, renamed, or their
``section``/homophone changes such that they move between XML files. The
only file that ever changes is ``entries/_index.yaml`` — per-entry YAMLs
stay stable across renumbering.
"""

import argparse
import sys
from bisect import insort
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml

from index_loader import load_index, write_index

# Same file order renumber.py walks (mem-27-extra and mem-28-examples last).
FILE_ORDER = [
    'mem-01-b.xml', 'mem-02-ch.xml', 'mem-03-D.xml', 'mem-04-gh.xml',
    'mem-05-H.xml', 'mem-06-j.xml', 'mem-07-l.xml', 'mem-08-m.xml',
    'mem-09-n.xml', 'mem-10-ng.xml', 'mem-11-p.xml', 'mem-12-q.xml',
    'mem-13-Q.xml', 'mem-14-r.xml', 'mem-15-S.xml', 'mem-16-t.xml',
    'mem-17-tlh.xml', 'mem-18-v.xml', 'mem-19-w.xml', 'mem-20-y.xml',
    'mem-21-a.xml', 'mem-22-e.xml', 'mem-23-I.xml', 'mem-24-o.xml',
    'mem-25-u.xml', 'mem-26-suffixes.xml', 'mem-27-extra.xml',
    'mem-28-examples.xml',
]
FILE_INDEX = {name: i for i, name in enumerate(FILE_ORDER)}

SUFFIXES_FILE = 'mem-26-suffixes.xml'
SECTION_TO_FILE = {'extra': 'mem-27-extra.xml', 'examples': 'mem-28-examples.xml'}
LETTER_TO_FILE = {
    'b': 'mem-01-b.xml', 'ch': 'mem-02-ch.xml', 'D': 'mem-03-D.xml',
    'gh': 'mem-04-gh.xml', 'H': 'mem-05-H.xml', 'j': 'mem-06-j.xml',
    'l': 'mem-07-l.xml', 'm': 'mem-08-m.xml', 'n': 'mem-09-n.xml',
    'ng': 'mem-10-ng.xml', 'p': 'mem-11-p.xml', 'q': 'mem-12-q.xml',
    'Q': 'mem-13-Q.xml', 'r': 'mem-14-r.xml', 'S': 'mem-15-S.xml',
    't': 'mem-16-t.xml', 'tlh': 'mem-17-tlh.xml', 'v': 'mem-18-v.xml',
    'w': 'mem-19-w.xml', 'y': 'mem-20-y.xml', 'a': 'mem-21-a.xml',
    'e': 'mem-22-e.xml', 'I': 'mem-23-I.xml', 'o': 'mem-24-o.xml',
    'u': 'mem-25-u.xml',
}


def infer_file(entry: Dict) -> str:
    """Compute the XML file an entry belongs to (matches yaml2xml.py)."""
    section = entry.get('section', 'main')
    if section in SECTION_TO_FILE:
        return SECTION_TO_FILE[section]

    # mem-26-suffixes.xml holds suffixes only; verb prefixes historically
    # live in their letter file (e.g. bI- in mem-01-b.xml).
    subtype = entry.get('pos_subtype', '')
    entry_name = entry.get('entry_name', '')
    if subtype == 'suff' or entry_name.startswith('-'):
        return SUFFIXES_FILE

    name = entry_name.lstrip('-')
    if name.startswith('tlh'): letter = 'tlh'
    elif name.startswith('ch'): letter = 'ch'
    elif name.startswith('gh'): letter = 'gh'
    elif name.startswith('ng'): letter = 'ng'
    elif name.startswith("'") and len(name) > 1 and name[1] in 'aeIou':
        letter = name[1]
    elif name and name[0] in LETTER_TO_FILE:
        letter = name[0]
    else:
        letter = name[0] if name else ''
    return LETTER_TO_FILE.get(letter, 'mem-21-a.xml')


def sort_key_within_file(entry: Dict) -> Tuple[int, int, str]:
    """Sort key for a new entry within its XML file.

    Matches migrate_xml.py:597-603: non-derived first, then by homophone
    number, then Klingon-alphabetical by entry name.
    """
    tags = entry.get('metadata_tags', []) or []
    return (
        1 if 'deriv' in tags else 0,
        entry.get('homophone') or 0,
        entry.get('entry_name', ''),
    )


def load_entries_on_disk(data_dir: Path) -> Dict[str, Dict]:
    """Return {slug: entry_dict} for every entry YAML on disk."""
    result = {}
    for yaml_file in (data_dir / 'entries').rglob('*.yaml'):
        if yaml_file.name == '_index.yaml':
            continue
        with open(yaml_file, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        if not content:
            continue
        items = []
        if 'entry' in content:
            items.append(content['entry'])
        if 'entries' in content:
            items.extend(content['entries'])
        for entry in items:
            slug = entry.get('slug')
            if not slug:
                print(f'WARN: entry missing slug in {yaml_file}', file=sys.stderr)
                continue
            if slug in result:
                print(f'WARN: duplicate slug {slug!r}', file=sys.stderr)
            result[slug] = entry
    return result


def insert_new_slug(
    index: List[Dict[str, str]],
    entries: Dict[str, Dict],
    slug: str,
    target_file: str,
) -> None:
    """Insert ``slug`` into ``index`` at the sorted position within its file."""
    new_key = sort_key_within_file(entries[slug])

    # Range of index positions belonging to target_file.
    file_positions = [i for i, item in enumerate(index) if item['file'] == target_file]

    if not file_positions:
        # No entries in that file yet — place at end of the file's slot.
        # Insert immediately before the first index entry belonging to a
        # later XML file, or at the end if none.
        target_order = FILE_INDEX.get(target_file, len(FILE_ORDER))
        insert_at = len(index)
        for i, item in enumerate(index):
            if FILE_INDEX.get(item['file'], len(FILE_ORDER)) > target_order:
                insert_at = i
                break
        index.insert(insert_at, {'slug': slug, 'file': target_file})
        return

    # Walk existing file entries; insert before the first one whose sort key
    # is greater than the new entry's.
    insert_at = file_positions[-1] + 1
    for pos in file_positions:
        existing_slug = index[pos]['slug']
        existing = entries.get(existing_slug)
        if existing is None:
            continue
        if sort_key_within_file(existing) > new_key:
            insert_at = pos
            break
    index.insert(insert_at, {'slug': slug, 'file': target_file})


def renumber(data_dir: Path, check: bool = False) -> int:
    """Regenerate entries/_index.yaml. Returns 0 on success, 1 on drift."""
    entries = load_entries_on_disk(data_dir)
    disk_slugs = set(entries)

    index = list(load_index(data_dir))
    indexed_slugs = {item['slug'] for item in index}

    stale = [i for i, item in enumerate(index) if item['slug'] not in disk_slugs]
    added = disk_slugs - indexed_slugs

    if not stale and not added:
        print(f'index is up to date ({len(index)} entries)')
        return 0

    if check:
        for i in stale:
            print(f'DRIFT: index has {index[i]["slug"]!r} but no YAML exists', file=sys.stderr)
        for slug in sorted(added):
            print(f'DRIFT: YAML has {slug!r} but index does not', file=sys.stderr)
        return 1

    for i in reversed(stale):
        print(f'removing stale: {index[i]["slug"]}')
        del index[i]

    # Existing file assignments are preserved (the `file:` column acts as an
    # override for entries whose historical placement does not match the
    # letter/section heuristic). If you need to re-home an entry, edit
    # entries/_index.yaml directly.

    for slug in sorted(added, key=lambda s: (FILE_INDEX.get(infer_file(entries[s]), 99),) + sort_key_within_file(entries[s])):
        target_file = infer_file(entries[slug])
        print(f'inserting {slug} into {target_file}')
        insert_new_slug(index, entries, slug, target_file)

    write_index(data_dir, index)
    print(f'wrote {len(index)} entries to entries/_index.yaml')
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true',
                   help='exit 1 if the index is out of sync; do not write')
    p.add_argument('--data-dir', type=Path,
                   default=Path(__file__).resolve().parent.parent,
                   help='project root containing entries/')
    args = p.parse_args()
    sys.exit(renumber(args.data_dir, check=args.check))


if __name__ == '__main__':
    main()
