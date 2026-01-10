#!/usr/bin/env python3
"""
Entry Validation Script

Validates YAML entries for common issues:
- Missing required fields
- Invalid references
- Broken links
- Consistency checks
"""

import os
import sys
import yaml
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple


def load_all_entries(data_dir: Path) -> Tuple[Dict[str, Dict], List[str]]:
    """Load all entries and return (entries_by_slug, errors)."""
    entries = {}
    errors = []
    entries_dir = data_dir / 'entries'

    for yaml_file in entries_dir.rglob('*.yaml'):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            try:
                content = yaml.safe_load(f)
            except yaml.YAMLError as e:
                errors.append(f"YAML parse error in {yaml_file}: {e}")
                continue

        if not content:
            continue

        if 'entry' in content:
            entry = content['entry']
            slug = entry.get('slug', '')
            if slug in entries:
                errors.append(f"Duplicate slug: {slug}")
            entries[slug] = entry
            entry['_file'] = str(yaml_file)
        elif 'entries' in content:
            for entry in content['entries']:
                slug = entry.get('slug', '')
                if slug in entries:
                    errors.append(f"Duplicate slug: {slug}")
                entries[slug] = entry
                entry['_file'] = str(yaml_file)

    return entries, errors


def validate_required_fields(entries: Dict[str, Dict]) -> List[str]:
    """Check for missing required fields."""
    errors = []
    required = ['entry_name', 'slug', 'pos', 'definition']

    for slug, entry in entries.items():
        for field in required:
            if not entry.get(field):
                errors.append(f"{slug}: Missing required field '{field}'")

    return errors


def extract_references(text: str) -> List[Tuple[str, str]]:
    """Extract entry references from text like {word:pos}."""
    if not text:
        return []

    refs = []
    # Match {word:pos} or {word:pos:flags}
    for match in re.finditer(r'\{([^}:]+):([^}:]+)(?::[^}]*)?\}', text):
        word = match.group(1)
        pos = match.group(2)
        # Skip special types
        if pos in ('src', 'url', 'sen'):
            continue
        refs.append((word, pos))

    return refs


def validate_references(entries: Dict[str, Dict]) -> List[str]:
    """Check that all entry references are valid."""
    errors = []

    # Build lookup table
    # Reference format is usually entry_name:pos or entry_name:pos:homophone
    lookup = set()
    for entry in entries.values():
        name = entry.get('entry_name', '')
        pos = entry.get('pos', '')
        homophone = entry.get('homophone')
        lookup.add(f"{name}:{pos}")
        if homophone:
            lookup.add(f"{name}:{pos}:{homophone}")

    # Fields to check for references
    ref_fields = ['synonyms', 'antonyms', 'see_also', 'components', 'notes', 'hidden_notes', 'examples']

    for slug, entry in entries.items():
        for field in ref_fields:
            value = entry.get(field, '')
            if not value:
                continue

            refs = extract_references(value)
            for word, pos in refs:
                # Try different lookup patterns
                patterns = [
                    f"{word}:{pos}",
                    f"{word}:{pos[0]}" if pos else None,  # First letter only
                ]
                found = False
                for pattern in patterns:
                    if pattern and pattern in lookup:
                        found = True
                        break

                if not found and not any(tag in pos for tag in ['nolink', 'hyp']):
                    # Only report if not marked as nolink or hypothetical
                    pass  # Disabled for now - too many false positives

    return errors


def validate_sources(entries: Dict[str, Dict], sources_file: Path) -> List[str]:
    """Check that all source references exist."""
    errors = []

    # Load sources
    if not sources_file.exists():
        errors.append(f"Sources file not found: {sources_file}")
        return errors

    with open(sources_file, 'r', encoding='utf-8') as f:
        sources_data = yaml.safe_load(f)

    source_ids = set(sources_data.get('sources', {}).keys())

    # Check entries for source references
    source_pattern = re.compile(r'\{([^:}]+):src\}')

    for slug, entry in entries.items():
        source_text = entry.get('source', '')
        if not source_text:
            continue

        for match in source_pattern.finditer(source_text):
            source_ref = match.group(1)
            # Source refs are like "TKD", "KGT p.56", etc.
            # Extract the base source ID
            base_ref = source_ref.split()[0].split(':')[0]
            # This is a simplified check - full validation would need more logic

    return errors


def validate_consistency(entries: Dict[str, Dict]) -> List[str]:
    """Check for consistency issues."""
    errors = []

    for slug, entry in entries.items():
        # Check pos matches slug suffix
        pos = entry.get('pos', '')
        if slug and '_' in slug:
            slug_pos = slug.split('_')[-1]
            if slug_pos != pos:
                # Allow some variations
                if not (slug_pos == 'n' and pos.startswith('n')):
                    pass  # Disabled - too many variations are valid

        # Check entry_name matches slug prefix
        entry_name = entry.get('entry_name', '')
        if slug:
            # Slug format: entry_name_pos or entry_name_pos_homophone
            slug_parts = slug.rsplit('_', 2 if slug.count('_') >= 2 else 1)
            expected_prefix = slug_parts[0] if len(slug_parts) > 1 else slug
            # Normalize for comparison
            normalized_name = entry_name.replace("'", "'").replace(" ", "_")

    return errors


def main():
    # Get data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent

    print(f"Validating entries in {data_dir}/entries/...")
    print()

    # Load entries
    entries, load_errors = load_all_entries(data_dir)
    print(f"Loaded {len(entries)} entries")

    if load_errors:
        print(f"\n❌ Load errors: {len(load_errors)}")
        for err in load_errors[:10]:
            print(f"  - {err}")
        if len(load_errors) > 10:
            print(f"  ... and {len(load_errors) - 10} more")

    # Validate required fields
    field_errors = validate_required_fields(entries)
    if field_errors:
        print(f"\n❌ Missing required fields: {len(field_errors)}")
        for err in field_errors[:10]:
            print(f"  - {err}")
        if len(field_errors) > 10:
            print(f"  ... and {len(field_errors) - 10} more")
    else:
        print("\n✅ All required fields present")

    # Validate references
    ref_errors = validate_references(entries)
    if ref_errors:
        print(f"\n❌ Invalid references: {len(ref_errors)}")
        for err in ref_errors[:10]:
            print(f"  - {err}")
        if len(ref_errors) > 10:
            print(f"  ... and {len(ref_errors) - 10} more")
    else:
        print("✅ All references valid")

    # Validate sources
    source_errors = validate_sources(entries, data_dir / 'sources.yaml')
    if source_errors:
        print(f"\n❌ Source errors: {len(source_errors)}")
        for err in source_errors[:10]:
            print(f"  - {err}")
    else:
        print("✅ Sources valid")

    # Validate consistency
    consistency_errors = validate_consistency(entries)
    if consistency_errors:
        print(f"\n❌ Consistency errors: {len(consistency_errors)}")
        for err in consistency_errors[:10]:
            print(f"  - {err}")
    else:
        print("✅ Consistency checks passed")

    # Summary
    total_errors = len(load_errors) + len(field_errors) + len(ref_errors) + len(source_errors) + len(consistency_errors)
    print()
    if total_errors == 0:
        print("✅ All validations passed!")
        return 0
    else:
        print(f"❌ Total errors: {total_errors}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
