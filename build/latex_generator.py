#!/usr/bin/env python3
"""
LaTeX Dictionary Generator

Generates K-E and E-K dictionary sections in LaTeX format from YAML entries.

Usage:
    python3 build/latex_generator.py > dictionary.tex
"""

import os
import sys
import re
import yaml
from collections import defaultdict
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set

# Add build directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from definition_parser import parse_definition

# =============================================================================
# Constants
# =============================================================================

# Klingon alphabet in sort order
LETTERS = [
    "a", "b", "ch", "D", "e", "gh", "H", "I", "j", "l", "m", "n", "ng",
    "o", "p", "q", "Q", "r", "S", "t", "tlh", "u", "v", "w", "y", "'"
]

# Multi-character letters (must check these first when parsing)
DIGRAPHS = ["tlh", "ch", "gh", "ng"]

# Locale strings
LOCALE = {
    "base": "Klingon-English",
    "loanwords": "Borrowed Terran concepts",
    "ficnames": "Names",
    "names": "Names of Humans",
    "ficplaces": "Places in Space",
    "places": "Places in the Solar System and on Earth",
    "poses": {
        "v": "v.",
        "n": "n.",
        "adv": "adv.",
        "ques": "ques.",
        "conj": "conj.",
        "excl": "excl.",
        "sen": "sen.",
        "affix": "affix",
        "idiom": "idiom",
    }
}

# Section definitions with query filters
SECTIONS = [
    {
        "name": "base",
        "exclude_tags": {"nodict", "extcan", "hyp", "terran"},
        "exclude_pos": {"sen"},
        "include_fic_places": True,
        "exclude_names": True,
    },
    {
        "name": "ficnames",
        "require_tags": {"name", "fic"},
        "exclude_tags": {"nodict", "extcan", "hyp"},
        "exclude_pos": {"sen"},
    },
    {
        "name": "loanwords",
        "require_tags": {"terran"},
        "exclude_tags": {"nodict", "extcan", "hyp"},
        "exclude_pos": {"sen"},
        "include_fic_places": True,
        "include_fic_names": True,
    },
    {
        "name": "places",
        "require_tags": {"place"},
        "exclude_tags": {"nodict", "extcan", "hyp", "fic"},
        "exclude_pos": {"sen"},
        "allow_terran": True,  # Places can have terran tag
    },
]


# =============================================================================
# Grapheme Parsing
# =============================================================================

def parse_graphemes(word: str) -> List[str]:
    """
    Parse a Klingon word into its constituent graphemes (letters).

    Example: "tlhIngan" -> ["tlh", "I", "n", "g", "a", "n"]
    """
    result = []
    i = 0
    while i < len(word):
        matched = False
        # Check multi-character letters first (longest first)
        for digraph in DIGRAPHS:
            if word[i:i+len(digraph)] == digraph:
                result.append(digraph)
                i += len(digraph)
                matched = True
                break
        if not matched:
            result.append(word[i])
            i += 1
    return result


def get_letter_index(letter: str) -> int:
    """Get the sort index for a Klingon letter."""
    try:
        return LETTERS.index(letter)
    except ValueError:
        # Unknown character - sort at end
        return len(LETTERS)


def klingon_sort_key(entry: 'Entry') -> Tuple:
    """
    Generate a sort key for a Klingon entry.
    Sort by: graphemes, simple_pos, homophone number
    """
    graphemes = entry.graphemes if hasattr(entry, 'graphemes') else []
    pos = entry.pos if hasattr(entry, 'pos') else ""
    homophone = entry.homophone if hasattr(entry, 'homophone') else 0

    letter_indices = tuple(get_letter_index(g) for g in graphemes)
    return (letter_indices, pos, homophone)


# =============================================================================
# Entry Loading
# =============================================================================

@dataclass
class Entry:
    """Represents a dictionary entry."""
    entry_name: str
    slug: str
    pos: str
    pos_subtype: Optional[str]
    definition: str
    definition_struct: Optional[dict]
    graphemes: List[str]
    tags: Set[str]
    categories: Set[str]
    status: str
    components: Optional[str]
    notes: Optional[str]
    see_also: Optional[str]
    synonyms: Optional[str]
    antonyms: Optional[str]
    homophone: int = 0
    derived: List['Entry'] = field(default_factory=list)

    @property
    def simple_pos(self) -> str:
        """Get the base part of speech."""
        return self.pos

    @property
    def boqwi_tags(self) -> Set[str]:
        """Get all tags for filtering (includes pos_subtype)."""
        result = self.tags | self.categories
        if self.pos_subtype:
            # pos_subtype can contain multiple values like "t_c"
            for part in self.pos_subtype.split('_'):
                result.add(part)
        return result


