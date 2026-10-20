package com.gathin.tvhome;

import org.junit.Test;
import static org.junit.Assert.assertEquals;

public class DayPhaseTest {
    private static int at(String time) {
        return DayPhase.frame(DayPhase.parse(time, -1), DayPhase.DEFAULT_SUNRISE, DayPhase.DEFAULT_SUNSET);
    }

    @Test public void defaultDayRunsThroughEveryFrame() {
        assertEquals(0, at("00:00"));
        assertEquals(0, at("04:29"));
        assertEquals(1, at("04:30"));
        assertEquals(3, at("05:59"));
        assertEquals(4, at("06:00"));   // sunrise
        assertEquals(7, at("07:30"));
        assertEquals(7, at("07:59"));
        assertEquals(8, at("08:00"));
        assertEquals(8, at("16:29"));
        assertEquals(9, at("16:30"));
        assertEquals(12, at("18:00"));  // sunset
        assertEquals(15, at("19:59"));
        assertEquals(0, at("20:00"));
        assertEquals(0, at("23:59"));
    }

    @Test public void themeTimesMoveTheFrames() {
        int rise = DayPhase.parse("05:15", -1), set = DayPhase.parse("17:40", -1);
        assertEquals(4, DayPhase.frame(rise, rise, set));
        assertEquals(12, DayPhase.frame(set + 10, rise, set));
        assertEquals(8, DayPhase.frame(12 * 60, rise, set));
    }

    @Test public void nonsenseTimesFallBackToSixAndSix() {
        assertEquals(12, DayPhase.frame(18 * 60, 20 * 60, 6 * 60));
        assertEquals(-1, DayPhase.parse("25:00", -1));
        assertEquals(-1, DayPhase.parse("6pm", -1));
        assertEquals(-1, DayPhase.parse("", -1));
        assertEquals(-1, DayPhase.parse(null, -1));
        assertEquals(6 * 60 + 5, DayPhase.parse(" 6:05 ", -1));
    }

    @Test public void minutesWrapAroundTheDay() {
        assertEquals(0, DayPhase.frame(1440 + 60, DayPhase.DEFAULT_SUNRISE, DayPhase.DEFAULT_SUNSET));
        assertEquals(0, DayPhase.frame(-30, DayPhase.DEFAULT_SUNRISE, DayPhase.DEFAULT_SUNSET));
    }

    @Test public void fileNamesHaveTwoDigits() {
        assertEquals("wallpaper-00.jpg", DayPhase.fileName(0));
        assertEquals("wallpaper-15.jpg", DayPhase.fileName(15));
    }
}
