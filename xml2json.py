#!/usr/bin/env python3

# xml2json.py
#
# Read the database XML files and output a JSON representation of the database
# to stdout, and report unresolvable links to stderr.
#
# The JSON structure is roughly:
#
# {
#   "format_version" : "1"
#   "version" : "<database_version>",
#   "locales" : {
#     "de" : "Deutsch",
#     "en" : "English",
#     ...
#   },
#   "supported_locales" : [
#     "de",
#     "en",
#     ...
#   ],
#   "qawHaq" : {
#     "<search_name>" : {
#         "_id" : "<id>",
#         "entry_name" : "<entry name>",
#         "part_of_speech" : "<part_of_speech>",
#         "definition" : {
#           "de" : "<definition_de>",
#           "en" : "<definition>",
#           ...
#         },
#         "synonyms" : "<synonyms>",
#         "antonyms" : "<antonyms>",
#         "see_also" : "<see_also>",
#         "notes" : {
#           "de" : "<notes_de>",
#           "en" : "<notes>",
#           ...
#         },
#         "hidden_notes" : "<hidden_notes>",
#         "components" : "<components>",
#         "examples" : {
#           "de" : "<examples_de>",
#           "en" : "<examples>",
#           ...
#         },
#         "search_tags" : {
#           "de" : ["<search_tag_de>", ...],
#           "en" : ["<search_tag>", ...],
#           ...
#         },
#         "source" : "<source>"
#     },
#     ...
#   }
# }
#
# format_version must be incremented if the format changes in a backwards
# incompatible way (adding new fields ought to be backwards compatible).
#
# version is the version of the database
#
# locales is a map of key/value pairs with locale codes as the key and localized
# locale names as the value
#
# supported_locales is a list of locale codes that are considered complete enough
# to display in the menu by default
#
# search_name is constructed as: entry_name:base_part_of_speech(:homophone_num),
# where entry_name is the entry name, base_part_of_speech is the first field of
# the part of speech (e.g. "n" rather than "n:name"), and homophone_num is the
# homophone number parsed from the part_of_speech field, if present. Entries
# with no homophones do not specify a homophone field.
#
# The search_tags and search_tags_de fields are treated as comma-separated lists
# and split into arrays of separate search tags.
#
# The remaining values are taken directly from the XML database. Empty values
# are omitted from the JSON representation.

import xml.etree.ElementTree as ET
import json
import sys
import fileinput
import os
import re
import unicodedata
from collections import OrderedDict

# A single entry parsed from the XML tree
class EntryNode:
    # Constructor from XML node
    def __init__(self, node):
        self.data = {}
        # Iterate over columns in the entry and store their values
        for child in node:
            if child.tag == 'column':
                name = child.attrib['name']
                namesplit = name.split('_')
                # Normalize Unicode characters into decomposed form
                text = unicodedata.normalize('NFKD', ''.join(child.itertext()))
                if text:
                    # Store localized fields hierarchically
                    if namesplit[0] in [
                        'definition',
                        'notes',
                        'search', # 'search_tags'
                        'examples',
                    ]:
                        if namesplit[0] == 'search':
                            component = 'search_tags'
                        else:
                            component = namesplit[0]

                        if len(namesplit) > 1:
                            locale = namesplit[-1]
                            if locale == 'tags': # 'search_tags'
                                locale = 'en'
                        else:
                            locale = 'en'

                        if locale == 'HK': # 'zh_HK'
                            locale = 'zh_HK'

                        if not component in self.data:
                            self.data[component] = {}

                        # Split search tags into array
                        if component == 'search_tags':
                            data = re.split(', *', text)
                        else:
                            data = text

                        self.data[component][locale] = data
                    # Non localized fields are stored at the entry's top level
                    else:
                        self.data[name] = text

    # Normalize the search name from the stored entry name and part of speech
    def searchName(self):
        return normalize(self.data['entry_name'], self.data['part_of_speech'])

