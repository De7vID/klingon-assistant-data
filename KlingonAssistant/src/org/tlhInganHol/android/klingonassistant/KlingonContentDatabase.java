/*
 * Copyright (C) 2012 De'vID jonpIn (David Yonge-Mallo)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.tlhInganHol.android.klingonassistant;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;

import android.app.SearchManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.database.SQLException;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteDiskIOException;
import android.database.sqlite.SQLiteException;
import android.database.sqlite.SQLiteOpenHelper;
import android.database.sqlite.SQLiteQueryBuilder;
import android.os.Environment;
import android.preference.PreferenceManager;
import android.provider.BaseColumns;
import android.util.Log;
import android.widget.Toast;

/**
 * Contains logic to return specific entries from the database, and load the database table when it
 * needs to be created.
 */
public class KlingonContentDatabase {
  private static final String                  TAG                          = "KlingonContentDatabase";

  // The columns included in the database table.
  public static final String                   KEY_ID                       = BaseColumns._ID;
  public static final String                   KEY_ENTRY_NAME               = "entry_name";
  public static final String                   KEY_PART_OF_SPEECH           = "part_of_speech";
  public static final String                   KEY_DEFINITION               = "definition";
  public static final String                   KEY_SYNONYMS                 = "synonyms";
  public static final String                   KEY_ANTONYMS                 = "antonyms";
  public static final String                   KEY_SEE_ALSO                 = "see_also";
  public static final String                   KEY_NOTES                    = "notes";
  public static final String                   KEY_HIDDEN_NOTES             = "hidden_notes";
  public static final String                   KEY_COMPONENTS               = "components";
  public static final String                   KEY_EXAMPLES                 = "examples";
  public static final String                   KEY_SEARCH_TAGS              = "search_tags";
  public static final String                   KEY_SOURCE                   = "source";
  // Languages other than English.
  public static final String                   KEY_DEFINITION_DE            = "definition_de";

  // The order of the keys to access the columns.
  public static final int                      COLUMN_ID                    = 0;
  public static final int                      COLUMN_ENTRY_NAME            = 1;
  public static final int                      COLUMN_PART_OF_SPEECH        = 2;
  public static final int                      COLUMN_DEFINITION            = 3;
  public static final int                      COLUMN_SYNONYMS              = 4;
  public static final int                      COLUMN_ANTONYMS              = 5;
  public static final int                      COLUMN_SEE_ALSO              = 6;
  public static final int                      COLUMN_NOTES                 = 7;
  public static final int                      COLUMN_HIDDEN_NOTES          = 8;
  public static final int                      COLUMN_COMPONENTS            = 9;
  public static final int                      COLUMN_EXAMPLES              = 10;
  public static final int                      COLUMN_SEARCH_TAGS           = 11;
  public static final int                      COLUMN_SOURCE                = 12;
  public static final int                      COLUMN_DEFINITION_DE         = 13;
  public static final String[]                 ALL_KEYS                     = { KEY_ID,
          KEY_ENTRY_NAME, KEY_PART_OF_SPEECH, KEY_DEFINITION, KEY_SYNONYMS, KEY_ANTONYMS,
          KEY_SEE_ALSO, KEY_NOTES, KEY_HIDDEN_NOTES, KEY_COMPONENTS, KEY_EXAMPLES, KEY_SEARCH_TAGS,
          KEY_SOURCE, KEY_DEFINITION_DE,                                   };

  // The name of the database and the database object for accessing it.
  private static final String                  DATABASE_NAME                = "qawHaq.db";
  private static final String                  FTS_VIRTUAL_TABLE            = "mem";

  // This should be kept in sync with the version number in the database
  // entry {boQwI':n}.
  private static final int                     DATABASE_VERSION             = 201311113;

  private final KlingonDatabaseOpenHelper      mDatabaseOpenHelper;
  private static final HashMap<String, String> mColumnMap                   = buildColumnMap();
  private final Context                        mContext;

  // Keeps track of whether db created/upgraded message has been displayed already.
  private static boolean                       mNewDatabaseMessageDisplayed = false;

  /**
   * Constructor
   *
   * @param context
   *          The Context within which to work, used to create the DB
   */
  public KlingonContentDatabase(Context context) {
    // Create a database helper to access the Klingon Database.
    mDatabaseOpenHelper = new KlingonDatabaseOpenHelper(context);
    mContext = context;

    // Initialise the database, and create it if necessary.
    try {
      // Log.d(TAG, "1. Initialising db.");
      mDatabaseOpenHelper.initDatabase();
    } catch (IOException e) {
      throw new Error("Unable to create database.");
    }

    // Open the database for use.
    try {
      // Log.d(TAG, "2. Opening db.");
      mDatabaseOpenHelper.openDatabase();
    } catch (SQLException e) {
      // Possibly an attempt to write a readonly database.
      // Do nothing.
    }

  }

