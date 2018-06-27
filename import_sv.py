#!/usr/bin/env python3

from collections import defaultdict
from collections import namedtuple

import fileinput
import glob
import re

EntryKey = namedtuple("EntryKey", ["entry_name", "part_of_speech"])
DefinitionPair = namedtuple("DefinitionPair", ["definition", "definition_sv"])
definitions_map = defaultdict(list)
strip_characters = dict.fromkeys(map(ord, '<>«»~'), None)

# Note: This file must be downloaded from [ http://klingonska.org/dict/dict.zdb ].
dictfile = fileinput.FileInput("dict.zdb", mode='r')

# Skip everything up to the start of the word list.
while dictfile.readline() != "=== start-of-word-list ===\n":
    pass

# Read and process the word list and the verb prefix list.
for line in dictfile:

    # Each entry begins after a blank line.
    if line == "\n":
        tlh = dictfile.readline()
        if tlh == "=== end-of-verb-prefix-list ===\n":
            break
        tlh = re.sub(r"tlh:\t(?:\[\d\] )?{(.*)}(?: \[\d?\.?\d\])?", r"\1", tlh.rstrip())
        tlh = tlh.translate(strip_characters)

        pos = dictfile.readline().rstrip()
        pos = re.sub(r"pos:\t(.*)", r"\1", pos)

        en  = ""
        nextline = dictfile.readline().rstrip()
        while not(re.compile("sv:.*").match(nextline)):
            nextline = dictfile.readline().rstrip()
            en += nextline
        en  = re.sub(r"(.*) \[.*\]", r"\1", en)
        en  = re.sub(r"en:\t(.*)", r"\1", en)
        en  = en.replace("--", "-")
        en  = en.translate(strip_characters)

        sv  = nextline
        nextline = dictfile.readline().rstrip()
        while not(re.compile("[a-z][a-z][a-z]?[a-z]?:.*").match(nextline)):
            nextline = dictfile.readline().rstrip()
            sv += nextline
        sv  = re.sub(r"(.*) \[.*\]", r"\1", sv)
        sv  = re.sub(r"sv:\t(.*)", r"\1", sv)
        sv  = sv.replace("--", "-")
        sv  = sv.translate(strip_characters)

        key = EntryKey(entry_name = tlh, part_of_speech = pos)
        pair = DefinitionPair(definition = en, definition_sv = sv)
        definitions_map[key].append(pair)

# print(definitions_map)

# Put the Swedish entries into the mem-*.xml files.
for filename in glob.glob("mem-*.xml"):
    print(filename)
    with fileinput.FileInput(filename, inplace=True) as memfile:
        for line in memfile:
            # Find the beginning of an entry.
            if re.compile("      <column name=\"_id\">\d*</column>\n").match(line):
                print(line, end='')

                entry_name = memfile.readline().rstrip()
                print(entry_name)
                entry_name = re.sub(r"      <column name=\"entry_name\">(.*)</column>", r"\1", entry_name)

                part_of_speech = memfile.readline().rstrip()
                print(part_of_speech)
                part_of_speech = re.sub(r"      <column name=\"part_of_speech\">(.*)</column>", r"\1", part_of_speech)
                if re.compile("adv(?:.*)").match(part_of_speech):
                    part_of_speech = "adverbial"
                elif re.compile("conj(?:.*)").match(part_of_speech):
                    part_of_speech = "conjunction"
                elif re.compile("excl(?:.*)").match(part_of_speech):
                    part_of_speech = "exclamation"
                elif re.compile("n:(?:.*)name(?:.*)").match(part_of_speech):
                    part_of_speech = "name"
                elif re.compile("n:(?:.*)num(?:.*)").match(part_of_speech):
                    part_of_speech = "numeral"
                elif re.compile("n:(?:.*)pro(?:.*)").match(part_of_speech):
                    part_of_speech = "pronoun"
                elif re.compile("n|n:(?:.*)").match(part_of_speech):
                    part_of_speech = "noun"
                elif re.compile("ques(?:.*)").match(part_of_speech):
                    part_of_speech = "question word"
                elif re.compile("v:pref").match(part_of_speech):
                    part_of_speech = "verb prefix"
                elif re.compile("v:.*").match(part_of_speech):
                    part_of_speech = "verb"

                definition = memfile.readline().rstrip()
                print(definition)
                definition = re.sub(r"      <column name=\"definition\">(.*)</column>", r"\1", definition)

                # Skip over "de" and "fa" definitions.
                print(memfile.readline().rstrip())
                print(memfile.readline().rstrip())

                # Try to match the Swedish definition.
                key = EntryKey(entry_name = entry_name, part_of_speech = part_of_speech)
                pairs_list = definitions_map[key]
                if len(pairs_list) == 0:
                    definition_sv = ""
                elif len(pairs_list) == 1:
                    definition_sv = pairs_list[0].definition_sv
                    del definitions_map[key]
                else:
                    for i in range(0, len(pairs_list)):
                        if pairs_list[i].definition == definition:
                          definition_sv = pairs_list[i].definition_sv
                          del pairs_list[i]
                          break

                sv_line = memfile.readline().rstrip()
                if definition_sv != "":
                    sv_line = re.sub(r"><", ">%s<" % definition_sv, sv_line)
                print(sv_line)
            else:
                print(line, end='')

