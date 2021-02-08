#!/usr/bin/env python3

# export_to_anki.py
#
# Exports the entire database to an Anki deck. See xml2json.py for input file format.

import genanki
import json
import re
import subprocess

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

# Base the GUID on only the Klingon text and part of speech.
class GeneralNote(genanki.Note):
  @property
  def guid(self):
    return genanki.guid_for(self.fields[0], self.fields[1])

# Base the GUID on only the Klingon text, part of speech, and a unique number.
class NumberedNote(genanki.Note):
  @property
  def guid(self):
    return genanki.guid_for(self.fields[0], self.fields[1], self.fields[3])

vocab_deck = genanki.Deck(2024552849, "boQwI' vocabulary")

def extract_definition(data):
  definition = data['definition']['en']
  link_matches = re.findall(r"{[^{}]*}", definition)
  for link_match in link_matches:
    link_text = re.sub(r"{([^{}:]*)(:.*)?}", r"<b>\1</b>", link_match)
    definition = re.sub(link_match, link_text, definition, 1)
  return definition

print("Generating json file...")
cmd = subprocess.run(["xml2json.py"], capture_output=True)
json_string = cmd.stdout.decode()
qawHaq = json.loads(json_string)['qawHaq']

for search_name in qawHaq:
  search_name_parts = search_name.split(':')
  entry_name = search_name_parts[0]
  pos = search_name_parts[1]

  if len(search_name_parts) == 2:
    # No homophones. Create one note with front and back.
    data = qawHaq[search_name]
    pos_parts = data['part_of_speech'].split(':')
    attrs = []
    if len(pos_parts) > 1:
      attrs = pos_parts[1].split(',')
    if ('alt' in attrs):
      print("skipped alt entry: " + search_name)
    elif ('hyp' in attrs):
      print("skipped hyp entry: " + search_name)
    elif ('extcan' in attrs):
      print("skipped extcan entry: " + search_name)
    elif (data.get('source') == None):
      print("skipped entry with no source: " + search_name)
    else:
      if entry_name == "0":
        entry_name = "(null prefix)"
      note = GeneralNote(
        model = basic_and_reversed_model,
        fields = [entry_name, pos, extract_definition(data)])
      vocab_deck.add_note(note)
      print("wrote basic note: " + search_name)

  else:
    number = search_name_parts[2]

    if number == '1':
      # Homophones. Process them all when encountering number 1 to avoid duplicates.
      counter = 1
      combined_en_definition = ""
      data = qawHaq.get(entry_name + ":" + pos + ":1")
      while (data != None):
        definition = extract_definition(data)
        e2k_note = NumberedNote(
          model = homophone_e2k_model,
          fields = [entry_name, pos, definition, str(counter)])
        vocab_deck.add_note(e2k_note)
        print("wrote e2k note: " + entry_name + ":" + pos + ":" + str(counter))
        combined_en_definition += str(counter) + ". " + definition + "<br>"

        counter += 1
        data = qawHaq.get(entry_name + ":" + pos + ":" + str(counter))

      k2e_note = GeneralNote(
        model = homophone_k2e_model,
        fields = [entry_name, pos, combined_en_definition])
      vocab_deck.add_note(k2e_note)
      print("wrote k2e note: " + entry_name + ":" + pos)

genanki.Package(vocab_deck).write_to_file('klingon_vocab.apkg')
