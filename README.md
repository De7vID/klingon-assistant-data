klingon-assistant-data
======================

Klingon language data files for **boQwI'** and associated apps.

The `notes` fields are for typical users of the lexicon. An attempt should be
made to keep information there "in-universe". The `hidden_notes` field is for
(typically) "out-of-universe" information such as puns (what Marc Okrand calls
"coincidences"), or background stories about how a word or phrase was invented
(such as having to retrofit a movie edit). For some entries (e.g., {Hov leng:n}
or the names of actors or actresses), keeping the notes "in-universe" might not
be possible, so this is not a strict requirement.

The `entry_name` field should exactly match how the definition appears in the
original source if possible. This is important as the database is used by
software which may compare its entries to other lexicons. In particular, KWOTD
(Klingon Word Of The Day) functionality in {boQwI'} partially depends on
matching the `entry_name` to the word or phase received from the {Hol 'ampaS}
server. A mismatch may result in failure to retrieve the KWOTD. However, full
sentences should have final punctuation for consistency. (If the English
translation has final punctuation, the Klingon sentence should use the same
punctuation mark, but otherwise it should end in a period, or an exclamation
mark if that is more appropriate.)

If a definition appears multiple times in the same source, the broadest
definition should be used. For example, {tu':v} appears as "discover, find,
observe, notice" in TKD in the K-E side, but also as just "find, observe" in
the body text, as well as separately under each of those four words in the E-K
side. The K-E definition should be used in this case. Contradictions (e.g.,
differences between K-E and E-K definitions) and errors should be noted in
`hidden_notes`.

If an entry is defined differently in different sources, the definitions should
be reconciled, and the reconciliation noted under `hidden_notes` or `notes` as
appropriate. Sometimes, it may be appropriate to split a word into multiple
entries. For example, {meS:v} has separate entries for "tie a knot" and
"encrypt", even though the latter meaning is obviously derived from the former.
There is some discretion in whether an entry should be split up or not.

Translations of the `definition` field can take liberties as necessary to
convey the meaning. For example, it may be the case that disambiguating text in
brackets in the original English definition is not necessary in another
language, or conversely, that disambiguating text needs to be added. Words
which are in brackets or quotes may need to be added as `search_tags` (in the
corresponding language as appropriate) if they are likely to be searched. (A
quirk of the database system means that words in the `definition` fields which
are enclosed in brackets or quotes are not tokenised as search terms
automatically.)

The `notes` fields in languages other than English should be direct
translations if possible, but may differ if it is necessary to include
information specific to a language. For example, the German entry for
{ngech:n:2} notes a common misunderstanding specific to the German language.
Every link and source referenced in the English notes should be referenced in
the translations (to the degree that it is possible).

When adding a new entry, the `blank.xml` template should be used. There is a
script `call_google_translate.py` which may be used to automatically translate
the `definition` and `notes` fields. An attempt will be made to use Google
Translate to translate any non-English `definition` or `notes` field which
contain only the content "TRANSLATE". (The non-English `definition` fields are
already filled in with "TRANSLATE" in the template.) After calling the
translation script, it may be necessary to do some postprocessing. Instructions
are found in the comments to the script file.

The database source files are divided into letters, with additional sections for
suffixes, extra entries, and example entries. For the purposes of this database,
"canon" is defined as having come from (or approved by) Marc Okrand. Canon
words and phrases which appear in pedagogical sources (books, audiotapes or CDs,
software, and **qep'a'** or **qepHom**) belong in the main section (i.e., any
file other than `extra` or `examples`). The `extra` section is for miscellaneous
entries such as words of uncertain provenance or known not to have come from or
been approved by Marc Okrand (e.g., they were invented by the author of a Star
Trek novel), transliterations of Terran fauna, flora, or place names not
accepted as native Klingon words (such as strawberry or New York), and things
which are low-priority when searching or don't belong elsewhere. It is also for
canon sentences which appear in the TV shows or movies, or on DVD cases or
advertising materials (because, from an "in-universe" point of view, these
would not normally be found in a dictionary or phrasebook, unless they happen to
be proverbs or such). The `examples` section is for entries created for
pedagogical purposes (such as Beginner's Conversation sentences) or to make
search easier (because a search term corresponds to a verb with suffixes or a
complex noun). It also contains canon examples, if they are parenthetical
(created by Okrand merely for the purpose of explaining an entry which is in
the main section). Entries from the `extra` and `examples` sections are excluded
when using the "random" function within the Android app.

It is a convention to link only once to another entry within each entry.
Subsequent references to another entry should be tagged with `nolink`. If there
is already a link to another entry in `notes`, then the target entry should not
typically appear again in `see_also`.

Commits containing manual translations should change only one language (though
occasionally it may make sense to translate one or a few entries into multiple
languages, such as after a large vocabulary reveal at an event such as the KLI
{qep'a'} or Saarbrücken {qepHom'a'}). Commits created using the
`commit_submissions.py` script are exempt from this rule, but must be manually
reviewed.

There is a script `review_changes.sh` which takes in a language code and an
optional commit (which defaults to `upstream/master` if omitted). This should
be used by translators to check translations before a pull request is made.

After changes to the database, it is important to run the `write_db.sh` script
(in the [Android](https://github.com/De7vID/klingon-assistant-android) repo) to
ensure that the database still compiles. Running this script also updates the
`EXTRA` file (which marks where the "extra" section of the database begins).
Optionally, one may also run the `check_audio_files.pl` script (in the
`scripts` directory of the [main](https://github.com/De7vID/klingon-assistant)
repo) to see if any syllables have been added which are not available in the
[TTS](https://github.com/De7vID/klingon-assistant-tts-android).

Conventions for translators
---------------------------

### German

- All adjectivally used verbs should be translated as "[quality] sein", not
just the quality as an adjective.

- Any suggestions and recommendations ("for x, use y") should be written in a
neutral form ("for x, y is used"). The autotranslated sentences use the very
formal "Sie" which looks too formal for this app. To avoid discussions about
using the informal "du", such phrases can be rearranged into general statements
like "dieses Wort wird verwendet" ("this word is used").

### Chinese (Hong Kong)

- The Cantonese transliteration of "Klingon" used in Hong Kong is "克林崗", and
  not "克林貢" which is used in Taiwanese Mandarin (and which is returned by
  Google Translate for "Traditional Chinese").

### Finnish

- Translations need not to be direct translations from TKD entries, but later
  clarifications and additions must be considered when choosing the Finnish word.
  The Finnish translation may have less or more words than the English one, if
  they are not necessary to understand the translation. Parenthesized notes may
  be similarly removed if they are not necessary.
- Adjectives are translated as "olla [adjektiivi]"
- Fictive things (not including proper names) are translated as "eräs [X:ää]
  muistuttava [Y]" tai "eräs [Y]" where Y is eg. "eläin" (this includes all
  Klingon animals that are only glossed as their Earth equivalent in the English
  dictionary)
- If the object of a verb is inflected in Finnish in other case than accusative
  (jokin) or partitive (jotakin), the Finnish definition must include the word
  "jokin" inflected appropriately (for example. **parHa'** "pitää jostakin").
- Remember to use the correct transitivity (eg. pyöriä **jIr** vs. pyörittää
  **jIrmoH**).