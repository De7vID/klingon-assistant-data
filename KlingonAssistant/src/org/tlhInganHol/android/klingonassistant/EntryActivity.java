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

import java.util.regex.Matcher;

import android.app.SearchManager;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.res.Resources;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.text.Html;
import android.text.SpannableStringBuilder;
import android.text.Spanned;
import android.text.method.LinkMovementMethod;
import android.text.style.ClickableSpan;
import android.text.style.RelativeSizeSpan;
import android.text.style.StyleSpan;
import android.text.style.SuperscriptSpan;
import android.text.style.TypefaceSpan;
import android.text.style.URLSpan;
import android.view.View;

import com.actionbarsherlock.view.Menu;
import com.actionbarsherlock.view.MenuItem;
import com.actionbarsherlock.widget.ShareActionProvider;

/**
 * Displays an entry and its definition.
 */
public class EntryActivity extends BaseActivity {
  // private static final String TAG = "EntryActivity";

  // The intent holding the data to be shared.
  private Intent              mShareEntryIntent                = null;

  @Override
  protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    setDrawerContentView(R.layout.entry);
    Resources resources = getResources();

    JellyBeanSpanFixTextView entryTitle = (JellyBeanSpanFixTextView) findViewById(R.id.entry_title);
    JellyBeanSpanFixTextView entryText = (JellyBeanSpanFixTextView) findViewById(R.id.definition);

    // TODO: Save and restore bundle state to preserve links.

    Uri uri = getIntent().getData();
    // Log.d(TAG, "EntryActivity - uri: " + uri.toString());
    // TODO: Disable the "About" menu item if this is the "About" entry.

    // Retrieve the entry's data.
    // Note: managedQuery is deprecated since API 11.
    Cursor cursor = managedQuery(uri, KlingonContentDatabase.ALL_KEYS, null, null, null);
    KlingonContentProvider.Entry entry = new KlingonContentProvider.Entry(cursor, getBaseContext());

    // Handle alternative spellings here.
    if (entry.isAlternativeSpelling()) {
      // TODO: Immediate redirect to query in entry.getDefinition();
    }

