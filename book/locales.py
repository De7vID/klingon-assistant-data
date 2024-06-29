#!/usr/bin/env python3

EN = {
    "id": "en",

    "english": "English",
    "finnish": "Finnish",
    "german": "German",
    "russian": "Russian",

    "dictionary": "Dictionary",
    "proofreader": "Proofreader",
    "corpus": "Corpus",
    "check": "Check",
    "no_errors": "No errors were found.",
    "errors_marked": "Detected errors are marked on the text below.",

    "unknown": "unknown",
    "adjective": "stative verb",
    "transitive verb": "tr. verb",
    "possibly transitive verb": "possibly tr. verb",
    "intransitive verb": "itr. verb",
    "possibly intransitive verb": "possibly itr. verb",
    "verb prefix": "prefix",
    "verb suffix": "verb suffix",
    "verb": "verb",
    "noun suffix": "noun suffix",
    "noun": "noun",
    "question word": "ques.",
    "adverb": "adverb",
    "conjunction": "conj.",
    "exclamation": "excl.",
    "sentence": "sent.",

    "plural": "plural",
    "singular": "singular",

    "slang": "slang",
    "regional": "reg.",
    "archaic": "archaic",
    "hypothetical": "hyp.",
    "extracanonical": "extcan.",

    "examples": "Examples",
    "components": "Components",
    "derived": "Derived words",
    "synonyms": "Synonyms",
    "antonyms": "Antonyms",
    "see_also": "See also",
    "source": "Sources",
    "hidden_notes": "Hidden notes",

    "wiki": "Search in the Dictionary of Contemporary Klingon (Klingon Wiki)",
    "klingonska": "Search in the Klingonska Archive of Okrandian Canon",

    "dictionary_info": "About the dictionary",
    "search": "Search",
}

FI = {
    "id": "fi",

    "english": "Englanti",
    "finnish": "Suomi",
    "german": "Saksa",
    "russian": "Venäjä",

    "dictionary": "Sanakirja",
    "proofreader": "Kielentarkistin",
    "corpus": "Korpus",
    "check": "Tarkista",
    "no_errors": "Virheitä ei löytynyt.",
    "errors_marked": "Löydetyt virheet on merkitty alla olevaan tekstiin.",

    "unknown": "tuntematon",
    "adjective": "adjektiivi",
    "transitive verb": "tr. verbi",
    "possibly transitive verb": "todn. tr. verbi",
    "intransitive verb": "itr. verbi",
    "possibly intransitive verb": "todn. itr. verbi",
    "verb prefix": "etuliite",
    "verb suffix": "pääte",
    "verb": "verbi",
    "noun suffix": "liite",
    "noun": "substantiivi",
    "question word": "kysymyssana",
    "adverb": "adverbi",
    "conjunction": "konjunktio",
    "exclamation": "huudahdus",
    "sentence": "esimerkkilause",

    "plural": "monikko",
    "singular": "yksikkö",

    "slang": "slangia",
    "regional": "alueell.",
    "archaic": "vanh.",
    "hypothetical": "hyp.",
    "extracanonical": "ekstrakan.",

    "examples": "Esimerkkejä",
    "components": "Osat",
    "derived": "Johdetut sanat",
    "synonyms": "Synonyymi",
    "antonyms": "Antonyymi",
    "see_also": "Katso myös",
    "source": "Lähteet",
    "hidden_notes": "Lisätietoja",

    "wiki": "Etsi Klingon Wikin sanakirjasta",
    "klingonska": "Etsi Klingonskan kaanonin arkistosta",

    "dictionary_info": "Tietoa sanakirjasta",
    "search": "Hae",
}

DE = {
    "id": "de",

    "english": "Englisch",
    "finnish": "Finnisch",
    "german": "Deutsch",
    "russian": "Russisch",

    "dictionary": "Wörterbuch",
    "proofreader": "Sprachprüfer",
    "corpus": "Sprachkorpus",
    "check": "Überprüfen",
    "no_errors": "Es wurden keine Fehler gefunden.",
    "errors_marked": "Fehler wurden im unten eingefügten Text markiert.",

    "tuntematon": "unbekannt",
    "adjective": "Zustandsverb",
    "transitive verb": "trans. Verb",
    "possibly transitive verb": "mögl. trans. Verb",
    "intransitive verb": "intr. Verb",
    "possibly intransitive verb": "mögl. itr. Verb",
    "verb prefix": "Verbpräfix",
    "verb suffix": "Verbsuffix",
    "verb": "Verb",
    "noun suffix": "Substantivsuffix",
    "noun": "Substantiv",
    "question word": "Fragewort",
    "adverb": "Adverb",
    "conjunction": "Bindewort",
    "exclamation": "Ausruf",
    "sentence": "Satz",

    "plural": "Mehrzahl",
    "singular": "Einzahl",

    "slang": "Slang",
    "regional": "regional",
    "archaic": "veraltet",
    "hypothetical": "hypothet.",
    "extracanonical": "extrakanon.",

    "examples": "Beispiele",
    "components": "Komponenten",
    "derived": "Wortbildungen",
    "synonyms": "Synonyme",
    "antonyms": "Antonyme",
    "see_also": "Siehe auch",
    "source": "Quellen",
    "hidden_notes": "Versteckte Notizen",

    "wiki": "Suche im Klingonisch-Wiki",
    "klingonska": "Suche im Klingonska Kanonarchiv",

    "dictionary_info": "Über das Wörterbuch",
    "search": "Suchen",
}

RU = {
    "id": "ru",

    "english": "английский",
    "finnish": "финский",
    "german": "немецкий",
    "russian": "русский",

    "dictionary": "Словарь",
    "proofreader": "Корректор",
    "corpus": "Текстовый корпус",
    "check": "Проверить",
    "no_errors": "Ошибок не найдено.",
    "errors_marked": "Обнаруженные ошибки отмечены в тексте ниже.",

    "unknown": "неизвестно",
    "adjective": "прилагательное",
    "transitive verb": "перех. гл.",
    "possibly transitive verb": "возможно перех. гл.",
    "intransitive verb": "неперех. гл.",
    "possibly intransitive verb": "возможно неперех. гл.",
    "verb prefix": "префикс гл.",
    "verb suffix": "суффикс гл.",
    "verb": "глагол",
    "noun suffix": "суффикс сущ.",
    "noun": "существительное",
    "question word": "вопросительное сл.",
    "adverb": "наречие",
    "conjunction": "союз",
    "exclamation": "восклицание",
    "sentence": "пример предлж.",

    "plural": "множественное число",
    "singular": "единственное число",

    "slang": "сленг",
    "regional": "региональный",
    "archaic": "устаревший",
    "hypothetical": "гипотетический",
    "extracanonical": "внеканонический",

    "examples": "Примеры",
    "components": "Компоненты",
    "derived": "Производные слова",
    "synonyms": "Синонимы",
    "antonyms": "Антонимы",
    "see_also": "См. также",
    "source": "Источники",
    "hidden_notes": "Скрытые заметки",

    "wiki": "Искать в словаре современного клингона (Klingon Wiki)",
    "klingonska": "Искать в архиве канона Klingonska",

    "dictionary_info": "О словаре",
    "search": "Поиск",
}

locale_map = {
    "en": EN,
    "fi": FI,
    "de": DE,
    "ru": RU,
}
