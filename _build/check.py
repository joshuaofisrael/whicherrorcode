#!/usr/bin/env python3
"""QA for Which Error Code. Usage: python3 _build/check.py [--launch]

Launch mode reads the robots meta tag only. The HTML comment noindex-flag
stays on every page, including after launch, so a raw "noindex" text search
is a false positive.

--launch also requires the Cloudflare beacon and the GA4 loader on every page,
and fails with ga4-id-empty while GA4_ID in _build/build.py is blank.
"""
import glob, re, json, os, sys, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCH = "--launch" in sys.argv
LEGAL = {"terms", "privacy", "disclaimer", "copyright", "ad-disclosure"}
NEED_SOURCES = {"codes", "filters", "guides"}
FOOTER = ("/about/", "/contact/", "/privacy/", "/terms/", "/disclaimer/", "/copyright/", "/ad-disclosure/", "/image-policy/")
CONSENT_KEYS = ("ad_storage", "ad_user_data", "ad_personalization", "analytics_storage")
bad = 0
titles = {}
descs = {}
files = [f for f in glob.glob(ROOT + "/**/*.html", recursive=True) if "/_build/" not in f]

def fail(msg):
    global bad
    print(msg)
    bad += 1

def robots_meta(h):
    m = re.search(r'<meta name="robots" content="([^"]*)"', h)
    return m.group(1) if m else ""

def ga4_constant():
    src = open(os.path.join(ROOT, "_build", "build.py"), encoding="utf-8").read()
    m = re.search(r'^GA4_ID = "([^"]*)"', src, re.M)
    return m.group(1) if m else None

def photo_unlinked(h):
    hits = []
    for m in re.finditer(r"<img\b", h, re.I):
        pre = h[:m.start()]
        start = max(pre.rfind("<a "), pre.rfind("<a\n"))
        close = pre.rfind("</a>")
        if start < 0 or close > start or 'href="/image-policy/"' not in pre[start:]:
            hits.append(m.start())
    return hits

GA4 = ga4_constant()
if LAUNCH and not (GA4 and re.fullmatch(r"G-[A-Z0-9]+", GA4)):
    fail("ga4-id-empty")

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
    for prop in ("og:type", "og:site_name", "og:title", "og:description", "og:url", "og:image"):
        if f'property="{prop}"' not in h:
            fail(f"og {rel} {prop}")
    if h.count("<h1") != 1:
        fail(f"h1count {rel} {h.count('<h1')}")
    dm = re.search(r'<meta name="description" content="(.*?)"', h)
    if not dm or not dm.group(1).strip() or len(html.unescape(dm.group(1))) > 155:
        fail(f"desc {rel} {0 if not dm else len(html.unescape(dm.group(1)))}")
    elif dm:
        descs.setdefault(html.unescape(dm.group(1)), []).append(rel)
    rc = robots_meta(h)
    if not rc:
        fail(f"robots-meta {rel}")
    if LAUNCH:
        if "static.cloudflareinsights.com/beacon.min.js" not in h:
            fail(f"nobeacon {rel}")
        if 'data-ga4-loader="1"' not in h or "/assets/consent.js" not in h or "https://www.googletagmanager.com/gtag/js" not in h:
            fail(f"noga4 {rel}")
        if any(key not in h for key in CONSENT_KEYS) or "'denied'" not in h:
            fail(f"noconsent {rel}")
        for token in ('id="cookie-banner"', 'id="cookie-accept"', 'id="cookie-reject"', 'id="cookie-settings"'):
            if token not in h:
                fail(f"consent-ui {rel} {token}")
        if rel != "404.html" and "noindex" in rc.lower():
            fail(f"noindex {rel}")
        if rel == "404.html" and "noindex" not in rc.lower():
            fail(f"404-indexable {rel}")
        if GA4 and f'data-ga4-id="{GA4}"' not in h:
            fail(f"ga4-id-mismatch {rel}")
    else:
        if "noindex" not in rc.lower():
            fail(f"preview-missing-noindex {rel}")
        if "static.cloudflareinsights.com/beacon.min.js" in h or "data-ga4-loader" in h:
            fail(f"preview-analytics {rel}")
    if "noindex-flag:" not in h:
        fail(f"flag {rel}")
    if "—" in h or "–" in h:
        fail(f"dash {rel}")
    t = re.search(r"<title>(.*?)</title>", h).group(1)
    titles.setdefault(t, []).append(rel)
    if len(html.unescape(t)) > 60:
        fail(f"longtitle {len(html.unescape(t))} {rel} {t}")
    if "<article" in h and 'class="byline"' not in h and top not in LEGAL and top != "contact":
        if top in ("codes", "filters", "guides", "about", "methodology"):
            fail(f"byline {rel}")
    if top in NEED_SOURCES and 'class="sources"' not in h:
        fail(f"sources {rel}")
    if 'class="faq"' in h and "FAQPage" not in h:
        fail(f"faqschema {rel}")
    if "<article" in h and '"@type": "Article"' not in h:
        fail(f"article-schema {rel}")
    if 'class="crumbs"' in h and '"@type": "BreadcrumbList"' not in h:
        fail(f"crumbs-schema {rel}")
    if rel == "index.html" and '"@type": "WebSite"' not in h:
        fail("website-schema")
    if rel == "privacy/index.html" and ("Google Analytics 4" not in h or "Cloudflare Web Analytics" not in h):
        fail("privacy-analytics-names")
    foot = re.search(r'<footer class="site">.*?</footer>', h, re.S)
    foot = foot.group(0) if foot else ""
    for href in FOOTER:
        if f'href="{href}"' not in foot:
            fail(f"footer {rel} {href}")
    if 'id="cookie-settings"' not in foot:
        fail(f"cookie-settings {rel}")
    for _ in photo_unlinked(h):
        fail(f"photo {rel}")
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
for d, fs in descs.items():
    if len(fs) > 1:
        fail(f"dupdesc {fs}")

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
if sm.count("<lastmod>") != len(locs) or not re.search(r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>", sm):
    fail("sitemap lastmod")
llms = open(os.path.join(ROOT, "llms.txt"), encoding="utf-8").read()
if "whicherrorcode.com" not in llms:
    fail("llms")
key = "e5e7fc4f0a0e96a11d330aa8cf3cba1c"
key_path = os.path.join(ROOT, key + ".txt")
if not os.path.isfile(key_path) or open(key_path, encoding="utf-8").read().strip() != key:
    fail("indexnow")
print("files", len(files), "sitemap", len(locs), "issues", bad)
sys.exit(1 if bad else 0)
