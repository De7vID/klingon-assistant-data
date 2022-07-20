#!/usr/bin/env python3

import json
import logging
import os
import re
import subprocess
import sys
from typing import Collection, DefaultDict, Dict, Callable, Any, List, Literal, Set

import yajwiz
from yajwiz import BoqwizEntry

import locales

logger = logging.getLogger("dictionary")

script_path = os.path.abspath(os.path.dirname(__file__))
cmd = subprocess.run([script_path + "/../xml2json.py"], capture_output=True)
json_string = cmd.stdout.decode()
dictionary = yajwiz.boqwiz.BoqwizDictionary.from_json(json.loads(json_string))

derived_index = DefaultDict[str, List[BoqwizEntry]](list)

def make_derived_index():
    global derived_index
    for entry in dictionary.entries.values():
        if "sen" in entry.tags:
            continue

        for component in get_links(entry.components or ""):
            derived_index[component].append(entry)
            if component.count(":") == 1:
                derived_index[component + ":1"].append(entry)


QUERY_OPERATORS: Dict[str, Callable[[BoqwizEntry, str], Any]] = {
    "tlh": lambda entry, arg: re.search(fix_xifan(arg), entry.name),
    "notes": lambda entry, arg: re.search(arg, entry.notes.get("en", ""), re.IGNORECASE),
    "ex": lambda entry, arg: re.search(arg, entry.examples.get("en", "")),
    "pos": lambda entry, arg: set(arg.split(",")) <= ({entry.simple_pos} | entry.tags),
    "antonym": lambda entry, arg: re.search(fix_xifan(arg), entry.antonyms or ""),
    "synonym": lambda entry, arg: re.search(fix_xifan(arg), entry.synonyms or ""),
    "components": lambda entry, arg: re.search(fix_xifan(arg), entry.components or ""),
    "see": lambda entry, arg: re.search(fix_xifan(arg), entry.see_also or ""),
}

def add_operators(language: str):
    QUERY_OPERATORS[language] = lambda entry, arg: (re.search(arg, entry.definition[language]) or arg in entry.search_tags.get(language, []))
    QUERY_OPERATORS[language+"notes"] = lambda entry, arg: re.search(arg, entry.notes.get(language, ""))
    QUERY_OPERATORS[language+"ex"] = lambda entry, arg: re.search(arg, entry.examples.get(language, ""))

def init_operators():
    for language in dictionary.locales:
        add_operators(language)

init_operators()

def get_wiki_name(name: str) -> str:
    name = name.replace(" ", "")
    ans = ""
    for letter in yajwiz.split_to_letters(name):
        if letter == "q":
            ans += "k"

        elif letter == "'":
            ans += "-"

        else:
            ans += letter

    return ans.capitalize()

