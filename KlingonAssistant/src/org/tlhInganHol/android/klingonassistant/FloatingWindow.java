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
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.animation.Animation;
import android.view.animation.AnimationUtils;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.widget.Toast;

/**
 * This implementation provides multiple windows. You may extend this class or use it as a reference
 * for a basic foundation for your own windows.
 * 
 * <p>
 * Functionality includes system window decorators, moveable, resizeable, hideable, closeable, and
 * bring-to-frontable.
 * 
 * <p>
 * The persistent notification creates new windows. The hidden notifications restores previously
 * hidden windows.
 * 
 * @author Mark Wei <markwei@gmail.com>
 * 
 */
public class FloatingWindow extends StandOutWindow {

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
    // create a new layout from body.xml
    LayoutInflater inflater = (LayoutInflater) getSystemService(LAYOUT_INFLATER_SERVICE);
    View view = inflater.inflate(R.layout.floating, frame, true);

    TextView idText = (TextView) view.findViewById(R.id.id1);
    idText.setText(String.valueOf(id));
  }

  // every window is initially same size
  @Override
  public StandOutLayoutParams getParams(int id, Window window) {
    return new StandOutLayoutParams(id, 400, 300, StandOutLayoutParams.CENTER,
            StandOutLayoutParams.CENTER, 200, 100);
  }

  // we want the system window decorations, we want to drag the body, we want
  // the ability to hide windows, and we want to tap the window to bring to
  // front
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
}
