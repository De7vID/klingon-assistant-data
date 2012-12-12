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

import org.tlhInganHol.android.klingonassistant.R;

import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import com.actionbarsherlock.app.ActionBar;
import com.actionbarsherlock.app.SherlockPreferenceActivity;
import com.actionbarsherlock.view.MenuItem;

public class Preferences extends SherlockPreferenceActivity {

    // Language preferences.
    public static final String KEY_KLINGON_UI_CHECKBOX_PREFERENCE = "klingon_ui_checkbox_preference";
    public static final String KEY_SHOW_GERMAN_DEFINITIONS_CHECKBOX_PREFERENCE = "show_german_definitions_checkbox_preference";
    public static final String KEY_SEARCH_GERMAN_DEFINITIONS_CHECKBOX_PREFERENCE = "search_german_definitions_checkbox_preference";

    // Input preferences.
    public static final String XIFAN_HOL_CHECKBOX_PREFERENCE = "xifan_hol_checkbox_preference";
    public static final String SWAP_QS_CHECKBOX_PREFERENCE = "swap_qs_checkbox_preference";

    // Informational preferences.
    public static final String KEY_SHOW_TRANSITIVITY_CHECKBOX_PREFERENCE = "show_transitivity_checkbox_preference";
    public static final String KEY_SHOW_ADDITIONAL_INFORMATION_CHECKBOX_PREFERENCE = "show_additional_information_checkbox_preference";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Load the preferences from an XML resource.
        addPreferencesFromResource(R.xml.preferences);

        ActionBar actionBar = getSupportActionBar();
        actionBar.setDisplayHomeAsUpEnabled(true);
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        switch (item.getItemId()) {
            case android.R.id.home:
                finish();
                return true;
            default:
                return super.onOptionsItemSelected(item);
        }
    }

}