  /**
   * Builds a map for all columns that may be requested, which will be given to the
   * SQLiteQueryBuilder. This is a good way to define aliases for column names, but must include all
   * columns, even if the value is the key. This allows the ContentProvider to request columns w/o
   * the need to know real column names and create the alias itself.
   */
  private static HashMap<String, String> buildColumnMap() {
    HashMap<String, String> map = new HashMap<String, String>();
    map.put(KEY_ENTRY_NAME, KEY_ENTRY_NAME);
    map.put(KEY_DEFINITION, KEY_DEFINITION);
    map.put(KEY_ID, "rowid AS " + KEY_ID);
    map.put(SearchManager.SUGGEST_COLUMN_INTENT_DATA_ID, "rowid AS "
            + SearchManager.SUGGEST_COLUMN_INTENT_DATA_ID);
    map.put(SearchManager.SUGGEST_COLUMN_SHORTCUT_ID, "rowid AS "
            + SearchManager.SUGGEST_COLUMN_SHORTCUT_ID);
    return map;
  }

  /**
   * Returns a Cursor positioned at the entry specified by rowId
   *
   * @param rowId
   *          id of entry to retrieve
   * @param columns
   *          The columns to include, if null then all are included
   * @return Cursor positioned to matching entry, or null if not found.
   */
  public Cursor getEntry(String rowId, String[] columns) {
    // Log.d(TAG, "getEntry called with rowId: " + rowId);

    String selection = "rowid = ?";
    String[] selectionArgs = new String[] { rowId };

    return query(selection, selectionArgs, columns);

    /*
     * This builds a query that looks like: SELECT <columns> FROM <table> WHERE rowid = <rowId>
     */
  }

  /**
   * Convert a string written in "xifan hol" shorthand to {tlhIngan Hol}. This is a mapping which
   * makes it easier to type, since shifting is unnecessary.
   *
   * Make the following replacements: d -> D f -> ng h -> H (see note below) i -> I k -> Q s -> S x
   * -> tlh z -> '
   *
   * When replacing "h" with "H", the following must be preserved: ch -> ch gh -> gh tlh -> tlh ngh
   * -> ngh (n + gh) ngH -> ngH (ng + H)
   *
   * TODO: Consider allowing "invisible h". But this probably makes things too "loose". // c -> ch
   * (but ch -/> chh) // g -> gh (but gh -/> ghh and ng -/> ngh)
   */
  private String expandShorthand(String shorthand) {
    SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(mContext);
    if (!sharedPrefs.getBoolean(Preferences.XIFAN_HOL_CHECKBOX_PREFERENCE, /* default */false)) {
      // The user has disabled the "xifan hol" shorthand, so just do nothing and return.
      return shorthand;
    }
    if (sharedPrefs.getBoolean(Preferences.SWAP_QS_CHECKBOX_PREFERENCE, /* default */false)) {
      // Map q to Q and k to q.
      shorthand = shorthand.replaceAll("q", "Q");
      shorthand = shorthand.replaceAll("k", "q");
    }

    // Note: The order of the replacements is important.
    return shorthand.replaceAll("ngH", "NGH") // differentiate "ngh" from "ngH"
            .replaceAll("h", "H") // side effects: ch -> cH, gh -> gH (also ngh -> ngH), tlh -> tlH
            .replaceAll("cH", "ch") // restore "ch"
            .replaceAll("gH", "gh") // restore "gh" (also "ngh")
            .replaceAll("tlH", "tlh") // restore "tlh"
            .replaceAll("g", "gX") // g -> gX, side effects: gh -> gXh, ng -> ngX
            .replaceAll("gXh", "gh") // restore "gh"
            .replaceAll("ngX", "ng") // restore "ng"
            .replaceAll("gX", "gh") // g -> gh
            .replaceAll("NGH", "ngH") // restore "ngH"
            .replaceAll("c", "cX") // c -> cX, side effect: ch -> cXh
            .replaceAll("cXh", "ch") // restore "ch"
            .replaceAll("cX", "ch") // c -> ch

            .replaceAll("d", "D") // do unambiguous replacements
            .replaceAll("f", "ng").replaceAll("i", "I").replaceAll("k", "Q") // If the swap Qs
                                                                             // preference was
                                                                             // selected, this will
                                                                             // have no effect.
            .replaceAll("s", "S").replaceAll("z", "'").replaceAll("x", "tlh");
  }

