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
import android.content.res.Configuration;
import android.database.Cursor;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.support.constraint.ConstraintLayout;
// import android.support.design.widget.FloatingActionButton;
import android.support.design.widget.NavigationView;
// import android.support.design.widget.Snackbar;
import android.support.v4.view.GravityCompat;
import android.support.v4.widget.DrawerLayout;
import android.support.v7.app.ActionBarDrawerToggle;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.text.Spannable;
import android.text.SpannableString;
import android.text.style.RelativeSizeSpan;
import android.text.style.TypefaceSpan;
import android.view.LayoutInflater;
import android.view.Menu;
import android.view.MenuInflater;
import android.view.MenuItem;
import android.view.SubMenu;
import android.view.View;
import android.widget.TextView;
import java.util.Locale;

public class BaseActivity extends AppCompatActivity
    implements NavigationView.OnNavigationItemSelectedListener {
  private static final String TAG = "BaseActivity";

  // This must uniquely identify the {boQwI'} entry.
  protected static final String QUERY_FOR_ABOUT = "boQwI':n";

  private static final String STATE_ACTIVE_POSITION =
      "org.tlhInganHol.android.klingonassistant_v2.activePosition";

  // Help pages.
  private static final String QUERY_FOR_PRONUNCIATION = "QIch:n";
  private static final String QUERY_FOR_PREFIXES = "moHaq:n";
  private static final String QUERY_FOR_NOUN_SUFFIXES = "DIp:n";
  private static final String QUERY_FOR_VERB_SUFFIXES = "wot:n";

  // Classes of phrases.
  private static final String QUERY_FOR_EMPIRE_UNION_DAY = "*:sen:eu";
  // private static final String QUERY_FOR_IDIOMS                 = "*:sen:idiom";
  private static final String QUERY_FOR_CURSE_WARFARE = "*:sen:mv";
  private static final String QUERY_FOR_NENTAY = "*:sen:nt";
  // private static final String QUERY_FOR_PROVERBS               = "*:sen:prov";
  private static final String QUERY_FOR_QI_LOP = "*:sen:Ql";
  private static final String QUERY_FOR_REJECTION = "*:sen:rej";
  private static final String QUERY_FOR_REPLACEMENT_PROVERBS = "*:sen:rp";
  private static final String QUERY_FOR_SECRECY_PROVERBS = "*:sen:sp";
  private static final String QUERY_FOR_TOASTS = "*:sen:toast";
  private static final String QUERY_FOR_LYRICS = "*:sen:lyr";
  private static final String QUERY_FOR_BEGINNERS_CONVERSATION = "*:sen:bc";
  private static final String QUERY_FOR_JOKES = "*:sen:joke";

  // protected SlideMenuAdapter mAdapter;
  // protected ListView mList;

  private int mActivePosition = 0;

  // Helper method to determine whether the device is (likely) a tablet in horizontal orientation.
  public boolean isHorizontalTablet() {
    Configuration config = getResources().getConfiguration();
    if (config.orientation == Configuration.ORIENTATION_LANDSCAPE
        && (config.screenLayout & Configuration.SCREENLAYOUT_SIZE_MASK)
            >= Configuration.SCREENLAYOUT_SIZE_LARGE) {
      return true;
    }
    return false;
  }

  @Override
  protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);

    // if (savedInstanceState != null) {
    //   mActivePosition = savedInstanceState.getInt(STATE_ACTIVE_POSITION);
    // }

    // Override for Klingon language.
    SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());
    if (sharedPrefs.getBoolean(
        Preferences.KEY_KLINGON_UI_CHECKBOX_PREFERENCE, /* default */ false)) {
      Configuration configuration = getBaseContext().getResources().getConfiguration();
      configuration.locale = new Locale("tlh", "CAN");
      getBaseContext()
          .getResources()
          .updateConfiguration(configuration, getBaseContext().getResources().getDisplayMetrics());
    }

    setContentView(R.layout.activity_base);
    Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
    setSupportActionBar(toolbar);
    getSupportActionBar().setDisplayHomeAsUpEnabled(true);
    // getSupportActionBar().setIcon(R.drawable.ic_ka);

    // Display the title in Klingon font.
    SpannableString klingonAppName =
        new SpannableString(
            KlingonContentProvider.convertStringToKlingonFont(
                getBaseContext().getResources().getString(R.string.app_name)));
    Typeface klingonTypeface = KlingonAssistant.getKlingonFontTypeface(getBaseContext());
    klingonAppName.setSpan(
        new KlingonTypefaceSpan("", klingonTypeface),
        0,
        klingonAppName.length(),
        Spannable.SPAN_EXCLUSIVE_EXCLUSIVE);
    getSupportActionBar().setTitle(klingonAppName);

    // FloatingActionButton fab = (FloatingActionButton) findViewById(R.id.fab);
    // fab.setOnClickListener(
    //     new View.OnClickListener() {
    //       @Override
    //       public void onClick(View view) {
    //         // Snackbar.make(view, "Replace with your own action", Snackbar.LENGTH_LONG)
    //         //     .setAction("Action", null)
    //         //     .show();
    //         // displaySearchResults("jagh qIp SuvwI':sen@@jagh:n, qIp:v, SuvwI':n");
    //         onSearchRequested();
    //       }
    //     });

    DrawerLayout drawer = (DrawerLayout) findViewById(R.id.drawer_layout);
    ActionBarDrawerToggle toggle =
        new ActionBarDrawerToggle(
            this,
            drawer,
            toolbar,
            R.string.navigation_drawer_open,
            R.string.navigation_drawer_close);
    drawer.setDrawerListener(toggle);
    toggle.syncState();

    NavigationView navigationView = (NavigationView) findViewById(R.id.nav_view);
    navigationView.setNavigationItemSelectedListener(this);
    Menu navMenu = navigationView.getMenu();
    for (int i = 0; i < navMenu.size(); i++) {
      MenuItem menuItem = navMenu.getItem(i);
      SubMenu subMenu = menuItem.getSubMenu();
      if (subMenu != null && subMenu.size() > 0) {
        for (int j = 0; j < subMenu.size(); j++) {
          MenuItem subMenuItem = subMenu.getItem(j);
          applyTypefaceToMenuItem(subMenuItem, false);
        }
      }
      applyTypefaceToMenuItem(menuItem, true);
    }

    View headerView = navigationView.getHeaderView(0);
    TextView appNameView = (TextView) headerView.findViewById(R.id.app_name_view);
    TextView versionView = (TextView) headerView.findViewById(R.id.version_view);
    appNameView.setText(klingonAppName);
    versionView.setText("v" + KlingonContentDatabase.getDatabaseVersion() + " (alpha)");

    // If the device is in landscape orientation and the screen size is large (or bigger), then
    // make the slide-out menu static. Otherwise, hide it by default.
    // MenuDrawer.Type drawerType = MenuDrawer.Type.BEHIND;
    // if (isHorizontalTablet()) {
    //   drawerType = MenuDrawer.Type.STATIC;
    // }

    // Activate type-to-search for local search. Typing will automatically
    // start a search of the database.
    setDefaultKeyMode(DEFAULT_KEYS_SEARCH_LOCAL);
  }

  private void applyTypefaceToMenuItem(MenuItem menuItem, boolean enlarge) {
    final SharedPreferences sharedPrefs =
        PreferenceManager.getDefaultSharedPreferences(getBaseContext());
    boolean useKlingonUI =
        sharedPrefs.getBoolean(Preferences.KEY_KLINGON_UI_CHECKBOX_PREFERENCE, /* default */ false);
    boolean useKlingonFont =
        sharedPrefs.getBoolean(
            Preferences.KEY_KLINGON_FONT_CHECKBOX_PREFERENCE, /* default */ false);
    Typeface klingonTypeface = KlingonAssistant.getKlingonFontTypeface(getBaseContext());
    String title = menuItem.getTitle().toString();
    SpannableString spannableString;
    if (useKlingonFont) {
      spannableString =
          new SpannableString(KlingonContentProvider.convertStringToKlingonFont(title));
      spannableString.setSpan(
          new KlingonTypefaceSpan("", klingonTypeface),
          0,
          spannableString.length(),
          Spannable.SPAN_EXCLUSIVE_EXCLUSIVE);
    } else {
      spannableString = new SpannableString(title);
      if (useKlingonUI) {
        // If the UI is in Klingon (Latin), use a serif typeface.
        spannableString.setSpan(
            new TypefaceSpan("serif"),
            0,
            spannableString.length(),
            Spannable.SPAN_EXCLUSIVE_EXCLUSIVE);
      }
    }
    if (enlarge) {
      spannableString.setSpan(
          new RelativeSizeSpan(1.2f),
          0,
          spannableString.length(),
          Spannable.SPAN_EXCLUSIVE_EXCLUSIVE);
    }
    menuItem.setTitle(spannableString);
  }

  @Override
  public boolean onCreateOptionsMenu(Menu menu) {
    MenuInflater inflater = getMenuInflater();
    inflater.inflate(R.menu.options_menu, menu);
    for (int i = 0; i < menu.size(); i++) {
      MenuItem menuItem = menu.getItem(i);
      applyTypefaceToMenuItem(menuItem, false);
    }
    return true;
  }

  // Set the content view for the menu drawer.
  protected void setDrawerContentView(int layoutResId) {
    ConstraintLayout constraintLayout = (ConstraintLayout) findViewById(R.id.drawer_content);
    constraintLayout.removeAllViews();
    LayoutInflater.from(getBaseContext()).inflate(layoutResId, constraintLayout, true);
  }

  @SuppressWarnings("StatementWithEmptyBody")
  @Override
  public boolean onNavigationItemSelected(MenuItem item) {
    // Handle navigation view item clicks here.

    switch (item.getItemId()) {
      case R.id.pronunciation:
        // Show "Pronunciation" screen.
        displayHelp(QUERY_FOR_PRONUNCIATION);
        break;
      case R.id.prefixes:
        // Show "Prefixes" screen.
        displayHelp(QUERY_FOR_PREFIXES);
        break;
      case R.id.prefix_chart:
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
      case R.id.sources:
        // Show "Sources" screen.
        displaySources();
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

        // Handle KLI activities here.
      case R.id.kli_lessons:
        launchExternal("http://www.kli.org/learn-klingon-online/");
        break;

      case R.id.kli_questions:
        launchExternal("http://www.kli.org/questions/categories/");
        break;

        /*
        case R.id.kli_discord:
          launchExternal("https://discordapp.com/channels/235416538927202304/");
          break;
          */

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

    DrawerLayout drawer = (DrawerLayout) findViewById(R.id.drawer_layout);
    drawer.closeDrawer(GravityCompat.START);
    return true;
  }

  // Private method to launch a YouTube playlist.
  private void launchYouTubePlaylist(String listId) {
    Intent intent = new Intent(Intent.ACTION_VIEW);
    // Set CLEAR_TOP so that hitting the "back" key comes back here.
    intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
    intent.setData(Uri.parse("http://www.youtube.com/playlist?list=" + listId));
    startActivity(intent);
  }

  // Method to launch an external app or web site.
  protected void launchExternal(String externalUrl) {
    Intent intent = new Intent(Intent.ACTION_VIEW);
    // Set NEW_TASK so the external app or web site is independent.
    intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
    intent.setData(Uri.parse(externalUrl));
    startActivity(intent);
  }

  // Private method to request a translation.
  private void requestTranslation() {
    /* TUTORIAL
    //  // See: https://developers.google.com/+/mobile/android/share/prefill
    //  // TODO: Ideally, this should post to the "Klingon language" community under the "Requests for
    //  // translation" category.
    //  ArrayList<Person> recipients = new ArrayList<Person>();
    //  recipients.add(PlusShare.createPerson("+KlingonTeacher","KlingonTeacher"));
    //  recipients.add(PlusShare.createPerson("110116202842822234244","De'vID"));

    //  try {
    //    Intent requestTranslationIntent = new PlusShare.Builder(this)
    //                                                   .setType("text/plain")
    //                                                   .setText("I request a Klingon translation for:\n\n")
    //                                                   .setRecipients(recipients)
    //                                                   .getIntent();
    //    startActivity(requestTranslationIntent);
    //  } catch(Exception e) {
    //    // Fail gracefully if Google+ is not found.
    //    Toast.makeText(
    //            getBaseContext(),
    //            getBaseContext().getResources().getString(R.string.gplus_missing),
    //            Toast.LENGTH_LONG).show();
    //  }
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
      intent =
          new Intent(Intent.ACTION_VIEW, Uri.parse("https://www.facebook.com/groups/" + groupId));
    }
    // Set CLEAR_TOP so that hitting the "back" key comes back here.
    intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
    startActivity(intent);
  }

  // Protected method to display the "help" entries.
  protected void displayHelp(String helpQuery) {
    // Note: managedQuery is deprecated since API 11.
    Cursor cursor =
        managedQuery(
            Uri.parse(KlingonContentProvider.CONTENT_URI + "/lookup"),
            null /* all columns */,
            null,
            new String[] {helpQuery},
            null);
    // Assume cursor.getCount() == 1.
    Uri uri =
        Uri.parse(
            KlingonContentProvider.CONTENT_URI
                + "/get_entry_by_id/"
                + cursor.getString(KlingonContentDatabase.COLUMN_ID));

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

  // Protected method to display the sources page.
  protected void displaySources() {
    Intent sourcesIntent = new Intent(this, SourcesActivity.class);
    startActivity(sourcesIntent);
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

  // private AdapterView.OnItemClickListener mItemClickListener =
  //     new AdapterView.OnItemClickListener() {
  //       @Override
  //       public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
  //         mActivePosition = position;
  //         mDrawer.setActiveView(view, position);
  //         mAdapter.setActivePosition(position);
  //         onSlideMenuItemClicked(position, (SlideMenuItem) mAdapter.getItem(position));
  //       }
  //     };

  @Override
  protected void onSaveInstanceState(Bundle outState) {
    super.onSaveInstanceState(outState);
    outState.putInt(STATE_ACTIVE_POSITION, mActivePosition);
  }

  // @Override
  // public void onActiveViewChanged(View v) {
  //   mDrawer.setActiveView(v, mActivePosition);
  // }

  @Override
  public boolean onOptionsItemSelected(MenuItem item) {
    // noinspection SimplifiableIfStatement
    switch (item.getItemId()) {
      case R.id.search:
        onSearchRequested();
        return true;
      case android.R.id.home:
        // TODO: Toggle menu.
        // mDrawer.toggleMenu();
        break;
        /*
        case R.id.social_network:
          SharedPreferences sharedPrefs =
              PreferenceManager.getDefaultSharedPreferences(getBaseContext());
          if (sharedPrefs
              .getString(Preferences.KEY_SOCIAL_NETWORK_LIST_PREFERENCE, "gplus")
              .equals("gplus")) {
            // Launch Google+ Klingon speakers community.
            launchExternal("https://plus.google.com/communities/108380135139365833546");
          } else {
            // Launch Facebook "Learn Klingon" group.
            launchFacebook("LearnKlingon");
          }
          break;
          */
        /* TUTORIAL */
        /*
        case R.id.request_translation:
          requestTranslation();
          break;
          */
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
    DrawerLayout drawer = (DrawerLayout) findViewById(R.id.drawer_layout);
    if (drawer.isDrawerOpen(GravityCompat.START)) {
      drawer.closeDrawer(GravityCompat.START);
    } else {
      super.onBackPressed();
    }
  }
}
