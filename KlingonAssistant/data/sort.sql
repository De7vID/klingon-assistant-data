BEGIN TRANSACTION;
CREATE TEMPORARY TABLE k_backup(_id,entry_name,part_of_speech,definition,synonyms,antonyms,see_also,notes,hidden_notes,components,examples,search_tags,source);
INSERT INTO k_backup SELECT _id,entry_name,part_of_speech,definition,synonyms,antonyms,see_also,notes,hidden_notes,components,examples,search_tags,source FROM Klingon_Canon;
DROP TABLE Klingon_Canon;
CREATE TABLE Klingon_Canon(_id INTEGER PRIMARY KEY,entry_name TEXT,part_of_speech TEXT,definition TEXT,synonyms TEXT,antonyms TEXT,see_also TEXT,notes TEXT,hidden_notes TEXT,components TEXT,examples TEXT,search_tags TEXT,source TEXT);
INSERT INTO Klingon_Canon SELECT _id,entry_name,part_of_speech,definition,synonyms,antonyms,see_also,notes,hidden_notes,components,examples,search_tags,source FROM k_backup SORT BY _id ASC;
DROP TABLE k_backup;
COMMIT;

