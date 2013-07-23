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

import android.os.Bundle;
import android.view.Gravity;
import android.widget.TextView;

public class BaseActivity extends SherlockActivity {
    private static final String TAG = "BaseActivity";

    private MenuDrawer mDrawer;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getSupportActionBar();

        mDrawer = MenuDrawer.attach(this);

        TextView menuView = new TextView(this);
        menuView.setTextColor(0xFFFFFFFF);
        menuView.setText("This is a menu.");
        menuView.setGravity(Gravity.CENTER);
        mDrawer.setMenuView(menuView);

        // The drawable that replaces the up indicator in the action bar
        mDrawer.setSlideDrawable(R.drawable.ic_drawer);
        // Whether the previous drawable should be shown
        mDrawer.setDrawerIndicatorEnabled(true);
    }

    // Set the content view for the menu drawer.
    protected void setDrawerContentView(int layoutResId) {
        mDrawer.setContentView(layoutResId);
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
}