class DictionaryQuery:
    def __init__(self, query: str, language: str, link_format: Literal["html", "latex"] = "html"):
        self.query = query
        self.language = language
        self.locale_strings = locales.locale_map[language]
        self.link_format = link_format
        self.link_renderer = LinkRenderer(self) if link_format == "html" else LinkRendererLatex(self)

    def execute_query(self):
        """
        Dictionary query:
        1. Analyze it whole as a Klingon word
        2. Split at spaces and analyze each word
        3. Parse text as a dsl query and execute it
        """
        if not self.query:
            return ""

        query = self.query
        query = re.sub(r"[’`‘]", "'", query)
        query = re.sub(r"[”“]", "\"", query)
        query = re.sub(r"\s{2,}", " ", query)
        query = query.strip()

        parts = []

        analyses = yajwiz.analyze(fix_xifan(query))
        if analyses:
            parts += self.fix_analysis_parts(analyses)

        if ":" not in query:
            words = query.split(" ")
            analyses = []
            for word in words:
                analyses += yajwiz.analyze(fix_xifan(word))

            if analyses:
                parts += self.fix_analysis_parts(analyses)

        included = set()
        ans = []
        for part in parts:
            if part not in included:
                included.add(part)

                ans.append(self.render_entry(dictionary.entries[part]))

        ans += self.dsl_query(query, included)

        return ans

    def fix_analysis_parts(self, analyses: List[yajwiz.analyzer.Analysis]):
        parts = []
        names = []
        for part in [part for a in analyses for part in a["PARTS"]]:
            names.append(part[:part.index(":")])
            if part not in parts:
                parts.append(part)

        parts.sort(key=lambda p: names.index(p[:p.index(":")]))
        return parts

    def dsl_query(self, query: str, included: Set[str]):
        parts = [""]
        quote = False
        for i in range(len(query)):
            if not quote and query[i] == " ":
                parts += [""]
                continue

            if not quote and query[i] in "()":
                parts += [query[i], ""]
                continue

            if query[i] == "\"":
                quote = not quote
                continue

            parts[-1] += query[i]

        ans = []
        query_function = self.parse_or(parts)
        for entry_id, entry in dictionary.entries.items():
            try:
                f = query_function(entry)

            except:
                logger.exception("Error during executing query", exc_info=sys.exc_info())
                f = False

            if entry_id not in included and f:
                ans.append(self.render_entry(entry))

        return ans

    def parse_or(self, parts: List[str]):
        a = self.parse_and(parts)
        while parts and parts[0] in {"OR", "TAI"}:
            parts.pop(0)
            b = self.parse_and(parts)
            a = self.create_or(a, b)

        return a

    def parse_and(self, parts: List[str]):
        a = self.parse_term(parts)
        while parts and parts[0] not in {")", "OR", "TAI"}:
            if parts[0] in {"AND", "JA"}:
                parts.pop(0)

            b = self.parse_term(parts)
            a = self.create_and(a, b)

        return a

    def create_or(self, a, b):
        return lambda *args: (a(*args) or b(*args))

    def create_and(self, a, b):
        return lambda *args: (a(*args) and b(*args))

    def parse_term(self, parts: List[str]):
        if not parts:
            return lambda *args: True

        part = parts.pop(0)
        if part == "(":
            r = self.parse_or(parts)
            if parts: parts.pop(0) # )
            return r

        if part in {"NOT", "EI"}:
            r = self.parse_term(parts)
            return lambda *args: not r(*args)

        if ":" in part:
            op = part[:part.index(":")]
            arg = part[part.index(":")+1:]
            if op in QUERY_OPERATORS:
                return lambda entry: QUERY_OPERATORS[op](entry, arg)

            else:
                # illegal situation
                return lambda entry: False

        else:
            def func(entry: BoqwizEntry):
                if fix_xifan(part) in entry.name:
                    return True

                if any_word_starts_with(part, entry.search_tags.get(self.language, [])):
                    return True

                if any_word_starts_with(part, entry.definition.get(self.language, "").lower().split()):
                    return True

                return False

            return func

    def render_entry(self, entry: BoqwizEntry, include_derivs: bool = True) -> dict:
        ans = {
            "name": entry.name,
            "url_name": entry.name.replace(" ", "+"),
            "wiki_name": get_wiki_name(entry.name),
            "graphemes": yajwiz.split_to_letters(entry.name),
            "syllables": yajwiz.split_to_syllables(entry.name),
            "morphemes": list(map(list, yajwiz.split_to_morphemes(entry.name))),
            "pos": self.locale_strings["unknown"],
            "simple_pos": "affix" if entry.name.startswith("-") or entry.name.endswith("-") or entry.name == "0" else entry.simple_pos,
            "boqwi_tags": list(entry.tags),
            "tags": [],
            "rendered_link": self.link_renderer.render_link(entry.name, entry.simple_pos, entry.tags),
        }
        if entry.simple_pos == "v":
            if "is" in entry.tags:
                ans["pos"] = self.locale_strings["adjective"]

            elif "t_c" in entry.tags:
                ans["pos"] = self.locale_strings["transitive verb"]

            elif "t" in entry.tags:
                ans["pos"] = self.locale_strings["possibly transitive verb"]

            elif "i_c" in entry.tags:
                ans["pos"] = self.locale_strings["intransitive verb"]

            elif "i" in entry.tags:
                ans["pos"] = self.locale_strings["possibly intransitive verb"]

            elif "pref" in entry.tags:
                ans["pos"] = self.locale_strings["verb prefix"]

            elif "suff" in entry.tags:
                ans["pos"] = self.locale_strings["verb suffix"]

            else:
                ans["pos"] = self.locale_strings["verb"]

        elif entry.simple_pos == "n":
            if "suff" in entry.tags:
                ans["pos"] = self.locale_strings["noun suffix"]

            else:
                ans["pos"] = self.locale_strings["noun"]

        elif entry.simple_pos == "ques":
            ans["pos"] = self.locale_strings["question word"]

        elif entry.simple_pos == "adv":
            ans["pos"] = self.locale_strings["adverb"]

        elif entry.simple_pos == "conj":
            ans["pos"] = self.locale_strings["conjunction"]

        elif entry.simple_pos == "excl":
            ans["pos"] = self.locale_strings["exclamation"]

        elif entry.simple_pos == "sen":
            ans["pos"] = self.locale_strings["sentence"]

        if "slang" in entry.tags:
            ans["tags"].append(self.locale_strings["slang"])

        if "reg" in entry.tags:
            ans["tags"].append(self.locale_strings["regional"])

        if "archaic" in entry.tags:
            ans["tags"].append(self.locale_strings["archaic"])

        if "hyp" in entry.tags:
            ans["tags"].append(self.locale_strings["hypothetical"])

        if "extcan" in entry.tags:
            ans["tags"].append(self.locale_strings["extracanonical"])

        for i in range(1, 10):
            if str(i) in entry.tags:
                ans["homonym"] = i

        ans["definition"] = self.fix_links(self.get_unless_translated(entry.definition))

        if self.language != "en":
            ans["english"] = self.fix_links(entry.definition["en"])

        if entry.notes:
            ans["notes"] = self.fix_links(self.get_unless_translated(entry.notes))

        if entry.examples:
            ans["examples"] = self.fix_links(self.get_unless_translated(entry.examples))

        if entry.components:
            ans["components"] = self.fix_links(entry.components)

        if entry.simple_pos == "n":
            if "inhps" in entry.tags and entry.components:
                ans["inflections"] = self.locale_strings["plural"] + ": " + self.fix_links(entry.components)
                del ans["components"]

            elif "inhpl" in entry.tags and entry.components:
                ans["inflections"] = self.locale_strings["singular"] + ": " + self.fix_links(entry.components)
                del ans["components"]

            elif "suff" not in entry.tags and "inhpl" not in entry.tags:
                if "body" in entry.tags:
                    ans["inflections"] = "-Du'"

                elif "being" in entry.tags:
                    ans["inflections"] = "-pu', -mey"

        for field in ["synonyms", "antonyms", "see_also", "source", "hidden_notes"]:
            if getattr(entry, field):
                ans[field] = self.fix_links(getattr(entry, field))

        if include_derivs:
            derived = []
            for entry2 in derived_index[entry.id]:
                derived.append(self.render_entry(entry2, include_derivs=False))

            if derived:
                ans["derived"] = derived

        return ans

    def get_unless_translated(self, d):
        if self.language not in d or not d[self.language]:
            return d.get("en", "")

        elif "AUTOTRANSLATED" in d[self.language] or d[self.language] == "TRANSLATE":
            return d["en"]

        else:
            return d[self.language]

    def fix_links(self, text: str) -> str:
        ans = ""
        while "{" in text:
            i = text.index("{")
            ans += text[:i]
            text = text[i+1:]
            i = text.index("}")
            link = text[:i]
            ans += self.link_renderer.fix_link(link)
            text = text[i+1:]

        ans += text
        return ans.replace("\n", "<br>")

