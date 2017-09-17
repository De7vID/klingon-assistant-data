/*
 * Copyright (C) 2014 De'vID jonpIn (David Yonge-Mallo)
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

package org.tlhInganHol.android.klingonassistant_v2;

import android.app.SearchManager;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.res.Resources;
import android.database.Cursor;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.speech.tts.TextToSpeech;
import android.support.annotation.NonNull;
import android.support.design.widget.BottomNavigationView;
import android.support.v4.view.MenuItemCompat;
import android.support.v7.widget.ShareActionProvider;
import android.text.Html;
import android.text.SpannableStringBuilder;
import android.text.Spanned;
import android.text.method.LinkMovementMethod;
import android.text.style.ClickableSpan;
import android.text.style.ForegroundColorSpan;
import android.text.style.RelativeSizeSpan;
import android.text.style.StyleSpan;
import android.text.style.SuperscriptSpan;
import android.text.style.TypefaceSpan;
import android.text.style.URLSpan;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.TextView;
import java.util.Locale;
import java.util.regex.Matcher;

/** Displays an entry and its definition. */
public class EntryActivity extends BaseActivity
    // TTS:
    implements TextToSpeech.OnInitListener {

  private static final String TAG = "EntryActivity";

  // The intent holding the data to be shared.
  private Intent mShareEntryIntent = null;

  // The parent query that this entry is a part of.
  private String mParentQuery = null;
  private String mEntryName = null;

  // Intents for the bottom navigation buttons.
  // Note that the renumber.py script ensures a max difference of 10 between
  // the IDs of adjacent entries, within the same "mem" file.
  private Intent mPreviousEntryIntent = null;
  private Intent mNextEntryIntent = null;
  private static final int MAX_ENTRY_ID_DIFF = 10;

  // TTS:
  /** The {@link TextToSpeech} used for speaking. */
  private TextToSpeech mTts;

  private MenuItem mSpeakButton;
  private boolean ttsInitialized = false;

  @Override
  protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);

    // TTS:
    // Initialize text-to-speech. This is an asynchronous operation.
    // The OnInitListener (second argument) is called after initialization completes.
    // Log.d(TAG, "Initialising TTS");
    mTts =
        new TextToSpeech(
            this,
            this, // TextToSpeech.OnInitListener
            "org.tlhInganHol.android.klingonttsengine"); // Requires API 14.

    setDrawerContentView(R.layout.entry);
    Resources resources = getResources();

    TextView entryTitle = (TextView) findViewById(R.id.entry_title);
    TextView entryText = (TextView) findViewById(R.id.definition);

    // TODO: Save and restore bundle state to preserve links.

    Uri uri = getIntent().getData();
    // Log.d(TAG, "EntryActivity - uri: " + uri.toString());
    // TODO: Disable the "About" menu item if this is the "About" entry.
    mParentQuery = getIntent().getStringExtra(SearchManager.QUERY);

    // Retrieve the entry's data.
    // Note: managedQuery is deprecated since API 11.
    Cursor cursor = managedQuery(uri, KlingonContentDatabase.ALL_KEYS, null, null, null);
    final KlingonContentProvider.Entry entry =
        new KlingonContentProvider.Entry(cursor, getBaseContext());
    int entryId = entry.getId();

    // Set up the bottom navigation buttons.
    BottomNavigationView bottomNavView =
        (BottomNavigationView) findViewById(R.id.bottom_navigation);
    for (int i = 1; i <= MAX_ENTRY_ID_DIFF; i++) {
      Intent entryIntent = getEntryByIdIntent(entryId + i);
      if (entryIntent != null) {
        mNextEntryIntent = entryIntent;
        break;
      }
    }
    if (mNextEntryIntent == null) {
      MenuItem nextButton = (MenuItem) bottomNavView.getMenu().findItem(R.id.action_next);
      nextButton.setEnabled(false);
      bottomNavView.findViewById(R.id.action_next).setVisibility(View.INVISIBLE);
    }
    for (int i = 1; i <= MAX_ENTRY_ID_DIFF; i++) {
      Intent entryIntent = getEntryByIdIntent(entryId - i);
      if (entryIntent != null) {
        mPreviousEntryIntent = entryIntent;
        break;
      }
    }
    if (mPreviousEntryIntent == null) {
      MenuItem previousButton = (MenuItem) bottomNavView.getMenu().findItem(R.id.action_previous);
      previousButton.setEnabled(false);
      bottomNavView.findViewById(R.id.action_previous).setVisibility(View.INVISIBLE);
    }
    bottomNavView.setOnNavigationItemSelectedListener(
        new BottomNavigationView.OnNavigationItemSelectedListener() {
          @Override
          public boolean onNavigationItemSelected(@NonNull MenuItem item) {
            switch (item.getItemId()) {
              case R.id.action_previous:
                goToPreviousEntry();
                break;
              case R.id.action_random:
                goToRandomEntry();
                break;
              case R.id.action_next:
                goToNextEntry();
                break;
            }
            return false;
          }
        });

    // Handle alternative spellings here.
    if (entry.isAlternativeSpelling()) {
      // TODO: Immediate redirect to query in entry.getDefinition();
    }

    // Get the shared preferences.
    SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());

    // Set the entry's name (along with info like "slang", formatted in HTML).
    entryTitle.invalidate();
    boolean useKlingonFont =
        sharedPrefs.getBoolean(
            Preferences.KEY_KLINGON_FONT_CHECKBOX_PREFERENCE, /* default */ false);
    Typeface klingonTypeface = KlingonAssistant.getKlingonFontTypeface(getBaseContext());
    if (useKlingonFont) {
      // Preference is set to display this in {pIqaD}!
      entryTitle.setTypeface(klingonTypeface);
      entryTitle.setText(entry.getEntryNameInKlingonFont());
    } else {
      // Boring transcription based on English (Latin) alphabet.
      entryTitle.setText(Html.fromHtml(entry.getFormattedEntryName(/* isHtml */ true)));
    }
    mEntryName = entry.getEntryName();

    // Set the colour for the entry name depending on its part of speech.
    boolean useColours =
        sharedPrefs.getBoolean(Preferences.KEY_USE_COLOURS_CHECKBOX_PREFERENCE, /* default */ true);
    if (useColours) {
      entryTitle.setTextColor(entry.getTextColor());
    }

    // Create the expanded definition.
    String pos = entry.getFormattedPartOfSpeech(/* isHtml */ false);
    String expandedDefinition = pos;

    // Determine whether to show the German definition. If shown, it is primary, and the English
    // definition is shown as secondary.
    String englishDefinition = entry.getDefinition();
    boolean displayGermanEntry = entry.shouldDisplayGermanDefinition();
    int englishDefinitionStart = -1;
    String englishDefinitionHeader = "\n" + resources.getString(R.string.label_english) + ": ";
    if (!displayGermanEntry) {
      // The simple case: just the English definition.
      expandedDefinition += englishDefinition;
    } else {
      // We display the German definition as the primary one, but keep track of the location of the
      // English definition to change its font size later.
      expandedDefinition += entry.getDefinition_DE();
      englishDefinitionStart = expandedDefinition.length();
      expandedDefinition += englishDefinitionHeader + englishDefinition;
    }

    // Set the share intent.
    setShareEntryIntent(entry);

    // Show the basic notes.
    String notes;
    if (entry.shouldDisplayGermanNotes()) {
      notes = entry.getNotes_DE();
    } else {
      notes = entry.getNotes();
    }
    if (!notes.equals("")) {
      expandedDefinition += "\n\n" + notes;
    }

    // If this entry is hypothetical or extended canon, display warnings.
    if (entry.isHypothetical() || entry.isExtendedCanon()) {
      expandedDefinition += "\n\n";
      if (entry.isHypothetical()) {
        expandedDefinition += resources.getString(R.string.warning_hypothetical);
      }
      if (entry.isExtendedCanon()) {
        expandedDefinition += resources.getString(R.string.warning_extended_canon);
      }
    }

    // Show synonyms, antonyms, and related entries.
    String synonyms = entry.getSynonyms();
    String antonyms = entry.getAntonyms();
    String seeAlso = entry.getSeeAlso();
    if (!synonyms.equals("")) {
      expandedDefinition += "\n\n" + resources.getString(R.string.label_synonyms) + ": " + synonyms;
    }
    if (!antonyms.equals("")) {
      expandedDefinition += "\n\n" + resources.getString(R.string.label_antonyms) + ": " + antonyms;
    }
    if (!seeAlso.equals("")) {
      expandedDefinition += "\n\n" + resources.getString(R.string.label_see_also) + ": " + seeAlso;
    }

    // Display components if that field is not empty, unless we are showing an analysis link, in
    // which case we want to hide the components.
    boolean showAnalysis = entry.isSentence() || entry.isDerivative();
    String components = entry.getComponents();
    if (!components.equals("")) {
      // Treat the components column of inherent plurals and their
      // singulars differently than for other entries.
      if (entry.isInherentPlural()) {
        expandedDefinition +=
            "\n\n" + String.format(resources.getString(R.string.info_inherent_plural), components);
      } else if (entry.isSingularFormOfInherentPlural()) {
        expandedDefinition +=
            "\n\n" + String.format(resources.getString(R.string.info_singular_form), components);
      } else if (!showAnalysis) {
        // This is just a regular list of components.
        expandedDefinition +=
            "\n\n" + resources.getString(R.string.label_components) + ": " + components;
      }
    }

    // Display plural information.
    if (!entry.isPlural() && !entry.isInherentPlural() && !entry.isPlural()) {
      if (entry.isBeingCapableOfLanguage()) {
        expandedDefinition += "\n\n" + resources.getString(R.string.info_being);
      } else if (entry.isBodyPart()) {
        expandedDefinition += "\n\n" + resources.getString(R.string.info_body);
      }
    }

    // If the entry is a useful phrase, link back to its category.
    if (entry.isSentence()) {
      String sentenceType = entry.getSentenceType();
      if (!sentenceType.equals("")) {
        // Put the query as a placeholder for the actual category.
        expandedDefinition +=
            "\n\n"
                + resources.getString(R.string.label_category)
                + ": {"
                + entry.getSentenceTypeQuery()
                + "}";
      }
    }

    // If the entry is a sentence, make a link to analyse its components.
    if (showAnalysis) {
      String analysisQuery = entry.getEntryName();
      if (!components.equals("")) {
        // Strip the brackets around each component so they won't be processed.
        analysisQuery += ":" + entry.getPartOfSpeech();
        int homophoneNumber = entry.getHomophoneNumber();
        if (homophoneNumber != -1) {
          analysisQuery += ":" + homophoneNumber;
        }
        analysisQuery +=
            KlingonContentProvider.Entry.COMPONENTS_MARKER + components.replaceAll("[{}]", "");
      }
      expandedDefinition +=
          "\n\n" + resources.getString(R.string.label_analyze) + ": {" + analysisQuery + "}";
    }

    // Show the examples.
    String examples;
    if (entry.shouldDisplayGermanExamples()) {
      examples = entry.getExamples_DE();
    } else {
      examples = entry.getExamples();
    }
    if (!examples.equals("")) {
      expandedDefinition += "\n\n" + resources.getString(R.string.label_examples) + ": " + examples;
    }

    // Show the source.
    String source = entry.getSource();
    if (!source.equals("")) {
      expandedDefinition += "\n\n" + resources.getString(R.string.label_sources) + ": " + source;
    }

    // If this is a verb (but not a prefix or suffix), show the transitivity information.
    String transitivity = "";
    if (entry.isVerb()
        && sharedPrefs.getBoolean(
            Preferences.KEY_SHOW_TRANSITIVITY_CHECKBOX_PREFERENCE, /* default */ true)) {
      // This is a verb and show transitivity preference is set to true.
      transitivity = entry.getTransitivityString();
    }
    int transitivityStart = -1;
    String transitivityHeader = "\n\n" + resources.getString(R.string.label_transitivity) + ": ";
    boolean showTransitivityInformation = !transitivity.equals("");
    if (showTransitivityInformation) {
      transitivityStart = expandedDefinition.length();
      expandedDefinition += transitivityHeader + transitivity;
    }

    // Show the hidden notes.
    String hiddenNotes = "";
    if (sharedPrefs.getBoolean(
        Preferences.KEY_SHOW_ADDITIONAL_INFORMATION_CHECKBOX_PREFERENCE, /* default */ true)) {
      // Show additional information preference set to true.
      hiddenNotes = entry.getHiddenNotes();
    }
    int hiddenNotesStart = -1;
    String hiddenNotesHeader =
        "\n\n" + resources.getString(R.string.label_additional_information) + ": ";
    if (!hiddenNotes.equals("")) {
      hiddenNotesStart = expandedDefinition.length();
      expandedDefinition += hiddenNotesHeader + hiddenNotes;
    }

    // Format the expanded definition, including linkifying the links to other entries.
    float smallTextScale = (float) 0.8;
    SpannableStringBuilder ssb = new SpannableStringBuilder(expandedDefinition);
    int intermediateFlags = Spanned.SPAN_EXCLUSIVE_EXCLUSIVE | Spanned.SPAN_INTERMEDIATE;
    int finalFlags = Spanned.SPAN_EXCLUSIVE_EXCLUSIVE;
    if (!pos.equals("")) {
      // Italicise the part of speech.
      ssb.setSpan(new StyleSpan(android.graphics.Typeface.ITALIC), 0, pos.length(), finalFlags);
    }
    if (displayGermanEntry) {
      // Reduce the size of the secondary (English) definition.
      ssb.setSpan(
          new RelativeSizeSpan(smallTextScale),
          englishDefinitionStart,
          englishDefinitionStart + englishDefinitionHeader.length() + englishDefinition.length(),
          finalFlags);
    }
    if (showTransitivityInformation) {
      // Reduce the size of the transitivity information.
      ssb.setSpan(
          new RelativeSizeSpan(smallTextScale),
          transitivityStart,
          transitivityStart + transitivityHeader.length() + transitivity.length(),
          finalFlags);
    }
    if (!hiddenNotes.equals("")) {
      // Reduce the size of the hidden notes.
      ssb.setSpan(
          new RelativeSizeSpan(smallTextScale),
          hiddenNotesStart,
          hiddenNotesStart + hiddenNotesHeader.length() + hiddenNotes.length(),
          finalFlags);
    }
    Matcher m = KlingonContentProvider.Entry.ENTRY_PATTERN.matcher(expandedDefinition);
    while (m.find()) {

      // Strip the brackets {} to get the query.
      String query = expandedDefinition.substring(m.start() + 1, m.end() - 1);
      LookupClickableSpan viewLauncher = new LookupClickableSpan(query);

      // Process the linked entry information.
      KlingonContentProvider.Entry linkedEntry =
          new KlingonContentProvider.Entry(query, getBaseContext());
      // Log.d(TAG, "linkedEntry.getEntryName() = " + linkedEntry.getEntryName());

      // Delete the brackets and metadata parts of the string (which includes analysis components).
      ssb.delete(m.start() + 1 + linkedEntry.getEntryName().length(), m.end());
      ssb.delete(m.start(), m.start() + 1);
      int end = m.start() + linkedEntry.getEntryName().length();

      // Insert link to the category for a useful phrase.
      if (entry.isSentence()
          && !entry.getSentenceType().equals("")
          && linkedEntry.getEntryName().equals("*")) {
        // Delete the "*" placeholder.
        ssb.delete(m.start(), m.start() + 1);

        // Insert the category name.
        ssb.insert(m.start(), entry.getSentenceType());
        end += entry.getSentenceType().length() - 1;
      }

      // Set the font and link.
      // This is true if this entry doesn't launch an EntryActivity.
      boolean disableEntryLink =
          linkedEntry.doNotLink() || linkedEntry.isSource() || linkedEntry.isURL();
      // The last span set on a range must have finalFlags.
      int maybeFinalFlags = disableEntryLink ? finalFlags : intermediateFlags;
      if (linkedEntry.isSource()) {
        // If possible, link to the source.
        String url = linkedEntry.getURL();
        if (!url.equals("")) {
          ssb.setSpan(new URLSpan(url), m.start(), end, intermediateFlags);
        }
        // Names of sources are in italics.
        ssb.setSpan(
            new StyleSpan(android.graphics.Typeface.ITALIC), m.start(), end, maybeFinalFlags);
      } else if (linkedEntry.isURL()) {
        // Linkify URL if there is one.
        String url = linkedEntry.getURL();
        if (!url.equals("")) {
          ssb.setSpan(new URLSpan(url), m.start(), end, maybeFinalFlags);
        }
      } else if (useKlingonFont) {
        // Display the text using the Klingon font. Categories (which have an entry of "*") must
        // be handled specially.
        String klingonEntryName =
            !linkedEntry.getEntryName().equals("*")
                ? linkedEntry.getEntryNameInKlingonFont()
                : KlingonContentProvider.convertStringToKlingonFont(entry.getSentenceType());
        ssb.delete(m.start(), end);
        ssb.insert(m.start(), klingonEntryName);
        end = m.start() + klingonEntryName.length();
        ssb.setSpan(new KlingonTypefaceSpan("", klingonTypeface), m.start(), end, maybeFinalFlags);
      } else {
        // Klingon is in bold serif.
        ssb.setSpan(
            new StyleSpan(android.graphics.Typeface.BOLD), m.start(), end, intermediateFlags);
        ssb.setSpan(new TypefaceSpan("serif"), m.start(), end, maybeFinalFlags);
      }
      // If linked entry is hypothetical or extended canon, insert a "?" in front.
      if (linkedEntry.isHypothetical() || linkedEntry.isExtendedCanon()) {
        ssb.insert(m.start(), "?");
        ssb.setSpan(
            new RelativeSizeSpan(smallTextScale), m.start(), m.start() + 1, intermediateFlags);
        ssb.setSpan(new SuperscriptSpan(), m.start(), m.start() + 1, maybeFinalFlags);
        end++;
      }
      // Only apply colours to verbs, nouns, and affixes (exclude BLUE and WHITE).
      if (!disableEntryLink) {
        // Link to view launcher.
        ssb.setSpan(viewLauncher, m.start(), end, useColours ? intermediateFlags : finalFlags);
      }
      // Set the colour last, so it's not overridden by other spans.
      if (useColours) {
        // if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
        //   // Work around a bug in Android 6.0.
        //   //
        // http://stackoverflow.com/questions/34631851/multiple-foregroundcolorspan-on-editable-issue-on-android-6-0
        //   ForegroundColorSpan[] oldSpans = ssb.getSpans(m.start(), end,
        // ForegroundColorSpan.class);
        //   for (ForegroundColorSpan span : oldSpans) {
        //     ssb.removeSpan(span);
        //   }
        // }
        ssb.setSpan(
            new ForegroundColorSpan(linkedEntry.getTextColor()), m.start(), end, finalFlags);
      }
      String linkedPos = linkedEntry.getBracketedPartOfSpeech(/* isHtml */ false);
      if (!linkedPos.equals("") && linkedPos.length() > 1) {
        ssb.insert(end, linkedPos);

        int rightBracketLoc = linkedPos.indexOf(")");
        if (rightBracketLoc != -1) {
          // linkedPos is always of the form " (pos)[ (def'n N)]", we want to italicise
          // the "pos" part only.
          ssb.setSpan(
              new StyleSpan(android.graphics.Typeface.ITALIC),
              end + 2,
              end + rightBracketLoc,
              finalFlags);
        }
      }

      // Rinse and repeat.
      expandedDefinition = ssb.toString();
      m = KlingonContentProvider.Entry.ENTRY_PATTERN.matcher(expandedDefinition);
    }

    // Display the entry name and definition.
    entryText.invalidate();
    entryText.setText(ssb);
    entryText.setMovementMethod(LinkMovementMethod.getInstance());
  }

  private Intent getEntryByIdIntent(int entryId) {
    Cursor cursor;
    cursor =
        managedQuery(
            Uri.parse(KlingonContentProvider.CONTENT_URI + "/get_entry_by_id/" + entryId),
            null /* all columns */,
            null,
            null,
            null);
    if (cursor.getCount() == 1) {
      Uri uri =
          Uri.parse(
              KlingonContentProvider.CONTENT_URI
                  + "/get_entry_by_id/"
                  + cursor.getString(KlingonContentDatabase.COLUMN_ID));

      Intent entryIntent = new Intent(this, EntryActivity.class);

      // Form the URI for the entry.
      entryIntent.setData(uri);

      return entryIntent;
    }
    return null;
  }

  private void goToPreviousEntry() {
    if (mPreviousEntryIntent != null) {
      startActivity(mPreviousEntryIntent);
      // TODO: Ideally, this should transition the other way, but then pressing the back key looks
      // weird.
      overridePendingTransition(R.anim.slide_in_right, R.anim.slide_out_left);
    }
  }

  private void goToRandomEntry() {
    Cursor cursor;
    Uri uri = Uri.parse(KlingonContentProvider.CONTENT_URI + "/get_random_entry");
    Intent randomEntryIntent = new Intent(this, EntryActivity.class);
    randomEntryIntent.setData(uri);
    startActivity(randomEntryIntent);
    overridePendingTransition(R.anim.slide_in_right, R.anim.slide_out_left);
  }

  private void goToNextEntry() {
    if (mNextEntryIntent != null) {
      startActivity(mNextEntryIntent);
      overridePendingTransition(R.anim.slide_in_right, R.anim.slide_out_left);
    }
  }

  @Override
  protected void onResume() {
    super.onResume();

    // TTS:
    // Initialize text-to-speech. This is an asynchronous operation.
    // The OnInitListener (second argument) is called after initialization completes.
    // This is needed in onResume because we send the user to the Google Play Store to
    // install the TTS engine if it isn't already installed, so the status of the TTS
    // engine may change when this app resumes.
    // Log.d(TAG, "Initialising TTS");
    mTts =
        new TextToSpeech(
            this,
            this, // TextToSpeech.OnInitListener
            "org.tlhInganHol.android.klingonttsengine"); // Requires API 14.
  }

  @Override
  protected void onDestroy() {
    // TTS:
    // Don't forget to shutdown!
    // Log.d(TAG, "Shutting down TTS");
    if (mTts != null) {
      mTts.stop();
      mTts.shutdown();
    }
    super.onDestroy();
  }

  /*
   * TODO: Override onSave/RestoreInstanceState, onPause/Resume/Stop, to re-create links.
   *
   * public onSaveInstanceState() { // Save the text and views here. super.onSaveInstanceState(); }
   * public onRestoreInstanceState() { // Restore the text and views here.
   * super.onRestoreInstanceState(); }
   */

  @Override
  public boolean onCreateOptionsMenu(Menu menu) {
    super.onCreateOptionsMenu(menu);
    MenuItem shareButton = menu.findItem(R.id.share);
    ShareActionProvider shareActionProvider =
        (ShareActionProvider) MenuItemCompat.getActionProvider(shareButton);

    if (shareActionProvider != null && mShareEntryIntent != null) {
      // Enable "Share" button.
      shareActionProvider.setShareIntent(mShareEntryIntent);
      shareButton.setVisible(true);
    }

    // TTS:
    // The button is disabled in the layout. It should only be enabled in EntryActivity.
    mSpeakButton = menu.findItem(R.id.speak);
    // if (ttsInitialized) {
    //   // Log.d(TAG, "enabling TTS button in onCreateOptionsMenu");
    mSpeakButton.setVisible(true);
    // }

    return true;
  }

  // Set the share intent for this entry.
  private void setShareEntryIntent(KlingonContentProvider.Entry entry) {
    if (entry.isAlternativeSpelling()) {
      return;
    }

    Resources resources = getResources();
    SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());
    mShareEntryIntent = new Intent(Intent.ACTION_SEND);
    // if (sharedPrefs.getBoolean(
    //     Preferences.KEY_KLINGON_UI_CHECKBOX_PREFERENCE, /* default */ false)) {
    //   mShareEntryIntent.putExtra(
    //       Intent.EXTRA_TITLE, resources.getString(R.string.share_popup_title_tlh));
    // } else {
    mShareEntryIntent.putExtra(Intent.EXTRA_TITLE, resources.getString(R.string.share_popup_title));
    // }

    mShareEntryIntent.setType("text/plain");
    String subject = "{" + entry.getFormattedEntryName(/* isHtml */ false) + "}";
    mShareEntryIntent.putExtra(Intent.EXTRA_SUBJECT, subject);
    String snippet = subject + "\n" + entry.getFormattedDefinition(/* isHtml */ false);
    mShareEntryIntent.putExtra(
        Intent.EXTRA_TEXT, snippet + "\n\n" + resources.getString(R.string.shared_from));
  }

  // Private class for handling clickable spans.
  private class LookupClickableSpan extends ClickableSpan {
    private String mQuery;

    LookupClickableSpan(String query) {
      mQuery = query;
    }

    @Override
    public void onClick(View view) {
      Intent intent = new Intent(view.getContext(), KlingonAssistant.class);
      intent.setAction(Intent.ACTION_SEARCH);
      intent.putExtra(SearchManager.QUERY, mQuery);

      view.getContext().startActivity(intent);
      overridePendingTransition(R.anim.slide_in_right, R.anim.slide_out_left);
    }
  }

  @Override
  public void onBackPressed() {
    // TODO: Make the animation go in the other direction if this entry was reached using the
    // "Previous" button.
    super.onBackPressed();
    overridePendingTransition(R.anim.slide_in_left, R.anim.slide_out_right);
  }

  @Override
  public boolean onOptionsItemSelected(MenuItem item) {
    if (item.getItemId() == R.id.speak) {
      // TTS:
      if (!ttsInitialized) {
        // The TTS engine is not installed (or disabled). Send user to Google Play Store or other market.
        try {
          launchExternal(
              "market://details?id=org.tlhInganHol.android.klingonttsengine");
        } catch (android.content.ActivityNotFoundException e) {
          // Fall back to browser.
          launchExternal(
              "https://play.google.com/store/apps/details?id=org.tlhInganHol.android.klingonttsengine");
        }
      } else if (mEntryName != null) {
        // The TTS engine is working, and there's something to say, say it.
        // Log.d(TAG, "Speaking");
        // Toast.makeText(getBaseContext(), mEntryName, Toast.LENGTH_LONG).show();
        mTts.speak(mEntryName, TextToSpeech.QUEUE_FLUSH, null);
      }
    }
    return super.onOptionsItemSelected(item);
  }

  // TTS:
  // Implements TextToSpeech.OnInitListener.
  public void onInit(int status) {
    // status can be either TextToSpeech.SUCCESS or TextToSpeech.ERROR.
    if (status == TextToSpeech.SUCCESS) {
      // Set preferred language to Canadian Klingon.
      // Note that a language may not be available, and the result will indicate this.
      int result = mTts.setLanguage(new Locale("tlh", "", ""));
      if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
        // Lanuage data is missing or the language is not supported.
        Log.e(TAG, "Language is not available.");
      } else {
        // Check the documentation for other possible result codes.
        // For example, the language may be available for the locale,
        // but not for the specified country and variant.

        // The TTS engine has been successfully initialized.
        ttsInitialized = true;
        // if (mSpeakButton != null) {
        //   // Log.d(TAG, "enabling TTS button in onInit");
        //   mSpeakButton.setVisible(true);
        // }
      }
    } else {
      // Initialization failed.
      Log.e(TAG, "Could not initialize TextToSpeech.");
    }
  }
}