def parse_pos_field(part_of_speech: str) -> Tuple[str, Optional[str], Set[str], Set[str]]:
    """
    Parse the combined part_of_speech field.

    Returns: (pos, pos_subtype, categories, tags)
    """
    if not part_of_speech:
        return "", None, set(), set()

    parts = part_of_speech.split(",")
    pos_part = parts[0] if parts else ""

    # Split pos:subtype
    if ":" in pos_part:
        pos, subtype = pos_part.split(":", 1)
    else:
        pos = pos_part
        subtype = None

    # Rest are categories/tags
    other = set(parts[1:]) if len(parts) > 1 else set()

    # Separate known tags from categories
    known_tags = {
        "nodict", "extcan", "hyp", "fic", "terran", "klcp1", "klcp2",
        "name", "place", "being", "body", "food", "weap", "inhpl", "inhps"
    }
    tags = other & known_tags
    categories = other - known_tags

    return pos, subtype, categories, tags


def load_entries(data_dir: Path) -> List[Entry]:
    """Load all entries from YAML files."""
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

        # Handle single entry or multiple entries
        raw_entries = []
        if 'entry' in content:
            raw_entries.append(content['entry'])
        elif 'entries' in content:
            raw_entries.extend(content['entries'])

        for raw in raw_entries:
            entry = parse_entry(raw)
            if entry:
                entries.append(entry)

    return entries


def parse_entry(raw: dict) -> Optional[Entry]:
    """Parse a raw YAML entry into an Entry object."""
    entry_name = raw.get('entry_name', '')
    if not entry_name:
        return None

    # Parse definition
    definition_raw = raw.get('definition', '')
    if isinstance(definition_raw, dict):
        definition = definition_raw.get('text', '')
        definition_struct = definition_raw
    else:
        definition = definition_raw
        definition_struct = None

    # Parse part of speech
    part_of_speech = raw.get('part_of_speech', '')
    pos, pos_subtype, categories, tags = parse_pos_field(part_of_speech)

    # Also get explicit pos/tags if present
    if raw.get('pos'):
        pos = raw['pos']
    if raw.get('pos_subtype'):
        pos_subtype = raw['pos_subtype']

    # Get status
    status = raw.get('status', 'canonical')

    # Parse graphemes
    graphemes = parse_graphemes(entry_name)

    # Extract homophone number from slug
    slug = raw.get('slug', '')
    homophone = 0
    if slug:
        match = re.search(r'_(\d+)$', slug)
        if match:
            homophone = int(match.group(1))

    return Entry(
        entry_name=entry_name,
        slug=slug,
        pos=pos,
        pos_subtype=pos_subtype,
        definition=definition,
        definition_struct=definition_struct,
        graphemes=graphemes,
        tags=tags,
        categories=categories,
        status=status,
        components=raw.get('components'),
        notes=raw.get('notes'),
        see_also=raw.get('see_also'),
        synonyms=raw.get('synonyms'),
        antonyms=raw.get('antonyms'),
        homophone=homophone,
    )


# =============================================================================
# Entry Filtering
# =============================================================================

def filter_entries(entries: List[Entry], section: dict) -> List[Entry]:
    """Filter entries based on section criteria."""
    result = []

    exclude_tags = section.get('exclude_tags', set())
    require_tags = section.get('require_tags', set())
    exclude_pos = section.get('exclude_pos', set())

    for entry in entries:
        # Skip based on status
        if entry.status in ('nodict',):
            continue

        # Skip suffixes for main listing
        if entry.entry_name.startswith('-'):
            continue

        # Check excluded tags
        effective_exclude = exclude_tags.copy()
        if section.get('allow_terran'):
            effective_exclude.discard('terran')

        if effective_exclude & entry.boqwi_tags:
            # Special handling for fic places
            if section.get('include_fic_places') and 'place' in entry.tags and 'fic' in entry.tags:
                pass  # Allow fic places
            elif section.get('include_fic_names') and 'name' in entry.tags and 'fic' in entry.tags:
                pass  # Allow fic names
            else:
                continue

        # Check required tags
        if require_tags and not (require_tags <= entry.boqwi_tags):
            continue

        # Check excluded POS
        if entry.pos in exclude_pos:
            continue

        # Check name exclusion
        if section.get('exclude_names') and 'name' in entry.tags:
            if 'fic' not in entry.tags:  # Allow fictional names in base
                continue

        result.append(entry)

    return result


