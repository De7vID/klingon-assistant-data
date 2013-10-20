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

import android.app.SearchManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.text.Html;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.TwoLineListItem;
import wei.mark.standout.StandOutWindow;

/**
 * The main activity for the dictionary. Displays search results triggered by the search dialog and
 * handles actions from search suggestions.
 */
public class KlingonAssistant extends BaseActivity {
  private static final String TAG = "KlingonAssistant";

  // Preference key for whether to show help.
  public static final String  KEY_SHOW_HELP                    = "show_help";

  // This holds the {pIqaD} typeface.
  private static Typeface     mKlingonFontTypeface             = null;

  // The two main views in app's main screen.
  private TextView            mTextView;
  private ListView            mListView;

  @Override
  public void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);

    SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());
    if (sharedPrefs.getBoolean(Preferences.KEY_KLINGON_UI_CHECKBOX_PREFERENCE, /* default */false)) {
      setDrawerContentView(R.layout.main_tlh);
    } else {
      setDrawerContentView(R.layout.main);
    }

    mTextView = (TextView) findViewById(R.id.text);
    mListView = (ListView) findViewById(R.id.list);

    StandOutWindow.closeAll(this, FloatingWindow.class);
    StandOutWindow.show(this, FloatingWindow.class, StandOutWindow.DEFAULT_ID);

    handleIntent(getIntent());
  }

  @Override
  protected void onNewIntent(Intent intent) {
    // Because this activity has set launchMode="singleTop", the system calls this method
    // to deliver the intent if this activity is currently the foreground activity when
    // invoked again (when the user executes a search from this activity, we don't create
    // a new instance of this activity, so the system delivers the search intent here)
    handleIntent(intent);
  }

  // Helper method to determine if a shared text came from Twitter, and if so, strip it of
  // everything but the actual tweet.
  private String stripTweet(String text) {
    if (text.indexOf("https://twitter.com/download") == -1) {
      // All shared tweets contain the Twitter download link, regardless of the UI language.
      // So if this isn't found, then it's not a tweet.
      return text;
    }
    // If it's a tweet, the second line is the actual content.
    String[] textParts = text.split("\n");
    if (textParts.length >= 2) {
      return textParts[1];
    }
    return text;
  }

  private void handleIntent(Intent intent) {
    if (Intent.ACTION_VIEW.equals(intent.getAction())) {
      // handles a click on a search suggestion; launches activity to show entry
      String entryId = intent.getDataString();
      // Log.d(TAG, "entryId = " + entryId);
      launchEntry(entryId);

    } else if (Intent.ACTION_SEARCH.equals(intent.getAction())) {
      // handles a search query
      String query = intent.getStringExtra(SearchManager.QUERY);
      showResults(query);

    } else if (Intent.ACTION_SEND.equals(intent.getAction())) {
      // handles another plain text shared from another app
      if ("text/plain".equals(intent.getType())) {
        String sharedText = intent.getStringExtra(Intent.EXTRA_TEXT);
        if (sharedText != null) {
          /* if (BuildConfig.DEBUG) {
            Log.d(TAG, "Incoming text:\n" + sharedText);
          } */
          // Sanitise incoming text. Also cap at 140 chars, for reasons of speed and because that's
          // the limit used by Twitter.
          sharedText = stripTweet(sharedText);
          sharedText = sharedText.replaceAll("[:\\*<>\\n]", " ").trim().replaceAll("\\s+", " ");
          if (sharedText.length() > 140) {
            sharedText = sharedText.substring(0, 140);
          }
          // TODO: Turn off "xifan hol" mode for this search, since it doesn't really make sense
          // here.
          /* if (BuildConfig.DEBUG) {
            Log.d(TAG, "Shared text:\n" + sharedText);
          } */
          showResults(sharedText);
        }
      }

    } else {
      // Show help if the flag is set. If the flag has not ever been set,
      // either the database does not yet exist, or it had been created by
      // an older version of this program.
      SharedPreferences sharedPrefs = PreferenceManager
              .getDefaultSharedPreferences(getBaseContext());
      if (sharedPrefs.getBoolean(KEY_SHOW_HELP, /* default */true)) {
        try {
          // Attempt to show it.
          displayHelp(QUERY_FOR_ABOUT);

          // Unset the flag since the help has been shown.
          SharedPreferences.Editor sharedPrefsEd = PreferenceManager.getDefaultSharedPreferences(
                  getBaseContext()).edit();
          sharedPrefsEd.putBoolean(KEY_SHOW_HELP, false);
          sharedPrefsEd.commit();

        } catch (Exception e) {
          // No big deal if help screen isn't shown on start. Do nothing.
        }
      }
    }
  }

  public static Typeface getKlingonFontTypeface(Context context) {
    if (mKlingonFontTypeface == null) {
      mKlingonFontTypeface = Typeface.createFromAsset(context.getAssets(), "fonts/pIqaD.ttf");
    }
    return mKlingonFontTypeface;
  }

  // Launch an entry activity with the entry's info.
  private void launchEntry(String entryId) {
    if (entryId == null) {
      return;
    }

    Intent entryIntent = new Intent(this, EntryActivity.class);

    // Form the URI for the entry.
    Uri uri = Uri.parse(KlingonContentProvider.CONTENT_URI + "/get_entry_by_id/" + entryId);
    entryIntent.setData(uri);

    startActivity(entryIntent);
    overridePendingTransition(R.anim.slide_in_right, R.anim.slide_out_left);
  }

  class EntryAdapter extends BaseAdapter implements AdapterView.OnItemClickListener {

    private final Cursor         mCursor;
    private final LayoutInflater mInflater;

    public EntryAdapter(Cursor cursor) {
      mCursor = cursor;
      mInflater = (LayoutInflater) KlingonAssistant.this
              .getSystemService(Context.LAYOUT_INFLATER_SERVICE);
    }

    @Override
    public int getCount() {
      return mCursor.getCount();
    }

    @Override
    public Object getItem(int position) {
      return position;
    }

    @Override
    public long getItemId(int position) {
      return position;
    }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
      TwoLineListItem view = (convertView != null) ? (TwoLineListItem) convertView
              : createView(parent);
      mCursor.moveToPosition(position);
      bindView(view, mCursor);
      return view;
    }

    private TwoLineListItem createView(ViewGroup parent) {
      TwoLineListItem item = (TwoLineListItem) mInflater.inflate(
              android.R.layout.simple_list_item_2, parent, false);

      // Set single line to true if you want shorter definitions.
      item.getText2().setSingleLine(false);
      item.getText2().setEllipsize(TextUtils.TruncateAt.END);

      return item;
    }

    private void bindView(TwoLineListItem view, Cursor cursor) {
      KlingonContentProvider.Entry entry = new KlingonContentProvider.Entry(cursor,
              getBaseContext());

      // TODO(davinci): Format with colour and size.
      String indent1 = entry.isIndented() ? "&nbsp;&nbsp;&nbsp;&nbsp;" : "";
      String indent2 = entry.isIndented() ? "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" : "";

      // Use serif for the entry, so capital-I and lowercase-l are distinguishable.
      view.getText1().setTypeface(Typeface.SERIF);
      view.getText1().setText(
              Html.fromHtml(indent1 + entry.getFormattedEntryName(/* isHtml */true)));

      // Use sans serif for the definition.
      view.getText2().setTypeface(Typeface.SANS_SERIF);
      view.getText2().setText(
              Html.fromHtml(indent2 + entry.getFormattedDefinition(/* isHtml */true)));
    }

    @Override
    public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
      mCursor.moveToPosition(position);
      launchEntry(mCursor.getString(KlingonContentDatabase.COLUMN_ID));
    }
  }

  /**
   * Searches the dictionary and displays results for the given query.
   *
   * @param query
   *          The search query
   */
  private void showResults(String query) {

    // Note: managedQuery is deprecated since API 11.
    Cursor cursor = managedQuery(Uri.parse(KlingonContentProvider.CONTENT_URI + "/lookup"),
            null /* all columns */, null, new String[] { query }, null);

    KlingonContentProvider.Entry queryEntry = new KlingonContentProvider.Entry(query,
            getBaseContext());
    String entryNameWithPoS = queryEntry.getEntryName()
            + queryEntry.getBracketedPartOfSpeech(/* isHtml */true);

    SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());
    if (cursor == null || cursor.getCount() == 0) {
      // There are no results.
      if (sharedPrefs
              .getBoolean(Preferences.KEY_KLINGON_UI_CHECKBOX_PREFERENCE, /* default */false)) {
        mTextView.setText(Html.fromHtml(getString(R.string.no_results_tlh,
                new Object[] { entryNameWithPoS })));
      } else {
        mTextView.setText(Html.fromHtml(getString(R.string.no_results,
                new Object[] { entryNameWithPoS })));
      }

    } else {
      // Display the number of results.
      int count = cursor.getCount();
      String countString;
      if (queryEntry.getEntryName().equals("*")) {
        // Searching for a class of phrases.
        countString = queryEntry.getSentenceType();
        if (countString.equals("")) {
          // The sentence type was indeterminate.
          // This only ever happens if the user enters "*:sen" as a search string.
          count = 0;
          countString = "Sentences:";
        } else {
          // Display, e.g., "Lyrics:".
          countString += ":";
        }
      } else if (sharedPrefs.getBoolean(Preferences.KEY_KLINGON_UI_CHECKBOX_PREFERENCE, /* default */
              false)) {
        countString = getResources().getQuantityString(R.plurals.search_results_tlh, count,
                new Object[] { count, entryNameWithPoS });
      } else {
        countString = getResources().getQuantityString(R.plurals.search_results, count,
                new Object[] { count, entryNameWithPoS });
      }
      mTextView.setText(Html.fromHtml(countString));

      // Create a cursor adapter for the entries and apply them to the ListView.
      EntryAdapter entryAdapter = new EntryAdapter(cursor);
      mListView.setAdapter(entryAdapter);
      mListView.setOnItemClickListener(entryAdapter);

      // Launch the entry automatically.
      // TODO: See if list view above can be skipped entirely.
      if (count == 1) {
        launchEntry(cursor.getString(KlingonContentDatabase.COLUMN_ID));
      }
    }
  }

  @Override
  public boolean onSearchRequested() {
    SearchManager searchManager = (SearchManager) getSystemService(Context.SEARCH_SERVICE);

    if (searchManager != null) {
      SharedPreferences sharedPrefs = PreferenceManager
              .getDefaultSharedPreferences(getBaseContext());
      if (sharedPrefs
              .getBoolean(Preferences.KEY_KLINGON_UI_CHECKBOX_PREFERENCE, /* default */false)) {
        // Use the Klingon UI strings.
        searchManager.startSearch(null, false, new ComponentName(this, KlingonAssistant.class),
                null, false);
      } else {
        // Use the non-Klingon UI strings.
        searchManager.startSearch(null, false, new ComponentName(this, KlingonAssistantAlt.class),
                null, false);
      }
      return true;
    }
    return false;
  }

  @Override
  public void onBackPressed() {
    super.onBackPressed();
    if (!isTaskRoot()) {
      overridePendingTransition(R.anim.slide_in_left, R.anim.slide_out_right);
    }
  }
}
