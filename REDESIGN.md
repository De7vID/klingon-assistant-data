This directory contains the source files of the Klingon lexicon database. The source files are named `mem-NN-description.xml`, where `NN` is a two-digit number and `description` labels the contents of the file. The @generate_db.sh script concatenates these and processes them using @xml2sql.pl and @xml2json.py to produce qawHaq.db and qawHaq.json, respectively, which are used by Klingon language apps.

The original design of the database was only intended to store English definitions for Klingon entries (words, affixes, phrases, etc.). The fields were as follows:

* `entry_name`
* `part_of_speech`
* `definition`
* `synonyms`
* `antonyms`
* `see_also`
* `notes`
* `hidden_notes`
* `components`
* `examples`
* `search_tags`
* `source`

An explanation of the fields can be found in @mem-00-header.xml.

The schema was modified to accommodate additional languages, by adding additional fields where `LC` is a language code:

* `definition_LC`
* `notes_LC`
* `examples_LC`
* `search_tags_LC`

However, this modification suffered from several problems as the sources of the Klingon language expanded, and more languages were added.

The `definition` field originally held a single English definition from TKD (The Klingon Dictionary). As the years passed, more sources were published, and there started to be yearly events where new vocabulary was revealed. The original `source` field was intended to hold only one source for the definition, but as more sources were added, it became necessary to add multiple sources for a single entry, as in the following examples.

      <column name="source">[1] {TKD:src}, [2] {KGT p.56:src}</column>
      <column name="source">[1] {Saarbrücken qepHom'a' 2021:src}, [2] {Saarbrücken qepHom'a' 2025:src}</column>
      <column name="source">[1] {qep'a' 25 (2018):src}, [2] {Saarbrücken qepHom'a' 2023:src}, [3] {KLI mailing list 2023.12.15:src}</column>
      <column name="source">[1] {TKD 6.6:src}, [2] {KGT p.178-9:src}, [3] {HQ 13.1, p.8-10, Mar. 2004:src}, [4] {Saarbrücken qepHom'a' 2015:src}, [5] {Smithsonian GO FLIGHT app:src}, [6] {paq'batlh 2ed p.130-131:src}</column>

`TKD`, `KGT`, and `paq'batlh` are books with sections and page numbers, `HQ` is an academic journal with volume, issue, page numbers, and date, and the `qep'a'` and `Saarbrücken qepHom'a'` are yearly events. However, the `source` field does not hold any of this information in a structured way, making it difficult for example to find entries with information from the same source, or to validate a source. A source should be treated as a structured entity, and the `source` field of the database should be a list of such entities. Furthermore, individual sources can be associated with specific fields, so that the final `source` is the union of all sources associated with any field. For example, the `definition` field might have sources A and B, while the `notes` field might have sources B and C, so the final `source` field would be A, B, and C.

One bit of structured data which might be useful to note is the relationship between some sources. For example, "SkyBox S27" is a trading card, the text of which was reprinted in the journal HolQeD, issue 5.3, page 15, September 1996, which is represented currently in the database as in the following example:

      <column name="source">[1] {TKDA:src}, [2] {SkyBox S27:src} (reprinted in {HQ 5.3, p.15, Sep. 1996:src}), [3] {Klingon Monopoly:src}</column>

Multiple definitions from different sources had to be combined. This isn't a serious problem for computer applications, but made it difficult to reconstruct E-K (English to Klingon) entries for a print dictionary. For example, in the original TKD, the Klingon word {joq} had E-K entries for "flap, flutter, wave", "flutter, flap, wave", and "wave, flap, flutter". This lexicon stores only the `definition` "flap, flutter, wave", from which the others can be easily derived. Similarly, for {laQ} TKD had "fire, energize (e.g., thrusters)" and "energize, fire (e.g., thrusters)", and this lexicon stores only the former. However, brackets do not always apply to all the comma-separated parts of a definition. For example, the definition of {yotlh} is "field (of land), park (e.g., recreational)". In a print dictionary, the E-K side would have this definition, as well as "park (e.g., recreational), field (of land)". Sometimes a comma is part of a definition, so it isn't as straightforward as splitting on commas to reconstruct the E-K lookups. Here are some examples of definitions as they exist in this lexicon, the permutable parts, the parenthetical information which are applicable to all the parts, and the E-K lookups which are desired to be reconstructed from them.

definition: flap, flutter, wave
  part: flap
  part: flutter
  part: wave
E-K lookups:
    flap, flutter, wave
    flutter, flap, wave
    wave, flap, flutter

definition: fire, energize (e.g., thrusters)
  part: fire
  part: energize
  parenthetical: e.g., thrusters
E-K lookups:
    fire, energize (e.g., thrusters)
    energize, fire (e.g., thrusters)

definition: field (of land), park (e.g., recreational)
part: field (of land)
part: park (e.g., recreational)
E-K lookups:
    field (of land), park (e.g., recreational)
    park (e.g., recreational), field (of land)

definition: fire, shoot (torpedo, rocket, missile)
  part: fire
  part: shoot
  parenthetical: torpedo, rocket, missile
E-K lookups:
    fire, shoot (torpedo, rocket, missile)
    shoot, fire (torpedo, rocket, missile)

definition: cousin (cross-cousin; child of {'IrneH:n} or {'e'mam:n})
  part: cousin
  parenthetical: cross-cousin; child of {'IrneH:n} or {'e'mam:n}
E-K lookups:
    cousin (cross-cousin; child of {'IrneH:n} or {'e'mam:n})

definition: sink for cleaning hands, face, food, etc.
  part: sink for cleaning hands, face, food, etc.
E-K lookups:
    sink for cleaning hands, face, food, etc.

definition: structure, organization (the way things fit together; the arrangement of the parts of something bigger)
  part: structure
  part: organization
  parenthetical: the way things fit together; the arrangement of the parts of something bigger

For "be" verbs (which have `part_of_speech` set to `v:is`), the E-K lookups should be sorted by the word after "be". For example:

definition: be hostile, be malicious, be unfriendly, be antagonistic
  part: be hostile
  part: be malicious
  part: be unfriendly
  part: be antagonistic
E-K lookups:
    hostile, be hostile, be malicious, be unfriendly, be antagonistic
    malicious, be malicious, be hostile, be unfriendly, be antagonistic
    unfriendly, be unfriendly, be hostile, be malicious, be antagonistic
    antagonistic, be antagonistic, be hostile, be malicious, be unfriendly

The next case is a bit tricky, as the parts contain internal commas. Furthermore, permuting the parts naively to generate the E-K lookups would produce two entries next to each other in the E-K list, which is undesirable. So each part should have an optional keyword which is used for sorting the E-K lookups.

definition: travel with a purpose, for a specific reason; travel on a mission
  part: travel with a purpose, for a specific reason
  part: travel on a mission
    keyword: mission
E-K lookups:
    travel with a purpose, for a specific reason; travel on a mission
    mission, travel on a mission; travel with a purpose, for a specific reason

There might be other cases of `definition` data with commas, semicolons, and brackets which need special handling, which need to be determined by examining the data.

The `synonyms`, `antonyms`, and `see_also` fields are straightforward pointers to other entries in the lexicon.

The `notes` field often contains information from multiple sources, so really it should hold multiple items each of which is associated with a specific source. Some notes have no source. For example:

entry_name: lu
definition: fall (suffer loss of status)
  part: fall (suffer loss of status)
note: See {pum:v:2} for a literal fall.
note: {lu qeng:n:name,nolink} "The Fall of Kang" is a famous poem by G'trok.
  source: KGT, p.107

This is represented in the existing database (modulo whitespace) as:

      <column name="notes">See {pum:v:2} for a literal fall.

      {lu qeng:n:name,nolink} "The Fall of Kang" is a famous poem by G'trok.[1, p.107]</column>
      <column name="source">[1] {KGT:src}</column>

Some notes have multiple sources. For example:

entry_name: QIch wab Ho'DoS
definition: pronunciation
note: To fully understand the sounds of Klingon, it is recommended that you purchase {The Klingon Dictionary:src}, which has a fuller description of the sounds, as well as the audio recordings {Conversational Klingon:src} and {Power Klingon:src}, in which you can hear them spoken.
  source: TKD
  source: CK
  source: PK

Some `note` entries are repeated across different lexicon entries. The following appears in the `notes` field of each of the musical scale entries:

note: The tones of the Klingon musical scale are: {yu:n}, {bIm:n}, {'egh:n}, {loS:n:2}, {vagh:n:2}, {jav:n:2}, {Soch:n:2}, {chorgh:n:2}, {yu:n:nolink}.
  source: KGT

Similarly, each part of a `definition` can have its own source(s):

definition: field (of land), park (e.g., recreational)
  part: field (of land)
    source: TKD
  part: park (e.g., recreational)
    source: Saarbrücken qepHom'a' 2016

    <column name="source">[1] {TKD:src}, [2] {Saarbrücken qepHom'a' 2016:src}</column>

The `hidden_notes` field is not consumed by any application, but is intended for the maintainers of the lexicon to have additional information about an entry which is not visible to end users. If it makes sense, it can be represented differently than other fields.

The `components` field's primary purpose is to list the components which make up a complex entry, such as a sentence. For example:

      <column name="entry_name">batlh bIHeghjaj.</column>
      <column name="components">{batlh:adv}, {bI-:v}, {Hegh:v}, {-jaj:v}</column>

However, the field has also been repurposed to link nouns which are "inherently plural" in Klingon. (This is a concept where a word is grammatically singular, but semantically plural.) For example:

      <column name="entry_name">mang</column>
      <column name="part_of_speech">n:being,inhps</column>
      <column name="components">{negh:n}</column>

      <column name="entry_name">negh</column>
      <column name="part_of_speech">n:being,inhpl</column>
      <column name="components">{mang:n}</column>

These are different things and should probably have been represented differently.

The `examples` field was originally a list of pointers to other entries, like `see_also`. However, it can now be rather complex. First, here are some examples of simple cases:

      <column name="entry_name">leS</column>
      <column name="examples">{wa'leS:n}, {cha'leS:n}</column>

      <column name="entry_name">lIj</column>
      <column name="examples">{qeylIS'e' lIjlaHbe'bogh vay':n:name}</column>

      <column name="entry_name">lI'</column>
      <column name="examples">{Qu'vaD lI' net tu'bej.:sen}</column>

With the publication of books written in Klingon such as the paq'batlh, the `examples` field (and its translation `examples_LC` fields) can become quite complex:

      <column name="entry_name">yeq</column>
      <column name="examples">
    ▶ {HarghmeH yeq chaH:sen:nolink}
       {molor HI''a' luSuv:sen:nolink}
       {lughIjlu'be' 'ej pujHa' 'e' lu'aghmeH Suv:sen:nolink}
      "United to do battle together!
       Against the tyrant Molor!
       Against fear and against weakness!"[2, p.122-123]
    ▶ {nIteb chegh molor ngIq ghoqwI':sen:nolink}
       {joqwI''e' cha'bogh qeylIS:sen:nolink}
       {luDel 'e' ra' molor:sen:nolink}
      "One by one Molor's scouts return,
       He asks them which banner
       Kahless marches under."
      {lujang meQboghnom 'oH:sen:nolink}
       {yeqchu'taHghach Daw' je:sen:nolink}
       {'oS joqwI':sen:nolink}
      "They reply it is the meQboghnom,
       The banner of unity
       And revolution."[2, p.138-141]</column>
          <column name="examples_de">
    ▶ {HarghmeH yeq chaH:sen:nolink}
       {molor HI''a' luSuv:sen:nolink}
       {lughIjlu'be' 'ej pujHa' 'e' lu'aghmeH Suv:sen:nolink}
      "Vereint, gemeinsam zu kämpfen!
       Gegen den Tyrannen Molor!
       Gegen Angst und gegen Schwäche!"[2, S.122-123]
    ▶ {nIteb chegh molor ngIq ghoqwI':sen:nolink}
       {joqwI''e' cha'bogh qeylIS:sen:nolink}
       {luDel 'e' ra' molor:sen:nolink}
      "Mann für Mann kehrten Molors Späher zurück,
       Er fragte sie welche Flagge
       Kahless mit sich trug."
      {lujang meQboghnom 'oH:sen:nolink}
       {yeqchu'taHghach Daw' je:sen:nolink}
       {'oS joqwI':sen:nolink}
      "Sie sagten es ist der meQboghnom,
       Die Flagge der Einheit
       Und Revolution."[2, S.138-141]</column>
          <column name="examples_fr">
    ▶ {HarghmeH yeq chaH:sen:nolink}
       {molor HI''a' luSuv:sen:nolink}
       {lughIjlu'be' 'ej pujHa' 'e' lu'aghmeH Suv:sen:nolink}
      "Unis pour lutter ensemble !
       Contre the tyran Molor !
       Contre la peur et la faiblesse !"[2, p.122-123]
    ▶ {nIteb chegh molor ngIq ghoqwI':sen:nolink}
       {joqwI''e' cha'bogh qeylIS:sen:nolink}
       {luDel 'e' ra' molor:sen:nolink}
      "Un par un, les éclaireurs de Molor retournent,
       Il demande qu'ils décrivent
       Le drapeau que montre Kahless."
      {lujang meQboghnom 'oH:sen:nolink}
       {yeqchu'taHghach Daw' je:sen:nolink}
       {'oS joqwI':sen:nolink}
      "Ils répondent il est le meQboghnom,
       Le drapeau représente
       L'unite et la révolution."[2, p.138-141]</column>
      <column name="source">[1] {TKD:src}, [2] {paq'batlh 2ed:src}, [3] {KLI mailing list 2022.05.27:src}</column>

The same example may appear in multiple lexicon entries, and it is undesirable to have duplicate copies including duplicable translations, which may get out of sync. Therefore, examples should be stored as separate entities which can be referenced from multiple lexicon entries. Each example entity can have multiple translations associated with it.

The `search_tags_LC` are not direct translations of `search_tags`. These fields are intended for computer applications where a user might search for lexicon entries using words which not in the definition but are somehow related to it. This can of course vary by language.

The `mem-NN-description.xml` files have gotten very large. Ideally, the database should be constructed from many smaller source files each of which is easier to manage.

The task is to resign the database schema to address these issues, and to write migration scripts to convert the existing database to the new schema. The goal is to support existing use cases while making it much easier to produce a print dictionary. Come up with the design first before doing any implementation.