  /**
   * Returns a Cursor over all entries that match the given query.
   *
   * @param query
   *          The query, including entry name and metadata, to search for.
   * @return Cursor over all entries that match, or null if none found.
   */
  public Cursor getEntryMatches(String query) {
    // Sanitize for SQL. Assume double-quote is a typo for single-quote. Also trim.
    query = query.replaceAll("\"", "'").trim();

    // Log.d(TAG, "getEntryMatches called with query: \"" + query + "\"");
    MatrixCursor resultsCursor = new MatrixCursor(ALL_KEYS);
    HashSet<Integer> resultsSet = new HashSet<Integer>();

    // Parse the query's metadata, and get the base query.
    KlingonContentProvider.Entry queryEntry = new KlingonContentProvider.Entry(query, mContext);
    String queryBase = queryEntry.getEntryName();

    // If the query has components specified, then we're in analysis mode, and the solution is
    // already given to us.
    ArrayList<KlingonContentProvider.Entry> analysisComponents = queryEntry
            .getComponentsAsEntries();
    if (!analysisComponents.isEmpty()) {
      // Add the given list of components to the results.
      addGivenComponentsToResults(analysisComponents, resultsCursor, resultsSet);

      // Finally, add the complete query entry itself.
      addExactMatch(queryBase, queryEntry, resultsCursor, /* indent */false);

      // Since the components are in the db, do no further analysis.
      return resultsCursor;
    }

    String looseQuery;
    if (query.indexOf(':') != -1) {
      // If this is a system query, don't use "xifan hol" loosening.
      looseQuery = queryBase;
      if (queryBase.equals("*") && queryEntry.isSentence()) {
        // Specifically, if this is a query for a sentence class, search exactly for the matching
        // sentences.
        // We know the query begins with "*:" so strip that to get the sentence class.
        return getMatchingSentences(query.substring(2));
      }
    } else {
      // Assume the user is searching for an "exact" Klingon word or phrase, subject to
      // "xifan hol" loosening.
      looseQuery = expandShorthand(queryBase);
    }
    if (queryEntry.basePartOfSpeechIsUnknown() && queryEntry.getEntryName().length() > 4) {
      // If the POS is unknown and the query is greater than 4 characters, try to parse it
      // as a complex word or sentence.
      parseQueryAsComplexWordOrSentence(looseQuery, resultsCursor, resultsSet);
    } else {
      // Otherwise, assume the base query is a prefix of the desired result.
      Cursor resultsWithGivenPrefixCursor = getEntriesContainingQuery(looseQuery, /* isPrefix */
              true);
      copyCursorEntries(resultsCursor, resultsSet, resultsWithGivenPrefixCursor, /* filter */true,
              queryEntry);
      if (resultsWithGivenPrefixCursor != null) {
        resultsWithGivenPrefixCursor.close();
      }
    }

    // If the query was made without a base part of speech, expand the
    // search to include entries not beginning with the query, and also
    // search on the (English) definition and search tags.
    if (queryEntry.basePartOfSpeechIsUnknown()) {
      // Try the entries, but not from the beginning.
      if (queryEntry.getEntryName().length() > 2) {
        Cursor resultsWithGivenQueryCursor = getEntriesContainingQuery(looseQuery, /* isPrefix */
                false);
        copyCursorEntries(resultsCursor, resultsSet, resultsWithGivenQueryCursor, /* filter */
                false, null);
        if (resultsWithGivenQueryCursor != null) {
          resultsWithGivenQueryCursor.close();
        }
      }

      // Match definitions, from beginning.
      Cursor resultsMatchingDefinitionFromBeginning = getEntriesMatchingDefinition(queryBase, /* isPrefix */
              true, /* useSearchTags */false);
      copyCursorEntries(resultsCursor, resultsSet, resultsMatchingDefinitionFromBeginning, /* filter */
              false, null);
      if (resultsMatchingDefinitionFromBeginning != null) {
        resultsMatchingDefinitionFromBeginning.close();
      }

      // Match definitions, anywhere else.
      if (queryEntry.getEntryName().length() > 2) {
        Cursor resultsMatchingDefinition = getEntriesMatchingDefinition(queryBase, /* isPrefix */
                false,/* useSearchTags */false);
        copyCursorEntries(resultsCursor, resultsSet, resultsMatchingDefinition, /* filter */false,
                null);
        if (resultsMatchingDefinition != null) {
          resultsMatchingDefinition.close();
        }

        // Match search tags, from beginning, then anywhere else.
        Cursor resultsMatchingSearchTagsFromBeginning = getEntriesMatchingDefinition(queryBase, /* isPrefix */
                true,/* useSearchTags */true);
        copyCursorEntries(resultsCursor, resultsSet, resultsMatchingSearchTagsFromBeginning,
        /* filter */false, null);
        if (resultsMatchingSearchTagsFromBeginning != null) {
          resultsMatchingSearchTagsFromBeginning.close();
        }
        Cursor resultsMatchingSearchTags = getEntriesMatchingDefinition(queryBase, /* isPrefix */
                false,/* useSearchTags */true);
        copyCursorEntries(resultsCursor, resultsSet, resultsMatchingSearchTags, /* filter */false,
                null);
        if (resultsMatchingSearchTags != null) {
          resultsMatchingSearchTags.close();
        }
      }

    }

    return resultsCursor;
  }

