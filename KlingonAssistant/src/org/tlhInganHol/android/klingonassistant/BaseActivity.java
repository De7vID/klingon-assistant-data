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

package org.tlhInganHol.android.klingonassistant;

import java.util.ArrayList;
import java.util.List;

import android.app.SearchManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.preference.PreferenceManager;
import android.util.Log;
import android.view.Menu;
import android.view.MenuInflater;
import android.view.MenuItem;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ListView;
import android.widget.Toast;
import net.simonvt.menudrawer.MenuDrawer;
import net.simonvt.menudrawer.Position;
import wei.mark.standout.StandOutWindow;

import android.support.v4.view.MenuItemCompat;
import android.support.v7.app.ActionBar;
import android.support.v7.app.ActionBarActivity;
import android.support.v7.widget.SearchView;

// TUTORIAL:
// import com.google.android.gms.plus.PlusShare;
// import com.google.android.gms.plus.PlusShare.Builder;
// import com.google.android.gms.plus.model.people.Person;
// import java.util.Arrays;


public class BaseActivity extends ActionBarActivity implements SlideMenuAdapter.MenuListener {
    private static final String TAG = "BaseActivity";

    // This must uniquely identify the {boQwI'} entry.
    protected static final String QUERY_FOR_ABOUT                = "boQwI':n";

    private static final String STATE_ACTIVE_POSITION =
            "org.tlhInganHol.android.klingonassistant.activePosition";

    // Help pages.
    private static final String QUERY_FOR_PRONUNCIATION          = "QIch:n";
    private static final String QUERY_FOR_PREFIXES               = "moHaq:n";
    private static final String QUERY_FOR_NOUN_SUFFIXES          = "DIp:n";
    private static final String QUERY_FOR_VERB_SUFFIXES          = "wot:n";

    // Classes of phrases.
    private static final String QUERY_FOR_EMPIRE_UNION_DAY       = "*:sen:eu";
    // private static final String QUERY_FOR_IDIOMS                 = "*:sen:idiom";
    private static final String QUERY_FOR_CURSE_WARFARE          = "*:sen:mv";
    private static final String QUERY_FOR_NENTAY                 = "*:sen:nt";
    // private static final String QUERY_FOR_PROVERBS               = "*:sen:prov";
    private static final String QUERY_FOR_QI_LOP                 = "*:sen:Ql";
    private static final String QUERY_FOR_REJECTION              = "*:sen:rej";
    private static final String QUERY_FOR_REPLACEMENT_PROVERBS   = "*:sen:rp";
    private static final String QUERY_FOR_SECRECY_PROVERBS       = "*:sen:sp";
    private static final String QUERY_FOR_TOASTS                 = "*:sen:toast";
    private static final String QUERY_FOR_LYRICS                 = "*:sen:lyr";
    private static final String QUERY_FOR_BEGINNERS_CONVERSATION = "*:sen:bc";
    private static final String QUERY_FOR_JOKES                  = "*:sen:joke";

    private KillReceiver mKillReceiver;
    protected static final String ACTION_KILL = "org.tlhInganHol.android.klingonassistant.intent.action.KILL";
    protected static final String KILL_TYPE = "org.tlhInganHol.android.klingonassistant.intent.action/kill";

    // Request code to change FloatingWindow's data.
    public static final int DATA_CHANGED_QUERY = 0;

    private MenuDrawer mDrawer;

    protected SlideMenuAdapter mAdapter;
    protected ListView mList;

    private int mActivePosition = 0;

