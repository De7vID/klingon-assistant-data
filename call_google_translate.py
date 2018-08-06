#!/usr/bin/env python3

# Calls Google Translate to produce translations.
# To use, set "language" and "dest_language" below. (They are normally the same,
# unless Google uses a different language code than we do.) Then fill in
# the definition_[language] fields with "TRANSLATE" or
# "TRANSLATE: [replacement definition]". The latter is to allow for a better
# translation when the original definition is ambiguous, e.g., if the definition
# is "launcher", a better translation might result from
# "TRANSLATE: rocket launcher".

from googletrans import Translator

import fileinput
import re
import time

# TODO: Refactor this and also use in renumber.py.
# Ignore mem-00-header.xml and mem-28-footer.xml because they don't contain entries.
filenames = ['mem-01-b.xml', 'mem-02-ch.xml', 'mem-03-D.xml', 'mem-04-gh.xml', 'mem-05-H.xml', 'mem-06-j.xml', 'mem-07-l.xml', 'mem-08-m.xml', 'mem-09-n.xml', 'mem-10-ng.xml', 'mem-11-p.xml', 'mem-12-q.xml', 'mem-13-Q.xml', 'mem-14-r.xml', 'mem-15-S.xml', 'mem-16-t.xml', 'mem-17-tlh.xml', 'mem-18-v.xml', 'mem-19-w.xml', 'mem-20-y.xml', 'mem-21-a.xml', 'mem-22-e.xml', 'mem-23-I.xml', 'mem-24-o.xml', 'mem-25-u.xml', 'mem-26-suffixes.xml', 'mem-27-extra.xml']

translator = Translator()
language = "zh-HK"
dest_language = "zh-TW"
limit = 250
for filename in filenames:
  with fileinput.FileInput(filename, inplace=True) as file:
    definition = ""
    for line in file:
      definition_match = re.search(r"definition\">?(.+)<", line)
      definition_translation_match = re.search(r"definition_(.+)\">TRANSLATE(?:: (.*))?<", line)

      if (definition_match):
        definition = definition_match.group(1)

      if (limit > 0 and \
          definition != "" and \
          definition_translation_match and \
          language.replace('-','_') == definition_translation_match.group(1)):
        if definition_translation_match.group(2):
          definition = definition_translation_match.group(2)
        translation = translator.translate(definition, src='en', dest=dest_language)
        line = re.sub(r">(.*)<", ">%s [AUTOTRANSLATED]<" % translation.text, line)

        # Rate-limit calls to Google Translate.
        limit = limit - 1
        time.sleep(0.1)

      print(line, end='')
