cat data.json | jq -r '
def fix_links: if . then gsub(":[^{}]+\\}"; "}") | gsub("\n"; "\n   ") else . end;

.qawHaq[] |
":" + .entry_name + ": /" + .part_of_speech + "/ " + (.definition.en|fix_links) +
(if .notes.en then "\n   " + (.notes.en|fix_links) + "\n" else "" end) +
(if .synonyms then "\n   Synonyms: " + (.synonyms|fix_links) + "\n" else "" end) +
(if .antonyms then "\n   Antonyms: " + (.antonyms|fix_links) + "\n" else "" end) +
(if .components then "\n   Components: " + (.components|fix_links) + "\n" else "" end) +
(if .see_also then "\n   See also: " + (.see_also|fix_links) + "\n" else "" end) +
(if .source then "\n   Sources: " + (.source|fix_links) + "\n" else "" end)
' | sed -E 's/^\s+$//' >tlh-en.jargon

cat data.json | jq -r '
def fix_links: if . then gsub(":[^{}]+\\}"; "}") | gsub("\n"; "\n   ") else . end;

.qawHaq[] |
":" + .entry_name + ": /" + .part_of_speech + "/ " + (.definition.fi|fix_links) +
(if .notes.fi and (.notes.fi|contains("TRANSLATE")|not) then "\n   " + (.notes.fi|fix_links) + "\n" elif .notes.fi then "\n   " + (.notes.en|fix_links) + "\n" else "" end) +
(if .synonyms then "\n   Synonyymit: " + (.synonyms|fix_links) + "\n" else "" end) +
(if .antonyms then "\n   Antonyymit: " + (.antonyms|fix_links) + "\n" else "" end) +
(if .components then "\n   Osat: " + (.components|fix_links) + "\n" else "" end) +
(if .see_also then "\n   Katso myös: " + (.see_also|fix_links) + "\n" else "" end) +
(if .source then "\n   Lähteet: " + (.source|fix_links) + "\n" else "" end)
' | sed -E 's/^\s+$//' >tlh-fi.jargon