    // Helper method to determine whether the device is (likely) a tablet in horizontal orientation.
    public boolean isHorizontalTablet() {
        Configuration config = getResources().getConfiguration();
        if (config.orientation == Configuration.ORIENTATION_LANDSCAPE &&
            (config.screenLayout & Configuration.SCREENLAYOUT_SIZE_MASK) >= Configuration.SCREENLAYOUT_SIZE_LARGE) {
            return true;
        }
        return false;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (savedInstanceState != null) {
            mActivePosition = savedInstanceState.getInt(STATE_ACTIVE_POSITION);
        }

        // Close the floating window, if there is one. Work around a race condition.
        Log.d(TAG, "Starting activity with non-floating window. Close floating window.");
        Handler killFloatingWindowHandler = new Handler();
        Runnable killFloatingWindowRunnable = new Runnable() {
            public void run() {
                StandOutWindow.closeAll(BaseActivity.this, FloatingWindow.class);
            }
        };
        killFloatingWindowHandler.postDelayed(killFloatingWindowRunnable, 100);  // 100 ms

        // Get the action bar.
        ActionBar actionBar = getSupportActionBar();
        actionBar.setDisplayHomeAsUpEnabled(true);

        // If the device is in landscape orientation and the screen size is large (or bigger), then
        // make the slide-out menu static. Otherwise, hide it by default.
        MenuDrawer.Type drawerType = MenuDrawer.Type.BEHIND;
        if (isHorizontalTablet()) {
            drawerType = MenuDrawer.Type.STATIC;
        }
        mDrawer = MenuDrawer.attach(this, drawerType, Position.LEFT, MenuDrawer.MENU_DRAG_CONTENT);

        List<Object> items = new ArrayList<Object>();
        SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());
        if (sharedPrefs.getBoolean(Preferences.KEY_KLINGON_UI_CHECKBOX_PREFERENCE, /* default */false)) {
            items.add(new SlideMenuCategory(R.string.menu_reference_tlh));
                items.add(new SlideMenuItem(R.string.menu_pronunciation_tlh, R.id.pronunciation, 0));
                items.add(new SlideMenuItem(R.string.menu_prefixes_tlh, R.id.prefixes, 0));
                items.add(new SlideMenuItem(R.string.menu_prefix_charts_tlh, R.id.prefix_charts, 0));
                items.add(new SlideMenuItem(R.string.menu_noun_suffixes_tlh, R.id.noun_suffixes, 0));
                items.add(new SlideMenuItem(R.string.menu_verb_suffixes_tlh, R.id.verb_suffixes, 0));
            items.add(new SlideMenuCategory(R.string.menu_phrases_tlh));
                items.add(new SlideMenuItem(R.string.beginners_conversation_tlh, R.id.beginners_conversation, 0));
                items.add(new SlideMenuItem(R.string.jokes_tlh, R.id.jokes, 0));
                items.add(new SlideMenuItem(R.string.nentay_tlh, R.id.nentay, 0));
                items.add(new SlideMenuItem(R.string.military_celebration_tlh, R.id.military_celebration, 0));
                items.add(new SlideMenuItem(R.string.toasts_tlh, R.id.toasts, 0));
                items.add(new SlideMenuItem(R.string.lyrics_tlh, R.id.lyrics, 0));
                items.add(new SlideMenuItem(R.string.curse_warfare_tlh, R.id.curse_warfare, 0));
                items.add(new SlideMenuItem(R.string.replacement_proverbs_tlh, R.id.replacement_proverbs, 0));
                items.add(new SlideMenuItem(R.string.secrecy_proverbs_tlh, R.id.secrecy_proverbs, 0));
                items.add(new SlideMenuItem(R.string.empire_union_day_tlh, R.id.empire_union_day, 0));
                items.add(new SlideMenuItem(R.string.rejection_tlh, R.id.rejection, 0));
            items.add(new SlideMenuCategory(R.string.menu_media_tlh));
                items.add(new SlideMenuItem(R.string.media_1_title_tlh, R.id.media_1, 0));
                items.add(new SlideMenuItem(R.string.media_2_title_tlh, R.id.media_2, 0));
                items.add(new SlideMenuItem(R.string.media_3_title_tlh, R.id.media_3, 0));
                items.add(new SlideMenuItem(R.string.media_4_title_tlh, R.id.media_4, 0));
                items.add(new SlideMenuItem(R.string.media_5_title_tlh, R.id.media_5, 0));
                items.add(new SlideMenuItem(R.string.media_6_title_tlh, R.id.media_6, 0));
            /*
            items.add(new SlideMenuCategory(R.string.menu_social_tlh));
                items.add(new SlideMenuItem(R.string.menu_gplus_tlh, R.id.gplus, 0));
                items.add(new SlideMenuItem(R.string.menu_facebook_tlh, R.id.facebook, 0));
                items.add(new SlideMenuItem(R.string.menu_kag_tlh, R.id.kag, 0));
                items.add(new SlideMenuItem(R.string.menu_kidc_tlh, R.id.kidc, 0));
            */
        } else {
            items.add(new SlideMenuCategory(R.string.menu_reference));
                items.add(new SlideMenuItem(R.string.menu_pronunciation, R.id.pronunciation, 0));
                items.add(new SlideMenuItem(R.string.menu_prefixes, R.id.prefixes, 0));
                items.add(new SlideMenuItem(R.string.menu_prefix_charts, R.id.prefix_charts, 0));
                items.add(new SlideMenuItem(R.string.menu_noun_suffixes, R.id.noun_suffixes, 0));
                items.add(new SlideMenuItem(R.string.menu_verb_suffixes, R.id.verb_suffixes, 0));
            items.add(new SlideMenuCategory(R.string.menu_phrases));
                items.add(new SlideMenuItem(R.string.beginners_conversation, R.id.beginners_conversation, 0));
                items.add(new SlideMenuItem(R.string.jokes, R.id.jokes, 0));
                items.add(new SlideMenuItem(R.string.nentay, R.id.nentay, 0));
                items.add(new SlideMenuItem(R.string.military_celebration, R.id.military_celebration, 0));
                items.add(new SlideMenuItem(R.string.toasts, R.id.toasts, 0));
                items.add(new SlideMenuItem(R.string.lyrics, R.id.lyrics, 0));
                items.add(new SlideMenuItem(R.string.curse_warfare, R.id.curse_warfare, 0));
                items.add(new SlideMenuItem(R.string.replacement_proverbs, R.id.replacement_proverbs, 0));
                items.add(new SlideMenuItem(R.string.secrecy_proverbs, R.id.secrecy_proverbs, 0));
                items.add(new SlideMenuItem(R.string.empire_union_day, R.id.empire_union_day, 0));
                items.add(new SlideMenuItem(R.string.rejection, R.id.rejection, 0));
                // Not all general proverbs are properly tagged yet.
                // Too many idioms; also no known Klingon term for "idiom".
            items.add(new SlideMenuCategory(R.string.menu_media));
                items.add(new SlideMenuItem(R.string.media_1_title, R.id.media_1, 0));
                items.add(new SlideMenuItem(R.string.media_2_title, R.id.media_2, 0));
                items.add(new SlideMenuItem(R.string.media_3_title, R.id.media_3, 0));
                items.add(new SlideMenuItem(R.string.media_4_title, R.id.media_4, 0));
                items.add(new SlideMenuItem(R.string.media_5_title, R.id.media_5, 0));
                items.add(new SlideMenuItem(R.string.media_6_title, R.id.media_6, 0));
            /*
            items.add(new SlideMenuCategory(R.string.menu_social));
                items.add(new SlideMenuItem(R.string.menu_gplus, R.id.gplus, 0));
                items.add(new SlideMenuItem(R.string.menu_facebook, R.id.facebook, 0));
                items.add(new SlideMenuItem(R.string.menu_kag, R.id.kag, 0));
                items.add(new SlideMenuItem(R.string.menu_kidc, R.id.kidc, 0));
            */
        }
        mList = new ListView(this);

