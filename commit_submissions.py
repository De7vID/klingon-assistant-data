#!/usr/bin/env python3

from collections import namedtuple

import csv
import fileinput
import re
import urllib.request

# Read the CSV file exported from Google Forms.
SUBMISSIONS_CSV_URL = "https://docs.google.com/feeds/download/spreadsheets/Export?key=1hkmsq5bkLmQAwmWv8d7UmKR7j6m7wqUgo0wZNIRrR-A&exportFormat=csv"
response = urllib.request.urlopen(SUBMISSIONS_CSV_URL)
content = response.read().decode('utf8')
reader = csv.reader(content.splitlines())

# Create a named tuple using the first row of the exported spreadsheet.
Submission = namedtuple("Submission", next(reader))

# Read the submissions.
submissions = [Submission(*r) for r in reader]

# TODO: Refactor this and also use in renumber.py.
# Ignore mem-00-header.xml and mem-28-footer.xml because they don't contain entries.
filenames = ['mem-01-b.xml', 'mem-02-ch.xml', 'mem-03-D.xml', 'mem-04-gh.xml', 'mem-05-H.xml', 'mem-06-j.xml', 'mem-07-l.xml', 'mem-08-m.xml', 'mem-09-n.xml', 'mem-10-ng.xml', 'mem-11-p.xml', 'mem-12-q.xml', 'mem-13-Q.xml', 'mem-14-r.xml', 'mem-15-S.xml', 'mem-16-t.xml', 'mem-17-tlh.xml', 'mem-18-v.xml', 'mem-19-w.xml', 'mem-20-y.xml', 'mem-21-a.xml', 'mem-22-e.xml', 'mem-23-I.xml', 'mem-24-o.xml', 'mem-25-u.xml', 'mem-26-suffixes.xml', 'mem-27-extra.xml']

# Cycle through the database files and insert the submissions.
for filename in filenames:
  with fileinput.FileInput(filename, inplace=True) as file:
    matches = []
    for line in file:
      # Note that Google Sheets swallows any initial apostrophe, so take that into account.
      entry_name_match = re.search(r"entry_name\">'?(.+)<", line)
      part_of_speech_match = re.search(r"part_of_speech\">(.+)<", line)
      definition_translation_match = re.search(r"definition_(.+)\">(.*)<", line)

      # Select submissions matching entry_name.
      if (entry_name_match):
        matches = [r for r in submissions if r.entry_name == entry_name_match.group(1)]

      # Narrow submissions to those matching part_of_speech also.
      if (matches != [] and part_of_speech_match):
        matches = [r for r in matches if r.part_of_speech == part_of_speech_match.group(1)]

      # Extract submissions matching the language and insert them.
      if (matches != [] and definition_translation_match):
        language_match = [r for r in matches if r.language.replace('-','_') == definition_translation_match.group(1)]
        if (language_match != []):

          # Do an in-place substitution for the submitted translation.
          # (If multiple matching submissions exist, only the last one is used.)
          line = re.sub(r">(.*)<", ">%s<" % language_match[-1].definition_translation, line)

          # Mark submission as used by removing it.
          submissions = [s for s in submissions if s not in language_match]

      print(line, end='')

if (submissions != []):
  print("Warning: submissions not used.")
  print(submissions)
else:
  print("Qapla'!")
