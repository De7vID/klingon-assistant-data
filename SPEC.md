# Klingon Lexicon Database Redesign Specification

**Version:** 1.0
**Status:** Draft
**Date:** 2026-01-09

## Table of Contents

1. [Overview](#1-overview)
2. [Design Principles](#2-design-principles)
3. [Data Model](#3-data-model)
4. [File Format and Organization](#4-file-format-and-organization)
5. [Source Registry](#5-source-registry)
6. [Entry Schema](#6-entry-schema)
7. [Definition Structure](#7-definition-structure)
8. [Notes System](#8-notes-system)
9. [Examples System](#9-examples-system)
10. [E-K Dictionary Generation](#10-e-k-dictionary-generation)
11. [Validation Rules](#11-validation-rules)
12. [Output Generation](#12-output-generation)
13. [Migration Strategy](#13-migration-strategy)
14. [Implementation Phases](#14-implementation-phases)

---

## 1. Overview

### 1.1 Purpose

This specification defines the redesigned schema for the Klingon lexicon database used by **boQwI'** (Klingon Language Assistant) and associated applications. The redesign addresses limitations of the current schema identified in REDESIGN.md.

### 1.2 Goals

1. **Structured Sources**: Replace unstructured source strings with first-class source entities supporting type-specific metadata
2. **E-K Dictionary Support**: Enable automated generation of English-to-Klingon dictionary entries with proper permutation and sorting
3. **Reusable Content**: Allow notes and examples to be shared across entries without duplication
4. **Cleaner Data Model**: Separate overloaded fields (components vs. plural counterparts, POS vs. categories vs. tags)
5. **Granular Source Files**: Split large XML files into manageable per-entry files
6. **Backward Compatibility**: Generate SQLite output identical to current schema for existing apps
7. **Multi-format Print Output**: Support generation of K-E, E-K, and thematic print dictionaries from single source

### 1.3 Constraints

- **Mobile-first optimization**: Minimize joins, support fast cold-start queries
- **Full backward compatibility**: Existing Android app versions must continue to work
- **Technology-agnostic**: Build pipeline tools can be implemented in any language

---

## 2. Design Principles

### 2.1 English-Primary Model

English is the canonical definition language. Other language translations:
- Can have their own structure (not necessarily 1:1 mapping to English parts)
- Can have language-specific notes (marked with an indicator when not applicable to English)
- Are stored in language packs separate from the base database (Klingon + English)

### 2.2 Language-Agnostic Schema

Languages are data, not schema. Adding a new language requires only adding translation data, not schema changes. The system supports an arbitrary number of languages.

### 2.3 Soft References with Validation

Entry references (synonyms, see_also, components, inline `{entry:pos}` syntax) are stored as text strings, not foreign keys. A validation step checks referential integrity during build.

### 2.4 Git for History

No audit fields (created_date, modified_by) in the schema. Git history provides complete change tracking. Draft/WIP entries exist only in feature branches.

### 2.5 Deterministic Generation

All derived data (slugs, xifan hol forms, PUA forms, E-K permutations) is generated deterministically from source data using fixed rules with no manual overrides.

---

## 3. Data Model

### 3.1 Entity Relationship Overview

```
┌─────────────┐       ┌─────────────┐
│   Source    │       │    Note     │
│  (registry) │       │  (shared)   │
└──────┬──────┘       └──────┬──────┘
       │                     │
       │ cited by            │ referenced by
       ▼                     ▼
┌─────────────────────────────────────┐
│               Entry                  │
│  ┌─────────────┐  ┌──────────────┐  │
│  │ Definitions │  │  Components  │  │
│  │   (parts)   │  │    (tree)    │  │
│  └─────────────┘  └──────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  │
│  │   Aliases   │  │ Translations │  │
│  └─────────────┘  └──────────────┘  │
└─────────────────┬───────────────────┘
                  │
                  │ referenced by
                  ▼
           ┌─────────────┐
           │   Example   │
           │  (shared)   │
           │  ┌───────┐  │
           │  │Stanzas│  │
           │  └───────┘  │
           └─────────────┘
```

### 3.2 Core Entities

| Entity | Description | Storage |
|--------|-------------|---------|
| **Source** | Canonical source reference with metadata | Centralized registry file |
| **Entry** | Lexicon entry (word, affix, phrase, sentence) | Individual files grouped by POS/letter |
| **Note** | Reusable note content with sources | Dedicated notes directory |
| **Example** | Reusable example with stanzas and translations | Within entry files or shared |

### 3.3 Identifier Strategy

- **Entry ID**: Deterministic slug generated from `entry_name` (ASCII-safe, URL-safe)
- **Source ID**: Short identifier (e.g., `tkd`, `kgt`, `qepha_2018`)
- **Note ID**: Human-readable identifier (e.g., `musical_scale`, `inherent_plural_note`)
- **Example ID**: Generated or specified identifier

Slug generation rules:
- Klingon `'` (qaghwI') is preserved (as `'` or URL-encoded)
- Initial `-` (affixes) becomes `_`
- Sentence-final punctuation is dropped
- Spaces become `_`
- POS and homophone number appended: `bol_v_1`, `bol_v_2`

---

## 4. File Format and Organization

### 4.1 Recommended Format: YAML

YAML is recommended over XML for the new granular file structure:

**Rationale:**
- More human-readable than XML or JSON
- Less verbose (no closing tags, minimal punctuation)
- Excellent support for nested structures (components tree, stanzas)
- Easy to edit in text editors (vim, VSCode)
- Wide tooling support in all languages
- Native list and map syntax

### 4.2 Directory Structure

```
data/
├── sources.yaml                    # Centralized source registry
├── notes/                          # Shared reusable notes
│   ├── musical_scale.yaml
│   └── inherent_plural.yaml
├── entries/
│   ├── verbs/
│   │   ├── b/
│   │   │   ├── bach.yaml
│   │   │   └── bol.yaml           # Contains bol:v:1, bol:v:2, and bolwI'
│   │   ├── j/
│   │   │   └── joq.yaml
│   │   └── ...
│   ├── nouns/
│   │   ├── b/
│   │   │   └── batlh.yaml
│   │   └── ...
│   ├── suffixes/
│   │   ├── verb/
│   │   │   └── _ghach.yaml        # Initial - becomes _
│   │   └── noun/
│   │       └── _pu'.yaml
│   ├── sentences/
│   │   └── b/
│   │       └── batlh_biHeghjaj.yaml
│   └── sources/                    # Source entries (type: src)
│       └── tkd.yaml
└── build/
    ├── generate_db.py
    └── validate.py
```

### 4.3 File Naming Conventions

| Entry Type | Example Entry | Filename |
|------------|---------------|----------|
| Verb | `joq` | `entries/verbs/j/joq.yaml` |
| Noun | `batlh` | `entries/nouns/b/batlh.yaml` |
| Suffix (verb) | `-ghach` | `entries/suffixes/verb/_ghach.yaml` |
| Suffix (noun) | `-pu'` | `entries/suffixes/noun/_pu'.yaml` |
| Sentence | `batlh bIHeghjaj.` | `entries/sentences/b/batlh_biHeghjaj.yaml` |
| Homophone verbs | `bol` (v:1, v:2) | `entries/verbs/b/bol.yaml` |

### 4.4 Grouping Rules

A single file contains:
1. All homophones with the same `entry_name` and base part of speech
2. Suffix-only derived forms (e.g., `bolwI'` with `bol`)

Derived entries are nested within their root entry.

---

## 5. Source Registry

### 5.1 Source Entity Schema

```yaml
# sources.yaml
sources:
  tkd:
    name: "The Klingon Dictionary"
    short_name: "TKD"
    type: book
    metadata:
      author: "Marc Okrand"
      year: 1992
      editions:
        - edition: 1
          year: 1985
        - edition: 2
          year: 1992
      page_prefix: "p."  # Used for citations: "p.45"

  kgt:
    name: "Klingon for the Galactic Traveler"
    short_name: "KGT"
    type: book
    metadata:
      author: "Marc Okrand"
      year: 1997
      page_prefix: "p."

  holqed:
    name: "HolQeD"
    short_name: "HQ"
    type: journal
    metadata:
      publisher: "Klingon Language Institute"
      # Volume, issue, pages specified per-citation

  qepha_2018:
    name: "qep'a' 25"
    short_name: "qep'a' 25"
    type: event
    metadata:
      year: 2018
      event_number: 25
      location: "Indianapolis, IN"

  qephom_2016:
    name: "Saarbrücken qepHom'a' 2016"
    short_name: "qepHom'a' 2016"
    type: event
    metadata:
      year: 2016
      location: "Saarbrücken, Germany"

  skybox_s27:
    name: "SkyBox S27"
    short_name: "SkyBox S27"
    type: media
    metadata:
      media_type: "trading card"
      item_id: "S27"
    reprinted_in: holqed  # Parent-child relationship
    reprint_citation:
      volume: 5
      issue: 3
      page_start: 15
      date: "1996-09"

  kli_mailing_list:
    name: "KLI mailing list"
    short_name: "KLI mailing list"
    type: mailing_list
    metadata:
      url: "https://www.kli.org/..."
      # Date specified per-citation
```

### 5.2 Source Types and Metadata

| Type | Required Metadata | Optional Metadata |
|------|-------------------|-------------------|
| `book` | `year`, `page_prefix` | `author`, `editions[]` |
| `journal` | (none - per-citation) | `publisher` |
| `event` | `year` | `event_number`, `location` |
| `media` | `media_type` | `item_id`, `url` |
| `mailing_list` | (none - per-citation) | `url` |
| `newsgroup` | `group_name` | |
| `audio` | `year` | `format` (CD, cassette) |
| `game` | `year`, `platform` | |
| `tv_show` | `show_name`, `year` | `episode` |
| `magazine` | `publication_name` | |

### 5.3 Citation Structure

Citations reference sources with additional location metadata:

```yaml
sources:
  - source: kgt
    page_start: 178
    page_end: 179
  - source: holqed
    volume: 13
    issue: 1
    page_start: 8
    page_end: 10
    date: "2004-03"
  - source: kli_mailing_list
    date: "2023-12-15"
    message_id: "abc123"  # Optional disambiguation
```

---

## 6. Entry Schema

### 6.1 Entry Structure

```yaml
# entries/verbs/j/joq.yaml

entry:
  # Core identification
  entry_name: "joq"
  slug: "joq_v"  # Generated, but shown for clarity

  # Name variants (auto-generated)
  entry_name_xifan: "joq"      # xifan hol representation
  entry_name_pua: "\uF8D6\uF8DD\uF8D8"  # Unicode PUA

  # Part of speech (split from current combined field)
  pos: "v"
  pos_subtype: "i"  # i, t, is, ambi, pref, suff, etc.

  # Categories and tags (split from current combined field)
  categories: []  # anim, archaic, food, inv, slang, weap, etc.
  metadata_tags: ["klcp1"]  # klcp1, fic, hyp, extcan, terran, etc.

  # Status
  status: "active"  # active, deprecated, non-canon, nodict

  # Aliases (alternative spellings)
  aliases:
    - alias: "joQ"
      frequency: "rare"  # common, rare

  # Definition (English - canonical)
  definition:
    parts:
      - text: "flap"
        sources:
          - source: tkd
      - text: "flutter"
        sources:
          - source: tkd
      - text: "wave"
        sources:
          - source: tkd
    global_parenthetical: null  # e.g., "e.g., thrusters"

  # Relations
  synonyms: []
  antonyms: []
  see_also: []

  # Notes (references to shared notes or inline)
  notes:
    - note_ref: "some_shared_note"
    - text: "This is an inline note specific to this entry."
      sources:
        - source: kgt
          page_start: 45

  # Hidden notes (maintainer only)
  hidden_notes: "Internal comment about this entry"

  # Print-specific notes
  print_notes: "See also the related entry on p.XX"

  # Components (for derived/complex entries)
  components: null

  # Plural counterpart (for inhpl/inhps nouns)
  plural_counterpart: null

  # Examples
  examples:
    - example_ref: "joq_example_1"
    - inline:
        klingon: "{wa'leS:n}, {cha'leS:n}"
        # Inline examples don't need translations

  # Translations (per language)
  translations:
    de:
      definition: "flattern, wehen"
      notes: []
      search_tags: ["Flagge"]
    fr:
      definition: "battre (des ailes), flotter, ondoyer"
      notes: []
      search_tags: []
    # ... other languages

  # Search tags (English)
  search_tags: ["flag", "banner", "waving"]

  # Derived entries (nested)
  derived:
    - entry:
        entry_name: "joqwI'"
        slug: "joqwI'_n"
        pos: "n"
        pos_subtype: null
        definition:
          parts:
            - text: "flag"
              sources:
                - source: tkd
        # ... other fields
```

### 6.2 Part of Speech Values

**Base POS:**
- `v` - verb
- `n` - noun
- `adv` - adverbial
- `conj` - conjunction
- `ques` - question word
- `sen` - sentence
- `excl` - exclamation
- `src` - source (meta-entry)

**POS Subtypes:**

| Base POS | Subtypes |
|----------|----------|
| `v` | `i`, `t`, `is`, `ambi`, `i_c`, `t_c`, `pref`, `suff` |
| `n` | `name`, `num`, `pro`, `body`, `being`, `place`, `inhpl`, `inhps`, `plural`, `suff` |
| `sen` | `eu`, `idiom`, `mv`, `nt`, `phr`, `prov`, `Ql`, `rej`, `rp`, `sp`, `toast`, `lyr`, `bc` |
| `excl` | `epithet` |

### 6.3 Status Values

| Status | Description | Included in Build |
|--------|-------------|-------------------|
| `active` | Normal entry | Yes |
| `deprecated` | Superseded or incorrect | Yes (flagged) |
| `non-canon` | Extended canon, hypothetical | Yes (flagged) |
| `nodict` | Search convenience only | App only, not print |

### 6.4 Components Tree Structure

For complex entries (sentences, derived words), components form a parse tree:

```yaml
# entries/sentences/b/batlh_biHeghjaj.yaml
entry:
  entry_name: "batlh bIHeghjaj."
  pos: "sen"
  definition:
    parts:
      - text: "May you die with honor."

  components:
    type: "sentence"
    children:
      - ref: "batlh:adv"
        role: "adverbial"
      - type: "verb_complex"
        children:
          - ref: "bI-:v:pref"
            role: "prefix"
          - ref: "Hegh:v"
            role: "verb_stem"
          - ref: "-jaj:v:suff"
            role: "suffix"
            suffix_type: "rover"
```

Decomposition depth is configurable per entry - some entries may decompose fully to roots and affixes, others may stop at existing lexicon entries.

---

## 7. Definition Structure

### 7.1 Definition Parts

Each definition consists of one or more parts, each with optional sources and sort keywords:

```yaml
definition:
  parts:
    - text: "field (of land)"
      sources:
        - source: tkd
    - text: "park (e.g., recreational)"
      sources:
        - source: qephom_2016
      sort_keyword: "park"  # Optional explicit sort key
  global_parenthetical: null
```

### 7.2 Global Parentheticals

When a parenthetical applies to ALL parts of a definition, it's stored separately:

```yaml
# "fire, energize (e.g., thrusters)"
definition:
  parts:
    - text: "fire"
    - text: "energize"
  global_parenthetical: "e.g., thrusters"
```

### 7.3 Sort Keywords

For E-K dictionary generation, each part has an implicit or explicit sort keyword:

| Rule | Example | Sort Key |
|------|---------|----------|
| Default | `fire` | `fire` |
| Be-verb (auto-strip) | `be hostile` | `hostile` |
| Explicit override | `travel on a mission` | `mission` (explicit) |

---

## 8. Notes System

### 8.1 Shared Notes

Notes that appear across multiple entries are stored in the `notes/` directory:

```yaml
# notes/musical_scale.yaml
note:
  id: "musical_scale"
  text: "The tones of the Klingon musical scale are: {yu:n}, {bIm:n}, {'egh:n}, {loS:n:2}, {vagh:n:2}, {jav:n:2}, {Soch:n:2}, {chorgh:n:2}, {yu:n:nolink}."
  sources:
    - source: kgt

  translations:
    de:
      text: "Die Töne der klingonischen Tonleiter sind: ..."
    # ... other languages
```

### 8.2 Note References

Entries reference shared notes by ID:

```yaml
notes:
  - note_ref: "musical_scale"
  - text: "Inline note for this entry only."
    sources:
      - source: tkd
        page_start: 100
```

### 8.3 Language-Specific Notes

English notes are canonical. Notes that apply only to non-English languages use a special indicator:

```yaml
notes:
  - text: "This note is canon."
    sources:
      - source: tkd
  - text: "This note is only relevant in German."
    languages: ["de"]  # Indicates NOT applicable to English
    sources:
      - source: some_german_source
```

---

## 9. Examples System

### 9.1 Example Structure

Examples are reusable entities with stanza-based structure:

```yaml
# Defined inline or in a shared location
example:
  id: "yeq_paqbatlh_1"
  source:
    source: paqbatlh_2ed
    page_start: 122
    page_end: 123

  stanzas:
    - klingon: |
        HarghmeH yeq chaH
        molor HI''a' luSuv
        lughIjlu'be' 'ej pujHa' 'e' lu'aghmeH Suv
      translations:
        en: |
          United to do battle together!
          Against the tyrant Molor!
          Against fear and against weakness!
        de: |
          Vereint, gemeinsam zu kämpfen!
          Gegen den Tyrannen Molor!
          Gegen Angst und gegen Schwäche!
        fr: |
          Unis pour lutter ensemble !
          Contre le tyran Molor !
          Contre la peur et la faiblesse !

    - klingon: |
        nIteb chegh molor ngIq ghoqwI'
        joqwI''e' cha'bogh qeylIS
        luDel 'e' ra' molor
      translations:
        en: |
          One by one Molor's scouts return,
          He asks them which banner
          Kahless marches under.
        # ... other translations
```

### 9.2 Example References

Entries reference examples by ID (whole example is the linkable unit):

```yaml
examples:
  - example_ref: "yeq_paqbatlh_1"
  - inline:
      klingon: "{wa'leS:n}"
      # Simple inline examples without full structure
```

### 9.3 Example Scope

All examples appear in all languages. If a translation is missing for a language, the example still appears (with untranslated stanzas).

---

## 10. E-K Dictionary Generation

### 10.1 Overview

E-K (English-to-Klingon) lookups are generated as cached/materialized views from definition parts.

### 10.2 Generation Rules

For each definition part:

1. **Extract sort key**:
   - Use explicit `sort_keyword` if provided
   - For `v:is` entries, strip leading "be "
   - Otherwise, use first word of part text

2. **Generate permutations**: Create one E-K entry per unique sort key
   - All parts contribute their sort key
   - Permutations list the sort key's part first, then others

3. **Include parentheticals**:
   - Part-specific parentheticals stay with their part
   - Global parentheticals are appended to all permutations

### 10.3 Examples

**Input:**
```yaml
entry_name: "joq"
pos: "v"
pos_subtype: "i"
definition:
  parts:
    - text: "flap"
    - text: "flutter"
    - text: "wave"
```

**Generated E-K entries:**
| Sort Key | Display |
|----------|---------|
| `flap` | flap, flutter, wave |
| `flutter` | flutter, flap, wave |
| `wave` | wave, flap, flutter |

**Be-verb input:**
```yaml
entry_name: "ghegh"
pos: "v"
pos_subtype: "is"
definition:
  parts:
    - text: "be hostile"
    - text: "be malicious"
    - text: "be unfriendly"
    - text: "be antagonistic"
```

**Generated E-K entries:**

For be-verbs, the display format is "X, be X, be Y, be Z" where X is the adjective (sort key) without "be", followed by the full form, then other full forms:

| Sort Key | Display |
|----------|---------|
| `antagonistic` | antagonistic, be antagonistic, be hostile, be malicious, be unfriendly |
| `hostile` | hostile, be hostile, be malicious, be unfriendly, be antagonistic |
| `malicious` | malicious, be malicious, be hostile, be unfriendly, be antagonistic |
| `unfriendly` | unfriendly, be unfriendly, be hostile, be malicious, be antagonistic |

### 10.4 E-K Cache

The build process:
1. Generates all E-K permutations during build
2. Stores them in a materialized table/view
3. Invalidates cache when source definitions change

---

## 11. Validation Rules

### 11.1 Required Validations

| Rule | Description | Severity |
|------|-------------|----------|
| **Reference Integrity** | All `{entry:pos}` references must point to existing entries | Error |
| **Source Completeness** | Every non-note field must have at least one source | Error |
| **Translation Coverage** | Warn if languages are missing translations | Warning |
| **POS Consistency** | Components must reference entries with valid POS | Error |
| **Plural Pair Bidirectional** | inhpl/inhps entries must reference each other | Error |
| **Slug Uniqueness** | Generated slugs must be unique | Error |
| **Source Validity** | All source references must exist in source registry | Error |

### 11.2 Existing Validation Rules

All validation currently performed by `generate_db.sh` must be preserved:
- Missing German/Portuguese/Finnish definitions
- Broken entry references
- Misplaced spaces/commas
- Missing translations (fields containing "TRANSLATE")
- New `{ngh}`/`{ngH}` entries (require parser updates)
- Two-letter verbs (require parser updates)

### 11.3 Inline Reference Validation

All inline references (`{entry:pos}` syntax) must resolve to existing entries:
- References in definition text
- References in notes
- References in examples

---

## 12. Output Generation

### 12.1 Primary Outputs

Both outputs are generated directly from source files (neither derives from the other):

| Output | Format | Purpose |
|--------|--------|---------|
| `qawHaq.db` | SQLite | Android app, iOS app |
| `qawHaq.json` | JSON | Web applications, tooling |

### 12.2 SQLite Schema (Backward Compatible)

The generated SQLite database must be compatible with existing app versions:

```sql
CREATE TABLE entries (
  _id INTEGER PRIMARY KEY,
  entry_name TEXT,
  part_of_speech TEXT,      -- Combined format: "v:t,slang,klcp1"
  definition TEXT,
  synonyms TEXT,
  antonyms TEXT,
  see_also TEXT,
  notes TEXT,
  hidden_notes TEXT,
  components TEXT,
  examples TEXT,
  search_tags TEXT,
  source TEXT,              -- Formatted: "[1] {TKD:src}, [2] {KGT p.56:src}"
  -- Language-specific columns
  definition_de TEXT,
  notes_de TEXT,
  examples_de TEXT,
  search_tags_de TEXT,
  -- ... other languages
);

-- FTS5 for search
CREATE VIRTUAL TABLE entries_fts USING fts5(
  entry_name,
  definition,
  search_tags,
  -- ... other searchable columns
);
```

### 12.3 Base + Language Packs

**Base database** (`qawHaq.db`):
- Klingon: entry_name, components, examples (Klingon text)
- English: definition, notes, examples (translations), search_tags
- Structure: sources, relations, metadata

**Language pack** (`qawHaq_de.db`, etc.):
- Language-specific: definition_XX, notes_XX, examples_XX, search_tags_XX

Apps load base + selected language pack(s).

### 12.4 Print Dictionary Outputs

The schema supports generating multiple print formats:

| Format | Description |
|--------|-------------|
| K-E | Klingon-to-English, alphabetical by entry_name |
| E-K | English-to-Klingon, alphabetical by sort key |
| Thematic | Grouped by category (food, weapons, etc.) |
| By Source | Entries from a specific source/book |

---

## 13. Migration Strategy

### 13.1 Approach: Shadow Writes

During migration, both old and new build pipelines run in parallel:
1. Old pipeline produces `qawHaq.db` from XML sources
2. New pipeline produces `qawHaq_new.db` from YAML sources
3. Comparison tool identifies differences
4. Continue until parity achieved

### 13.2 Discrepancy Handling

| Difference Type | Action |
|-----------------|--------|
| Formatting only (whitespace, ordering) | Auto-approve |
| Small semantic differences | Manual review |
| Large differences | Block, require investigation |

### 13.3 Ambiguous Parsing

When migrating definition text to structured parts:
- Conservative parsing: if ambiguous, keep as single part
- Flag all migrated entries for human review
- Human resolution required for ambiguous cases

### 13.4 Migration Completion

Migration is complete when:
- All entries converted to YAML format
- New pipeline produces byte-identical SQLite output
- All validation rules pass
- Human review of flagged entries complete

---

## 14. Implementation Phases

### Phase 1: Source Registry

**Scope:**
- Define source registry schema
- Create `sources.yaml` with all existing sources
- Build source validation
- Update build to use source registry for source display

**Deliverables:**
- `sources.yaml` file
- Source validation script
- Documentation of source types and metadata

### Phase 2: Entry File Structure

**Scope:**
- Define YAML schema for entries
- Create directory structure
- Build script to split existing XML into YAML files
- Implement file-to-memory parsing

**Deliverables:**
- Entry YAML schema
- Migration script (XML → YAML)
- Directory structure with migrated entries
- Parser for YAML entries

### Phase 3: Definition Structure

**Scope:**
- Parse existing definitions into parts
- Implement global parenthetical extraction
- Add sort keyword support
- Human review of ambiguous parses

**Deliverables:**
- Definition parsing logic
- Sort keyword extraction
- Review queue for ambiguous entries

### Phase 4: Notes and Examples

**Scope:**
- Identify shared notes across entries
- Extract to `notes/` directory
- Structure examples with stanzas
- Update entry references

**Deliverables:**
- Shared notes extraction
- Example restructuring
- Reference update across entries

### Phase 5: E-K Generation

**Scope:**
- Implement E-K permutation generation
- Build E-K cache/materialized view
- Be-verb auto-stripping
- Print dictionary output

**Deliverables:**
- E-K generation logic
- Cache invalidation
- Print-ready E-K output

### Phase 6: Validation and Testing

**Scope:**
- Implement all validation rules
- Shadow write comparison
- Fix discrepancies
- Performance testing

**Deliverables:**
- Complete validation suite
- Comparison tools
- Performance benchmarks

### Phase 7: Migration Completion

**Scope:**
- Final human review
- Remove old XML pipeline
- Documentation update
- Contributor guide for new format

**Deliverables:**
- Retired XML sources
- Updated contributor documentation
- Training materials

---

## Appendix A: Reference Syntax

The existing `{entry:pos:flags}` syntax is preserved:

| Syntax | Meaning |
|--------|---------|
| `{tlhIngan Hol}` | Link to entry, auto-analyze |
| `{tlhIngan Hol:n}` | Link to noun entry |
| `{pum:v:2}` | Link to verb, homophone 2 |
| `{jIH:n:1h}` | Homophone 1, hide number in display |
| `{word:n:nolink}` | Mention without hyperlink |
| `{TKD:src}` | Source reference |

---

## Appendix B: File Format Examples

### B.1 Complete Entry Example

```yaml
# entries/verbs/l/laQ.yaml
entry:
  entry_name: "laQ"
  slug: "laQ_v"

  pos: "v"
  pos_subtype: "t"
  categories: []
  metadata_tags: ["klcp1"]
  status: "active"

  definition:
    parts:
      - text: "fire"
        sources:
          - source: tkd
      - text: "energize"
        sources:
          - source: tkd
    global_parenthetical: "e.g., thrusters"

  synonyms: []
  antonyms: []
  see_also: ["{chu':v}"]

  notes:
    - text: "Used for activating weapons or engines."
      sources:
        - source: kgt
          page_start: 67

  hidden_notes: null
  print_notes: null
  components: null
  plural_counterpart: null

  examples:
    - inline:
        klingon: "{peng laQ:sen:nolink}"

  translations:
    de:
      definition: "feuern, aktivieren (z.B. Triebwerke)"
      notes: []
      search_tags: []

  search_tags: ["activate", "weapon", "thruster"]
```

### B.2 Shared Note Example

```yaml
# notes/musical_scale.yaml
note:
  id: "musical_scale"
  text: "The tones of the Klingon musical scale are: {yu:n}, {bIm:n}, {'egh:n}, {loS:n:2}, {vagh:n:2}, {jav:n:2}, {Soch:n:2}, {chorgh:n:2}, {yu:n:nolink}."
  sources:
    - source: kgt
      page_start: 71
      page_end: 74

  translations:
    de:
      text: "Die Töne der klingonischen Tonleiter sind: {yu:n}, {bIm:n}, {'egh:n}, {loS:n:2}, {vagh:n:2}, {jav:n:2}, {Soch:n:2}, {chorgh:n:2}, {yu:n:nolink}."
```

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **boQwI'** | "helper" - the Android app name |
| **E-K** | English-to-Klingon (dictionary direction) |
| **FTS** | Full-Text Search (SQLite FTS5) |
| **inhpl** | Inherently plural noun |
| **inhps** | Singular form of inherently plural noun |
| **K-E** | Klingon-to-English (dictionary direction) |
| **klcp1** | Klingon Language Certification Program level 1 |
| **nodict** | Entry excluded from print dictionary |
| **nolink** | Display mention without hyperlink |
| **paq'batlh** | "Book of Honor" - Klingon epic poem |
| **POS** | Part of Speech |
| **PUA** | Private Use Area (Unicode) |
| **qaghwI'** | The Klingon letter `'` (glottal stop) |
| **qawHaq** | "memory bank" - the database name |
| **TKD** | The Klingon Dictionary |
| **xifan hol** | Phonetic ASCII encoding (one char per Klingon letter) |
