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

import com.actionbarsherlock.app.SherlockActivity;
import com.actionbarsherlock.view.MenuItem;

import net.simonvt.menudrawer.MenuDrawer;
import net.simonvt.menudrawer.Position;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.support.v4.app.FragmentActivity;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ListView;

import java.util.ArrayList;
import java.util.List;


public class BaseActivity extends SherlockActivity implements SlideMenuAdapter.MenuListener {
    private static final String TAG = "BaseActivity";

    private static final String STATE_ACTIVE_POSITION =
            "org.tlhInganHol.android.klingonassistant.activePosition";

    private MenuDrawer mDrawer;

    protected SlideMenuAdapter mAdapter;
    protected ListView mList;

    private int mActivePosition = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (savedInstanceState != null) {
            mActivePosition = savedInstanceState.getInt(STATE_ACTIVE_POSITION);
        }

        getSupportActionBar();

        mDrawer = MenuDrawer.attach(this, MenuDrawer.Type.BEHIND, Position.LEFT, MenuDrawer.MENU_DRAG_CONTENT);

        List<Object> items = new ArrayList<Object>();
        SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(getBaseContext());
        if (sharedPrefs.getBoolean(Preferences.KEY_KLINGON_UI_CHECKBOX_PREFERENCE, /* default */false)) {
            items.add(new SlideMenuCategory(R.string.menu_reference_tlh));
                items.add(new SlideMenuItem(R.string.menu_pronunciation_tlh, R.id.pronunciation, 0));
                items.add(new SlideMenuItem(R.string.menu_prefixes_tlh, R.id.prefixes, 0));
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
            items.add(new SlideMenuCategory(R.string.menu_social_tlh));
                items.add(new SlideMenuItem(R.string.menu_gplus_tlh, R.id.gplus, 0));
        } else {
            items.add(new SlideMenuCategory(R.string.menu_reference));
                items.add(new SlideMenuItem(R.string.menu_pronunciation, R.id.pronunciation, 0));
                items.add(new SlideMenuItem(R.string.menu_prefixes, R.id.prefixes, 0));
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
            items.add(new SlideMenuCategory(R.string.menu_social));
                items.add(new SlideMenuItem(R.string.menu_gplus, R.id.gplus, 0));
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
    }

    // Set the content view for the menu drawer.
    protected void setDrawerContentView(int layoutResId) {
        mDrawer.setContentView(layoutResId);
    }

    protected void onSlideMenuItemClicked(int position, SlideMenuItem item) {
        mDrawer.closeMenu();
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
            case android.R.id.home:
                mDrawer.toggleMenu();
                break;
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
}
