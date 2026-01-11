# Migration Status

**Last Updated:** 2026-01-11

This document tracks the progress of migrating the Klingon lexicon database from XML to YAML format, as specified in SPEC.md.

## Current Status: Phase 5 In Progress

The YAML pipeline is now functional and produces **byte-identical output** to the XML pipeline for both SQLite (qawHaq.db) and JSON (qawHaq.json) formats. E-K dictionary generation is now implemented.

## Completed Work

### Phase 1: Source Registry ✓
- Created `sources.yaml` with source metadata
- Source parsing integrated into migration script
- Sources are stored in structured format within entry YAML files

### Phase 2: Entry File Structure ✓
- **6,142 YAML files** containing **6,407 entries** migrated from XML
- Directory structure: `entries/{pos_type}/{first_letter}/{entry}.yaml`
- Suffixes stored separately: `entries/suffixes/{verb|noun}/`
- Migration script: `build/migrate_xml.py`
- YAML parsers: `build/yaml2sql.py`, `build/yaml2json.py`
- Build script: `generate_db_yaml.sh`

### Shared Notes
- **18 shared note files** extracted to `notes/` directory
- Notes that appear in 3+ entries are stored as reusable references

## File Structure

```
data/
├── entries/              # 6,142 YAML entry files
│   ├── verbs/
│   ├── nouns/
│   ├── adverbials/
│   ├── conjunctions/
│   ├── questions/
│   ├── sentences/
│   ├── exclamations/
│   └── suffixes/
│       ├── verb/
│       └── noun/
├── notes/                # 18 shared note files
├── sources.yaml          # Source registry
├── build/
│   ├── migrate_xml.py    # XML to YAML migration
│   ├── yaml2sql.py       # YAML to SQL generation
│   ├── yaml2json.py      # YAML to JSON generation
│   ├── definition_parser.py  # Parse definitions for E-K
│   ├── source_parser.py
│   ├── ek_generator.py   # Generate E-K dictionary (Markdown/JSON)
│   ├── latex_generator.py # Generate LaTeX dictionary
│   ├── ek_dictionary.md  # E-K output (Markdown)
│   ├── ek_index.json     # E-K output (JSON)
│   └── dictionary.tex    # LaTeX output (K-E + E-K)
├── generate_db_yaml.sh   # New YAML-based build script
├── generate_db.sh        # Original XML-based build script (still works)
└── mem-*.xml             # Original XML source files (retained for now)
```

## Build Commands

### Using YAML Pipeline (New)
```bash
# Generate database from YAML sources
./generate_db_yaml.sh

# Non-interactive mode (for CI/CD)
./generate_db_yaml.sh --noninteractive
```

### Using XML Pipeline (Original)
```bash
# Generate database from XML sources
./generate_db.sh

# Non-interactive mode
./generate_db.sh --noninteractive
```

### Generating E-K Dictionary
```bash
# Generate E-K dictionary from YAML entries
python3 build/ek_generator.py

# Outputs:
#   build/ek_dictionary.md  - Markdown for print
#   build/ek_index.json     - JSON for apps
```

### Generating LaTeX Dictionary
```bash
# Generate complete LaTeX dictionary (K-E + E-K)
python3 build/latex_generator.py > build/dictionary.tex

# Sections: base, ficnames, loanwords, places
```

## Verification

The YAML pipeline has been verified to produce identical output:

| Output | YAML Pipeline | XML Pipeline | Match |
|--------|---------------|--------------|-------|
| qawHaq.db entries | 6,407 | 6,407 | ✓ |
| qawHaq.json size | 6,496,002 bytes | 6,496,002 bytes | ✓ |
| SQL dump diff | 0 lines | - | ✓ |
| JSON diff | 0 lines | - | ✓ |

## Remaining Work

### Phase 3: Definition Structure ✓
- ✓ Parse definitions into structured parts for E-K dictionary
- ✓ Extract global parentheticals
- ✓ Add sort keyword support
- ✓ Guard cases (`no_permute` flag) for definitions that should not be split
- ✓ Deduplication (`dedup` flag) to prevent nearby duplicate E-K entries
- Pending: Human review of ambiguous parses

### Phase 4: Notes and Examples (Future)
- Further extraction of shared notes
- Structure examples with stanzas
- Update entry references

### Phase 5: E-K Generation ✓
- ✓ Implement E-K permutation generation (`build/ek_generator.py`)
- ✓ Be-verb format: "X, be X, be Y, be Z"
- ✓ Print dictionary output (`build/ek_dictionary.md`)
- ✓ JSON index output (`build/ek_index.json`)
- ✓ TKD convention formatting: _English_ — **Klingon**
- ✓ LaTeX dictionary generator (`build/latex_generator.py`)
  - Generates K-E and E-K sections
  - Handles all sections: base, ficnames, loanwords, places

**E-K Statistics:**
- 6,437 entries loaded
- 8,102 E-K lookup entries generated
- 1,389 entries with multiple parts (permutations)
- 29 guard cases (no_permute)
- 91 dedup cases

**LaTeX Output Statistics:**
- 5,300 base entries
- 111 fictional names
- 416 loanwords
- 249 places

### Phase 6: Validation and Testing (Future)
- Implement all validation rules from SPEC.md
- Performance testing

### Phase 7: Migration Completion (Future)
- Remove XML source files
- Update documentation
- Update contributor guide

## Entry YAML Format

Each entry file contains either a single entry or multiple homophones:

```yaml
# Single entry
entry:
  entry_name: "bach"
  slug: "bach_v"
  part_of_speech: "v:t_c,klcp1,weap"
  pos: "v"
  pos_subtype: "t_c"
  status: "active"
  definition: "shoot"
  notes: "..."
  sources:
    raw: "[1] {TKD:src}"
    citations:
      - source: tkd
  translations:
    de:
      definition: "schießen"
    # ... other languages
  _original_id: 10002
```

## Notes

1. The `_original_id` field preserves the entry's ID from the original XML for backward compatibility.

2. The `part_of_speech` field retains the original combined format for backward compatibility, while `pos`, `pos_subtype`, `categories`, and `metadata_tags` provide the parsed components.

3. The `sources` field contains both the `raw` original text and parsed `citations` for future use.

4. XML source files are retained during the transition period but are no longer the source of truth for the YAML pipeline.

5. The `definition` field can be a simple string or a structured object with:
   - `text`: The full definition text
   - `parts`: Array of definition parts for E-K permutation
   - `global_parenthetical`: Parenthetical that applies to all parts
   - `no_permute`: Guard flag to prevent E-K permutation (for birds, exclamations, etc.)
   - `dedup`: Flag to prevent nearby duplicate E-K entries (for actor/actress, etc.)
   - `etc_suffix`: Flag indicating definition ends with ", etc."
