/*
 * Copyright (C) 2013 De'vID jonpIn (David Yonge-Mallo)
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
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.res.Resources;
import android.os.Build;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.widget.SearchView;
import com.actionbarsherlock.app.SherlockActivity;
import com.actionbarsherlock.view.Menu;
import com.actionbarsherlock.view.MenuInflater;
import com.actionbarsherlock.view.MenuItem;
import com.actionbarsherlock.widget.ShareActionProvider;

/**
 * Displays an entry and its definition.
 */
public class PrefixChartActivity extends BaseActivity {
  // private static final String TAG = "PrefixChartActivity";

  // The intent holding the data to be shared.
  private Intent              mShareEntryIntent                = null;

  @Override
  protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    setDrawerContentView(R.layout.prefix_charts);
    Resources resources = getResources();
    SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());

    JellyBeanSpanFixTextView entryTitle = (JellyBeanSpanFixTextView) findViewById(R.id.entry_title);
    if (sharedPrefs.getBoolean(Preferences.KEY_KLINGON_UI_CHECKBOX_PREFERENCE, /* default */false)) {
      entryTitle.setText(resources.getString(R.string.menu_prefix_charts_tlh));
    } else {
      entryTitle.setText(resources.getString(R.string.menu_prefix_charts));
    }

    // Activate type-to-search for local search. Typing will automatically
    // start a search of the database.
    setDefaultKeyMode(DEFAULT_KEYS_SEARCH_LOCAL);
  }

  @Override
  public boolean onCreateOptionsMenu(Menu menu) {
    MenuInflater inflater = getSupportMenuInflater();
    SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());
    if (sharedPrefs.getBoolean(Preferences.KEY_KLINGON_UI_CHECKBOX_PREFERENCE, /* default */false)) {
      inflater.inflate(R.menu.options_menu_tlh, menu);
    } else {
      inflater.inflate(R.menu.options_menu, menu);
    }
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.HONEYCOMB) {
      SearchManager searchManager = (SearchManager) getSystemService(Context.SEARCH_SERVICE);
      SearchView searchView = (SearchView) menu.findItem(R.id.search).getActionView();
      searchView.setSearchableInfo(searchManager.getSearchableInfo(getComponentName()));
      searchView.setIconifiedByDefault(false);
    }
    MenuItem shareButton = menu.findItem(R.id.share);
    ShareActionProvider shareActionProvider = (ShareActionProvider) shareButton.getActionProvider();

    if (shareActionProvider != null && mShareEntryIntent != null) {
      // Enable "Share" button.
      shareActionProvider.setShareIntent(mShareEntryIntent);
      shareButton.setVisible(true);
    }
    return true;
  }

  @Override
  public void onBackPressed() {
    super.onBackPressed();
    overridePendingTransition(R.anim.slide_in_left, R.anim.slide_out_right);
  }
}
