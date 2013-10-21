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

import java.util.ArrayList;
import java.util.List;

import wei.mark.standout.StandOutWindow;
import wei.mark.standout.constants.StandOutFlags;
import wei.mark.standout.ui.Window;
import android.content.Context;
import android.content.Intent;
import android.database.Cursor;
import android.graphics.Typeface;
import android.net.Uri;
import android.support.v4.content.CursorLoader;
import android.text.Editable;
import android.text.Html;
import android.text.TextWatcher;
import android.util.Log;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.TwoLineListItem;

public class FloatingWindow extends StandOutWindow {
  private static final String TAG = "FloatingWindow";

  // The two main views in float mode.
  private EditText            mEditText;
  private ListView            mListView;

  @Override
  public String getAppName() {
    return getResources().getString(R.string.app_name);
  }

  @Override
  public int getAppIcon() {
    return R.drawable.ic_ka;
  }

  @Override
  public String getTitle(int id) {
    return getAppName();
  }

  @Override
  public void createAndAttachView(int id, FrameLayout frame) {
    LayoutInflater inflater = (LayoutInflater) getSystemService(LAYOUT_INFLATER_SERVICE);
    View view = inflater.inflate(R.layout.floating, frame, true);

    mEditText = (EditText) view.findViewById(R.id.float_edit);
    mListView = (ListView) view.findViewById(R.id.float_list);

    mEditText.addTextChangedListener((TextWatcher) new SearchTextWatcher());
  }

  @Override
  public StandOutLayoutParams getParams(int id, Window window) {
    return new StandOutLayoutParams(id, 400, 300, StandOutLayoutParams.CENTER,
            StandOutLayoutParams.CENTER, 200, 100);
  }

  @Override
  public int getFlags(int id) {
    return StandOutFlags.FLAG_DECORATION_SYSTEM | StandOutFlags.FLAG_DECORATION_CLOSE_DISABLE
            | StandOutFlags.FLAG_DECORATION_MAXIMIZE_DISABLE | StandOutFlags.FLAG_BODY_MOVE_ENABLE
            | StandOutFlags.FLAG_WINDOW_BRING_TO_FRONT_ON_TAP
            | StandOutFlags.FLAG_WINDOW_EDGE_LIMITS_ENABLE;
  }

  @Override
  public String getPersistentNotificationTitle(int id) {
    return getAppName();
  }

  @Override
  public String getPersistentNotificationMessage(int id) {
    return getResources().getString(R.string.float_mode_status);
  }

  @Override
  public List<DropDownListItem> getDropDownItems(int id) {
    List<DropDownListItem> items = new ArrayList<DropDownListItem>();
    items.add(new DropDownListItem(0, "Restore", new Runnable() {

      @Override
      public void run() {
        Intent intent = new Intent(FloatingWindow.this, KlingonAssistant.class);
        // This needs to be set since this is called outside of an activity.
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        intent.setAction(Intent.ACTION_MAIN);
        startActivity(intent);
      }
    }));
    return items;
  }

  // Helper class to watch the search text.
  class SearchTextWatcher implements TextWatcher {
    @Override
    public void onTextChanged(CharSequence s, int start, int before, int count) {
    }

    @Override
    public void beforeTextChanged(CharSequence s, int start, int count, int after) {
    }

    @Override
    public void afterTextChanged(Editable s) {
      String query = s.toString();
      if (query.equals("")) {
        mListView.setAdapter(null);
        return;
      }

      CursorLoader cursorLoader = new CursorLoader(getBaseContext(),
            Uri.parse(KlingonContentProvider.CONTENT_URI + "/lookup"),
            null /* all columns */, null, new String[] { query }, null);
      Cursor cursor = cursorLoader.loadInBackground();

      KlingonContentProvider.Entry queryEntry = new KlingonContentProvider.Entry(query, getBaseContext());
      String entryNameWithPoS = queryEntry.getEntryName() + queryEntry.getBracketedPartOfSpeech(/* isHtml */true);
      Log.d(TAG, "entryNameWithPoS: " + entryNameWithPoS);
      Log.d(TAG, "cursor.getCount(): " + cursor.getCount());

      EntryAdapter entryAdapter = new EntryAdapter(cursor);
      mListView.setAdapter(entryAdapter);
      mListView.setOnItemClickListener(entryAdapter);
    }
  }

  // Launch an entry activity with the entry's info.
  private void launchEntry(String entryId) {
    if (entryId == null) {
      return;
    }

    Intent entryIntent = new Intent(this, EntryActivity.class);

    // Form the URI for the entry.
    Uri uri = Uri.parse(KlingonContentProvider.CONTENT_URI + "/get_entry_by_id/" + entryId);
    entryIntent.setData(uri);

    // This needs to be set since this is called outside of an activity.
    entryIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
    startActivity(entryIntent);
  }

  // TODO: This entire class is copied from KlingonAssistant. Merge the copies.
  class EntryAdapter extends BaseAdapter implements AdapterView.OnItemClickListener {

    private final Cursor         mCursor;
    private final LayoutInflater mInflater;

    public EntryAdapter(Cursor cursor) {
      mCursor = cursor;
      mInflater = (LayoutInflater) getSystemService(LAYOUT_INFLATER_SERVICE);
    }

    @Override
    public int getCount() {
      return mCursor.getCount();
    }

    @Override
    public Object getItem(int position) {
      return position;
    }

    @Override
    public long getItemId(int position) {
      return position;
    }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
      TwoLineListItem view = (convertView != null) ? (TwoLineListItem) convertView
              : createView(parent);
      mCursor.moveToPosition(position);
      bindView(view, mCursor);
      return view;
    }

    private TwoLineListItem createView(ViewGroup parent) {
      TwoLineListItem item = (TwoLineListItem) mInflater.inflate(
              android.R.layout.simple_list_item_2, parent, false);

      // Set single line to true if you want shorter definitions.
      item.getText2().setSingleLine(false);
      item.getText2().setEllipsize(TextUtils.TruncateAt.END);

      return item;
    }

    private void bindView(TwoLineListItem view, Cursor cursor) {
      KlingonContentProvider.Entry entry = new KlingonContentProvider.Entry(cursor,
              getBaseContext());

      // TODO(davinci): Format with colour and size.
      String indent1 = entry.isIndented() ? "&nbsp;&nbsp;&nbsp;&nbsp;" : "";
      String indent2 = entry.isIndented() ? "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" : "";

      // Use serif for the entry, so capital-I and lowercase-l are distinguishable.
      view.getText1().setTypeface(Typeface.SERIF);
      view.getText1().setText(
              Html.fromHtml(indent1 + entry.getFormattedEntryName(/* isHtml */true)));

      // Use sans serif for the definition.
      view.getText2().setTypeface(Typeface.SANS_SERIF);
      view.getText2().setText(
              Html.fromHtml(indent2 + entry.getFormattedDefinition(/* isHtml */true)));
    }

    @Override
    public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
      mCursor.moveToPosition(position);
      launchEntry(mCursor.getString(KlingonContentDatabase.COLUMN_ID));
    }
  }

}