  // Helper method to add a list of components to the list of search results.
  private void addGivenComponentsToResults(
          ArrayList<KlingonContentProvider.Entry> analysisComponents, MatrixCursor resultsCursor,
          HashSet<Integer> resultsSet) {
    // Create a list of complex words.
    ArrayList<KlingonContentProvider.ComplexWord> complexWordsList = new ArrayList<KlingonContentProvider.ComplexWord>();

    // Keep track of current state. The verb suffix level is required for analysing rovers.
    KlingonContentProvider.ComplexWord currentComplexWord = null;
    KlingonContentProvider.Entry currentPrefixEntry = null;
    int verbSuffixLevel = 0;
    for (KlingonContentProvider.Entry componentEntry : analysisComponents) {
      String componentEntryName = componentEntry.getEntryName();
      boolean isNoun = componentEntry.isNoun();
      boolean isVerb = componentEntry.isVerb();
      boolean isPrefix = componentEntry.isPrefix();
      boolean isSuffix = componentEntry.isSuffix();

      if (!isSuffix && (!isVerb || currentPrefixEntry == null)) {
        // A new word is about to begin, so flush a complex word if there is one.
        if (currentComplexWord != null) {
          // We set a strict match because this is information given explicitly in the db.
          addComplexWordToResults(currentComplexWord, resultsCursor, resultsSet, /* isLenient */
                  false);
          currentComplexWord = null;
        }
      }

      if (!isNoun && !isVerb && !isPrefix && !isSuffix) {
        // Add this word directly.
        addExactMatch(componentEntryName, componentEntry, resultsCursor, /* indent */false);
        continue;
      }

      // At this point, we know this is either a suffix, or a prefix, verb, or noun which begins a
      // new word.
      if (isSuffix && (currentComplexWord != null)) {
        // A suffix, attach to the current word.
        // Note that isNoun here indicates whether the suffix is a noun suffix, not
        // whether the stem is a noun or verb. This is important since noun suffixes
        // can be attached to nouns formed from verbs using {-wI'} or {-ghach}.
        verbSuffixLevel = currentComplexWord.attachSuffix(componentEntryName, isNoun,
                verbSuffixLevel);
      } else if (isPrefix) {
        // A prefix, save to attach to the next verb.
        currentPrefixEntry = componentEntry;
      } else if (isNoun || isVerb) {
        // Create a new complex word, so reset suffix level.
        // Note that this can be a noun, a verb, or an unattached suffix (like in the entry {...-Daq
        // qaDor.}.
        currentComplexWord = new KlingonContentProvider.ComplexWord(componentEntryName, isNoun);
        currentComplexWord.setHomophoneNumber(componentEntry.getHomophoneNumber());
        verbSuffixLevel = 0;
        if (isVerb && currentPrefixEntry != null) {
          currentComplexWord.attachPrefix(currentPrefixEntry.getEntryName());
          currentPrefixEntry = null;
        }
      }
    }
    if (currentComplexWord != null) {
      // Flush any outstanding word.
      addComplexWordToResults(currentComplexWord, resultsCursor, resultsSet, /* isLenient */false);
    }
  }

  // Helper method to copy entries from one cursor to another.
  // If filter is true, queryEntry must be provided.
  private void copyCursorEntries(MatrixCursor destCursor, HashSet<Integer> destSet,
          Cursor srcCursor, boolean filter, KlingonContentProvider.Entry queryEntry) {
    if (srcCursor != null && srcCursor.getCount() != 0) {
      srcCursor.moveToFirst();
      do {
        KlingonContentProvider.Entry resultEntry = new KlingonContentProvider.Entry(srcCursor,
                mContext);

        // Filter by the query if requested to do so. If filter is
        // true, the entry will be added only if it is a match that
        // satisfies certain requirements.
        if (!filter || queryEntry.isSatisfiedBy(resultEntry)) {
          // Prevent duplicates.
          Object[] entryObject = convertEntryToCursorRow(resultEntry, /* indent */false);
          Integer intId = new Integer(resultEntry.getId());
          if (!destSet.contains(intId)) {
            destSet.add(intId);
            destCursor.addRow(entryObject);
          }
        }
      } while (srcCursor.moveToNext());
    }

    // Modify cursor to be like query() below.
    destCursor.moveToFirst();
  }

  // Helper method to search for entries whose prefixes match the query.
  private Cursor getEntriesContainingQuery(String queryBase, boolean isPrefix) {
    // Note: it is important to use the double quote character for quotes
    // because the single quote character is a letter in (transliterated)
    // Klingon. Also, force LIKE to be case-sensitive to distinguish
    // {q} and {Q}.
    SQLiteDatabase db = mDatabaseOpenHelper.getReadableDatabase();
    db.rawQuery("PRAGMA case_sensitive_like = ON", null);
    // If the query must be a prefix of the entry name, do not precede with wildcard.
    String precedingWildcard = isPrefix ? "" : "%";
    Cursor cursor = null;
    try {
      cursor = db.query(true, FTS_VIRTUAL_TABLE, ALL_KEYS, KlingonContentDatabase.KEY_ENTRY_NAME
              + " LIKE \"" + precedingWildcard + queryBase.trim() + "%\"", null, null, null, null,
              null);
    } catch (SQLiteException e) {
      // Do nothing.
    }
    return cursor;
  }

  // Helper method to search for an exact match.
  private Cursor getExactMatches(String entryName) {
    SQLiteDatabase db = mDatabaseOpenHelper.getReadableDatabase();
    db.rawQuery("PRAGMA case_sensitive_like = ON", null);
    Cursor cursor = null;
    try {
      cursor = db.query(true, FTS_VIRTUAL_TABLE, ALL_KEYS, KlingonContentDatabase.KEY_ENTRY_NAME
              + " LIKE \"" + entryName.trim() + "\"", null, null, null, null, null);
    } catch (SQLiteException e) {
      // Do nothing.
    }
    return cursor;
  }

  // Helper method to search for a sentence class.
  private Cursor getMatchingSentences(String sentenceClass) {
    SQLiteDatabase db = mDatabaseOpenHelper.getReadableDatabase();
    db.rawQuery("PRAGMA case_sensitive_like = ON", null);
    Cursor cursor = null;
    try {
      cursor = db.query(true, FTS_VIRTUAL_TABLE, ALL_KEYS,
              KlingonContentDatabase.KEY_PART_OF_SPEECH + " LIKE \"" + sentenceClass + "\"", null,
              null, null, null, null);
    } catch (SQLiteException e) {
      // Do nothing.
    }
    return cursor;
  }