# Convert an entry name and part of speech, which may include a homophone
# number and non-homophone tags, into a normalized search name
def normalize(name, pos):
    # Split part of speech into separate fields
    posSplit = pos.split(':')
    pos = posSplit[0]
    # If there is a second field, it contains comma-separated tags
    if len(posSplit) > 1:
        flags = posSplit[1]
    else:
        flags = ''
    homophone = ''
    # Look for a homophone number in the flags. Ignore an 'h' which is used
    # to indicate a hidden homophone number.
    for flag in flags.split(','):
        flag = flag.rstrip('h')
        if flag.isdigit():
            homophone = ':' + flag
            break
    return name + ':' + pos + homophone

# Traverse the database tree and try to identify links that cannot be resolved
# unambiguously to an entry. Report any unresolvable links to stderr.
def validatelinks(root, node):
    # If this node is a dict or a list, recurse into its children
    if isinstance(node, dict):
        for subnode in node:
            validatelinks(root, node[subnode])
    elif isinstance(node, list):
        for item in node:
            validatelinks(root, item)
    else:
        # Find all text in {curly braces}
        remaining = node
        while remaining.find('{') != -1:
            remaining = remaining[remaining.find('{')+1:]
            tag = remaining[0:remaining.find('}')]

            # For {sentences with components@@sentences, with, components},
            # check the individual components.
            if tag.find('@@') != -1:
                for term in tag.split('@@')[1].split(','):
                    validatelinks(root, '{' + term.strip(' ') + '}')
                continue

            tagsplit = tag.split(':')

            if len(tagsplit) > 1:
                # The second field identifies the text type: don't bother
                # validating url links, src attributions, or sentences.
                if tagsplit[1] == 'url' or \
                    tagsplit[1] == 'src' or \
                    tagsplit[1] == 'sen':
                    continue
                # Check the flags in the third field and ignore text tagged
                # with the "nolink" flag.
                if len(tagsplit) > 2 and 'nolink' in tagsplit[2].split(','):
                    continue

                # Normalize the search name and check if an entry exists
                normalized = normalize(tagsplit[0], ':'.join(tagsplit[1:]))
                if not normalized in root:
                    hom = ''

                    # Check if the failure to resolve was due to an ambiguous
                    # homophone
                    if normalized + ':1' in root:
                        hom = ' (homophone exists)'
                    # A homophone number of 0 explicitly indicates that the
                    # link is supposed to lead to all homophones
                    elif normalized[-2:] == ':0':
                        if normalized[:-2] + ':1' in root:
                            continue

                    sys.stderr.write('no entry for {' + tag + '}' + hom + '.\n')

# Section names of the individual XML fragments that make up the database
memparts = ['header', 'b', 'ch', 'D', 'gh', 'H', 'j', 'l', 'm', 'n', 'ng', 'p',
            'q', 'Q', 'r', 'S' ,'t', 'tlh', 'v', 'w', 'y', 'a', 'e', 'I', 'o',
            'u', 'suffixes', 'extra', 'footer']
filenames = []
concat=''
sdir = os.path.dirname(os.path.realpath(sys.argv[0]))

for i, part in enumerate(memparts):
    filenames.append(os.path.join(sdir,'mem-{0:02d}-{1}.xml'.format(i, part)))

# Concatenate the individual files into a single database string
mem = fileinput.FileInput(files=filenames)
for line in mem:
    concat += line
mem.close()

# Read the database version from the version file
ver = fileinput.FileInput(files=(os.path.join(sdir,'VERSION')))
version = ver[0].strip()
ver.close()

# Parse the database XML tree and store the parsed entries in a dict
xmltree = ET.fromstring(concat)
qawHaq = OrderedDict()
for child in xmltree[0]:
    node = EntryNode(child)
    qawHaq[node.searchName()] = node.data

# Now that the database has been parsed, search for unfollowable links
validatelinks(qawHaq, qawHaq)

ret = OrderedDict()
ret['format_version'] = '1'
ret['version'] = version
ret['locales'] = OrderedDict({
  'de' : 'Deutsch',
  'en' : 'English',
  'fa' : 'فارسى',
  'ru' : 'Русский язык',
  'sv' : 'Svenska',
  'zh_HK' : '中文 (香港)',
})
ret['supported_locales'] = [
  'de',
  'en',
  'sv',
]
ret['qawHaq'] = qawHaq

# Dump the database as JSON
print(json.dumps(ret))
