import fileinput
from pathlib import Path
import xml.etree.ElementTree as ET

filenames = sorted(Path(".").glob("mem-*.xml"))

languages = [
    "de",
    "fa",
    "fi",
    "pt",
    "ru",
    "sv",
    "zh_HK",
]

def read_english_entries():
    concat = ""
    mem = fileinput.FileInput(files=filenames)
    for line in mem:
        concat += line
    mem.close()
    return ET.fromstring(concat)

def read_mixins():
    for lang in languages:
        for filename in filenames:
            path = Path(lang) / filename
            if not path.exists():
                continue

            element = ET.parse(path).getroot()
            for mixin in element.findall("mixin"):
                yield mixin

def merge():
    english = read_english_entries()
    mixins = read_mixins()

    entry_index = {}
    for element in english.findall(f"database/table"):
        entry_index[element.attrib["uid"]] = element

    for mixin in mixins:
        target_uid = mixin.attrib["target"]
        target_element = entry_index.get(target_uid, None)
        if target_element is None:
            print(f"{target_uid} not found in english")
            continue

        target_element.extend(mixin)

    return english

def main():
    data = merge()
    print(ET.tostring(data, encoding="unicode"))

if __name__ == "__main__":
    main()