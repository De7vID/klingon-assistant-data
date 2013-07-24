package org.tlhInganHol.android.klingonassistant;

public class SlideMenuItem {

    int mTitle;
    int mResId;
    int mIconRes;

    SlideMenuItem(int title, int resId, int iconRes) {
        mTitle = title;
        mResId = resId;
        mIconRes = iconRes;
    }

    int getItemId() {
        return mResId;
    }
}
