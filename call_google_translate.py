#!/usr/bin/env python3

# Calls Google Translate to produce translations. To use, fill in any missing
# definition_[language] or notes_[language] fields in the mem-*.xml files with
# "TRANSLATE". For definitions, it's also possible to fill in "TRANSLATE:
# [replacement definition]". This allows for a better translation when the
# original definition is ambiguous, e.g., if the definition is "launcher", a
# better translation might result from "TRANSLATE: rocket launcher".

# Commands to add the required fields for a new language with language code "xx":
# sed -i $"s/\(\s*\)\(<column name=\"synonyms\">\)/\1<column name=\"definition_xx\">TRANSLATE<\/column>\\n\1\2/g" mem-*.xml
# sed -i $"s/\(\s*\)\(<column name=\"hidden_notes\">\)/\1<column name=\"notes_xx\">TRANSLATE<\/column>\\n\1\2/g" mem-*.xml
# sed -i $"s/\(\s*\)\(<column name=\"search_tags\">\)/\1<column name=\"examples_xx\"><\/column>\\n\1\2/g" mem-*.xml
# sed -i $"s/\(\s*\)\(<column name=\"source\">\)/\1<column name=\"search_tags_xx\"><\/column>\\n\1\2/g" mem-*.xml

# Special handling for Hong Kong Chinese: Because Google Translate does not
# support "zh-HK", the language code "zh-TW" is used instead. There are some
# differences between Hong Kong Chinese and Taiwan Chinese, and in particular,
# the zh-HK transliteration of "Klingon" is "克林貢" (and not "克林崗" as is
# used in Taiwan Chinese). This is fixed automatically below, but other changes
# may need to be made. Chinese uses fullwidth punctuation, and in some cases
# the fullwidth semicolon may have to be replaced:
# grep "{[^}]*：.*}" mem-*.xml
# It might also be useful to replace full-width commas with enumeration commas
# (but care should be taken that the replacements are appropriate):
# sed -i "s/\(：[^，]*\)}，{/\1}、{/g" mem-*.xml
# Likewise, "smart" quotes should be replaced with the correct quotation marks:
# sed -i "s/“/「/g" mem-*.xml
# sed -i "s/”/」/g" mem-*.xml

# For all languages: It might be useful to run this command to remove
# extraneous spaces before references after this script is run:
# sed -i "s/\(notes_.*\) \(\[[1-9]\]\)/\1\2/g" mem-*.xml

from googletrans import Translator

import fileinput
import re
import time

# TODO: Refactor this and also use in renumber.py.
# Ignore mem-00-header.xml and mem-29-footer.xml because they don't contain entries.
filenames = ['mem-01-b.xml', 'mem-02-ch.xml', 'mem-03-D.xml', 'mem-04-gh.xml', 'mem-05-H.xml', 'mem-06-j.xml', 'mem-07-l.xml', 'mem-08-m.xml', 'mem-09-n.xml', 'mem-10-ng.xml', 'mem-11-p.xml', 'mem-12-q.xml', 'mem-13-Q.xml', 'mem-14-r.xml', 'mem-15-S.xml', 'mem-16-t.xml', 'mem-17-tlh.xml', 'mem-18-v.xml', 'mem-19-w.xml', 'mem-20-y.xml', 'mem-21-a.xml', 'mem-22-e.xml', 'mem-23-I.xml', 'mem-24-o.xml', 'mem-25-u.xml', 'mem-26-suffixes.xml', 'mem-27-extra.xml', 'mem-28-examples.xml']

# Supported languages. Map to another language code if Google Translate does not exactly support the same language.
supported_languages_map = {
  "de": "de",
  "fa": "fa",
  "sv": "sv",
  "ru": "ru",
  "zh-HK": "zh-TW",
  "pt": "pt",
  "fi": "fi",
}

# Check for balanced brackets.
def balanced_brackets(line):
  BRACKETS = dict(zip('{[(','}])'))
  stack = []
  for char in line:
    if char in BRACKETS:
      stack.append(BRACKETS[char])
    elif char not in BRACKETS.values():
      pass
    elif not (stack and char == stack.pop()):
      return False
  return not stack

