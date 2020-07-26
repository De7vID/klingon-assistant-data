#!/usr/bin/env python3

# Script to extract new words from https://www.kli.org/activities/qepmey/qepa-chamah-sochdich/new-words/.

import pandas as pd

df_list = pd.read_html('new_words.html')
df = df_list[1]

def print_entry(entry_name, part_of_speech, definition, notes):
  print("    <table name=\"mem\">")
  print("      <column name=\"_id\"></column>")
  print("      <column name=\"entry_name\">{}</column>".format(entry_name))
  print("      <column name=\"part_of_speech\">{}</column>".format(part_of_speech))
  print("      <column name=\"definition\">{}</column>".format(definition))
  print("      <column name=\"definition_de\">TRANSLATE</column>")
  print("      <column name=\"definition_fa\">TRANSLATE</column>")
  print("      <column name=\"definition_sv\">TRANSLATE</column>")
  print("      <column name=\"definition_ru\">TRANSLATE</column>")
  print("      <column name=\"definition_zh_HK\">TRANSLATE</column>")
  print("      <column name=\"definition_pt\">TRANSLATE</column>")
  print("      <column name=\"synonyms\"></column>")
  print("      <column name=\"antonyms\"></column>")
  print("      <column name=\"see_also\"></column>")
  print("      <column name=\"notes\">{}</column>".format(notes))
  print("      <column name=\"notes_de\"></column>")
  print("      <column name=\"notes_fa\"></column>")
  print("      <column name=\"notes_sv\"></column>")
  print("      <column name=\"notes_ru\"></column>")
  print("      <column name=\"notes_zh_HK\"></column>")
  print("      <column name=\"notes_pt\"></column>")
  print("      <column name=\"hidden_notes\"></column>")
  print("      <column name=\"components\"></column>")
  print("      <column name=\"examples\"></column>")
  print("      <column name=\"examples_de\"></column>")
  print("      <column name=\"examples_fa\"></column>")
  print("      <column name=\"examples_sv\"></column>")
  print("      <column name=\"examples_ru\"></column>")
  print("      <column name=\"examples_zh_HK\"></column>")
  print("      <column name=\"examples_pt\"></column>")
  print("      <column name=\"search_tags\"></column>")
  print("      <column name=\"search_tags_de\"></column>")
  print("      <column name=\"search_tags_fa\"></column>")
  print("      <column name=\"search_tags_sv\"></column>")
  print("      <column name=\"search_tags_ru\"></column>")
  print("      <column name=\"search_tags_zh_HK\"></column>")
  print("      <column name=\"search_tags_pt\"></column>")
  print("      <column name=\"source\">[1] {qep'a' 27 (2020):src}</column>")
  print("    </table>")
  print("")

for index, row in df.iterrows():
  entry_name = str(row[0])
  part_of_speech = str(row[1])
  if part_of_speech == "Number":
    part_of_speech = "n:num"
  elif part_of_speech == "Noun":
    part_of_speech = "n"
  elif part_of_speech == "Verb":
    part_of_speech = "v"
  elif part_of_speech == "Body Part":
    part_of_speech = "n:body"
  elif part_of_speech == "Language User":
    part_of_speech = "n:being"
  elif part_of_speech == "Adverb":
    part_of_speech = "adv"
  definition = str(row[2])
  if definition.startswith("be ") and part_of_speech == "v":
    part_of_speech = "v:is"
  notes = str(row[3])
  if notes == "nan":
    notes = ""
  print_entry(entry_name, part_of_speech, definition, notes)
