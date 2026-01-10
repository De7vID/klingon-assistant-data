# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Klingon language dictionary data files for **boQwI'** and associated apps. This is a git submodule containing XML source files that are compiled into the SQLite database used by the Android app.

## File Organization

XML source files organized by Klingon letter:
- `mem-01-b.xml` through `mem-25-u.xml` - Main lexicon entries by letter
- `mem-26-suffixes.xml` - Grammatical suffixes
- `mem-27-extra.xml` - Non-canon/uncertain entries, transliterations, movie sentences
- `mem-28-examples.xml` - Pedagogical examples and complex word searches
- `mem-00-header.xml` / `mem-29-footer.xml` - XML structure wrappers

## Build Commands

### XML Pipeline (Original)
```bash
# Generate database (interactive mode with diff review)
./generate_db.sh

# Generate database non-interactively (used by Android build)
./generate_db.sh --noninteractive

# Generate only the combined XML file (for debugging)
./generate_db.sh --xmlonly

# Review changes for a specific language before PR
./review_changes.sh <lang_code> [commit]
```

### YAML Pipeline (New)
```bash
# Generate database from YAML sources (interactive mode)
./generate_db_yaml.sh

# Generate database non-interactively (for CI/CD)
./generate_db_yaml.sh --noninteractive
```

The YAML pipeline reads from `entries/*.yaml` and produces identical output to the XML pipeline. See `MIGRATION_STATUS.md` for details on the migration.

The `generate_db.sh` script validates entries and checks for:
- Missing German/Portuguese/Finnish definitions
- Broken entry references
- Misplaced spaces/commas
- Missing translations (fields containing "TRANSLATE")
- New `{ngh}`/`{ngH}` entries or two-letter verbs (require parser updates)

## Entry Guidelines

- Use `blank.xml` template when adding new entries
- `entry_name` must exactly match the original source (important for KWOTD matching)
- `notes` fields are for "in-universe" information; `hidden_notes` for meta/out-of-universe info
- Full sentences should have final punctuation
- Link to other entries only once per entry; use `nolink` tag for subsequent references
- Translations can take liberties to convey meaning; words in brackets/quotes may need `search_tags`

## Parser Caveats

The Android parser has hardcoded lists that must be updated when adding certain entries:

1. **{ngh}/{ngH} entries**: The sequence "ngh" is ambiguous in xifan hol mode (could be **n**+**gh** or **ng**+**H**). Update the hardcoded list in `KlingonContentDatabase.java`.

2. **Two-letter verbs**: Short queries (≤4 letters) have special handling. Update the hardcoded list when adding 2-letter verbs.

The `generate_db.sh` script outputs warnings when entries matching these criteria are added or changed.

## Translation Workflow

- Run `call_google_translate.py` to auto-translate fields containing "TRANSLATE"
- Commits with manual translations should change only one language
- Use "Squash and merge" for large translation PRs
- Run `review_changes.sh <lang>` before submitting PRs

## E-K Dictionary Generation

The `build/` directory contains tools for generating English-to-Klingon dictionary entries:

```bash
# Generate E-K dictionary from YAML entries
python3 build/ek_generator.py
```

This produces:
- `build/ek_dictionary.md` - Markdown format for print dictionary
- `build/ek_index.json` - JSON format for apps

Key files:
- `build/definition_parser.py` - Parses definitions into structured parts
- `build/ek_generator.py` - Generates E-K permutations

Definition flags in YAML entries:
- `no_permute: true` - Guard cases that should NOT be split (birds, exclamations)
- `dedup: true` - Prevent nearby duplicate E-K entries (actor/actress)
- `etc_suffix: true` - Definition ends with ", etc."