# =============================================================================
# LaTeX Formatting
# =============================================================================

def escape_latex(text: str) -> str:
    """Escape special LaTeX characters."""
    if not text:
        return ""
    # Don't escape already-escaped sequences or commands
    # This is a simplified version
    text = text.replace('&', '\\&')
    text = text.replace('%', '\\%')
    text = text.replace('$', '\\$')
    text = text.replace('#', '\\#')
    text = text.replace('_', '\\_')
    return text


def format_klingon_link(entry_name: str, pos: str, homophone: int = 0) -> str:
    """Format a Klingon word as a LaTeX link."""
    pos_abbr = pos if pos else "n"
    if homophone > 0:
        return f"\\klingonref[{pos_abbr}]{{{entry_name}}}[{homophone}]"
    return f"\\klingonref[{pos_abbr}]{{{entry_name}}}"


def render_entry_link(entry: Entry) -> str:
    """Render an entry as a LaTeX link."""
    return format_klingon_link(entry.entry_name, entry.pos, entry.homophone)


def format_inline_references(text: str) -> str:
    """Convert {entry:pos} references to LaTeX format."""
    if not text:
        return ""

    def replace_ref(match):
        ref = match.group(1)
        parts = ref.split(':')
        entry_name = parts[0]
        pos = parts[1] if len(parts) > 1 else "n"
        # Handle flags like nolink
        if len(parts) > 2 and 'nolink' in parts[2]:
            return f"\\klingon{{{entry_name}}}"
        return f"\\klingonref[{pos}]{{{entry_name}}}"

    return re.sub(r'\{([^}]+)\}', replace_ref, text)


def get_display_tags(entry: Entry) -> List[str]:
    """Get human-readable tags for display."""
    display = []

    tag_labels = {
        'slang': 'slang',
        'regional': 'regional',
        'archaic': 'archaic',
        'klcp1': 'beginner',
    }

    for tag, label in tag_labels.items():
        if tag in entry.boqwi_tags:
            display.append(label)

    return display


# =============================================================================
# Verb + Suffix Detection
# =============================================================================

def is_verb_plus_suffixes(entry: Entry) -> bool:
    """
    Check if an entry is a verb with suffixes that should be displayed
    under the root verb.
    """
    name = entry.entry_name

    # Nouns ending in certain suffixes are NOT verb+suffix
    if entry.pos == "n":
        if not any(name.endswith(s) for s in ["wI'", "ghach", "'a'", "Hom"]):
            return False

    # Adverbs ending in -logh are NOT verb+suffix
    if entry.pos == "adv" and name.endswith("logh"):
        return False

    # Special cases that look like verb+suffix but aren't
    special_cases = {
        "DeghwI'": False,
        "HISlaH": False,
        "jonwI'": False,
        "pupqa'": False,
        "roSbe'": False,
        "DItlhHa'": True,
        "ngapHa'": True,
    }
    if name in special_cases:
        return special_cases[name]

    # Check components if available
    if entry.components:
        # Parse components like "{bI-:v}, {Hegh:v}, {-jaj:v}"
        comp_parts = re.findall(r'\{([^}]+)\}', entry.components)
        if len(comp_parts) > 1:
            # Check if all parts after the first are suffixes
            if all(p.split(':')[0].startswith('-') for p in comp_parts[1:]):
                return True

    return False


# =============================================================================
# K-E Dictionary Generation
# =============================================================================