    // Get the shared preferences.
    SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());

    // Set the entry's name (along with info like "slang", formatted in HTML).
    entryTitle.invalidate();
    if (sharedPrefs
            .getBoolean(Preferences.KEY_KLINGON_FONT_CHECKBOX_PREFERENCE, /* default */false)) {
      // Preference is set to display this in {pIqaD}!
      entryTitle.setTypeface(KlingonAssistant.getKlingonFontTypeface(getBaseContext()));
      entryTitle.setText(entry.getEntryNameInKlingonFont());
    } else {
      // Boring transcription based on English (Latin) alphabet.
      entryTitle.setText(Html.fromHtml(entry.getFormattedEntryName(/* isHtml */true)));
    }

    // Create the expanded definition.
    String pos = entry.getFormattedPartOfSpeech(/* isHtml */false);
    String expandedDefinition = pos + entry.getDefinition();

    // Show the German definition.
    String definition_DE = "";
    boolean displayGermanEntry = entry.shouldDisplayGerman();
    int germanDefinitionStart = -1;
    String germanDefinitionHeader = "\n" + resources.getString(R.string.label_german) + ": ";
    if (displayGermanEntry) {
      germanDefinitionStart = expandedDefinition.length();
      definition_DE = entry.getDefinition_DE();
      expandedDefinition += germanDefinitionHeader + definition_DE;
    }

    // Set the share intent.
    setShareEntryIntent(entry);

    // Show the basic notes.
    String notes = entry.getNotes();
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
        expandedDefinition += "\n\n"
                + String.format(resources.getString(R.string.info_inherent_plural), components);
      } else if (entry.isSingularFormOfInherentPlural()) {
        expandedDefinition += "\n\n"
                + String.format(resources.getString(R.string.info_singular_form), components);
      } else if (!showAnalysis) {
        // This is just a regular list of components.
        expandedDefinition += "\n\n" + getResources().getString(R.string.label_components) + ": "
                + components;
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
        expandedDefinition += "\n\n" + resources.getString(R.string.label_category) + ": {"
                + entry.getSentenceTypeQuery() + "}";
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
        analysisQuery += KlingonContentProvider.Entry.COMPONENTS_MARKER
                + components.replaceAll("[{}]", "");
      }
      expandedDefinition += "\n\n" + resources.getString(R.string.label_analyze) + ": {"
              + analysisQuery + "}";
    }

    // Show the examples.
    String examples = entry.getExamples();
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
            && sharedPrefs.getBoolean(Preferences.KEY_SHOW_TRANSITIVITY_CHECKBOX_PREFERENCE, /* default */
                    false)) {
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
    if (sharedPrefs.getBoolean(Preferences.KEY_SHOW_ADDITIONAL_INFORMATION_CHECKBOX_PREFERENCE, /* default */
            false)) {
      // Show additional information preference set to true.
      hiddenNotes = entry.getHiddenNotes();
    }
    int hiddenNotesStart = -1;
    String hiddenNotesHeader = "\n\n" + resources.getString(R.string.label_additional_information)
            + ": ";
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
      // Reduce the size of the German definition.
      ssb.setSpan(new RelativeSizeSpan(smallTextScale), germanDefinitionStart,
              germanDefinitionStart + germanDefinitionHeader.length() + definition_DE.length(),
              finalFlags);
    }
    if (showTransitivityInformation) {
      // Reduce the size of the transitivity information.
      ssb.setSpan(new RelativeSizeSpan(smallTextScale), transitivityStart, transitivityStart
              + transitivityHeader.length() + transitivity.length(), finalFlags);
    }
    if (!hiddenNotes.equals("")) {
      // Reduce the size of the hidden notes.
      ssb.setSpan(new RelativeSizeSpan(smallTextScale), hiddenNotesStart, hiddenNotesStart
              + hiddenNotesHeader.length() + hiddenNotes.length(), finalFlags);
    }
    Matcher m = KlingonContentProvider.Entry.ENTRY_PATTERN.matcher(expandedDefinition);
    while (m.find()) {

      // Strip the brackets {} to get the query.
      String query = expandedDefinition.substring(m.start() + 1, m.end() - 1);
      LookupClickableSpan viewLauncher = new LookupClickableSpan(query);

      // Process the linked entry information.
      KlingonContentProvider.Entry linkedEntry = new KlingonContentProvider.Entry(query,
              getBaseContext());
      // Log.d(TAG, "linkedEntry.getEntryName() = " + linkedEntry.getEntryName());

      // Delete the brackets and metadata parts of the string (which includes analysis components).
      ssb.delete(m.start() + 1 + linkedEntry.getEntryName().length(), m.end());
      ssb.delete(m.start(), m.start() + 1);
      int end = m.start() + linkedEntry.getEntryName().length();

      // Insert link to the category for a useful phrase.
      if (entry.isSentence() && !entry.getSentenceType().equals("")
              && linkedEntry.getEntryName().equals("*")) {
        // Delete the "*" placeholder.
        ssb.delete(m.start(), m.start() + 1);

        // Insert the category name.
        ssb.insert(m.start(), entry.getSentenceType());
        end += entry.getSentenceType().length() - 1;
      }

      // Set the font and link.
      // TODO: Source should link to description of the source.
      // This is true if this entry doesn't launch an EntryActivity.
      boolean disableEntryLink = linkedEntry.doNotLink() || linkedEntry.isSource()
              || linkedEntry.isURL();
      // The last span set on a range must have finalFlags.
      int maybeFinalFlags = disableEntryLink ? finalFlags : intermediateFlags;
      if (linkedEntry.isSource()) {
        // Names of sources are in italics.
        ssb.setSpan(new StyleSpan(android.graphics.Typeface.ITALIC), m.start(), end,
                maybeFinalFlags);
      } else if (linkedEntry.isURL()) {
        // Linkify URL if there is one.
        String url = linkedEntry.getURL();
        if (!url.equals("")) {
          ssb.setSpan(new URLSpan(url), m.start(), end, maybeFinalFlags);
        }
      } else {
        // Klingon is in bold serif.
        ssb.setSpan(new StyleSpan(android.graphics.Typeface.BOLD), m.start(), end,
                intermediateFlags);
        ssb.setSpan(new TypefaceSpan("serif"), m.start(), end, maybeFinalFlags);
      }
      // If linked entry is hypothetical or extended canon, insert a "?" in front.
      if (linkedEntry.isHypothetical() || linkedEntry.isExtendedCanon()) {
        ssb.insert(m.start(), "?");
        ssb.setSpan(new RelativeSizeSpan(smallTextScale), m.start(), m.start() + 1,
                intermediateFlags);
        ssb.setSpan(new SuperscriptSpan(), m.start(), m.start() + 1, maybeFinalFlags);
        end++;
      }
      if (!disableEntryLink) {
        // Link to view launcher.
        ssb.setSpan(viewLauncher, m.start(), end, finalFlags);
      }
      String linkedPos = linkedEntry.getBracketedPartOfSpeech(/* isHtml */false);
      if (!linkedPos.equals("") && linkedPos.length() > 1) {
        ssb.insert(end, linkedPos);

        int rightBracketLoc = linkedPos.indexOf(")");
        if (rightBracketLoc != -1) {
          // linkedPos is always of the form " (pos)[ (def'n N)]", we want to italicise
          // the "pos" part only.
          ssb.setSpan(new StyleSpan(android.graphics.Typeface.ITALIC), end + 2, end
                  + rightBracketLoc, finalFlags);
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
    ShareActionProvider shareActionProvider = (ShareActionProvider) shareButton.getActionProvider();

    if (shareActionProvider != null && mShareEntryIntent != null) {
      // Enable "Share" button.
      shareActionProvider.setShareIntent(mShareEntryIntent);
      shareButton.setVisible(true);
    }
    return true;
  }

  // Set the share intent for this entry.
  private void setShareEntryIntent(KlingonContentProvider.Entry entry) {
    if (entry.isAlternativeSpelling()) {
      return;
    }

    SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());
    mShareEntryIntent = new Intent(Intent.ACTION_SEND);
    if (sharedPrefs.getBoolean(Preferences.KEY_KLINGON_UI_CHECKBOX_PREFERENCE, /* default */false)) {
      mShareEntryIntent.putExtra(Intent.EXTRA_TITLE,
              getResources().getString(R.string.share_popup_title_tlh));
    } else {
      mShareEntryIntent.putExtra(Intent.EXTRA_TITLE,
              getResources().getString(R.string.share_popup_title));
    }

    mShareEntryIntent.setType("text/plain");
    String subject = "{" + entry.getFormattedEntryName(/* isHtml */false) + "}";
    mShareEntryIntent.putExtra(Intent.EXTRA_SUBJECT, subject);
    String snippet = subject + "\n" + entry.getFormattedDefinition(/* isHtml */false);
    mShareEntryIntent.putExtra(Intent.EXTRA_TEXT,
            snippet + "\n\n" + getResources().getString(R.string.shared_from));
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
    super.onBackPressed();
    overridePendingTransition(R.anim.slide_in_left, R.anim.slide_out_right);
  }
}