translator = Translator()
num_errors = 0
multiline_notes = ""
for filename in filenames:
  print("Translating file: {}".format(filename))
  with fileinput.FileInput(filename, inplace=True) as file:
    definition = ""
    notes = ""
    in_comment = False
    for line in file:
      # Detect start of comment block.
      if "<!-- " in line:
        in_comment = True

      if not in_comment:
        definition_match = re.search(r"definition\">(.*)<", line)
        definition_translation_match = re.search(r"definition_(.+)\">TRANSLATE(?:: (.*))?<", line)

        # Get the source (English) text to translate.
        if (definition_match):
          definition = definition_match.group(1)
          if not definition:
            print("<!-- ERROR: Missing definition. -->")
            num_errors += 1

        if (definition and definition_translation_match):
          language = supported_languages_map.get(definition_translation_match.group(1).replace('_','-'), "")
          if language != "":
            # Check for an override like "TRANSLATE: rocket launcher".
            if definition_translation_match.group(2):
              definition = definition_translation_match.group(2)

            # Preserve definitions of the form "{...}" verbatim.
            if definition.startswith('{') and definition.endswith('}'):
              line = re.sub(r">(.*)<", ">{}<".format(definition), line)
            else:
              translation = translator.translate(definition, src='en', dest=language)
              line = re.sub(r">(.*)<", ">{} [AUTOTRANSLATED]<".format(translation.text), line)

              # Rate-limit calls to Google Translate.
              time.sleep(0.01)

        # TODO: Refactor common parts with code for translating definitions.
        if multiline_notes == "":
          notes_match = re.search(r"\"notes\">(.*)", line)
        else:
          notes_match = re.search(r"(.*)", line)
        notes_translation_match = re.search(r"notes_(.+)\">TRANSLATE<", line)

        # Get the source (English) notes to translate.
        if (notes_match):
          if notes_match.group(1) == "</column>":
            # Skip empty notes.
            notes = ""
          elif not notes_match.group(1).endswith("</column>"):
            # Start or middle of multiline notes.
            notes = ""
            multiline_notes += notes_match.group(1) + "\n"
          else:
            # Single-line note or end of multiline notes.
            notes = multiline_notes + notes_match.group(1)[:-len("</column>")]
            multiline_notes = ""

          # Handle links and references by replacing them with "DONOTTRANSLATE" tokens.
          link_matches = re.findall(r"({[^{}]*}|\[[^\[\]]*\])", notes)
          link_number = 1
          for link_match in link_matches:
            notes = re.sub(link_match.replace("[", "\[").replace("]", "\]"), "DONOTTRANSLATE{}".format(link_number), notes, 1)
            link_number += 1

        if (notes and notes_translation_match):
          language = supported_languages_map.get(notes_translation_match.group(1).replace('_','-'), "")
          if language != "":
            translation = translator.translate(notes, src='en', dest=language)
            # Note that Google Translate returns the original text if translation fails for some reason.
            if translation.text != notes:
              translation_text = translation.text
              # Restore the links and references.
              link_number = 1
              missing_links = ""
              for link_match in link_matches:
                prev_translation_text = translation_text
                translation_text = re.sub(r"DONOTTRANSLATE{}".format(link_number), link_match, translation_text, 1)
                if translation_text == prev_translation_text:
                  print("<!-- ERROR: Missing link #{}. -->".format(link_number))
                  missing_links += link_match
                  num_errors += 1
                link_number += 1
              # Fix Hong Kong Chinese translation of the word "Klingon", which is different from the
              # one used in Taiwan Chinese.
              if language == "zh-TW":
                translation_text = translation_text.replace(u'克林貢',u'克林崗')
              # Missing links and references are appended to the end and may require manual correction.
              line = re.sub(r">(.*)<", ">{}{} [AUTOTRANSLATED]<".format(translation_text, missing_links), line)

            # Rate-limit calls to Google Translate.
            time.sleep(0.01)

        # Check that mismatched brackets were not introduced.
        if not balanced_brackets(line):
          print("<!-- ERROR: Mismatched brackets. -->")

      # Detect end of comment block.
      if " -->" in line:
        in_comment = False

      # The variable 'line' already contains a newline at the end, don't add another.
      print(line, end='')

if num_errors > 0:
  print("*** Number of errors: {} ***".format(num_errors))
