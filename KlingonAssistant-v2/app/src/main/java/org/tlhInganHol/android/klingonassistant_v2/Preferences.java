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

import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.SharedPreferences;
import android.content.SharedPreferences.OnSharedPreferenceChangeListener;
import android.content.res.Resources;
import android.os.Bundle;
import android.preference.CheckBoxPreference;
import android.preference.PreferenceManager;
import android.support.v7.widget.Toolbar;
import android.view.LayoutInflater;
import android.view.MenuItem;
import android.view.ViewGroup;
import java.util.Locale;

// Since this needs to extend PreferenceActivity, it does not have an action bar.
public class Preferences extends AppCompatPreferenceActivity
    implements OnSharedPreferenceChangeListener {

  // Tutorial preferences.
  // public static final String KEY_RUN_TUTORIAL_CHECKBOX_PREFERENCE = "run_tutorial_checkbox_preference";

  // Language preferences.
  public static final String KEY_KLINGON_UI_CHECKBOX_PREFERENCE = "klingon_ui_checkbox_preference";
  public static final String KEY_KLINGON_FONT_CHECKBOX_PREFERENCE =
      "klingon_font_checkbox_preference";
  private static final String KEY_LANGUAGE_DEFAULT_ALREADY_SET = "language_default_already_set";
  public static final String KEY_SHOW_GERMAN_DEFINITIONS_CHECKBOX_PREFERENCE =
      "show_german_definitions_checkbox_preference";
  public static final String KEY_SEARCH_GERMAN_DEFINITIONS_CHECKBOX_PREFERENCE =
      "search_german_definitions_checkbox_preference";

  // Input preferences.
  public static final String KEY_XIFAN_HOL_CHECKBOX_PREFERENCE = "xifan_hol_checkbox_preference";
  public static final String KEY_SWAP_QS_CHECKBOX_PREFERENCE = "swap_qs_checkbox_preference";

  // Social preferences.
  public static final String KEY_SOCIAL_NETWORK_LIST_PREFERENCE = "social_network_list_preference";

  // Informational preferences.
  public static final String KEY_USE_COLOURS_CHECKBOX_PREFERENCE =
      "use_colours_checkbox_preference";
  public static final String KEY_SHOW_TRANSITIVITY_CHECKBOX_PREFERENCE =
      "show_transitivity_checkbox_preference";
  public static final String KEY_SHOW_ADDITIONAL_INFORMATION_CHECKBOX_PREFERENCE =
      "show_additional_information_checkbox_preference";

  private CheckBoxPreference mKlingonUICheckBoxPreference;
  private CheckBoxPreference mKlingonFontCheckBoxPreference;
  private static boolean warningActive = false;

  // @TargetApi(Build.VERSION_CODES.N)
  public static boolean shouldPreferGerman() {
    Locale locale;
    // if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
    //   locale = Resources.getSystem().getConfiguration().getLocales().get(0);
    // } else {
    locale = Resources.getSystem().getConfiguration().locale;
    // }
    return locale.getLanguage().equals(Locale.GERMAN.getLanguage());
  }

  @Override
  protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);

    // Set up the toolbar for an AppCompatPreferenceActivity.
    setupActionBar();

    // Load the preferences from an XML resource.
    addPreferencesFromResource(R.xml.preferences);

    // Set the defaults for the German options based on the user's language, if it hasn't been
    // already set.
    SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());
    if (!sharedPrefs.getBoolean(KEY_LANGUAGE_DEFAULT_ALREADY_SET, /* default */ false)) {
      CheckBoxPreference mShowGermanCheckBoxPreference =
          (CheckBoxPreference)
              getPreferenceScreen().findPreference(KEY_SHOW_GERMAN_DEFINITIONS_CHECKBOX_PREFERENCE);
      CheckBoxPreference mSearchGermanCheckBoxPreference =
          (CheckBoxPreference)
              getPreferenceScreen()
                  .findPreference(KEY_SEARCH_GERMAN_DEFINITIONS_CHECKBOX_PREFERENCE);
      mShowGermanCheckBoxPreference.setChecked(shouldPreferGerman());
      mSearchGermanCheckBoxPreference.setChecked(shouldPreferGerman());

      SharedPreferences.Editor sharedPrefsEd = sharedPrefs.edit();
      sharedPrefsEd.putBoolean(KEY_LANGUAGE_DEFAULT_ALREADY_SET, true);
      sharedPrefsEd.commit();
    }

    // TUTORIAL
    // if (KlingonAssistant.INCLUDE_TUTORIAL) {
    //   Preference tutorialPreference = findPreference(KEY_RUN_TUTORIAL_CHECKBOX_PREFERENCE);
    //   tutorialPreference.setEnabled(true);
    // }
  }

  private void setupActionBar() {
    // This only works in ICS (API 14) and up.
    ViewGroup root =
        (ViewGroup) findViewById(android.R.id.list).getParent().getParent().getParent();
    Toolbar toolbar =
        (Toolbar) LayoutInflater.from(this).inflate(R.layout.view_toolbar, root, false);
    root.addView(toolbar, 0);
    setSupportActionBar(toolbar);
    getSupportActionBar().setDisplayHomeAsUpEnabled(true);
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

  @Override
  protected void onResume() {
    super.onResume();

    // Set up a listener whenever a key changes.
    getPreferenceScreen().getSharedPreferences().registerOnSharedPreferenceChangeListener(this);

    // Get a reference to the "use Klingon UI" checkbox and the "use Klingon font" checkbox.
    mKlingonUICheckBoxPreference =
        (CheckBoxPreference)
            getPreferenceScreen().findPreference(KEY_KLINGON_UI_CHECKBOX_PREFERENCE);
    mKlingonFontCheckBoxPreference =
        (CheckBoxPreference)
            getPreferenceScreen().findPreference(KEY_KLINGON_FONT_CHECKBOX_PREFERENCE);
  }

  @Override
  protected void onPause() {
    super.onPause();

    // Unregister the listener whenever a key changes.
    getPreferenceScreen().getSharedPreferences().unregisterOnSharedPreferenceChangeListener(this);
  }

  @Override
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
            .setPositiveButton(
                android.R.string.yes,
                new DialogInterface.OnClickListener() {
                  @Override
                  public void onClick(DialogInterface dialog, int whichButton) {
                    // User clicked OK.
                    warningActive = false;

                    // If the Klingon font preference is set, unset it if the user's UI
                    // language is unset.
                    if (!newValue && mKlingonFontCheckBoxPreference != null) {
                      mKlingonFontCheckBoxPreference.setChecked(false);
                    }
                  }
                })
            .setNegativeButton(
                android.R.string.no,
                new DialogInterface.OnClickListener() {
                  @Override
                  public void onClick(DialogInterface dialog, int whichButton) {
                    if (mKlingonUICheckBoxPreference != null) {
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

  @Override
  public void onBackPressed() {
    super.onBackPressed();
    if (!isTaskRoot()) {
      overridePendingTransition(R.anim.slide_in_left, R.anim.slide_out_right);
    }
  }
}
