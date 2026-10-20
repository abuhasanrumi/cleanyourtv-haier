package com.gathin.tvhome;

import android.accessibilityservice.AccessibilityService;
import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.widget.Toast;

/**
 * Sleep timer: Off, 30, 60, 90, 120 minutes, then the TV goes to standby. Many TVs give an app no way to
 * turn them off, so this asks Android's accessibility "lock screen" action, which puts a TV in standby,
 * through InputKeyService or HomeKeyService, whichever is switched on (INPUT_KEY_SERVICE=1 or
 * HOME_KEY_SERVICE=1 build-and-install.sh). Idea from the Control Center fork in SHOWCASE.md.
 */
final class Sleep {
    static final int[] STEPS = {30, 60, 90, 120};
    private static final String PREFS = "sleep";
    private static final String AT = "at";
    private static final String EXACT = "exact";
    /** An alarm that fires later than this (the TV was already off and the alarm waited) does nothing. */
    private static final long STALE_MS = 2 * 60_000L;
    private static final long WINDOW_MS = 10 * 60_000L;

    /** The accessibility service that can put the TV in standby, while one is connected. */
    private static AccessibilityService service;

    private Sleep() { }

    static void attach(AccessibilityService s) {
        service = s;
    }

    static void detach(AccessibilityService s) {
        if (service == s) service = null;
    }

    /** Whether a timer could turn the TV off right now. */
    static boolean available() {
        return service != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.P;
    }

    /** Fires when the timer runs out. */
    public static final class Alarm extends BroadcastReceiver {
        @Override
        public void onReceive(Context c, Intent intent) {
            long at = prefs(c).getLong(AT, 0);
            long late = STALE_MS + (prefs(c).getBoolean(EXACT, true) ? 0 : WINDOW_MS);
            prefs(c).edit().remove(AT).apply();
            if (at > 0 && Math.abs(System.currentTimeMillis() - at) < late && available()) {
                service.performGlobalAction(AccessibilityService.GLOBAL_ACTION_LOCK_SCREEN);
            }
        }
    }

    /** Minutes left, rounded up, or 0 when the timer is off. */
    static int minutesLeft(Context c) {
        long left = prefs(c).getLong(AT, 0) - System.currentTimeMillis();
        return left > 0 ? (int) ((left + 59_999) / 60_000) : 0;
    }

    /** Off → 30 → 60 → 90 → 120 → Off; from a running timer, the next step above what is left. */
    static int cycle(Context c) {
        int next = next(minutesLeft(c));
        set(c, next);
        return next;
    }

    /** The timer's state for a menu row: "Off" or "45 min". */
    static String label(Context c) {
        int left = minutesLeft(c);
        return left > 0 ? c.getString(R.string.sleep_minutes, left) : c.getString(R.string.sleep_off);
    }

    /** One press on a Sleep timer row: the next step, said in a toast. Returns the row's new label. */
    static String press(Context c) {
        if (!available()) {
            Toast.makeText(c, R.string.sleep_needs_service, Toast.LENGTH_LONG).show();
            return label(c);
        }
        int minutes = cycle(c);
        Toast.makeText(c, minutes > 0 ? c.getString(R.string.sleep_set, minutes)
                : c.getString(R.string.sleep_cancelled), Toast.LENGTH_SHORT).show();
        return label(c);
    }

    /** The step after {@code left} minutes, 0 after the last one. Pure, for the unit test. */
    static int next(int left) {
        for (int s : STEPS) if (s > left) return s;
        return 0;
    }

    private static void set(Context c, int minutes) {
        AlarmManager am = c.getSystemService(AlarmManager.class);
        PendingIntent pi = PendingIntent.getBroadcast(c, 0, new Intent(c, Alarm.class),
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        if (am != null) am.cancel(pi);
        if (minutes <= 0) {
            prefs(c).edit().remove(AT).apply();
            return;
        }
        long at = System.currentTimeMillis() + minutes * 60_000L;
        boolean exact = am != null && (Build.VERSION.SDK_INT < Build.VERSION_CODES.S || am.canScheduleExactAlarms());
        prefs(c).edit().putLong(AT, at).putBoolean(EXACT, exact).apply();
        if (am == null) return;
        // Exact where Android allows it (build-and-install.sh grants SCHEDULE_EXACT_ALARM over adb); without
        // that, Android 12+ may fire up to ten minutes late, which a sleep timer can live with.
        try {
            if (exact) am.setExactAndAllowWhileIdle(AlarmManager.RTC, at, pi);
            else am.setWindow(AlarmManager.RTC, at, WINDOW_MS, pi);
        } catch (SecurityException e) {
            prefs(c).edit().putBoolean(EXACT, false).apply();
            am.setWindow(AlarmManager.RTC, at, WINDOW_MS, pi);
        }
    }

    private static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
}
