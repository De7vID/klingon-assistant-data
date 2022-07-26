#!/usr/bin/env python3

import dictionary

SELECTED_LOCALE = "en"

LOCALES = {
    "en": {
        "base": "Base dictionary",
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
        "name": "base",
        "query": "NOT pos:nodict AND NOT pos:extcan AND NOT pos:hyp AND NOT pos:sen AND NOT pos:place AND NOT pos:name",
        "groupby": "first letter",
        "sort": True,
    },
    {
        "name": "ficnames",
        "query": "NOT pos:nodict AND NOT pos:extcan AND NOT pos:hyp AND NOT pos:sen AND pos:name,fic",
        "sort": False,
    },
    {
        "name": "names",
        "query": "NOT pos:nodict AND NOT pos:extcan AND NOT pos:hyp AND NOT pos:sen AND pos:name AND NOT pos:fic",
        "sort": False,
    },
    {
        "name": "ficplaces",
        "query": "NOT pos:nodict AND NOT pos:extcan AND NOT pos:hyp AND NOT pos:sen AND pos:place,fic",
        "sort": False,
    },
    {
        "name": "places",
        "query": "NOT pos:nodict AND NOT pos:extcan AND NOT pos:hyp AND NOT pos:sen AND pos:place AND NOT pos:fic",
        "sort": False,
    }
]

LETTERS = ["a", "b", "ch", "D", "e", "gh", "H", "I", "j", "l", "m", "n", "ng", "o", "p", "q", "Q", "r", "S", "t", "tlh", "u", "v", "w", "y", "'"]
def make_query(query: str, sort: bool):
    entries = dictionary.dictionary_query(query=query, link_format="latex", lang=SELECTED_LOCALE)
    if sort:
        entries.sort(key=lambda x: (tuple(map(LETTERS.index, x["graphemes"])), x["simple_pos"], x.get("homonym", 0)))

    return entries

def render_entry(entry):
    if entry["tags"]:
        tags = "\\textit{(" + ", ".join(entry["tags"]) + ")} "
    else:
        tags = ""

    print("\\entry{%s}{%s}{%s%s" % (entry["rendered_link"], LOCALE["poses"][entry["simple_pos"]], tags, entry["definition"]), end="")
    for deriv in entry.get("derived", []):
        if set(deriv["boqwi_tags"]) & {"nodict", "extcan", "hyp"}: # exclude these from derived entries as well
            continue

        if deriv["name"].startswith(entry["name"]):
            continue

        print("\\deriv{%s}{%s}{%s}" % (deriv["rendered_link"], LOCALE["poses"][deriv["simple_pos"]], deriv["definition"]), end="")

    print("}\n")

for section in SECTIONS:
    name = LOCALE[section["name"]]
    entries = make_query(section["query"], section["sort"])
    print("\\section{%s}" % name)
    if section.get("groupby") == "first letter":
        for letter in LETTERS:
            letter_entries = list(filter(lambda e: e["graphemes"] and e["graphemes"][0] == letter, entries))
            if letter_entries:
                print("\\subsection{%s}" % letter)
                print("\\begin{multicols}{2}")
                for entry in letter_entries:
                    render_entry(entry)

                print("\\end{multicols}")
    else:
        print("\\begin{multicols}{2}")
        for entry in entries:
            render_entry(entry)

        print("\\end{multicols}")
