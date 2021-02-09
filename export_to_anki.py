#!/usr/bin/env python3

# export_to_anki.py
#
# Exports the entire database to an Anki deck. See xml2json.py for input file format.

import genanki
import json
import re
import subprocess
import sys

CSS = """.card {
 font-family: arial;
 font-size: 20px;
 text-align: center;
 color: black;
 background-color: white;
}
"""

# Basic two-sided card, used when there are no homophones with the same
# part of speech.
basic_and_reversed_model = genanki.Model(
  1808191300,
  "boQwI' - Basic (and reversed card)",
  fields=[
    {'name': 'Klingon'},
    {'name': 'pos'},
    {'name': 'English'},
  ],
  templates=[
    {
      'name': 'K2E Card',
      'qfmt': '<b>{{Klingon}}</b> (<i>{{pos}}</i>)',
      'afmt': '{{FrontSide}}<hr id="answer">{{English}}',
    },
    {
      'name': 'E2K Card',
      'qfmt': '{{English}} (<i>{{pos}}</i>)',
      'afmt': '{{FrontSide}}<hr id="answer"><b>{{Klingon}}</b>',
    },
  ],
  css = CSS)

# Klingon-to-English card for when there are homophones with the same part of
# speech. The English card should include all definitions.
homophone_k2e_model = genanki.Model(
  1661579413,
  "boQwI' - Homophone Klingon-to-English",
  fields=[
    {'name': 'Klingon'},
    {'name': 'pos'},
    {'name': 'English'},
  ],
  templates=[
    {
      'name': 'K2E Card',
      'qfmt': '<b>{{Klingon}}</b> (<i>{{pos}}</i>)',
      'afmt': '{{FrontSide}}<hr id="answer">{{English}}',
    },
  ],
  css = CSS)

# English-to-Klingon card for when there are homophones with the same part of
# speech. Each English card contains a separate definition and a distinct number.
homophone_e2k_model = genanki.Model(
  1325261783,
  "boQwI' - Homophone English-to-Klingon",
  fields=[
    {'name': 'Klingon'},
    {'name': 'pos'},
    {'name': 'English'},
    {'name': 'number'},
  ],
  templates=[
    {
      'name': 'E2K Card',
      'qfmt': '{{English}} (<i>{{pos}}</i>)',
      'afmt': '{{FrontSide}}<hr id="answer"><b>{{Klingon}}</b>',
    },
  ],
  css = CSS)

pos_to_tag = {
  'v': 'Klingon_verb',
  'n': 'Klingon_noun',
  'adv': 'Klingon_adverbial',
  'conj': 'Klingon_conjunction',
  'ques': 'Klingon_question_word',
  'sen': 'Klingon_sentence',
  'excl': 'Klingon_exclamation',
}

src_to_tag = {
  "TKD": "Klingon_from_TKD",
  "TKDA": "Klingon_from_TKD",
  "KGT": "Klingon_from_KGT",
}

# Default deck name. Also used to hash the GUID.
# TODO: Make a dictionary from language to deck name and GUID.
deck_name = "boQwI' vocabulary (en)"

# Base the GUID on only the Klingon text and part of speech.
class GeneralNote(genanki.Note):
  @property
  def guid(self):
    return genanki.guid_for(deck_name, self.fields[0], self.fields[1])

# Base the GUID on only the Klingon text, part of speech, and a unique number.
class NumberedNote(genanki.Note):
  @property
  def guid(self):
    return genanki.guid_for(deck_name, self.fields[0], self.fields[1], self.fields[3])

def extract_definition(data):
  definition = data['definition']['en']
  link_matches = re.findall(r"{[^{}]*}", definition)
  for link_match in link_matches:
    link_text = re.sub(r"{([^{}:]*)(:.*)?}", r"<b>\1</b>", link_match)
    definition = re.sub(link_match, link_text, definition, 1)
  return definition