def render_ke_entry(entry: Entry, all_entries: Dict[str, Entry]) -> str:
    """Render a single K-E dictionary entry."""
    if entry.entry_name.startswith('-') or entry.entry_name == '0':
        return ""

    lines = []

    # Check if this should be commented out (verb+suffixes)
    prefix = "% " if is_verb_plus_suffixes(entry) else ""

    # Get tags for display
    tags = get_display_tags(entry)
    tags_str = f"\\textit{{({', '.join(tags)})}}" if tags else ""

    # Format definition
    definition = format_inline_references(entry.definition)

    # Add arrow for alt entries (references to other entries)
    if definition.startswith("\\klingonref[n]{") or definition.startswith("\\klingonref[v]{"):
        definition = definition[:15] + "\\color{black}{\\textrightarrow} " + definition[15:]
    elif definition.startswith("\\klingonref[excl]{"):
        definition = definition[:18] + "\\color{black}{\\textrightarrow} " + definition[18:]

    # Render the main entry
    rendered_link = render_entry_link(entry)
    pos_abbr = LOCALE["poses"].get(entry.pos, entry.pos)

    line = f"{prefix}\\entry{{{rendered_link}}}{{{pos_abbr}}}{{{tags_str}{definition}}}"

    # TODO: Add derived entries
    # For now, skip derived entries

    lines.append(line + "\n")

    return ''.join(lines)


def generate_ke_section(entries: List[Entry], section: dict) -> str:
    """Generate K-E dictionary section."""
    lines = []

    name = LOCALE[section["name"]]
    lines.append(f"\\subsection{{{name}}}\n")
    lines.append("\\begin{multicols}{2}\n")

    # Build lookup for all entries
    all_entries = {e.slug: e for e in entries}

    # Sort entries
    sorted_entries = sorted(entries, key=klingon_sort_key)

    for entry in sorted_entries:
        rendered = render_ke_entry(entry, all_entries)
        if rendered:
            lines.append(rendered)

    lines.append("\\end{multicols}\n")
    lines.append("\\newpage\n\n")

    return ''.join(lines)


# =============================================================================
# E-K Dictionary Generation
# =============================================================================

