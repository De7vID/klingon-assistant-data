package org.tlhInganHol.android.klingonassistant;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Typeface;
import android.preference.PreferenceManager;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.TextView;
import java.util.List;

public class SlideMenuAdapter extends BaseAdapter {

  public interface MenuListener {

    void onActiveViewChanged(View v);
  }

  private Context mContext;

  private List<Object> mItems;

  private MenuListener mListener;

  private int mActivePosition = -1;

  public SlideMenuAdapter(Context context, List<Object> items) {
    mContext = context;
    mItems = items;
  }

  public void setListener(MenuListener listener) {
    mListener = listener;
  }

  public void setActivePosition(int activePosition) {
    mActivePosition = activePosition;
  }

  @Override
  public int getCount() {
    return mItems.size();
  }

  @Override
  public Object getItem(int position) {
    return mItems.get(position);
  }

  @Override
  public long getItemId(int position) {
    return position;
  }

  @Override
  public int getItemViewType(int position) {
    return getItem(position) instanceof SlideMenuItem ? 0 : 1;
  }

  @Override
  public int getViewTypeCount() {
    return 2;
  }

  @Override
  public boolean isEnabled(int position) {
    return getItem(position) instanceof SlideMenuItem;
  }

  @Override
  public boolean areAllItemsEnabled() {
    return false;
  }

  @Override
  public View getView(int position, View convertView, ViewGroup parent) {
    View v = convertView;
    Object item = getItem(position);

    SharedPreferences sharedPrefs = PreferenceManager.getDefaultSharedPreferences(mContext);
    boolean useKlingonFont =
        sharedPrefs.getBoolean(
            Preferences.KEY_KLINGON_FONT_CHECKBOX_PREFERENCE, /* default */ false);
    Typeface klingonTypeface = KlingonAssistant.getKlingonFontTypeface(mContext);

    if (item instanceof SlideMenuCategory) {
      if (v == null) {
        v = LayoutInflater.from(mContext).inflate(R.layout.menu_row_category, parent, false);
      }

      TextView tv = (TextView) v;
      String title = tv.getContext().getResources().getString(((SlideMenuCategory) item).mTitle);
      if (useKlingonFont) {
        tv.setText(KlingonContentProvider.convertStringToKlingonFont(title));
        ((TextView) v).setTypeface(klingonTypeface);
      } else {
        tv.setText(title);
      }

    } else {
      if (v == null) {
        v = LayoutInflater.from(mContext).inflate(R.layout.menu_row_item, parent, false);
      }

      TextView tv = (TextView) v;
      String text = tv.getContext().getResources().getString(((SlideMenuItem) item).mTitle);
      if (useKlingonFont) {
        tv.setText(KlingonContentProvider.convertStringToKlingonFont(text));
        tv.setTypeface(klingonTypeface);
      } else {
        tv.setText(text);
      }
      tv.setCompoundDrawablesWithIntrinsicBounds(((SlideMenuItem) item).mIconRes, 0, 0, 0);
    }

    v.setTag(R.id.mdActiveViewPosition, position);

    if (position == mActivePosition) {
      mListener.onActiveViewChanged(v);
    }

    return v;
  }
}