  // Helper method to search for entries whose definitions or search tags match the query.
  private Cursor getEntriesMatchingDefinition(String piece, boolean isPrefix, boolean useSearchTags) {

    // The search key is either the definition or the search tags.
    String key = useSearchTags ? KlingonContentDatabase.KEY_SEARCH_TAGS
            : KlingonContentDatabase.KEY_DEFINITION;

    // If searching for a prefix, nothing can precede the query; otherwise,
    // it must be preceded by a space (it begins a word).
    String precedingWildcard = isPrefix ? "" : "% ";

    SQLiteDatabase db = mDatabaseOpenHelper.getReadableDatabase();
    db.rawQuery("PRAGMA case_sensitive_like = OFF", null);

    Cursor cursor = null;
    try {
      cursor = db.query(true, FTS_VIRTUAL_TABLE, ALL_KEYS, key + " LIKE \"" + precedingWildcard
              + piece.trim() + "%\"", null, null, null, null, null);
    } catch (SQLiteException e) {
      // Do nothing.
    }
    return cursor;
  }

  // Helper method to add one exact match to the results cursor.
  private void addExactMatch(String query, KlingonContentProvider.Entry filterEntry,
          MatrixCursor resultsCursor, boolean indent) {
    Cursor exactMatchesCursor = getExactMatches(query);
    // There must be a match.
    if (exactMatchesCursor == null || exactMatchesCursor.getCount() == 0) {
      Log.e(TAG, "Exact match error on query: " + query);
      return;
    }
    // Log.d(TAG, "Exact matches found: " + exactMatchesCursor.getCount());
    exactMatchesCursor.moveToFirst();
    do {
      KlingonContentProvider.Entry resultEntry = new KlingonContentProvider.Entry(
              exactMatchesCursor, mContext);
      if (filterEntry.isSatisfiedBy(resultEntry)) {
        Object[] exactMatchObject = convertEntryToCursorRow(resultEntry, indent);
        /*
         * if (BuildConfig.DEBUG) { Log.d(TAG, "addExactMatch: " + resultEntry.getEntryName()); }
         */
        resultsCursor.addRow(exactMatchObject);
        // Log.d(TAG, "added exact match to results: " + query);
        // Only add each one once.
        break;
      }
    } while (exactMatchesCursor.moveToNext());
    exactMatchesCursor.close();
  }

  // Helper method to parse a complex word or a sentence.
  private void parseQueryAsComplexWordOrSentence(String query, MatrixCursor resultsCursor,
          HashSet<Integer> resultsSet) {
    // This set stores the complex words.
    ArrayList<KlingonContentProvider.ComplexWord> complexWordsList = new ArrayList<KlingonContentProvider.ComplexWord>();

    // Split the query into sentences.
    String[] sentences = query.split(";,\\.?!");
    for (String sentence : sentences) {
      // Remove all non-valid characters and split the sentence into words (separated by spaces).
      String[] words = sentence.replaceAll("[^A-Za-z' ]", "").split("\\s+");
      for (int i = 0; i < words.length; i++) {
        String word = words[i];

        // Try to parse n-tuples of words as complex nouns.
        // Do this from longest to shortest, since we want longest matches first.
        // TODO: Refactor for space and time efficiency.
        for (int j = words.length; j > i; j--) {
          String compoundNoun = words[i];
          for (int k = i + 1; k < j; k++) {
            compoundNoun += " " + words[k];
          }
          // Log.d(TAG, "parseQueryAsComplexWordOrSentence: compoundNoun = " + compoundNoun);
          KlingonContentProvider.parseComplexWord(compoundNoun, /* isNoun */true, complexWordsList);
        }

        // Next, try to parse this as a verb.
        // Log.d(TAG, "parseQueryAsComplexWordOrSentence: verb = " + word);
        KlingonContentProvider.parseComplexWord(word, /* isNoun */false, complexWordsList);
      }
    }
    for (KlingonContentProvider.ComplexWord complexWord : complexWordsList) {
      // Be a little lenient and also match non-nouns and non-verbs.
      addComplexWordToResults(complexWord, resultsCursor, resultsSet, /* isLenient */true);
    }
  }

