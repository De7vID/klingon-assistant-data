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

import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.SharedPreferences.OnSharedPreferenceChangeListener;
import android.os.Build;
import android.os.Bundle;
import android.preference.PreferenceActivity;
import android.os.Process;
import android.preference.CheckBoxPreference;
import android.view.MenuItem;

public class Preferences extends PreferenceActivity implements OnSharedPreferenceChangeListener {

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

    private CheckBoxPreference mKlingonUICheckBoxPreference;
    private static boolean warningActive = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Load the preferences from an XML resource.
        addPreferencesFromResource(R.xml.preferences);

        // BACKPORT: No Action Bar.
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        switch (item.getItemId()) {
            // BACKPORT: No handling of android.R.id.home.
            default:
                return super.onOptionsItemSelected(item);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();

        // Set up a listener whenever a key changes.
        getPreferenceScreen().getSharedPreferences().registerOnSharedPreferenceChangeListener(this);

        // Get a reference to the use Klingon UI checkbox.
        mKlingonUICheckBoxPreference = (CheckBoxPreference)getPreferenceScreen()
            .findPreference(KEY_KLINGON_UI_CHECKBOX_PREFERENCE);

    }

    @Override
    protected void onPause() {
        super.onPause();

        // Unregister the listener whenever a key changes.
        getPreferenceScreen().getSharedPreferences().unregisterOnSharedPreferenceChangeListener(this);
    }

    public void onSharedPreferenceChanged(final SharedPreferences sharedPrefs, final String key) {

        if (key.equals(KEY_KLINGON_UI_CHECKBOX_PREFERENCE)) {
            final boolean newValue = sharedPrefs.getBoolean(key, /* default */ false);
            if (!warningActive) {
               // User has changed the UI language, display a warning.
               warningActive = true;
               new AlertDialog.Builder(this)
                   .setIcon(R.drawable.alert_dialog_icon)
                   .setTitle(R.string.warning)
                   .setMessage(R.string.change_ui_language_warning)
                   .setCancelable(false) // Can't be canceled with the BACK key.
                   .setPositiveButton(android.R.string.yes, new DialogInterface.OnClickListener() {
                       public void onClick(DialogInterface dialog, int whichButton) {
                           // User clicked OK.
                           warningActive = false;
                       }
                   })
                   .setNegativeButton(android.R.string.no, new DialogInterface.OnClickListener() {
                       public void onClick(DialogInterface dialog, int whichButton) {
                           if( mKlingonUICheckBoxPreference != null ) {
                               // User clicked Cancel, reset preference to previous value.
                               mKlingonUICheckBoxPreference.setChecked(!newValue);
                               warningActive = false;
                           }
                       }
                   })
                   .show();
            }
        }
    }
}
