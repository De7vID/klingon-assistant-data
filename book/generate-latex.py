#!/usr/bin/env python3

import dictionary
import re

SELECTED_LOCALE = "en"

LOCALES = {
    "en": {
        "base": "Klingon-English",
        "loanwords": "Borrowed Terran concepts",
        "ficnames": "Proper nouns",
        "names": "Names of humans",
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
}

LOCALE = LOCALES[SELECTED_LOCALE]

SECTIONS = [
    {
        # Includes fictional places and people, excludes real-life places and people.
        "name": "base",
        "query": "NOT pos:nodict AND NOT pos:extcan AND NOT pos:hyp AND NOT pos:sen AND NOT pos:terran AND(NOT pos:place OR pos:fic) AND (NOT pos:name OR pos:fic)",
        # "groupby": "first letter",
        "sort": True,
    },
    # {
    #     "name": "loanwords",
    #     "query": "NOT pos:nodict AND NOT pos:extcan AND NOT pos:hyp AND NOT pos:sen AND pos:terran AND(NOT pos:place OR pos:fic) AND (NOT pos:name OR pos:fic)",
    #     # "groupby": "first letter",
    #     "sort": True,
    # },
    # {
    #     "name": "ficnames",
    #     "query": "NOT pos:nodict AND NOT pos:extcan AND NOT pos:hyp AND NOT pos:sen AND pos:name,fic",
    #     "sort": False,
    # },
    # {
    #     "name": "names",
    #     "query": "NOT pos:nodict AND NOT pos:extcan AND NOT pos:hyp AND NOT pos:sen AND pos:name AND NOT pos:fic",
    #     "sort": False,
    # },
    # {
    #     "name": "ficplaces",
    #     "query": "NOT pos:nodict AND NOT pos:extcan AND NOT pos:hyp AND NOT pos:sen AND pos:place,fic",
    #     "sort": False,
    # },
    # {
    #     "name": "places",
    #     "query": "NOT pos:nodict AND NOT pos:extcan AND NOT pos:hyp AND NOT pos:sen AND pos:place AND NOT pos:fic",
    #     "sort": False,
    # }
]

LETTERS = ["a", "b", "ch", "D", "e", "gh", "H", "I", "j", "l", "m", "n", "ng", "o", "p", "q", "Q", "r", "S", "t", "tlh", "u", "v", "w", "y", "'"]
def make_query(query: str, sort: bool):
    entries = dictionary.dictionary_query(query=query, link_format="latex", lang=SELECTED_LOCALE)
    if sort:
        entries.sort(key=lambda x: (tuple(map(LETTERS.index, x["graphemes"])), x["simple_pos"], x.get("homonym", 0)))

    return entries

def components_are_verb_plus_suffixes(components):
    return len(components) > 1 and all(component.startswith("-") for component in components[1:])

def is_verb_plus_suffixes(entry):
    # Special handling for certain words that look like verb + suffixes, but aren't.
    match entry["name"]:
        case "DaSpu'":
            return False
        case "DeghwI'":
            return False
        case "DISjaj":
            return False
        case "jolpa'":
            return False
        case "muchpa'":
            return False
        case "pupqa'":
            return False
        case "Qulpa'":
            return False
        case "vutpa'":
            return False
    return any(components_are_verb_plus_suffixes(m) for m in entry["morphemes"])

def permutate_definition(definition):
    # Definitions might most generally be of the form "A, B, C, D (E)".
    brackets_re = re.search(r"(.+)( \(.*\))$", definition)
    if brackets_re:
        # This misses a few definitions separated by ";". Must be manually fixed.
        definition_list = brackets_re.group(1).split(", ")
        bracketed_text = brackets_re.group(2) if brackets_re.group(2) else ""
    else:
        definition_list = definition.split(", ")
        bracketed_text = ""

    if len(definition_list) == 2 and not definition_list[0].startswith("be ") and definition_list[0][:3] == definition_list[1][:3]:
        # "actor, actress", "abbess, abbot", and similar pairs. False positives must be fixed by hand.
        return [", ".join(definition_list) + bracketed_text]

    return [", ".join([d] + definition_list[0:i] + definition_list[i+1:]) + bracketed_text for i,d in enumerate(definition_list)]

def get_sort_key(definition):
    key = re.sub('["{}()\[\]\.,]', '', definition)
    key = re.sub('[-/]', ' ', key)

    # Strip stop words from key. Note that they're not mutually exclusive, e.g., "be in the X" is possible.
    if key.startswith("be "):
        # Sort "be X" verbs under "X".
        key = key[3:]

    if key.startswith("in "):
        key = key[3:]

    if key.startswith("a "):
        key = key[2:]

    if key.startswith("an "):
        key = key[3:]

    if key.startswith("the ") or key.startswith("The "):
        key = key[4:]

    if key.startswith("area ") and not key.startswith("area district"):
        key = key[5:]

    # Sort "type of X" under "X".
    if key.startswith("type of "):
        key = key[8:]

    # "1.25 light years..."
    if key.startswith("125 "):
        key = key[4:]

    return key[:15].ljust(15)

def render_reverse_entry(entry):
    if entry["name"].startswith("-") or entry["name"] == "0":
        # Skip prefixes.
        return

    if entry["definition"].startswith("the consonant ") or entry["definition"].startswith("the vowel "):
        # Skip the "letters".
        return

    if entry["definition"].startswith("\\klingonref"):
        # Skip "alt" entries which are just defined as other entries.
        return

    if entry["tags"]:
        tags = "\\textit{(" + ", ".join(entry["tags"]) + ")} "
    else:
        tags = ""

    for d in permutate_definition(entry["definition"]):
        print("\\reverseentry[%s]{%s}{%s}{%s%s}\n" % (get_sort_key(d), d, LOCALE["poses"][entry["simple_pos"]], tags, entry["rendered_link"]))


def render_entry(entry):
    if entry["name"].startswith("-") or entry["name"] == "0":
        # Skip prefixes.
        return

    if is_verb_plus_suffixes(entry):
        # Comment out verbs with suffixes, which will display under the root verb.
        print("% ", end="")

    if entry["tags"]:
        tags = "\\textit{(" + ", ".join(entry["tags"]) + ")} "
    else:
        tags = ""

    print("\\entry{%s}{%s}{%s%s" % (entry["rendered_link"], LOCALE["poses"][entry["simple_pos"]], tags, entry["definition"]), end="")
    for deriv in entry.get("derived", []):
        if deriv["tags"]:
            deriv_tags = "\\textit{(" + ", ".join(deriv["tags"]) + ")} "
        else:
            deriv_tags = ""

        if set(deriv["boqwi_tags"]) & {"nodict", "extcan", "hyp"}: # exclude these from derived entries as well
            continue

        if deriv["name"].startswith(entry["name"]):
            if is_verb_plus_suffixes(deriv):
                # Mark derived subentries. Other derivations are their own entries.
                print("{\\derivsubentry{%s}{%s}{%s%s}}" % (deriv["rendered_link"], LOCALE["poses"][deriv["simple_pos"]], deriv_tags, deriv["definition"]), end="")
            continue

        print("{\\deriv{%s}{%s}{%s%s}}" % (deriv["rendered_link"], LOCALE["poses"][deriv["simple_pos"]], deriv_tags, deriv["definition"]), end="")

    print("}\n")

for section in SECTIONS:
    name = LOCALE[section["name"]]
    entries = make_query(section["query"], section["sort"])
    print("\\subsection{%s}" % name)
    if section.get("groupby") == "first letter":
        for letter in LETTERS:
            letter_entries = list(filter(lambda e: e["graphemes"] and e["graphemes"][0] == letter, entries))
            if letter_entries:
                print("\\subsubsection{%s}" % letter)
                print("\\begin{multicols}{2}")
                for entry in letter_entries:
                    render_entry(entry)

                print("\\end{multicols}\n")
    else:
        print("\\begin{multicols}{2}")
        for entry in entries:
            render_entry(entry)

        print("\\end{multicols}\n")

    print("\\newpage\n\n");

print("% TODO: Sort the lists below.\n\n");

for section in SECTIONS:
    name = LOCALE[section["name"]]
    if name == "Klingon-English":
        name = "English-Klingon"
    entries = make_query(section["query"], section["sort"])
    print("\\subsection{%s}" % name)
    print("\\begin{multicols}{2}")
    for entry in entries:
        render_reverse_entry(entry)
    print("\\end{multicols}\n")

    # print("\\newpage\n\n");
