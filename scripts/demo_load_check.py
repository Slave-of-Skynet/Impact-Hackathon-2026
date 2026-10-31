"""5 concurrent demo clients (login -> child mode -> correct PIN) + a /healthz/ prober.

Usage (issue #59, local/staging only — never against the shared demo host):
    uv run python scripts/demo_load_check.py BASE_URL SECONDS EMAIL PASSWORD PIN
Prints health latency percentiles and how many probes exceeded Render's 5 s health-check timeout.
"""
import http.cookiejar
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

BASE, SECONDS, EMAIL, PASSWORD, PIN = sys.argv[1], float(sys.argv[2]), *sys.argv[3:6]
stop = time.monotonic() + SECONDS
health, flows, errors = [], [], []


def opener():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar)), jar


def csrf(jar):
    return next(c.value for c in jar if c.name == "csrftoken")


def req(op, path, data=None, timeout=120):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    r = urllib.request.Request(BASE + path, data=body, headers={"Referer": BASE + path})
    try:
        with op.open(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def client(n):
    while time.monotonic() < stop:
        op, jar = opener()
        t0 = time.monotonic()
        try:
            req(op, "/cont/intrare/")
            s, _ = req(op, "/cont/intrare/", {"csrfmiddlewaretoken": csrf(jar), "username": EMAIL, "password": PASSWORD})
            s, html = req(op, "/panou/")
            child = re.search(r'/familie/([0-9a-f-]{36})/mod-copil/', html)
            if not child:
                errors.append(f"c{n} no child (status {s})"); continue
            req(op, child.group(0), {"csrfmiddlewaretoken": csrf(jar)})
            s, _ = req(op, "/parinte/", {"csrfmiddlewaretoken": csrf(jar), "pin": PIN})
            flows.append(time.monotonic() - t0)
            if s >= 400:
                errors.append(f"c{n} pin {s}")
        except Exception as e:  # timeouts / resets count as errors, not crashes
            errors.append(f"c{n} {type(e).__name__}")


def prober():
    op, _ = opener()
    while time.monotonic() < stop:
        t0 = time.monotonic()
        try:
            s, _ = req(op, "/healthz/", timeout=30)
        except Exception:
            s = 0
        health.append((time.monotonic() - t0, s))
        time.sleep(1)


threads = [threading.Thread(target=client, args=(i,)) for i in range(5)] + [threading.Thread(target=prober)]
[t.start() for t in threads]
[t.join() for t in threads]
lat = sorted(h[0] for h in health)
pct = lambda p: round(lat[min(len(lat) - 1, int(p * len(lat)))], 2)
print(f"health probes={len(lat)} p50={pct(.5)}s p95={pct(.95)}s max={round(lat[-1], 2)}s "
      f">5s={sum(1 for x in lat if x > 5)} non200={sum(1 for h in health if h[1] != 200)}")
print(f"flows={len(flows)} avg_flow={round(sum(flows) / max(1, len(flows)), 1)}s errors={len(errors)} {errors[:5]}")
