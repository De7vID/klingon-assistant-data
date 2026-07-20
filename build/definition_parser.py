#!/usr/bin/env python3
"""
Definition Parser: Parse definition strings into structured parts for E-K generation.

Handles:
- Comma-separated parts: "flap, flutter, wave"
- Semicolon-separated alternatives: "cancel; abort"
- Global parentheticals: "fire, energize (e.g., thrusters)"
- Part-specific parentheticals: "field (of land), park (e.g., recreational)"
- Internal commas in parentheticals: "core (e.g., of apple, planet, or star)"
- Be-verb prefix stripping for sort keys
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class DefinitionPart:
    """A single part of a definition."""
    text: str
    sort_keyword: Optional[str] = None  # Explicit override for E-K sorting

    def get_sort_key(self, is_be_verb: bool = False) -> str:
        """Get the sort key for E-K generation."""
        if self.sort_keyword:
            return self.sort_keyword.lower()

        text = self.text.strip()

        # Strip parentheticals for sort key extraction
        text_no_parens = re.sub(r'\s*\([^)]*\)\s*', ' ', text).strip()

        # For be-verbs, strip "be " prefix
        if is_be_verb and text_no_parens.lower().startswith('be '):
            text_no_parens = text_no_parens[3:]

        # Get first word as sort key
        words = text_no_parens.split()
        if words:
            return words[0].lower()
        return text.lower()


@dataclass
class ParsedDefinition:
    """Parsed definition with structured parts."""
    parts: List[DefinitionPart]
    global_parenthetical: Optional[str] = None
    raw_text: str = ""  # Original text for backward compatibility
    no_permute: bool = False  # Guard flag: don't generate E-K permutations
    dedup: bool = False  # Deduplication: don't generate nearby duplicate E-K entries
    etc_suffix: bool = False  # Definition ends with ", etc."

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML output."""
        result = {}
        if len(self.parts) == 1 and not self.global_parenthetical and not self.no_permute:
            # Simple case: just store as string
            result['text'] = self.raw_text
        else:
            if len(self.parts) > 1 or self.global_parenthetical:
                result['text'] = self.raw_text
                result['parts'] = [{'text': p.text} for p in self.parts]
                if any(p.sort_keyword for p in self.parts):
                    for i, p in enumerate(self.parts):
                        if p.sort_keyword:
                            result['parts'][i]['sort_keyword'] = p.sort_keyword
                if self.global_parenthetical:
                    result['global_parenthetical'] = self.global_parenthetical
            else:
                result['text'] = self.raw_text
            if self.no_permute:
                result['no_permute'] = True
            if self.dedup:
                result['dedup'] = True
            if self.etc_suffix:
                result['etc_suffix'] = True
        return result


def tokenize_with_parens(text: str) -> List[Tuple[str, bool]]:
    """
    Tokenize text, tracking whether each token is inside parentheses.
    Returns list of (token, is_inside_parens) tuples.
    """
    tokens = []
    current = ""
    depth = 0

    for char in text:
        if char == '(':
            if current and depth == 0:
                tokens.append((current, False))
                current = ""
            current += char
            depth += 1
        elif char == ')':
            current += char
            depth -= 1
            if depth == 0:
                tokens.append((current, True))
                current = ""
        else:
            current += char

    if current:
        tokens.append((current, depth > 0))

    return tokens


def split_on_delimiters(text: str, delimiters: str = ',;') -> List[str]:
    """
    Split text on delimiters, but not inside parentheses.
    """
    parts = []
    current = ""
    depth = 0

    for char in text:
        if char == '(':
            depth += 1
            current += char
        elif char == ')':
            depth -= 1
            current += char
        elif char in delimiters and depth == 0:
            if current.strip():
                parts.append(current.strip())
            current = ""
        else:
            current += char

    if current.strip():
        parts.append(current.strip())

    return parts