class LinkRenderer:
    def __init__(self, query: DictionaryQuery):
        self.query = query

    def fix_link(self, link: str) -> str:
        link_text, link_type, tags, parts1, parts2 = parse_link(link)

        if "nolink" in tags:
            style = "affix" if "-" in link_text else link_type if link_type else "sen"
            return f"<b class=\"pos-{style}\" okrand>" + link_text + "</b>"

        elif link_type == "src":
            return "<i>" + link_text + "</i>"

        elif link_type == "url":
            addr = parts2[2]
            return f"<a target=_blank href=\"{addr}\">{link_text}</a>"

        elif len(parts1) == 2:
            style = link_type if link_type else "sen"
            return f"<a href=\"?q={link_text.replace(' ', '+')}\" class=\"pos-{style}\" okrand>{link_text}</a>"

        else:
            return self.render_link(link_text, link_type, tags)

    def render_link(self, link_text: str, link_type: str, tags: Collection[str]):
        hyp = "<sup>?</sup>" if "hyp" in tags else "*" if "extcan" in tags else ""
        hom = ""
        hom_pos = ""
        for i in range(1, 10):
            if str(i) in tags:
                hom = f"<sup>{i}</sup>"
                hom_pos = f"+pos:{i}"
                break

            elif f"{i}h" in tags:
                hom_pos = f"+pos:{i}"
                break

        pos = "+pos:"+link_type if link_type and link_type != "sen" else ""
        style = "affix" if "-" in link_text else link_type if link_type else "sen"

        defn = ""
        word_id = get_id(link_text, link_type, tags)
        if entry := dictionary.entries.get(word_id, None):
            defn = self.query.get_unless_translated(entry.definition)
            defn = f" title=\"{defn}\""

        return f"<a href=\"?q=tlh:&quot;^{link_text.replace(' ', '+')}$&quot;{pos}{hom_pos}\" class=\"pos-{style}\"{defn}>{hyp}<span okrand>{link_text}</span>{hom}</a>"