def permutate_definition(definition: str) -> List[str]:
    """
    Generate E-K permutations of a definition.
    This replicates the logic from book/generate-latex.py.
    """
    brackets_re = re.search(r"(.+)( \(.+\))$", definition)
    separator = ", "

    # Special case: {tlhoS} "almost, nearly, virtually, not quite; barely..."
    if definition.startswith("almost,"):
        positive, negative = definition.split("; ", 1)
        definition_list = positive.split(", ")
        return [separator.join([d] + definition_list[0:i] + definition_list[i+1:])
                for i, d in enumerate(definition_list)] + [negative]

    # Special case: entries with ";"
    elif definition.startswith("verb which ") or definition.startswith("travel with ") or definition.startswith("make a cracking"):
        definition_list = definition.split("; ")
        bracketed_text = ""
        separator = "; "

    # Special case: comma within brackets
    elif definition.startswith("cancel,") or definition.startswith("field (of land),") or definition.startswith("change (alteration)"):
        definition_list = definition.split(", ", 1)
        bracketed_text = ""

    elif definition.startswith("husk,"):
        definition_list = definition.split(", ", 3)
        bracketed_text = ""

    # Guard cases - don't split
    elif (definition.startswith("bird ") or definition.startswith("a bird ") or
          definition.startswith("a creature ") or definition.startswith("sink for ")):
        return [definition]

    elif (definition.startswith("have a tattoo") or definition.startswith("be positively charged") or
          definition.startswith("be negatively charged")):
        return [definition]

    elif (definition.startswith("good news,") or definition.startswith("expletive,") or
          definition.startswith("Stop,") or definition.startswith("uh,")):
        return [definition]

    elif definition.startswith("end (of stick,"):
        return [definition]

    # Strip "etc." suffix
    elif definition.startswith("road,") or definition.startswith("be amplified,"):
        definition_list = definition[:-6].split(", ")
        bracketed_text = ", etc."

    # Bracket applies to just last item
    elif (definition.startswith("hinge,") or definition.startswith("regard as") or
          definition.startswith("use, ") or definition.startswith("battle array, ") or
          definition.startswith("robot, ")):
        definition_list = definition.split(", ")
        bracketed_text = ""

    elif brackets_re and "(" not in brackets_re.group(1):
        definition_list = brackets_re.group(1).split(", ")
        bracketed_text = brackets_re.group(2) if brackets_re.group(2) else ""

    else:
        definition_list = definition.split(", ")
        bracketed_text = ""

    # Deduplication for 2-part definitions
    if len(definition_list) == 2:
        d0, d1 = definition_list[0], definition_list[1]

        if (not d0.startswith("be ") and not d0.startswith("under") and
            not d0.startswith("area ") and not d0.startswith("dis") and
            len(d0) >= 3 and len(d1) >= 3 and d0[:3] == d1[:3]):
            return [separator.join(definition_list) + bracketed_text]

        elif (d0.startswith("be ") and not d0.startswith("be in a ") and
              not d0.startswith("be the ") and len(d0) >= 7 and len(d1) >= 7 and
              d0[:7] == d1[:7]):
            return [separator.join(definition_list) + bracketed_text]

        elif d0 in ["be cooperative", "die"]:
            definition_list = [d0 + ", " + d1]

    # Multi-part grouping
    elif len(definition_list) == 3:
        if definition_list[0] in ["arts", "just now", "pane", "demon", "package", "put on (clothes"]:
            definition_list = [definition_list[0] + ", " + definition_list[1], definition_list[2]]
        elif definition_list[0] in ["confused prisoner", "food server", "gamble", "lurk",
                                     "have personality", "idol", "dripstone"]:
            definition_list = [definition_list[0], definition_list[1] + ", " + definition_list[2]]

    elif len(definition_list) == 4:
        if definition_list[0] == "lose":
            definition_list = [definition_list[0] + ", " + definition_list[3],
                             definition_list[1], definition_list[2]]
        elif definition_list[0] == "somebody":
            definition_list = [definition_list[0] + ", " + definition_list[1],
                             definition_list[2] + ", " + definition_list[3]]
        elif definition_list[0] == "everyone":
            definition_list = [definition_list[0] + ", " + definition_list[2],
                             definition_list[1], definition_list[3]]

    elif len(definition_list) == 5:
        if definition_list[0] == "rank (military":
            definition_list = [definition_list[0] + ", " + definition_list[1],
                             definition_list[2], definition_list[3]]
        elif definition_list[0] == "adapt to":
            definition_list = [definition_list[0] + ", " + definition_list[2],
                             definition_list[1], definition_list[3], definition_list[4]]
        elif definition_list[0] == "teen":
            definition_list = [definition_list[0] + ", " + definition_list[1],
                             definition_list[2],
                             definition_list[3] + ", " + definition_list[4]]

    # Generate permutations
    permutations = [separator.join([d] + definition_list[0:i] + definition_list[i+1:]) + bracketed_text
                   for i, d in enumerate(definition_list)]
    permutations[0] = definition
    return permutations


def get_ek_sort_key(definition: str) -> str:
    """
    Get the sort key for an E-K entry.
    This replicates the logic from book/generate-latex.py.
    """
    key = re.sub(r'^\((.+)\) ', '', definition)  # Remove "(belt) buckle" -> "buckle"
    key = re.sub(r'[()]', ' ', key)  # Sort "key (brackets)" after "key non-brackets"
    key = re.sub(r'["{}()\[\]\.,\']', '', key)
    key = re.sub(r'[-/]', ' ', key)

    # Strip stop words
    if key.startswith("be "):
        key = key[3:]
    if key.startswith("have ") and not key.startswith("have possess"):
        key = key[5:]
    if key.startswith("in "):
        key = key[3:]
    if key.startswith("a "):
        key = key[2:]
    if key.startswith("an "):
        key = key[3:]
    if key.startswith("the ") or key.startswith("The "):
        key = key[4:]
    elif key.startswith("use the "):
        key = key[8:]
    elif key.startswith("area ") and not key.startswith("area of") and not key.startswith("area district"):
        key = key[5:]
    elif key.startswith("absolute "):
        key = key[9:]
    elif key.startswith("absolutely "):
        key = key[11:]
    elif key.startswith("act of "):
        key = key[7:]
    elif key.startswith("type of "):
        key = key[8:]
    elif key.startswith("kind of "):
        key = key[8:]
    elif key.startswith("125 "):
        key = key[4:]
    elif key.startswith("go to"):
        key = "go"
    elif key.startswith("high in"):
        key = "high"
    elif key.startswith("make a full"):
        key = "withdrawal"
    elif key.startswith("make a cracking"):
        key = "cracking"
    elif key.startswith("have sex"):
        key = "sex"
    elif key.startswith("perform surgery"):
        key = "surgery"
    elif key.startswith("animal types"):
        key = "animal n"
    elif key.startswith("bird kinds"):
        key = "bird n"

    return key[:15].ljust(15)