def looks_like_item_list(parts: List[str]) -> bool:
    """
    Detect if parts look like items in a list rather than alternative definitions.

    "sink for cleaning hands, face, food, etc." -> True (items in a list)
    "flap, flutter, wave" -> False (alternative definitions)
    """
    if len(parts) <= 1:
        return False

    # If most parts are very short single words, might be a list
    short_parts = sum(1 for p in parts if len(p.split()) == 1 and len(p) < 10)

    # Check first part for patterns suggesting a list follows
    first = parts[0].lower()

    # Pattern: "X for Y" where Y is followed by list items
    list_prepositions = ['for', 'of', 'with', 'about', 'including', 'such as', 'like']
    for prep in list_prepositions:
        if f' {prep} ' in first:
            # First part contains a preposition, suggesting list might follow
            if short_parts >= len(parts) - 1:
                return True

    # Pattern: "etc." in parts suggests it's an enumeration
    if any('etc' in p.lower() for p in parts):
        return True

    return False


def extract_trailing_parenthetical(text: str) -> Tuple[str, Optional[str]]:
    """
    Extract trailing parenthetical from text.
    Returns (text_without_parens, parenthetical_content) or (text, None).
    """
    text = text.strip()
    if not text.endswith(')'):
        return text, None

    # Find matching opening paren
    depth = 0
    for i in range(len(text) - 1, -1, -1):
        if text[i] == ')':
            depth += 1
        elif text[i] == '(':
            depth -= 1
            if depth == 0:
                # Found the matching paren
                before = text[:i].strip()
                inside = text[i+1:-1].strip()
                return before, inside

    return text, None


def is_global_parenthetical(parts: List[str], last_paren: str) -> bool:
    """
    Heuristic to determine if a trailing parenthetical applies to all parts.

    Global: "fire, energize (e.g., thrusters)" - applies to both fire and energize
    Global: "structure, organization (the way things fit together...)" - applies to both
    Part-specific: "field (of land), park (e.g., recreational)" - each part has its own

    The key insight: if only the LAST part has a parenthetical, and the last part's
    base word (without parenthetical) is a simple word, it's likely global.
    But if other parts also have parentheticals, each is part-specific.
    """
    if not last_paren:
        return False

    # If there's only one part, it's not really "global"
    if len(parts) <= 1:
        return False

    # Check if any other part has a parenthetical
    for i, part in enumerate(parts[:-1]):
        if '(' in part and ')' in part:
            # Other parts have parentheticals, so last one is also part-specific
            return False

    # Extract the base word from the last part (without the parenthetical)
    base_last, _ = extract_trailing_parenthetical(parts[-1])
    base_last = base_last.strip()

    # If the base word is a simple single word (no spaces), it's likely that
    # the parenthetical is clarifying all parts, not just that word
    # Examples:
    #   "fire, energize (e.g., thrusters)" -> base_last = "energize" (simple)
    #   "structure, organization (the way things...)" -> base_last = "organization" (simple)
    if base_last and ' ' not in base_last:
        return True

    # Also check for explicit global indicators
    global_indicators = [
        'e.g.,',
        'i.e.,',
        'used in',
        'referring to',
        'for example',
        'in math',
        'in physics',
        'astronomy',
        'economics',
        'trigonometry',
        'general term',
        'verb type',
    ]

    last_paren_lower = last_paren.lower()
    for indicator in global_indicators:
        if indicator in last_paren_lower:
            return True

    return False


def is_guard_case(text: str) -> bool:
    """
    Check if a definition is a guard case that should NOT be split into parts.

    Guard cases include:
    - Bird/creature descriptions with internal commas
    - Exclamations/interjections
    - Phrases with internal structure (enumerations)
    - Definitions that would produce redundant permutations
    """
    lower = text.lower()

    # Bird/creature descriptions - commas are part of the description
    if any(lower.startswith(p) for p in [
        'bird ', 'a bird ', 'a creature ', 'bird with ', 'bird capable ',
        'a kind of bird'
    ]):
        return True

    # Sink/cleaning descriptions - "hands, face, food" is an enumeration
    if lower.startswith('sink for '):
        return True

    # Exclamations/interjections - commas are part of the expression
    if any(lower.startswith(p) for p in [
        'good news,', 'expletive,', 'stop,', 'uh,', 'well,'
    ]):
        return True

    # Definitions with internal commas in brackets that would break parsing
    if any(lower.startswith(p) for p in [
        'end (of stick,', 'end (of rope,', 'end (of handle,'
    ]):
        return True

    # Definitions that would generate redundant "have X, be X" entries
    if any(lower.startswith(p) for p in [
        'have a tattoo', 'be positively charged', 'be negatively charged'
    ]):
        return True

    return False


