package org.tlhInganHol.android.klingonassistant;

import android.graphics.Paint;
import android.graphics.Typeface;
import android.text.TextPaint;
import android.text.style.TypefaceSpan;

public class KlingonTypefaceSpan extends TypefaceSpan {
  private final Typeface mTypeface;

  public KlingonTypefaceSpan(String family, Typeface typeface) {
    super(family);
    mTypeface = typeface;
  }

  @Override
  public void updateMeasureState(TextPaint tp) {
    tp.setTypeface(mTypeface);
    tp.setFlags(tp.getFlags() | Paint.SUBPIXEL_TEXT_FLAG);
  }

  @Override
  public void updateDrawState(TextPaint tp) {
    tp.setTypeface(mTypeface);
    tp.setFlags(tp.getFlags() | Paint.SUBPIXEL_TEXT_FLAG);
  }
}