        mAdapter = new SlideMenuAdapter(this, items);
        mAdapter.setListener(this);
        mAdapter.setActivePosition(mActivePosition);

        mList.setAdapter(mAdapter);
        mList.setOnItemClickListener(mItemClickListener);

        mDrawer.setMenuView(mList);

        // Allow the menu to slide out when any part of the screen is dragged.
        mDrawer.setTouchMode(MenuDrawer.TOUCH_MODE_FULLSCREEN);

        // The drawable that replaces the up indicator in the action bar.
        mDrawer.setSlideDrawable(R.drawable.ic_drawer);
        // Whether the previous drawable should be shown.
        mDrawer.setDrawerIndicatorEnabled(true);

        // Activate type-to-search for local search. Typing will automatically
        // start a search of the database.
        setDefaultKeyMode(DEFAULT_KEYS_SEARCH_LOCAL);

        // Register a receiver for the kill order.
        mKillReceiver = new KillReceiver();
        registerReceiver(mKillReceiver, IntentFilter.create(ACTION_KILL, KILL_TYPE));
    }

    @Override
    protected void onDestroy() {
        unregisterReceiver(mKillReceiver);
        super.onDestroy();
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
      MenuInflater inflater = getMenuInflater();
      SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());
      if (sharedPrefs.getBoolean(Preferences.KEY_KLINGON_UI_CHECKBOX_PREFERENCE, /* default */false)) {
        inflater.inflate(R.menu.options_menu_tlh, menu);
      } else {
        inflater.inflate(R.menu.options_menu, menu);
      }

      if (isHoneycombOrAbove()) {
        /* TUTORIAL
        // Note: Request translation has been removed from the menu. It is now accessed indirectly through the G+ button.
        if (KlingonAssistant.INCLUDE_TUTORIAL) {
          if (isJellyBeanOrAbove()) {
            // The Google Play Services version we are using does not work in Froyo and below.
            // Furthermore, the TTS services we use require Jelly Bean.
            MenuItem requestTranslationItem = (MenuItem) menu.findItem(R.id.request_translation);
            MenuItemCompat.setVisible(requestTranslationItem, true);
          }
        }
        */

        // Note: This is commented out because the way that we are implementing the search button
        // is incompatible with the appcompat search view.
        // SearchManager searchManager = (SearchManager) getSystemService(Context.SEARCH_SERVICE);
        // SearchView searchView = (SearchView) MenuItemCompat.getActionView(menu.findItem(R.id.search));
        // searchView.setSearchableInfo(searchManager.getSearchableInfo(getComponentName()));
        // searchView.setIconifiedByDefault(false);
      }

      return true;
    }

    public static boolean isHoneycombOrAbove() {
      // API 11+.
      return Build.VERSION.SDK_INT >= Build.VERSION_CODES.HONEYCOMB;
    }

    public static boolean isJellyBeanOrAbove() {
      // API 16+.
      return Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN;
    }

    // Set the content view for the menu drawer.
    protected void setDrawerContentView(int layoutResId) {
        mDrawer.setContentView(layoutResId);
    }

    protected void onSlideMenuItemClicked(int position, SlideMenuItem item) {
        mDrawer.closeMenu();

        switch (item.getItemId()) {
        case R.id.pronunciation:
          // Show "Pronunciation" screen.
          displayHelp(QUERY_FOR_PRONUNCIATION);
          break;
        case R.id.prefixes:
          // Show "Prefixes" screen.
          displayHelp(QUERY_FOR_PREFIXES);
          break;
        case R.id.prefix_charts:
          // Show "Prefix chart" screen.
          displayPrefixChart();
          break;
        case R.id.noun_suffixes:
          // Show "Noun Suffixes" screen.
          displayHelp(QUERY_FOR_NOUN_SUFFIXES);
          break;
        case R.id.verb_suffixes:
          // Show "Verb Suffixes" screen.
          displayHelp(QUERY_FOR_VERB_SUFFIXES);
          break;

        // Handle media.
        case R.id.media_1:
          launchYouTubePlaylist(getBaseContext().getResources().getString(R.string.media_1_list_id));
          break;
        case R.id.media_2:
          launchYouTubePlaylist(getBaseContext().getResources().getString(R.string.media_2_list_id));
          break;
        case R.id.media_3:
          launchYouTubePlaylist(getBaseContext().getResources().getString(R.string.media_3_list_id));
          break;
        case R.id.media_4:
          launchYouTubePlaylist(getBaseContext().getResources().getString(R.string.media_4_list_id));
          break;
        case R.id.media_5:
          launchYouTubePlaylist(getBaseContext().getResources().getString(R.string.media_5_list_id));
          break;
        case R.id.media_6:
          launchYouTubePlaylist(getBaseContext().getResources().getString(R.string.media_6_list_id));
          break;

        // Handle social networks.
        /*
        case R.id.gplus:
          // Launch Google+ Klingon speakers community.
          launchExternal("https://plus.google.com/communities/108380135139365833546");
          break;

        case R.id.facebook:
          // Launch Facebook "Learn Klingon" group.
          launchFacebook("LearnKlingon");
          break;

        case R.id.kag:
          // Launch KAG Communications.
          launchExternal("http://www.kag.org/groups/hol-ampas/forum/");
          break;

        case R.id.kidc:
          // Launch KIDC's Klingon Imperial Forums.
          launchExternal("http://www.klingon.org/smboard/index.php?board=6.0");
          break;
        */

        // Handle classes of phrases.
        case R.id.empire_union_day:
          displaySearchResults(QUERY_FOR_EMPIRE_UNION_DAY);
          break;
          /*
           * case R.id.idioms: displaySearchResults(QUERY_FOR_IDIOMS); return true;
           */
        case R.id.curse_warfare:
          displaySearchResults(QUERY_FOR_CURSE_WARFARE);
          break;
        case R.id.nentay:
          displaySearchResults(QUERY_FOR_NENTAY);
          break;
          /*
           * case R.id.proverbs: displaySearchResults(QUERY_FOR_PROVERBS); return true;
           */
        case R.id.military_celebration:
          displaySearchResults(QUERY_FOR_QI_LOP);
          break;
        case R.id.rejection:
          displaySearchResults(QUERY_FOR_REJECTION);
          break;
        case R.id.replacement_proverbs:
          displaySearchResults(QUERY_FOR_REPLACEMENT_PROVERBS);
          break;
        case R.id.secrecy_proverbs:
          displaySearchResults(QUERY_FOR_SECRECY_PROVERBS);
          break;
        case R.id.toasts:
          displaySearchResults(QUERY_FOR_TOASTS);
          break;
        case R.id.lyrics:
          displaySearchResults(QUERY_FOR_LYRICS);
          break;
        case R.id.beginners_conversation:
          displaySearchResults(QUERY_FOR_BEGINNERS_CONVERSATION);
          break;
        case R.id.jokes:
          displaySearchResults(QUERY_FOR_JOKES);
          break;

          // Lists.
          // TODO: Handle lists here.

        default:
        }

    }

    // Private method to launch a YouTube playlist.
    private void launchYouTubePlaylist(String listId) {
      Intent intent = new Intent(Intent.ACTION_VIEW);
      // Set CLEAR_TOP so that hitting the "back" key comes back here.
      intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
      intent.setData(Uri.parse("http://www.youtube.com/playlist?list=" + listId));
      startActivity(intent);
    }

    // Private method to launch an external app or web site.
    private void launchExternal(String externalUrl) {
      Intent intent = new Intent(Intent.ACTION_VIEW);
      // Set NEW_TASK so the external app or web site is independent.
      intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
      intent.setData(Uri.parse(externalUrl));
      startActivity(intent);
    }

    // Private method to request a translation.
    private void requestTranslation() {
      /* TUTORIAL
      if (KlingonAssistant.INCLUDE_TUTORIAL) {
        // See: https://developers.google.com/+/mobile/android/share/prefill
        // TODO: Ideally, this should post to the "Klingon language" community under the "Requests for
        // translation" category.
        ArrayList<Person> recipients = new ArrayList<Person>();
        recipients.add(PlusShare.createPerson("+KlingonTeacher","KlingonTeacher"));
        recipients.add(PlusShare.createPerson("110116202842822234244","De'vID"));

        try {
          Intent requestTranslationIntent = new PlusShare.Builder(this)
                                                         .setType("text/plain")
                                                         .setText("I request a Klingon translation for:\n\n")
                                                         .setRecipients(recipients)
                                                         .getIntent();
          startActivity(requestTranslationIntent);
        } catch(Exception e) {
          // Fail gracefully if Google+ is not found.
          Toast.makeText(
                  getBaseContext(),
                  getBaseContext().getResources().getString(R.string.gplus_missing),
                  Toast.LENGTH_LONG).show();
        }
      }
      */
    }

    // Private method to launch a Facebook group.
    private void launchFacebook(String groupId) {
      Intent intent;
      try {
        // adb shell
        // am start -a android.intent.action.VIEW -d fb://group/LearnKlingon
        getBaseContext().getPackageManager().getPackageInfo("com.facebook.katana", 0);
        intent = new Intent(Intent.ACTION_VIEW, Uri.parse("fb://group/" + groupId));
      } catch (Exception e) {
        intent = new Intent(Intent.ACTION_VIEW, Uri.parse("https://www.facebook.com/groups/" + groupId));
      }
      // Set CLEAR_TOP so that hitting the "back" key comes back here.
      intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
      startActivity(intent);
    }

    // Protected method to display the "help" entries.
    protected void displayHelp(String helpQuery) {
      // Note: managedQuery is deprecated since API 11.
      Cursor cursor = managedQuery(Uri.parse(KlingonContentProvider.CONTENT_URI + "/lookup"),
              null /* all columns */, null, new String[] { helpQuery }, null);
      // Assume cursor.getCount() == 1.
      Uri uri = Uri.parse(KlingonContentProvider.CONTENT_URI + "/get_entry_by_id/" +
                          cursor.getString(KlingonContentDatabase.COLUMN_ID));

      Intent entryIntent = new Intent(this, EntryActivity.class);

      // Form the URI for the entry.
      entryIntent.setData(uri);

      startActivity(entryIntent);
      overridePendingTransition(R.anim.slide_in_right, R.anim.slide_out_left);
    }

    // Protected method to display the prefix chart.
    protected void displayPrefixChart() {
      Intent prefixChartIntent = new Intent(this, PrefixChartActivity.class);
      startActivity(prefixChartIntent);
      overridePendingTransition(R.anim.slide_in_right, R.anim.slide_out_left);
    }

    // Protected method to display search results.
    protected void displaySearchResults(String helpQuery) {
      Intent intent = new Intent(this, KlingonAssistant.class);
      intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
      intent.setAction(Intent.ACTION_SEARCH);
      intent.putExtra(SearchManager.QUERY, helpQuery);

      startActivity(intent);
      overridePendingTransition(R.anim.slide_in_right, R.anim.slide_out_left);
    }

    private AdapterView.OnItemClickListener mItemClickListener = new AdapterView.OnItemClickListener() {
        @Override
        public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
            mActivePosition = position;
            mDrawer.setActiveView(view, position);
            mAdapter.setActivePosition(position);
            onSlideMenuItemClicked(position, (SlideMenuItem) mAdapter.getItem(position));
        }
    };

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        outState.putInt(STATE_ACTIVE_POSITION, mActivePosition);
    }

    @Override
    public void onActiveViewChanged(View v) {
        mDrawer.setActiveView(v, mActivePosition);
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
      switch (item.getItemId()) {
      case R.id.search:
        onSearchRequested();
        return true;
      case android.R.id.home:
        mDrawer.toggleMenu();
        break;
      case R.id.social_network:
        SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());
        if (sharedPrefs.getString(Preferences.KEY_SOCIAL_NETWORK_LIST_PREFERENCE, /* default */"gplus").equals("gplus")) {
          // Launch Google+ Klingon speakers community.
          launchExternal("https://plus.google.com/communities/108380135139365833546");
        } else {
          // Launch Facebook "Learn Klingon" group.
          launchFacebook("LearnKlingon");
        }
        break;
      /* TUTORIAL */
      case R.id.request_translation:
        requestTranslation();
        break;
      case R.id.float_mode:
        // Minimize the app and cause it to "float".
        Log.d(TAG, "Show floating window.");
        StandOutWindow.show(this, FloatingWindow.class, StandOutWindow.DEFAULT_ID);

        // Broadcast the kill order to finish all non-floating activities.
        // Work around race condition.
        Log.d(TAG, "Broadcast kill order to non-floating window.");
        final Intent intent = new Intent(ACTION_KILL);
        intent.setType(KILL_TYPE);
        Handler killNonFloatingWindowHandler = new Handler();
        Runnable killNonFloatingWindowRunnable = new Runnable() {
            public void run() {
                sendBroadcast(intent);
            }
        };
        killNonFloatingWindowHandler.postDelayed(killNonFloatingWindowRunnable, 100);  // 100 ms

        return true;
      case R.id.about:
        // Show "About" screen.
        displayHelp(QUERY_FOR_ABOUT);
        return true;
      case R.id.preferences:
        // Show "Preferences" screen.
        startActivity(new Intent(this, Preferences.class));
        overridePendingTransition(R.anim.slide_in_right, R.anim.slide_out_left);
        return true;
      default:
      }

      return super.onOptionsItemSelected(item);
    }

    // Collapse slide-out menu if "Back" key is pressed and it's open.
    @Override
    public void onBackPressed() {
        final int drawerState = mDrawer.getDrawerState();
        if (drawerState == MenuDrawer.STATE_OPEN || drawerState == MenuDrawer.STATE_OPENING) {
            mDrawer.closeMenu();
            return;
        }

        super.onBackPressed();
    }

    private final class KillReceiver extends BroadcastReceiver {
        @Override
        public void onReceive(Context context, Intent intent) {
            Log.d(TAG, "Received kill order, finishing.");
            finish();
        }
    }
}