def should_dedup(parts: List[str], is_be_verb: bool = False) -> bool:
    """
    Check if a two-part definition should be deduplicated to prevent
    nearby duplicate E-K entries.

    Rules:
    - Non-be-verbs: first 3 characters match (actor/actress, abbess/abbot)
    - Be-verbs: first 7 characters match (be allergic/be allergic to)
    - Specific word pairs that are known to need dedup
    """
    if len(parts) != 2:
        return False

    p0, p1 = parts[0].lower().strip(), parts[1].lower().strip()

    # Specific word pairs that need deduplication
    dedup_pairs = [
        ('be cooperative', 'cooperate'),
        ('die', 'dice'),
    ]
    for pair in dedup_pairs:
        if p0.startswith(pair[0]) or p0.startswith(pair[1]):
            return True

    # Check for similar prefixes
    if is_be_verb or p0.startswith('be '):
        # Be-verb: check first 7 chars
        if len(p0) >= 7 and len(p1) >= 7 and p0[:7] == p1[:7]:
            return True
    else:
        # Non-be-verb: check first 3 chars (but not for "be", "in", "a", etc.)
        skip_prefixes = ['be ', 'in ', 'a ', 'an ', 'the ', 'under', 'area ', 'dis']
        if not any(p0.startswith(sp) for sp in skip_prefixes):
            if len(p0) >= 3 and len(p1) >= 3 and p0[:3] == p1[:3]:
                return True

    return False


def parse_definition(text: str, pos_subtype: Optional[str] = None) -> ParsedDefinition:
    """
    Parse a definition string into structured parts.

    Args:
        text: The definition string
        pos_subtype: Part of speech subtype (e.g., 'is' for be-verbs)

    Returns:
        ParsedDefinition with structured parts
    """
    if not text or not text.strip():
        return ParsedDefinition(parts=[], raw_text=text or "")

    text = text.strip()
    is_be_verb = pos_subtype == 'is'

    # Check for etc. suffix early (before guard case return)
    etc_suffix = text.rstrip().endswith(', etc.') or text.rstrip().endswith(' etc.')

    # Check for guard cases first (definitions that should NOT be split)
    if is_guard_case(text):
        return ParsedDefinition(
            parts=[DefinitionPart(text=text)],
            raw_text=text,
            no_permute=True,
            etc_suffix=etc_suffix
        )

    # Handle special cases

    # Sentences (contain .)
    if text.endswith('.') or text.endswith('!') or text.endswith('?'):
        if not any(c in text for c in ',;'):
            # Full sentence, treat as single part
            return ParsedDefinition(
                parts=[DefinitionPart(text=text)],
                raw_text=text
            )

    # Entry references
    if text.startswith('{') and text.endswith('}'):
        return ParsedDefinition(
            parts=[DefinitionPart(text=text)],
            raw_text=text
        )

    # First split on semicolons (strong separator for alternative phrasings)
    semicolon_parts = split_on_delimiters(text, ';')

    # Then consider splitting each part on commas
    raw_parts = []
    for sp in semicolon_parts:
        comma_parts = split_on_delimiters(sp, ',')
        if len(comma_parts) <= 1:
            raw_parts.append(sp)
        elif looks_like_item_list(comma_parts):
            # Commas are part of an enumeration, not separators
            raw_parts.append(sp)
        elif len(semicolon_parts) > 1:
            # If we have semicolons, treat each semicolon-section as a unit
            # (commas within are probably internal)
            raw_parts.append(sp)
        else:
            # No semicolons, so commas are the separators
            raw_parts.extend(comma_parts)

    if len(raw_parts) == 0:
        return ParsedDefinition(parts=[], raw_text=text)

    if len(raw_parts) == 1:
        # Single part, no splitting needed
        return ParsedDefinition(
            parts=[DefinitionPart(text=raw_parts[0])],
            raw_text=text
        )

    # Check if the last part ends with a parenthetical that might be global
    last_part = raw_parts[-1]
    base_last, paren_content = extract_trailing_parenthetical(last_part)

    global_paren = None
    if paren_content and is_global_parenthetical(raw_parts, paren_content):
        # This parenthetical applies to all parts
        global_paren = paren_content
        # Update last part to not include the parenthetical
        raw_parts[-1] = base_last

    # Create DefinitionPart objects
    parts = [DefinitionPart(text=p) for p in raw_parts if p.strip()]

    # Handle special keywords for E-K sorting
    # Check for parts that need explicit sort keywords
    is_be_verb = pos_subtype == 'is'

    # Detect parts with internal commas or semicolons that need keywords
    for i, part in enumerate(parts):
        # If part contains "travel on a mission", keyword should be "mission"
        if 'travel on a mission' in part.text.lower():
            parts[i].sort_keyword = 'mission'

    return ParsedDefinition(
        parts=parts,
        global_parenthetical=global_paren,
        raw_text=text,
        etc_suffix=etc_suffix,
        dedup=should_dedup([p.text for p in parts], is_be_verb)
    )