def get_src_tag(data):
  sources = data['source'].split(',')
  for source in sources:
    for src in src_to_tag:
      # Each source is of the form: "[1] {TKD:src}", "[2] {KGT p.123:src}", etc.
      source_matches = re.findall(r"\[\d\] {{{}( .*)?:src}}".format(src), source)
      if source_matches:
        return src_to_tag[src]

    for year in range(1994, 2021):
      ordinal = year - 1993
      source_matches = re.findall(r"\[\d\] {{qep'a' {} ({}):src}}".format(year, ordinal), source)
      if source_matches:
        return "Klingon_from_qepa{}_{}".format(year, ordinal)

      source_matches = re.findall(r"\[\d\] {{Saarbru\u0308cken qepHom'a' {}:src}}".format(year), source)
      if source_matches:
        return "Klingon_from_Saarbrücken{}".format(year)
  return None

def get_attrs(data):
  pos_parts = data['part_of_speech'].split(':')
  attrs = []
  if len(pos_parts) > 1:
    attrs = pos_parts[1].split(',')
  return attrs

def should_skip_entry(search_name, attrs, data):
  if ('alt' in attrs):
    print("skipped alt entry: " + search_name)
    return True
  elif ('hyp' in attrs):
    print("skipped hyp entry: " + search_name)
    return True
  elif ('extcan' in attrs):
    print("skipped extcan entry: " + search_name)
    return True
  elif (data.get('source') == None):
    print("skipped entry with no source: " + search_name)
    return True
  return False

# Read in input.
if '--test' in sys.argv:
  print("Reading test json file...")
  qawHaq = json.load(open('export_to_anki_test.json'))['qawHaq']
else:
  print("Generating json file...")
  cmd = subprocess.run(["xml2json.py"], capture_output=True)
  json_string = cmd.stdout.decode()
  qawHaq = json.loads(json_string)['qawHaq']

# Start of main logic.
vocab_deck = genanki.Deck(2024552849, deck_name)

for search_name in qawHaq:
  search_name_parts = search_name.split(':')
  entry_name = search_name_parts[0]
  pos = search_name_parts[1]
  pos_tag = pos_to_tag[pos]

  if len(search_name_parts) == 2:
    # No homophones. Create one note with front and back.
    data = qawHaq[search_name]
    attrs = get_attrs(data)
    if not should_skip_entry(search_name, attrs, data):
      if entry_name == "0":
        entry_name = "(null prefix)"
      elif ('pref' in attrs):
        pos_tag = 'Klingon_prefix'
      elif ('suff' in attrs):
        if pos == "v":
          pos_tag = 'Klingon_verb_suffix'
        elif pos == "n":
          pos_tag = 'Klingon_noun_suffix'
      src_tag = get_src_tag(data)
      tags = [t for t in [pos_tag, src_tag] if t]
      note = GeneralNote(
        model = basic_and_reversed_model,
        fields = [entry_name, pos, extract_definition(data)],
        tags = tags)
      vocab_deck.add_note(note)
      print("wrote basic note: \"" + search_name + "\" with tags: " + str(tags))

  else:
    number = search_name_parts[2]

    if number == '1':
      # Homophones. Process them all when encountering number 1 to avoid duplicates.
      counter = 1
      combined_en_definition = ""
      combined_src_tags = []
      search_name = entry_name + ":" + pos + ":1"
      data = qawHaq.get(search_name)
      while (data != None):
        attrs = get_attrs(data)
        if not should_skip_entry(search_name, attrs, data):
          definition = extract_definition(data)
          src_tag = get_src_tag(data)
          tags = [t for t in [pos_tag, src_tag] if t]
          e2k_note = NumberedNote(
            model = homophone_e2k_model,
            fields = [entry_name, pos, definition, str(counter)],
            tags = tags)
          vocab_deck.add_note(e2k_note)
          print("wrote e2k note: \"" + search_name + "\" with tags: " + str(tags))
          combined_en_definition += str(counter) + ". " + definition + "<br>"
          if src_tag is not None and src_tag not in combined_src_tags:
            combined_src_tags += [src_tag]
        counter += 1
        search_name = entry_name + ":" + pos + ":" + str(counter)
        data = qawHaq.get(search_name)

      tags = [pos_tag] + combined_src_tags
      k2e_note = GeneralNote(
        model = homophone_k2e_model,
        fields = [entry_name, pos, combined_en_definition],
        tags = tags)
      vocab_deck.add_note(k2e_note)
      print("wrote k2e note: \"" + entry_name + ":" + pos + "\" with tags: " + str(tags))

genanki.Package(vocab_deck).write_to_file('klingon_vocab.apkg')