class LinkRendererLatex(LinkRenderer):
    def fix_link(self, link: str) -> str:
        link_text, link_type, tags, parts1, parts2 = parse_link(link)

        if link_type not in ["src", "url"]:
            link_text = " ".join("\\mbox{" + word + "}" for word in link_text.split(" "))

        if "nolink" in tags:
            style = "affix" if "-" in link_text else link_type if link_type else "sen"
            return "\\klingonref[" + style + "]{\\klingontext{" + link_text + "}}"

        elif link_type == "src":
            return "\\klingonref[src]{" + link_text + "}"

        elif link_type == "url":
            addr = parts2[2]
            return "\\klingonref[url]{" + link_text + "}"

        elif len(parts1) == 2:
            style = link_type if link_type else "sen"
            return "\\klingonref[" + style + "]{\\klingontext{" + link_text + "}}"

        else:
            return self._render_link(link_text, link_type, tags)

    def render_link(self, link_text: str, link_type: str, tags: Collection[str]):
        link_text = " ".join("\\mbox{" + word + "}" for word in link_text.split(" "))
        return self._render_link(link_text, link_type, tags)

    def _render_link(self, link_text: str, link_type: str, tags: Collection[str]):
        hyp = "$^?$" if "hyp" in tags else "*" if "extcan" in tags else ""
        hom = ""
        for i in range(1, 10):
            if str(i) in tags:
                hom = f"$^{i}$"
                break

            elif f"{i}h" in tags:
                # hidden homonym number: not shown
                break

        style = "affix" if "-" in link_text else link_type if link_type else "sen"

        return "\\klingonref[%s]{%s\\klingontext{%s}%s}" % (style, hyp, link_text, hom)

def dictionary_query(query: str, lang: str, link_format: Literal["html", "latex"]):
    return DictionaryQuery(query=query, language=lang, link_format=link_format).execute_query()

def any_word_starts_with(word: str, words: List[str]):
    return any([part.lower().startswith(word.lower()) for part in words])

def get_id(link_text: str, link_type: str, tags: Collection[str]) -> str:
    homonyms = [tag.strip("h") for tag in tags if re.fullmatch(r"\d+h?", tag)]
    return link_text + ":" + ":".join([link_type] + homonyms)

def get_links(text: str) -> List[str]:
    ids = []
    while "{" in text:
        i = text.index("{")
        text = text[i+1:]
        i = text.index("}")
        link_text, link_type, tags, _, _ = parse_link(text[:i])
        ids.append(get_id(link_text, link_type, tags))
        text = text[i+1:]

    return ids

def parse_link(link: str):
    parts1 = link.split("@@")
    parts2 = parts1[0].split(":")
    link_text = parts2[0]
    link_type = parts2[1] if len(parts2) > 1 else ""
    tags = parts2[2].split(",") if len(parts2) > 2 else []
    return link_text, link_type, tags, parts1, parts2

def fix_xifan(query: str) -> str:
    query = re.sub(r"i", "I", query)
    query = re.sub(r"d", "D", query)
    query = re.sub(r"s", "S", query)
    query = re.sub(r"([^cgl]|[^t]l|^)h", r"\1H", query)
    query = re.sub(r"x", "tlh", query)
    query = re.sub(r"f", "ng", query)
    query = re.sub(r"c(?!h)", "ch", query)
    query = re.sub(r"(?<!n)g(?!h)", "gh", query)
    return query

make_derived_index()
