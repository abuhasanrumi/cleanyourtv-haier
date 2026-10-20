package com.gathin.tvhome;

import org.junit.Test;
import static org.junit.Assert.assertEquals;

public class SleepTest {
    @Test public void stepsGoOffThirtySixtyNinetyHundredTwentyOff() {
        assertEquals(30, Sleep.next(0));
        assertEquals(60, Sleep.next(30));
        assertEquals(90, Sleep.next(60));
        assertEquals(120, Sleep.next(90));
        assertEquals(0, Sleep.next(120));
    }

    @Test public void aRunningTimerStepsToTheNextStepAboveWhatIsLeft() {
        assertEquals(60, Sleep.next(42));
        assertEquals(30, Sleep.next(1));
        assertEquals(120, Sleep.next(119));
    }
}
