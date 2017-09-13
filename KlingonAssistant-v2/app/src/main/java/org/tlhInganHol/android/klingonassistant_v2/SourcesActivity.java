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

import android.content.SharedPreferences;
import android.content.res.Resources;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.widget.TextView;

/** Displays the sources page. */
public class SourcesActivity extends BaseActivity {
  // private static final String TAG = "SourcesActivity";

  @Override
  protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    setDrawerContentView(R.layout.sources);
    Resources resources = getResources();
    TextView entryTitle = (TextView) findViewById(R.id.entry_title);

    // Get the shared preferences.
    SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());

    // Set the title.
    entryTitle.invalidate();
    if (sharedPrefs.getBoolean(
        Preferences.KEY_KLINGON_FONT_CHECKBOX_PREFERENCE, /* default */ false)) {
      // Klingon (in {pIqaD}).
      entryTitle.setTypeface(KlingonAssistant.getKlingonFontTypeface(getBaseContext()));
      entryTitle.setText(
          KlingonContentProvider.convertStringToKlingonFont(
              resources.getString(R.string.menu_sources)));
    } else {
      entryTitle.setText(resources.getString(R.string.menu_sources));
    }

    // TODO: Bold the names of sources.
  }

  @Override
  public void onBackPressed() {
    super.onBackPressed();
    overridePendingTransition(R.anim.slide_in_left, R.anim.slide_out_right);
  }
}