def generate_ek_entries(parsed: ParsedDefinition, is_be_verb: bool = False) -> List[Tuple[str, str]]:
    """
    Generate E-K (English-to-Klingon) lookup entries.

    Returns list of (sort_key, display_text) tuples.
    """
    if not parsed.parts:
        return []

    if len(parsed.parts) == 1:
        part = parsed.parts[0]
        sort_key = part.get_sort_key(is_be_verb)
        display = parsed.raw_text
        return [(sort_key, display)]

    entries = []
    seen_keys = set()

    for i, part in enumerate(parsed.parts):
        sort_key = part.get_sort_key(is_be_verb)

        # Skip duplicate keys
        if sort_key in seen_keys:
            continue
        seen_keys.add(sort_key)

        # Build permuted display: this part first, then others
        other_parts = [p.text for j, p in enumerate(parsed.parts) if j != i]
        display_parts = [part.text] + other_parts
        display = ', '.join(display_parts)

        # Add global parenthetical
        if parsed.global_parenthetical:
            display += f' ({parsed.global_parenthetical})'

        entries.append((sort_key, display))

    return entries


# Test cases
if __name__ == '__main__':
    test_cases = [
        # Basic splitting
        ("flap, flutter, wave", None),
        ("fire, energize (e.g., thrusters)", None),
        ("field (of land), park (e.g., recreational)", None),
        ("shoot (torpedo, rocket, missile)", None),
        ("be hostile, be malicious, be unfriendly", "is"),
        ("travel with a purpose, for a specific reason; travel on a mission", None),
        ("cousin (cross-cousin; child of {'IrneH:n} or {'e'mam:n})", None),
        ("sink for cleaning hands, face, food, etc.", None),
        ("structure, organization (the way things fit together; the arrangement of the parts of something bigger)", None),
        # Guard cases - should NOT be split
        ("bird capable of mimicking speech", None),
        ("a creature that is never still, that moves around a lot", None),
        ("sink for cleaning hands, face, food, etc.", None),
        ("good news, it's a good thing that...", None),
        ("expletive, epithet", None),
        # Deduplication cases
        ("actor, actress", None),
        ("abbess, abbot", None),
        ("be allergic, be allergic to", "is"),
        ("be cooperative, cooperate", "is"),
    ]

    for text, pos_subtype in test_cases:
        print(f"\n{'='*60}")
        print(f"Input: {text}")
        print(f"POS subtype: {pos_subtype}")

        parsed = parse_definition(text, pos_subtype)
        print(f"Parts: {[p.text for p in parsed.parts]}")
        print(f"Global paren: {parsed.global_parenthetical}")
        print(f"Flags: no_permute={parsed.no_permute}, dedup={parsed.dedup}, etc_suffix={parsed.etc_suffix}")

        entries = generate_ek_entries(parsed, is_be_verb=(pos_subtype == 'is'))
        print("E-K entries:")
        for key, display in entries:
            print(f"  {key}: {display}")
