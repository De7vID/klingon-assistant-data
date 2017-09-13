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

/** Displays the prefix chart. */
public class PrefixChartActivity extends BaseActivity {
  // private static final String TAG = "PrefixChartActivity";

  @Override
  protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());

    boolean useKlingonUI =
        sharedPrefs.getBoolean(Preferences.KEY_KLINGON_UI_CHECKBOX_PREFERENCE, /* default */ false);
    if (useKlingonUI) {
      setDrawerContentView(R.layout.prefix_chart_tlh);
    } else {
      setDrawerContentView(R.layout.prefix_chart);
    }

    Resources resources = getResources();
    TextView entryTitle = (TextView) findViewById(R.id.entry_title);

    // Set the title.
    entryTitle.invalidate();
    if (sharedPrefs.getBoolean(
        Preferences.KEY_KLINGON_FONT_CHECKBOX_PREFERENCE, /* default */ false)) {
      // Klingon (in {pIqaD}).
      entryTitle.setTypeface(KlingonAssistant.getKlingonFontTypeface(getBaseContext()));
      entryTitle.setText(
          KlingonContentProvider.convertStringToKlingonFont(
              resources.getString(R.string.menu_prefix_chart)));
    } else {
      entryTitle.setText(resources.getString(R.string.menu_prefix_chart));
    }
  }

  @Override
  public void onBackPressed() {
    super.onBackPressed();
    overridePendingTransition(R.anim.slide_in_left, R.anim.slide_out_right);
  }
}