  private void addComplexWordToResults(KlingonContentProvider.ComplexWord complexWord,
          MatrixCursor resultsCursor, HashSet<Integer> resultsSet, boolean isLenient) {
    // The isLenient flag is for determining whether we are doing a real analysis (set to true), or
    // whether the correct analysis has already been supplied in the components (set to false). When
    // set to true, a bare word will match any part of speech (not just noun or verb). But for this
    // reason, duplicates are removed (since there may be many of them). However, when set to false,
    // duplicates will be kept (since the given correct analysis contains them).
    KlingonContentProvider.Entry filterEntry = new KlingonContentProvider.Entry(
            complexWord.filter(isLenient), mContext);
    Cursor exactMatchesCursor = getExactMatches(complexWord.stem());

    boolean stemAdded = false;
    if (exactMatchesCursor != null && exactMatchesCursor.getCount() != 0) {
      // Log.d(TAG, "found stem = " + complexWord.stem());

      // Add all exact matches for stem.
      exactMatchesCursor.moveToFirst();
      do {
        KlingonContentProvider.Entry resultEntry = new KlingonContentProvider.Entry(
                exactMatchesCursor, mContext);
        // An archaic or hypothetical word or phrase, even if it's an exact match, will never be
        // part of a complex word.
        // However, allow slang, regional, and extended canon.
        if (filterEntry.isSatisfiedBy(resultEntry) && !resultEntry.isArchaic()
                && !resultEntry.isHypothetical()) {
          // Log.d(TAG, "adding: " + resultEntry.getEntryName() + " (" +
          // resultEntry.getPartOfSpeech() + ")");
          Object[] exactMatchObject = complexWordCursorRow(resultEntry, complexWord);

          // If this is a bare word, prevent duplicates.
          Integer intId = new Integer(resultEntry.getId());
          if (!complexWord.isBareWord() || !resultsSet.contains(intId) || !isLenient) {
            /*
             * if (BuildConfig.DEBUG) { Log.d(TAG, "addComplexWordToResults: " +
             * resultEntry.getEntryName()); }
             */
            resultsCursor.addRow(exactMatchObject);
            stemAdded = true;
            if (complexWord.isBareWord()) {
              resultsSet.add(intId);
            }
          }
        }
      } while (exactMatchesCursor.moveToNext());
      exactMatchesCursor.close();
    }

    // Whether or not there was an exact match, if the complex word is a number, add its components.
    if (complexWord.isNumberLike()) {
      String numberRoot = complexWord.getNumberRoot();
      String numberRootAnnotation = complexWord.getNumberRootAnnotation();
      String numberModifier = complexWord.getNumberModifier();
      String numberSuffix = complexWord.getNumberSuffix();

      // First, add the root as a word. (The annotation is already included.)
      if (!numberRoot.equals("") && (!stemAdded || !numberRoot.equals(complexWord.stem()))) {
        filterEntry = new KlingonContentProvider.Entry(numberRoot + ":" + numberRootAnnotation,
                mContext);
        if (BuildConfig.DEBUG) {
          Log.d(TAG, "numberRoot: " + numberRoot);
        }
        addExactMatch(numberRoot, filterEntry, resultsCursor, /* indent */false);
        stemAdded = true;
      }

      // Next, add the modifier as a word.
      if (!numberModifier.equals("")) {
        filterEntry = new KlingonContentProvider.Entry(numberModifier + ":n:num", mContext);
        addExactMatch(numberModifier, filterEntry, resultsCursor, /* indent */true);
      }

      // Finally, add the number suffix.
      if (!numberSuffix.equals("")) {
        numberSuffix = "-" + numberSuffix;
        filterEntry = new KlingonContentProvider.Entry(numberSuffix + ":n:num,suff", mContext);
        addExactMatch(numberSuffix, filterEntry, resultsCursor, /* indent */true);
      }
    }

    // Now add all affixes, but only if one of the corresponding stems was a legitimate entry.
    if (stemAdded) {
      // Add the verb prefix.
      String prefix = complexWord.getVerbPrefix();
      if (!prefix.equals("")) {
        // Log.d(TAG, "verb prefix = " + prefix);
        filterEntry = new KlingonContentProvider.Entry(prefix + ":v:pref", mContext);
        addExactMatch(prefix, filterEntry, resultsCursor, /* indent */true);
      }

      // Add verb suffixes. Verb suffixes must go before noun suffixes since two of them
      // can turn a verb into a noun.
      // For purposes of analysis, pronouns are also verbs, but they cannot have prefixes.
      String[] verbSuffixes = complexWord.getVerbSuffixes();
      for (int j = 0; j < verbSuffixes.length; j++) {
        // Check verb suffix of the current type.
        if (!verbSuffixes[j].equals("")) {
          // Log.d(TAG, "verb suffix = " + verbSuffixes[j]);
          filterEntry = new KlingonContentProvider.Entry(verbSuffixes[j] + ":v:suff", mContext);
          addExactMatch(verbSuffixes[j], filterEntry, resultsCursor, /* indent */true);
        }

        // Check for the true rovers.
        String[] rovers = complexWord.getRovers(j);
        for (String rover : rovers) {
          filterEntry = new KlingonContentProvider.Entry(rover + ":v:suff", mContext);
          addExactMatch(rover, filterEntry, resultsCursor, /* indent */true);
        }
      }

      // Add noun suffixes.
      String[] nounSuffixes = complexWord.getNounSuffixes();
      for (int j = 0; j < nounSuffixes.length; j++) {
        if (!nounSuffixes[j].equals("")) {
          // Log.d(TAG, "noun suffix = " + nounSuffixes[j]);
          filterEntry = new KlingonContentProvider.Entry(nounSuffixes[j] + ":n:suff", mContext);
          addExactMatch(nounSuffixes[j], filterEntry, resultsCursor, /* indent */true);
        }
      }
    }
  }

