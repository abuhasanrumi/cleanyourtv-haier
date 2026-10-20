#!/usr/bin/env python3
"""How fast Home starts and how much memory it takes, before and after a debloat or a new launcher.

    TV_HOST=192.168.1.50 tools/venv/bin/python -I tools/bench.py before     # on the stock home
    tools/disable.sh ...; launcher/build-and-install.sh
    TV_HOST=192.168.1.50 tools/venv/bin/python -I tools/bench.py after      # prints both runs

It measures whichever app owns Home right now:

- cold start: Home force-stopped, then started (`am start -W`, TotalTime), median of 5 runs
- warm start: Settings opened, then Home again, median of 5 runs
- Home's memory (`dumpsys meminfo`, total PSS) and the TV's free memory (MemAvailable)
- enabled and disabled packages
- boot: when the screen came on, in seconds after power-on, if the TV's event log still has it
  (it does for a few minutes after a reboot, so reboot, wait for Home, then run this)

Each run is added to ~/.cleanyourtv/bench.csv, and the earlier runs for the same TV are printed under it.
The test opens Settings and restarts Home a few times; the screen flickers for about a minute. Restarting
Home cancels this launcher's sleep timer, and the accessibility services are switched back on afterwards.
"""
import csv
import os
import re
import sys
import time
from pathlib import Path
from statistics import median

RUNS = 5
STORE = Path(os.path.expanduser("~")) / ".cleanyourtv" / "bench.csv"
FIELDS = ["time", "tv_host", "model", "label", "home", "cold_ms", "cold_runs", "warm_ms", "home_pss_mb",
          "mem_total_mb", "mem_available_mb", "enabled_packages", "disabled_packages", "boot_screen_s"]
SETTINGS = "am start -W -a android.settings.SETTINGS"
HOME = "am start -W -a android.intent.action.MAIN -c android.intent.category.HOME"


def total_time(out):
    """TotalTime from `am start -W`, in ms, or None when the activity did not start fresh."""
    m = re.search(r"^TotalTime:\s*(\d+)", out, re.M)
    return int(m.group(1)) if m else None


def pss_kb(out):
    """Total PSS from `dumpsys meminfo <package>`: "TOTAL PSS: 45678" on Android 10+, "TOTAL 45678" before."""
    m = re.search(r"TOTAL PSS:\s*(\d+)", out) or re.search(r"^\s*TOTAL\s+(\d+)", out, re.M)
    return int(m.group(1)) if m else None


def meminfo_kb(out, key):
    m = re.search(rf"^{key}:\s*(\d+)\s*kB", out, re.M)
    return int(m.group(1)) if m else None


def boot_screen_ms(out):
    """The last boot_progress_enable_screen event: milliseconds after power-on when the screen came on."""
    found = re.findall(r"boot_progress_enable_screen\D*(\d+)", out)
    return int(found[-1]) if found else None


def count_packages(out):
    return sum(1 for line in out.splitlines() if line.startswith("package:"))


def mb(kb):
    return "" if kb is None else f"{kb / 1024:.0f}"


def run(shell, runs=RUNS, pause=time.sleep):
    """Takes the measurements with `shell(command) -> output`; returns a row for FIELDS."""
    component = shell("cmd package resolve-activity --brief -a android.intent.action.MAIN "
                      "-c android.intent.category.HOME").strip().splitlines()[-1].strip()
    if "/" not in component:
        raise SystemExit(f"Home is {component!r}, not one app (Android's chooser?). Pick a default home first.")
    pkg = component.split("/")[0]
    services = shell("settings get secure enabled_accessibility_services").strip()

    cold = []
    for _ in range(runs):
        shell(SETTINGS)
        shell(f"am force-stop {pkg}")
        t = total_time(shell(f"am start -W -n {component}"))
        if t is not None:
            cold.append(t)
        pause(2)
    warm = []
    for _ in range(runs):
        shell(SETTINGS)
        pause(1)
        t = total_time(shell(HOME))
        if t is not None:
            warm.append(t)
        pause(1)
    # A force-stop drops the package's accessibility services from the enabled list; put them back the
    # way tools/theme.sh does (clear, set again, switch accessibility on).
    if pkg in services:
        shell("settings put secure enabled_accessibility_services ''")
        shell(f"settings put secure enabled_accessibility_services '{services}'")
        shell("settings put secure accessibility_enabled 1")

    pause(3)
    pss = pss_kb(shell(f"dumpsys meminfo {pkg}"))
    mem = shell("cat /proc/meminfo")
    boot = boot_screen_ms(shell("logcat -b events -d -s boot_progress_enable_screen 2>/dev/null"))
    return {
        "time": time.strftime("%Y-%m-%d %H:%M"),
        "model": shell("getprop ro.product.model").strip(),
        "home": pkg,
        "cold_ms": f"{median(cold):.0f}" if cold else "",
        "cold_runs": " ".join(str(t) for t in cold),
        "warm_ms": f"{median(warm):.0f}" if warm else "",
        "home_pss_mb": mb(pss),
        "mem_total_mb": mb(meminfo_kb(mem, "MemTotal")),
        "mem_available_mb": mb(meminfo_kb(mem, "MemAvailable")),
        "enabled_packages": str(count_packages(shell("pm list packages -e"))),
        "disabled_packages": str(count_packages(shell("pm list packages -d"))),
        "boot_screen_s": "" if boot is None else f"{boot / 1000:.1f}",
    }


def history(path, host):
    if not path.is_file():
        return []
    with path.open(newline="") as f:
        return [r for r in csv.DictReader(f) if r.get("tv_host") == host]


def save(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.is_file()
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


COLUMNS = [("label", "run"), ("home", "home"), ("cold_ms", "cold ms"), ("warm_ms", "warm ms"),
           ("home_pss_mb", "Home MB"), ("mem_available_mb", "free MB"), ("enabled_packages", "enabled"),
           ("disabled_packages", "disabled"), ("boot_screen_s", "boot s")]


def table(rows):
    cells = [[h for _, h in COLUMNS]] + [[r.get(k, "") or "-" for k, _ in COLUMNS] for r in rows]
    widths = [max(len(row[i]) for row in cells) for i in range(len(COLUMNS))]
    return "\n".join("  ".join(c.ljust(w) for c, w in zip(row, widths)).rstrip() for row in cells)


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tv  # noqa: E402  (exits with a hint when TV_HOST is not set)
    dev = tv.connect()
    print(f"Measuring Home on {tv.HOST}; the screen will flicker for about a minute.", flush=True)
    try:
        row = run(lambda cmd: dev.shell(cmd, read_timeout_s=120.0))
    finally:
        dev.close()
    row.update(tv_host=tv.HOST, label=label)
    earlier = history(STORE, tv.HOST)
    save(STORE, row)
    print(f"{row['model']}, {row['mem_total_mb']} MB RAM. Cold start runs: {row['cold_runs'] or 'none'} ms\n")
    print(table(earlier[-5:] + [row]))
    print(f"\nSaved to {STORE}")


if __name__ == "__main__":
    main()
