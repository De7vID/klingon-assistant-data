import re
import argparse
from pathlib import Path
import fileinput
import sys

langs = ["de", "fa", "sv", "ru", "zh_HK", "pt", "fi"]

parser = argparse.ArgumentParser()
parser.add_argument("lang", choices=langs)
args = parser.parse_args()

xmlfiles = Path(".").glob("mem-*.xml")

stdout = sys.stdout

quitting = False
for xmlfile in xmlfiles:
    if quitting:
        break

    with fileinput.FileInput(xmlfile, inplace=True) as file:
        definitions = {}
        entry_name = ""
        entry_comment = ""
        part_of_speech = ""
        indent = ""
        for line in file:
            if quitting:
                print(line, end="")
                continue

            if m := re.search(r"^(\s*)<[^>]*definition\">(.*)<", line):
                definitions["en"] = m.group(2)

            elif m := re.search(r"^(\s*)<[^>]*definition_(.*)\">(.*)<", line):
                definitions[m.group(2)] = m.group(3)

            elif m := re.search(r"^(\s*)<[^>]*entry_name\">(.*)<", line):
                entry_name = m.group(2)
                indent = m.group(1)

            elif m := re.search(r"^(\s*)<[^>]*part_of_speech\">(.*)<", line):
                part_of_speech = m.group(2)

            elif line.strip().startswith("<!--") and entry_name and not part_of_speech:
                entry_comment = line.strip()

            elif len(definitions) > 0:
                if "TRANSLATE" in definitions[args.lang] or len(definitions[args.lang]) == 0:
                    print(f"--- {entry_name} ({part_of_speech}) ---", file=stdout)
                    for lang in ["en"] + langs:
                        if len(definitions[lang]) > 0 and "TRANSLATE" not in definitions[lang]:
                            print(lang.upper() + ": " + definitions[lang], file=stdout)

                    translation = definitions[args.lang].replace(" [AUTOTRANSLATED]", "").strip()
                    print("TRANSLATION:", translation, file=stdout)
                    print("Please accept the machine translation or write a new translation.", file=stdout)
                    print("(ENTER accepts, S skips, Q quits)> ", end="", file=stdout)
                    stdout.flush()
                    choice = input()
                    if choice == "":
                        definitions[args.lang] = translation

                    elif choice == "S":
                        pass

                    elif choice == "Q":
                        quitting = True

                    else:
                        definitions[args.lang] = choice

                print(indent + f'<column name="entry_name">{entry_name}</column>')
                if entry_comment:
                    print(indent + entry_comment)

                print(indent + f'<column name="part_of_speech">{part_of_speech}</column>')
                print(indent + f'<column name="definition">{definitions["en"]}</column>')
                for lang in langs:
                    print(indent + f'<column name="definition_{lang}">{definitions[lang]}</column>')
                
                entry_name = ""
                entry_comment = ""
                part_of_speech = ""
                definitions = {}
                print(line, end="")

            else:
                print(line, end="")