  private Object[] complexWordCursorRow(KlingonContentProvider.Entry entry,
          KlingonContentProvider.ComplexWord complexWord) {
    // TODO: Add warnings for mismatched affixes here.
    return new Object[] {
            entry.getId(),
            complexWord.getVerbPrefixString() + entry.getEntryName()
                    + complexWord.getSuffixesString(), entry.getPartOfSpeech(),
            entry.getDefinition(), entry.getSynonyms(), entry.getAntonyms(), entry.getSeeAlso(),
            entry.getNotes(), entry.getHiddenNotes(), entry.getComponents(), entry.getExamples(),
            entry.getSearchTags(), entry.getSource(), entry.getDefinition_DE(), };
  }

  private Object[] convertEntryToCursorRow(KlingonContentProvider.Entry entry, boolean indent) {
    return new Object[] { entry.getId(), entry.getEntryName(),
            entry.getPartOfSpeech() + (indent ? ",indent" : ""), entry.getDefinition(),
            entry.getSynonyms(), entry.getAntonyms(), entry.getSeeAlso(), entry.getNotes(),
            entry.getHiddenNotes(), entry.getComponents(), entry.getExamples(),
            entry.getSearchTags(), entry.getSource(), entry.getDefinition_DE(), };
  }

  /**
   * Returns a cursor for one entry given its _id.
   *
   * @param entryName
   *          The name of the entry to search for
   * @param columns
   *          The columns to include, if null then all are included
   * @return Cursor over all entries that match, or null if none found.
   */
  public Cursor getEntryById(String entryId, String[] columns) {
    // Log.d(TAG, "getEntryById called with entryid: " + entryId);
    Cursor cursor = mDatabaseOpenHelper.getReadableDatabase().query(true, FTS_VIRTUAL_TABLE,
            columns, KlingonContentDatabase.KEY_ID + "=" + entryId + "", null, null, null, null,
            null);
    if (cursor != null) {
      cursor.moveToFirst();
    }
    // Log.d(TAG, "cursor.getCount() = " + cursor.getCount());
    return cursor;
  }

  /**
   * Performs a database query.
   *
   * @param selection
   *          The selection clause
   * @param selectionArgs
   *          Selection arguments for "?" components in the selection
   * @param columns
   *          The columns to return
   * @return A Cursor over all rows matching the query
   */
  private Cursor query(String selection, String[] selectionArgs, String[] columns) {
    /*
     * The SQLiteBuilder provides a map for all possible columns requested to actual columns in the
     * database, creating a simple column alias mechanism by which the ContentProvider does not need
     * to know the real column names
     */
    SQLiteQueryBuilder builder = new SQLiteQueryBuilder();
    builder.setTables(FTS_VIRTUAL_TABLE);
    builder.setProjectionMap(mColumnMap);

    // DEBUG
    // Log.d(TAG, "query - columns: " + Arrays.toString(columns));
    // Log.d(TAG, "query - selection: " + selection);
    // Log.d(TAG, "query - selectionArgs: " + Arrays.toString(selectionArgs));

    Cursor cursor = builder.query(mDatabaseOpenHelper.getReadableDatabase(), columns, selection,
            selectionArgs, null, null, null);

    // DEBUG
    // Log.d(TAG, "query - cursor: " + cursor.toString());

    if (cursor == null) {
      return null;
    } else if (!cursor.moveToFirst()) {

      cursor.close();
      return null;
    }
    return cursor;
  }

  /**
   * This class helps create, open, and upgrade the Klingon database.
   */
  private static class KlingonDatabaseOpenHelper extends SQLiteOpenHelper {

    // The system path of the Klingon database.
    private static String  DATABASE_PATH = Environment.getDataDirectory()
                                                 + "/data/org.tlhInganHol.android.klingonassistant/databases/";

    // For storing the context the helper was called with for use.
    private final Context  mHelperContext;

    // The Klingon database.
    private SQLiteDatabase mDatabase;

    /**
     * Constructor Takes and keeps a reference of the passed context in order to access the
     * application assets and resources.
     *
     * @param context
     */
    KlingonDatabaseOpenHelper(Context context) {
      super(context, DATABASE_NAME, null, DATABASE_VERSION);
      mHelperContext = context;
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
      // This method is called when the database is created for the first
      // time. It would normally create the database using an SQL
      // command, then load the content. We do nothing here, and leave
      // the work of copying the pre-made database to the constructor of
      // the KlingonContentDatabase class.
      // Log.d(TAG, "onCreate called.");
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int existingVersion, int newVersion) {
      if (newVersion <= existingVersion) {
        // Already using a new version, do nothing.
        return;
      }

      // This method is called when the database needs to be updated.
      // db.execSQL("DROP TABLE IF EXISTS " + FTS_VIRTUAL_TABLE);
      mHelperContext.deleteDatabase(DATABASE_NAME);
      Toast.makeText(
              mHelperContext,
              "Database upgraded from v" + dottedVersion(existingVersion) + " to v"
                      + dottedVersion(newVersion) + ".", Toast.LENGTH_LONG).show();
      mNewDatabaseMessageDisplayed = true;

      // Show help after database upgrade.
      setShowHelpFlag();
    }

    private String dottedVersion(int version) {
      String s = Integer.toString(version);
      return s.substring(0, 4) + "." + s.substring(4, 6) + "." + s.substring(6, 8)
              + Character.toString((char) (s.charAt(8) - '0' + 'a'));
    }

