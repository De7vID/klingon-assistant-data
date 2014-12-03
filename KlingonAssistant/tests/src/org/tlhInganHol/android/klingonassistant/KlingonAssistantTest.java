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

import android.app.Activity;
import android.test.ActivityInstrumentationTestCase2;
import android.widget.Spinner;

/**
 * This is a simple framework for a test of an Application.  See
 * {@link android.test.ApplicationTestCase ApplicationTestCase} for more information on
 * how to write and extend Application tests.
 *
 * <p>To run this test, you can type:
 * adb shell am instrument -w \
 * -e class org.tlhInganHol.android.klingonassistant.KlingonAssistantTest \
 * org.tlhInganHol.android.klingonassistant.tests/android.test.InstrumentationTestRunner
 *
 * <p>Individual tests are defined as any method beginning with 'test'.
 *
 * <p>ActivityInstrumentationTestCase2 allows these tests to run alongside a running
 * copy of the application under inspection. Calling getActivity() will return a
 * handle to this activity (launching it if needed).
 */
public class KlingonAssistantTest extends ActivityInstrumentationTestCase2<KlingonAssistant> {

    public KlingonAssistantTest() {
        super("org.tlhInganHol.android.klingonassistant", KlingonAssistant.class);
    }

    /**
     * Test to make sure that spinner values are persisted across activity restarts.
     *
     * <p>Launches the main activity, and closes it.
     */
    public void testLaunch() {
        // Launch the activity
        Activity activity = getActivity();

        // Close the activity
        activity.finish();
    }
}
