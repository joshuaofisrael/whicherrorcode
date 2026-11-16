#!/usr/bin/env python3
"""QA for Which Error Code. Usage: python3 _build/check.py [--launch]"""
import glob, re, json, os, sys, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCH = "--launch" in sys.argv
LEGAL = {"terms", "privacy", "disclaimer", "copyright", "ad-disclosure"}
NEED_SOURCES = {"codes", "filters", "guides"}
bad = 0
titles = {}
files = [f for f in glob.glob(ROOT + "/**/*.html", recursive=True) if "/_build/" not in f]

def fail(msg):
    global bad
    print(msg)
    bad += 1

for f in files:
    h = open(f, encoding="utf-8").read()
    rel = os.path.relpath(f, ROOT)
    top = rel.split("/")[0]
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h):
        try:
            json.loads(m)
        except Exception as e:
            fail(f"JSONLD {rel} {e}")
    vis = re.sub(r"<script.*?</script>", "", h, flags=re.S)
    if top not in LEGAL and re.search(r"Joshua|Israel Ventures|©", vis):
        fail(f"LLC {rel}")
    if top in LEGAL and "is a trade name of Joshua Israel Ventures LLC" not in h:
        fail(f"nolegalline {rel}")
    if not re.search(r'<link rel="canonical" href="https://whicherrorcode.com/', h):
        fail(f"canonical {rel}")
    if h.count("<h1") != 1:
        fail(f"h1count {rel} {h.count('<h1')}")
    dm = re.search(r'<meta name="description" content="(.*?)"', h)
    if not dm or len(html.unescape(dm.group(1))) > 155:
        fail(f"desc {rel} {0 if not dm else len(html.unescape(dm.group(1)))}")
    if LAUNCH:
        if "static.cloudflareinsights.com/beacon.min.js" not in h:
            fail(f"nobeacon {rel}")
        if "noindex" in h and rel != "404.html":
            fail(f"noindex {rel}")
    elif "noindex" not in h:
        fail(f"preview-missing-noindex {rel}")
    if "noindex-flag:" not in h:
        fail(f"flag {rel}")
    if "—" in h or "–" in h:
        fail(f"dash {rel}")
    t = re.search(r"<title>(.*?)</title>", h).group(1)
    titles.setdefault(t, []).append(rel)
    if rel != "404.html" and 'class="byline"' not in h and top in ("codes", "filters", "guides", "about", "methodology", "brands"):
        if rel.count("/") >= 2 or top in ("about", "methodology", "guides"):
            if 'class="byline"' not in h and top != "brands":
                pass
    # byline on article pages
    if "<article" in h and 'class="byline"' not in h and top not in LEGAL and top != "contact":
        # brand hubs and appliance hubs are not all articles. Require byline where we emit article+byline.
        if top in ("codes", "filters", "guides", "about", "methodology"):
            fail(f"byline {rel}")
    if top in NEED_SOURCES and 'class="sources"' not in h:
        fail(f"sources {rel}")
    if 'class="faq"' in h and "FAQPage" not in h:
        fail(f"faqschema {rel}")
    if top == "codes" and rel.count("/") >= 3 and "Unplug the appliance" not in vis:
        fail(f"safety {rel}")
    for href in re.findall(r'(?:href|src)="([^"#?]*)', h):
        if not href or href.startswith("mailto:") or href.startswith("http://") or href.startswith("https://"):
            continue
        if not href.startswith("/"):
            fail(f"not-root {rel} {href}")
            continue
        p = os.path.join(ROOT, href.lstrip("/"))
        if not (os.path.isfile(p) or os.path.isfile(os.path.join(p, "index.html"))):
            fail(f"broken {rel} {href}")
    if rel == "index.html" and 'id="code-search"' not in h:
        fail("homepage search missing")

for t, fs in titles.items():
    if len(fs) > 1:
        fail(f"duptitle {t} {fs}")
    if len(html.unescape(t)) > 70:
        print("longtitle", len(html.unescape(t)), t)

cname = open(os.path.join(ROOT, "CNAME"), encoding="utf-8").read().strip()
if cname != "whicherrorcode.com":
    fail(f"CNAME {cname}")
robots = open(os.path.join(ROOT, "robots.txt"), encoding="utf-8").read()
for bot in ["Googlebot", "Bingbot", "GPTBot", "ClaudeBot", "PerplexityBot", "OAI-SearchBot", "CCBot", "Google-Extended", "Applebot-Extended", "Bytespider"]:
    if f"User-agent: {bot}" not in robots:
        fail(f"robots {bot}")
if "Sitemap: https://whicherrorcode.com/sitemap.xml" not in robots:
    fail("robots sitemap")
sm = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
locs = re.findall(r"<loc>(.*?)</loc>", sm)
if "404" in sm:
    fail("404 in sitemap")
if len(locs) < 80:
    fail(f"sitemap count {len(locs)}")
if len(locs) != len(set(locs)):
    fail("duplicate sitemap urls")
llms = open(os.path.join(ROOT, "llms.txt"), encoding="utf-8").read()
if "whicherrorcode.com" not in llms:
    fail("llms")
print("files", len(files), "sitemap", len(locs), "issues", bad)
sys.exit(1 if bad else 0)