    private void setShowHelpFlag() {
      // Set the flag to show the help screen.
      SharedPreferences.Editor sharedPrefsEd = PreferenceManager.getDefaultSharedPreferences(
              mHelperContext).edit();
      sharedPrefsEd.putBoolean(KlingonAssistant.KEY_SHOW_HELP, true);
      sharedPrefsEd.commit();
      // Log.d(TAG, "Flag set to show help.");
    }

    /**
     * Initialises the database by creating an empty database and writing to it from application
     * resource.
     */
    public void initDatabase() throws IOException {
      // TODO: Besides checking whether it exists, also check if its data needs to be updated.
      // This may not be necessary due to onUpgrade(...) above.
      boolean dbExists = checkDBExists();
      // Log.d(TAG, "dbExists = " + dbExists);

      if (dbExists) {
        // Log.d(TAG, "Database exists.");
        // Get a writeable database so that onUpgrade will be called on
        // it if the version number has increased.
        try {
          // Log.d(TAG, "Getting writable database.");
          SQLiteDatabase writeDB = this.getWritableDatabase();
          writeDB.close();
        } catch (SQLiteDiskIOException e) {
          // TODO(davinci): Log error or do something here and below.
          // Log.e(TAG, "SQLiteDiskIOException on getWritableDatabase().");
        } catch (SQLiteException e) {
          // Possibly unable to get provider because no transaction is active.
          // Do nothing.
        }
      }

      // Create the database if it doesn't exist.
      dbExists = checkDBExists();
      if (!dbExists) {
        // This will create the empty database if it doesn't already exist.
        // Log.d(TAG, "Getting readable database.");
        SQLiteDatabase readDB = this.getReadableDatabase();
        readDB.close();

        // Try to create the database from the xml file.
        try {
          // Log.d(TAG, "Copying database from resources.");
          copyDBFromResources();
        } catch (IOException e) {
          throw new Error("Error copying database from resources.");
        }

        // Inform the user the database has been created.
        if (!mNewDatabaseMessageDisplayed) {
          Toast.makeText(mHelperContext,
                  "Database v" + dottedVersion(DATABASE_VERSION) + " created.", Toast.LENGTH_LONG)
                  .show();
          mNewDatabaseMessageDisplayed = true;
        }

        // Show help after database creation.
        setShowHelpFlag();
      }
    }

    /**
     * Check if the database already exists so that it isn't copied every time the activity is
     * started.
     *
     * @return true if the database exists, false otherwise
     */
    private boolean checkDBExists() {
      // The commented way below is the proper way of checking for the
      // existence of the database. However, we do it this way to
      // prevent the "sqlite3_open_v2 open failed" error.
      File dbFile = new File(DATABASE_PATH + DATABASE_NAME);
      return dbFile.exists();

      // TODO(davinci): Investigate the below. It may be the reason why there
      // are problems on some devices.
      /*
       * SQLiteDatabase checkDB = null; try { String fullDBPath = DATABASE_PATH + DATABASE_NAME;
       * checkDB = SQLiteDatabase.openDatabase(fullDBPath, null, SQLiteDatabase.OPEN_READONLY);
       *
       * } catch(SQLiteCantOpenDatabaseException e) { // The database doesn't exist yet. It's fine
       * to do nothing // here, we just want to return false at the end. // Log.d(TAG,
       * "SQLiteCantOpenDatabaseException thrown: " + e);
       *
       * } catch(SQLiteDatabaseLockedException e) { // The database is locked. Also return false. //
       * Log.d(TAG, "SQLiteDatabaseLockedException thrown: " + e); }
       *
       * if( checkDB != null ) { checkDB.close(); }
       *
       * // Log.d(TAG, "checkDB == null: " + (checkDB == null)); return ( checkDB != null );
       */
    }

    /**
     * Copies the database from the application resources' assets folder to the newly created
     * database in the system folder.
     */
    private void copyDBFromResources() throws IOException {

      // Open the file in the assets folder as an input stream.
      InputStream inStream = mHelperContext.getAssets().open(DATABASE_NAME);

      // Path to the newly created empty database.
      String fullDBPath = DATABASE_PATH + DATABASE_NAME;

      // Open the empty database as the output stream.
      OutputStream outStream = new FileOutputStream(fullDBPath);

      // Transfer the database from the resources to the system path one block at a time.
      byte[] buffer = new byte[1024];
      int length;
      while ((length = inStream.read(buffer)) > 0) {
        outStream.write(buffer, 0, length);
      }

      // Close the streams.
      outStream.flush();
      outStream.close();
      inStream.close();

      // Log.d(TAG, "Database copy successful.");
    }

    /**
     * Opens the database.
     */
    public void openDatabase() throws SQLException {
      String fullDBPath = DATABASE_PATH + DATABASE_NAME;
      // Log.d(TAG, "openDatabase() called on path " + fullDBPath + ".");
      mDatabase = SQLiteDatabase.openDatabase(fullDBPath, null, SQLiteDatabase.OPEN_READONLY);
    }

    /**
     * Closes the database.
     */
    @Override
    public synchronized void close() {
      // Log.d(TAG, "Closing database.");
      if (mDatabase != null) {
        mDatabase.close();
      }
      super.close();
    }
  } // KlingonDatabaseOpenHelper
} // KlingonContentDatabase
