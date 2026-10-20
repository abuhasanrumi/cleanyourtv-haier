"""tools/bench.py against a fake TV: parsing, medians, the accessibility list put back, the CSV."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import bench  # noqa: E402


class FakeTv:
    def __init__(self, services="com.gathin.tvhome/.InputKeyService"):
        self.services = services
        self.commands = []
        self.cold = iter([900, 700, 800, 650, 750])
        self.warm = iter([120, 110, 130, 100, 115])

    def __call__(self, cmd):
        self.commands.append(cmd)
        if cmd.startswith("cmd package resolve-activity"):
            return "priority=0 preferredOrder=0 match=0x108000\ncom.gathin.tvhome/.MainActivity\n"
        if cmd == "settings get secure enabled_accessibility_services":
            return self.services + "\n"
        if cmd.startswith("am start -W -n"):
            return f"Starting: Intent {{ }}\nStatus: ok\nTotalTime: {next(self.cold)}\nWaitTime: 1000\nComplete\n"
        if cmd == bench.HOME:
            return f"Status: ok\nLaunchState: HOT\nTotalTime: {next(self.warm)}\nComplete\n"
        if cmd.startswith("dumpsys meminfo"):
            return "** MEMINFO in pid 123 [com.gathin.tvhome] **\n...\n           TOTAL PSS:    46080            TOTAL RSS: 1\n"
        if cmd == "cat /proc/meminfo":
            return "MemTotal:        2009088 kB\nMemFree:          100000 kB\nMemAvailable:     819200 kB\n"
        if cmd.startswith("logcat"):
            return "10-20 08:01:02.123  100  100 I boot_progress_enable_screen: 31544\n"
        if cmd == "getprop ro.product.model":
            return "H50P7UX\n"
        if cmd == "pm list packages -e":
            return "package:a\npackage:b\npackage:c\n"
        if cmd == "pm list packages -d":
            return "package:d\n"
        return ""


class BenchTest(unittest.TestCase):
    def test_a_run_on_a_fake_tv(self):
        tv = FakeTv()
        row = bench.run(tv, pause=lambda s: None)
        self.assertEqual(row["home"], "com.gathin.tvhome")
        self.assertEqual(row["cold_ms"], "750")
        self.assertEqual(row["cold_runs"], "900 700 800 650 750")
        self.assertEqual(row["warm_ms"], "115")
        self.assertEqual(row["home_pss_mb"], "45")
        self.assertEqual(row["mem_total_mb"], "1962")
        self.assertEqual(row["mem_available_mb"], "800")
        self.assertEqual((row["enabled_packages"], row["disabled_packages"]), ("3", "1"))
        self.assertEqual(row["boot_screen_s"], "31.5")
        self.assertEqual(row["model"], "H50P7UX")

    def test_every_cold_start_comes_after_settings_and_a_force_stop(self):
        tv = FakeTv()
        bench.run(tv, pause=lambda s: None)
        starts = [i for i, c in enumerate(tv.commands) if c.startswith("am start -W -n")]
        self.assertEqual(len(starts), bench.RUNS)
        for i in starts:
            self.assertEqual(tv.commands[i - 2], bench.SETTINGS)
            self.assertEqual(tv.commands[i - 1], "am force-stop com.gathin.tvhome")

    def test_accessibility_services_are_put_back(self):
        tv = FakeTv()
        bench.run(tv, pause=lambda s: None)
        self.assertIn("settings put secure enabled_accessibility_services "
                      "'com.gathin.tvhome/.InputKeyService'", tv.commands)
        self.assertIn("settings put secure accessibility_enabled 1", tv.commands)

    def test_services_of_other_apps_are_left_alone(self):
        tv = FakeTv(services="null")
        bench.run(tv, pause=lambda s: None)
        self.assertFalse(any("enabled_accessibility_services '" in c for c in tv.commands))

    def test_older_meminfo_and_missing_values(self):
        self.assertEqual(bench.pss_kb("  TOTAL    51200    40000\n"), 51200)
        self.assertIsNone(bench.pss_kb("No process found for: x\n"))
        self.assertIsNone(bench.total_time("Warning: Activity not started\nComplete\n"))
        self.assertIsNone(bench.boot_screen_ms(""))

    def test_the_chooser_is_refused(self):
        def shell(cmd):
            return "android\n" if cmd.startswith("cmd package resolve-activity") else ""
        with self.assertRaises(SystemExit):
            bench.run(shell, pause=lambda s: None)

    def test_csv_keeps_runs_per_tv(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bench.csv"
            bench.save(path, {"tv_host": "1.1.1.1", "label": "before", "cold_ms": "2400"})
            bench.save(path, {"tv_host": "2.2.2.2", "label": "other"})
            bench.save(path, {"tv_host": "1.1.1.1", "label": "after", "cold_ms": "700"})
            rows = bench.history(path, "1.1.1.1")
            self.assertEqual([r["label"] for r in rows], ["before", "after"])
            text = bench.table(rows)
            self.assertIn("before", text)
            self.assertIn("2400", text)


if __name__ == "__main__":
    unittest.main()
