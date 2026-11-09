"""Sample a Kiosk app's CPU usage and frame jank over a short window.

Requires ``adb`` on PATH and one connected device.

Usage:
    python perf_sample.py [seconds] [package]

Example:
    python perf_sample.py 12 de.ozerov.fully
"""
import re
import subprocess
import sys
import time


PKG = sys.argv[2] if len(sys.argv) > 2 else 'de.ozerov.fully'


def sh(cmd):
    p = subprocess.run(['adb', 'shell', cmd], capture_output=True, text=True)
    return p.stdout


def pid():
    out = sh('ps | grep ' + PKG)
    m = re.search(r'^\S+\s+(\d+)\s+.*' + re.escape(PKG) + r'\s*$', out, re.M)
    return int(m.group(1)) if m else None


def ticks(p):
    fields = sh('cat /proc/%d/stat' % p).split()
    return int(fields[13]) + int(fields[14])  # utime + stime


def janky():
    out = sh('dumpsys gfxinfo ' + PKG)
    frames = re.search(r'Total frames rendered:\s*(\d+)', out)
    jank = re.search(r'Janky frames:\s*\d+\s*\(([\d.]+)%\)', out)
    p90 = re.search(r'90th percentile:\s*(\d+)ms', out)
    return (frames.group(1) if frames else '?',
            jank.group(1) if jank else '?',
            p90.group(1) if p90 else '?')


def main():
    secs = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    p = pid()
    if not p:
        print('process not found: ' + PKG)
        return
    sh('dumpsys gfxinfo %s reset > /dev/null' % PKG)
    t0 = ticks(p)
    time.sleep(secs)
    t1 = ticks(p)
    cpu = (t1 - t0) / (100.0 * secs) * 100.0
    frames, jank, p90 = janky()
    load = sh('cat /proc/loadavg').strip().split()[0]
    print('window=%ds pid=%d pkg=%s' % (secs, p, PKG))
    print('CPU       : %.1f%% (single-core equivalent)' % cpu)
    print('loadavg1  : %s' % load)
    print('frames    : %s   janky: %s%%   p90: %sms' % (frames, jank, p90))


if __name__ == '__main__':
    main()
