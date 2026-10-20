package com.gathin.tvhome;

/**
 * Which of a theme's time-of-day wallpapers to show: wallpaper-00.jpg to wallpaper-15.jpg next to
 * wallpaper.jpg. Like a solar dynamic desktop, most frames sit around sunrise and sunset, where the sky
 * changes fastest, half an hour apart:
 *
 *   00 night, until 90 minutes before sunrise
 *   01 to 07 from 90 minutes before sunrise, one every 30 minutes (04 is sunrise)
 *   08 day, from two hours after sunrise until 90 minutes before sunset
 *   09 to 15 from 90 minutes before sunset, one every 30 minutes (12 is sunset), then 00 again
 *
 * A theme sets its town's times ("sunrise": "06:10", "sunset": "17:45"); without them, 06:00 and 18:00.
 * Pure maths on minutes since midnight, so it can be tested on the JVM.
 */
final class DayPhase {
    static final int FRAMES = 16;
    static final int DEFAULT_SUNRISE = 6 * 60;
    static final int DEFAULT_SUNSET = 18 * 60;
    private static final int STEP = 30;

    private DayPhase() { }

    /** The frame, 0 to 15, at {@code minute}; times less than six hours apart fall back to 06:00 and 18:00. */
    static int frame(int minute, int sunrise, int sunset) {
        if (sunrise < 0 || sunset > 1439 || sunset - sunrise < 6 * 60) {
            sunrise = DEFAULT_SUNRISE;
            sunset = DEFAULT_SUNSET;
        }
        int m = ((minute % 1440) + 1440) % 1440;
        int fromRise = m - (sunrise - 3 * STEP);
        if (fromRise < 0) return 0;
        if (fromRise < 8 * STEP) return 1 + fromRise / STEP;
        int fromSet = m - (sunset - 3 * STEP);
        if (fromSet < 0) return 8;
        if (fromSet < 7 * STEP) return 9 + fromSet / STEP;
        return 0;
    }

    /** The file name of frame {@code n}. */
    static String fileName(int n) {
        return String.format(java.util.Locale.ROOT, "wallpaper-%02d.jpg", n);
    }

    /** "HH:MM" in 24-hour time as minutes since midnight, or {@code fallback} for anything else. */
    static int parse(String text, int fallback) {
        if (text == null) return fallback;
        String t = text.trim();
        int colon = t.indexOf(':');
        if (colon < 1 || colon > 2 || t.length() != colon + 3) return fallback;
        try {
            int h = Integer.parseInt(t.substring(0, colon));
            int m = Integer.parseInt(t.substring(colon + 1));
            return h < 0 || h > 23 || m < 0 || m > 59 ? fallback : h * 60 + m;
        } catch (NumberFormatException e) {
            return fallback;
        }
    }
}
