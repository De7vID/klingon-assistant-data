#!/usr/bin/env python3

# Calls Google Translate to produce translations. To use, fill in any missing
# definition_[language] fields in the mem-*.xml files with "TRANSLATE" or
# "TRANSLATE: [replacement definition]". The latter is to allow for a better
# translation when the original definition is ambiguous, e.g., if the
# definition is "launcher", a better translation might result from "TRANSLATE:
# rocket launcher".

# Commands to add the required fields for a new language with language code "xx":
# sed -i $"s/\(\s*\)\(<column name=\"synonyms\">\)/\1<column name=\"definition_xx\">TRANSLATE<\/column>\\n\1\2/g" mem-*.xml
# sed -i $"s/\(\s*\)\(<column name=\"hidden_notes\">\)/\1<column name=\"notes_xx\"><\/column>\\n\1\2/g" mem-*.xml
# sed -i $"s/\(\s*\)\(<column name=\"search_tags\">\)/\1<column name=\"examples_xx\"><\/column>\\n\1\2/g" mem-*.xml
# sed -i $"s/\(\s*\)\(<column name=\"source\">\)/\1<column name=\"search_tags_xx\"><\/column>\\n\1\2/g" mem-*.xml

from googletrans import Translator

import fileinput
import re
import time

# TODO: Refactor this and also use in renumber.py.
# Ignore mem-00-header.xml and mem-28-footer.xml because they don't contain entries.
filenames = ['mem-01-b.xml', 'mem-02-ch.xml', 'mem-03-D.xml', 'mem-04-gh.xml', 'mem-05-H.xml', 'mem-06-j.xml', 'mem-07-l.xml', 'mem-08-m.xml', 'mem-09-n.xml', 'mem-10-ng.xml', 'mem-11-p.xml', 'mem-12-q.xml', 'mem-13-Q.xml', 'mem-14-r.xml', 'mem-15-S.xml', 'mem-16-t.xml', 'mem-17-tlh.xml', 'mem-18-v.xml', 'mem-19-w.xml', 'mem-20-y.xml', 'mem-21-a.xml', 'mem-22-e.xml', 'mem-23-I.xml', 'mem-24-o.xml', 'mem-25-u.xml', 'mem-26-suffixes.xml', 'mem-27-extra.xml']

# Supported languages. Map to another language code if Google Translate does not exactly support the same language.
supported_languages_map = {
  "de": "de",
  "fa": "fa",
  "sv": "sv",
  "ru": "ru",
  "zh-HK": "zh-TW",
  "pt": "pt",
}

translator = Translator()
for filename in filenames:
  with fileinput.FileInput(filename, inplace=True) as file:
    definition = ""
    for line in file:
      definition_match = re.search(r"definition\">(.*)<", line)
      definition_translation_match = re.search(r"definition_(.+)\">TRANSLATE(?:: (.*))?<", line)

      # Get the source (English) text to translate.
      if (definition_match):
        definition = definition_match.group(1)
        if not definition:
          print("<!-- ERROR: Missing definition. -->")

      if (definition and definition_translation_match):
        language = supported_languages_map.get(definition_translation_match.group(1).replace('_','-'), "")
        if language != "":
          # Check for an override like "TRANSLATE: rocket launcher".
          if definition_translation_match.group(2):
            definition = definition_translation_match.group(2)

          # Preserve definitions of the form "{...}" verbatim.
          if definition.startswith('{') and definition.endswith('}'):
            line = re.sub(r">(.*)<", ">%s<" % definition, line)
          else:
            translation = translator.translate(definition, src='en', dest=language)
            line = re.sub(r">(.*)<", ">%s [AUTOTRANSLATED]<" % translation.text, line)

            # Rate-limit calls to Google Translate.
            time.sleep(0.01)

      print(line, end='')