def is_bird_definition(definition: str) -> bool:
    """Check if a definition describes a type of bird."""
    if (definition.startswith("a bird ") or definition.startswith("a kind of bird") or
        definition.startswith("bird with ") or definition.startswith("bird capable ")):
        return True
    if " bird " in definition and " animal " not in definition:
        return True
    if definition.startswith("a ") and definition.endswith(" bird"):
        return True
    return False


def render_ek_entry(definition: str, entries: List[Entry], page_mark: str) -> str:
    """Render an E-K dictionary entry."""
    sort_key = get_ek_sort_key(definition)

    line = f"\\reverseentryhead[{sort_key.lower()}]{{{definition}}}{{{page_mark}}} "

    items = []
    for entry in entries:
        rendered_link = render_entry_link(entry)
        tags = get_display_tags(entry)
        tags_str = f" \\textit{{({', '.join(tags)})}} " if tags else ""
        pos_abbr = LOCALE["poses"].get(entry.pos, entry.pos)
        items.append(f"\\reverseentryitem{{{pos_abbr}{tags_str}}}{{{rendered_link}}}")

    line += ", ".join(items) + "\n"
    return line


def generate_ek_section(entries: List[Entry], section: dict) -> str:
    """Generate E-K dictionary section."""
    lines = []

    name = LOCALE[section["name"]]
    if name == "Klingon-English":
        name = "English-Klingon"

    lines.append(f"\\subsection{{{name}}}\n")
    lines.append("\\begin{multicols}{2}\n\n")

    # Group entries by definition
    definition_to_entries = defaultdict(list)
    for entry in entries:
        if entry.entry_name.startswith('-') or entry.entry_name == '0':
            continue

        definition = entry.definition
        if not definition or definition.startswith("\\klingonref"):
            continue

        # Special groupings
        if definition == "council, assembly":
            definition_to_entries["assembly, council"].append(entry)
        elif "type of animal" in definition:
            definition_to_entries["type of animal"].append(entry)
        elif is_bird_definition(definition):
            definition_to_entries["a kind of bird"].append(entry)
        else:
            definition_to_entries[definition].append(entry)

    # Generate reverse entries
    reverse_entries = []
    for definition, same_def_entries in definition_to_entries.items():
        # Skip letters
        if definition.startswith("the consonant ") or definition.startswith("the vowel "):
            continue

        # Handle animal/bird groupings
        is_type_of_animal = definition == "type of animal"
        is_kind_of_bird = definition == "a kind of bird"

        if is_type_of_animal:
            display_def = "animal (types of animals):"
        elif is_kind_of_bird:
            display_def = "bird (kinds of birds):"
        else:
            display_def = definition

        for perm in permutate_definition(display_def):
            sort_key = get_ek_sort_key(perm)
            page_mark = sort_key.split()[0].removesuffix(":")
            reverse_entries.append((sort_key.lower(), render_ek_entry(perm, same_def_entries, page_mark)))

    # Sort and output
    reverse_entries.sort(key=lambda x: x[0])
    for _, entry_text in reverse_entries:
        lines.append(entry_text)

    lines.append("\\end{multicols}\n")
    lines.append("\\newpage\n\n")

    return ''.join(lines)


# =============================================================================
# Main
# =============================================================================

def main():
    # Get data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent

    print(f"% LaTeX Dictionary Generator", file=sys.stderr)
    print(f"% Loading entries from {data_dir}/entries/...", file=sys.stderr)

    # Load all entries
    entries = load_entries(data_dir)
    print(f"% Loaded {len(entries)} entries", file=sys.stderr)

    # Generate each section
    for section in SECTIONS:
        section_entries = filter_entries(entries, section)
        print(f"% Section {section['name']}: {len(section_entries)} entries", file=sys.stderr)

        # Generate K-E
        ke_output = generate_ke_section(section_entries, section)
        print(ke_output)

        # Generate E-K
        ek_output = generate_ek_section(section_entries, section)
        print(ek_output)


if __name__ == '__main__':
    main()
