#!/usr/bin/env python3
"""Which Error Code static site builder. Run from the repo root.

  python3 _build/build.py            # pre launch: noindex on every page, root paths, CNAME
  python3 _build/build.py --launch   # domain live: indexable, Cloudflare beacon, GA4 after consent

NOINDEX is the single pre launch flag. Paths are always root relative.
Canonicals always use https://whicherrorcode.com/.
GA4_ID stays an empty string until the owner pastes a G-XXXXXXXXXX measurement id.
check.py --launch fails while that constant is empty.
"""
import os, sys, json, html, re, zlib, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from codes import BRANDS, APPLS, GROUPS
from filters import FILTERS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCH = "--launch" in sys.argv
NOINDEX = not LAUNCH
BASE = "https://whicherrorcode.com/"
BRAND = "Which Error Code"
TODAY = "2026-11-16"
TODAY_H = "16 Nov 2026"
# TODAY2 is the date of the 18 Nov 2026 update (new GE oven coverage). Only pages whose
# content changed that day use it; everything else keeps the original TODAY/TODAY_H so an
# unrelated rebuild does not manufacture freshness on pages nothing happened to.
TODAY2 = "2026-11-18"
TODAY2_H = "18 Nov 2026"
# TODAY3 is the date of the 19 Nov 2026 update (AdSense readiness + safety refresh + LG oven).
# Only pages whose content changed that day use it; unrelated rebuilds must not manufacture freshness.
TODAY3 = "2026-11-19"
TODAY3_H = "19 Nov 2026"
# TODAY4 is the 20 Nov 2026 washer-hub refresh. Only that page uses it.
TODAY4 = "2026-11-20"
TODAY4_H = "20 Nov 2026"
# TODAY5 is the 21 Nov 2026 Whirlpool range F-code pass and the Bosch dishwasher reread.
# Only pages whose text changed that day use it.
TODAY5 = "2026-11-21"
TODAY5_H = "21 Nov 2026"
_DATE_H = {TODAY: TODAY_H, TODAY2: TODAY2_H, TODAY3: TODAY3_H, TODAY4: TODAY4_H, TODAY5: TODAY5_H}
# Photo bank file oven-control-panel.png was not on disk for this run.
# Leave empty so no page points at a missing file. Set this to
# "/assets/photos/oven-control-panel.png" only after that file is committed.
OVEN_THUMB = ""
INDEXNOW_KEY = "e5e7fc4f0a0e96a11d330aa8cf3cba1c"
CF_BEACON_TOKEN = "eac63f2b5dbc4539a2d95249baab6472"
FORM_ENDPOINT = "https://formsubmit.co/joshuaofisrael@gmail.com"
CONTACT_EMAIL = "joshuaofisrael@gmail.com"
# Public GA4 measurement id. Empty until the owner pastes G-XXXXXXXXXX. Not a secret.
GA4_ID = "G-MNR4EL37WN"
# AdSense publisher id. Head script + meta only; no ad units until approval.
ADSENSE_CLIENT = "ca-pub-5681559774142917"
LEGAL_LINE = "Which Error Code is a trade name of Joshua Israel Ventures LLC, a Florida limited liability company."
E = html.escape
PAGES = []

BNAME = dict(BRANDS)
ANAME = {a: n for a, n, _ in APPLS}
APLUR = {a: p for a, _, p in APPLS}

LOGO = '<svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true" focusable="false"><rect width="64" height="64" rx="14" fill="#0b3954"/><rect x="14" y="14" width="36" height="28" rx="4" fill="#e6f4f1"/><path d="M18 38 V26 h6 l4 8 4-8 h6 v12 h-4 V30 l-4 8 h-4 l-4-8 v8z" fill="#087e8b"/><rect x="14" y="46" width="36" height="6" rx="3" fill="#ffb347"/></svg>'
NAV = [("/", "Home"), ("/codes/", "Error codes"), ("/filters/", "Water filters"), ("/guides/safety/", "Safety"), ("/contact/", "Contact")]

def url(path):
    return BASE + path.lstrip("/")

def clip(d, n=155):
    d = " ".join(d.split())
    if len(d) <= n:
        return d
    c = d[: n - 1]
    i = c.rfind(". ")
    if i > 80:
        return c[: i + 1]
    sp = c.rfind(" ")
    return (c[:sp] if sp > 80 else c).rstrip(",;:") + "."

def write(path, content):
    fp = os.path.join(ROOT, path.lstrip("/"))
    if path.endswith("/"):
        fp = os.path.join(fp, "index.html")
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "w", encoding="utf-8") as f:
        f.write(content)

def link(pair):
    return f'<a href="{pair[1]}" rel="nofollow noopener" target="_blank">{E(pair[0])}</a>'

def crumbs_for(items):
    return items

# AdSense low-value-content fix (20 Nov 2026): paths listed in _build/thin-noindex.txt
# get noindex,follow and stay out of the sitemap until they have real unique substance.
_THIN_NOINDEX = set()
try:
    import os as _os
    with open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "thin-noindex.txt"), encoding="utf-8") as _fh:
        _THIN_NOINDEX = {l.strip().strip("/") for l in _fh if l.strip() and not l.startswith("#")}
except FileNotFoundError:
    pass


def _is_thin(path):
    return str(path).strip("/") in _THIN_NOINDEX


def page(path, title, desc, body, jsonld=None, crumbs=None, noindex=False, robots_extra=False, lastmod=None):
    if _is_thin(path):
        noindex = True
    desc = clip(desc)
    canon = url(path if path != "/404.html" else "/")
    if path == "/404.html":
        canon = url("/404.html")
    force_no = noindex or NOINDEX
    # Real pages stay in the sitemap. The noindex flag is separate and flips at launch.
    # 404 and other utility pages pass noindex=True and stay out.
    if path != "/404.html" and not noindex:
        PAGES.append((path, lastmod or TODAY))
    blocks = jsonld if isinstance(jsonld, list) else ([jsonld] if jsonld else [])
    og_type = "article" if any(isinstance(x, dict) and x.get("@type") == "Article" for x in blocks) else "website"
    ld = []
    if path == "/":
        ld.append({"@context": "https://schema.org", "@type": "WebSite", "name": BRAND, "url": BASE,
                   "description": "Home appliance error codes and refrigerator water filter numbers, cited to the manufacturer.",
                   "publisher": {"@type": "Organization", "name": BRAND, "url": BASE, "logo": url("/logo.png")}})
        ld.append({"@context": "https://schema.org", "@type": "Organization", "name": BRAND, "url": BASE,
                   "logo": url("/logo.png")})
    if crumbs:
        ld.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": url(p)} for i, (p, n) in enumerate(crumbs)]})
    ld += blocks
    ldh = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    nav = "".join(f'<a href="{p}"' + (' aria-current="page"' if p == path else "") + f'>{n}</a>' for p, n in NAV)
    bc = ""
    if crumbs:
        bc = '<nav class="crumbs" aria-label="Breadcrumb"><ol>' + "".join(
            (f'<li><a href="{p}">{E(n)}</a></li>' if i < len(crumbs) - 1 else f'<li aria-current="page">{E(n)}</li>')
            for i, (p, n) in enumerate(crumbs)) + "</ol></nav>"
    robots = "noindex, follow" if force_no else "index, follow, max-image-preview:large"
    if LAUNCH:
        beacon = (f"<!-- Cloudflare Web Analytics --><script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{\"token\": \"{CF_BEACON_TOKEN}\"}}'></script><!-- End Cloudflare Web Analytics -->")
        # Consent Mode v2 defaults are denied. consent.js requests gtag only after Accept.
        ga4 = (
            "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
            "gtag('consent','default',{'ad_storage':'denied','ad_user_data':'denied','ad_personalization':'denied','analytics_storage':'denied','wait_for_update':500});</script>"
            f'<script src="/assets/consent.js?v=1" defer data-ga4-loader="1" data-ga4-id="{E(GA4_ID)}" data-ga4-src="https://www.googletagmanager.com/gtag/js"></script>'
        )
        # Publisher verification only: client script + account meta, no ad units on the page.
        adsense = (
            f'<meta name="google-adsense-account" content="{E(ADSENSE_CLIENT)}">'
            f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={E(ADSENSE_CLIENT)}" crossorigin="anonymous"></script>'
        )
        banner = (
            '<div id="cookie-banner" class="cookie-banner" role="region" aria-label="Cookie choices" hidden>'
            '<p>Google Analytics 4 stays off until you accept. Cloudflare Web Analytics does not use cookies.</p>'
            '<button type="button" class="btn" id="cookie-accept">Accept</button>'
            '<button type="button" class="btn alt" id="cookie-reject">Reject</button></div>'
        )
    else:
        beacon = "<!-- cf-beacon: added by launch build -->"
        ga4 = ""
        adsense = ""
        banner = ""
    flag = "on" if NOINDEX else "off"
    legal = ""
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{canon}">
<meta name="robots" content="{robots}">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="{BRAND}"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{canon}"><meta property="og:image" content="{url('/og.png')}"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/style.css?v=3">{adsense}{ga4}{ldh}
</head><body><a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap"><a class="brand" href="/">{LOGO}<span>{BRAND}</span></a><nav class="main" aria-label="Main">{nav}</nav></div></header>
<main id="main" class="wrap">{bc}{body}<!-- ad-slot: below-content (reserved; no ad code) --></main>
<footer class="site"><div class="wrap"><p class="fbrand"><strong>{BRAND}</strong> explains home appliance error codes and refrigerator water filter numbers from the manufacturer pages we cite. We are independent. Names are used only to identify the appliance. Codes and part numbers change by model, so check the manual for yours.</p>
<p class="flinks"><a href="/about/">About</a> | <a href="/methodology/">Sources and methods</a> | <a href="/image-policy/">Image policy</a> | <a href="/terms/">Terms of use</a> | <a href="/privacy/">Privacy</a> | <a href="/privacy/#analytics" id="cookie-settings">Cookie settings</a> | <a href="/disclaimer/">Disclaimer</a> | <a href="/ad-disclosure/">Advertising disclosure</a> | <a href="/copyright/">Copyright and DMCA</a> | <a href="/contact/">Contact</a></p>
{legal}</div></footer>
{banner}
<script src="/assets/site.js?v=1" defer></script>{beacon}
<!-- noindex-flag: {flag} -->
</body></html>'''

def article_ld(headline, path, about=None, published=None, modified=None):
    data = {"@context": "https://schema.org", "@type": "Article", "headline": headline,
            "datePublished": published or TODAY, "dateModified": modified or TODAY,
            "author": {"@type": "Organization", "name": BRAND, "url": BASE},
            "publisher": {"@type": "Organization", "name": BRAND, "url": BASE, "logo": {"@type": "ImageObject", "url": url("/logo.png")}},
            "image": url("/og.png"), "mainEntityOfPage": url(path)}
    if about:
        data["about"] = {"@type": "Thing", "name": about}
    return data

def faq_ld(faqs):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}

def faq_html(faqs):
    return '<section class="faq" aria-labelledby="faq-h"><h2 id="faq-h">Frequently asked questions</h2>' + "".join(
        f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q, a in faqs) + "</section>"

def sources_html(sources, note):
    return '<section class="sources" aria-labelledby="src-h"><h2 id="src-h">Sources</h2><ul>' + "".join(
        f"<li>{link(s)}</li>" for s in sources) + f'</ul><p class="note">{note}</p></section>'

SAFETY = '''<aside class="safety"><h2>Safety before any check</h2>
<p>Unplug the appliance or switch off its breaker before you move it, open a panel, or clean a filter. If it uses gas, shut the gas supply off before you go past the checks the manufacturer published. Do not open a gas valve, an igniter, or a gas line.</p>
<p>If you smell gas, leave the area and contact your gas utility or emergency services. If water is reaching the floor, shut the supply valve off. Stop and call a technician when the code returns, when the manufacturer says service is required, or when the check is not on the cited page.</p></aside>'''

def byline(date_h=None):
    return f'<p class="byline">By {BRAND}. Last verified {date_h or TODAY_H}.</p>'

def article_thumb(src, alt, caption="AI-generated image"):
    """One news-photo style thumbnail; caption links to the image policy. Skip if src is empty."""
    if not src:
        return ""
    return (
        f'<figure class="article-thumb"><a href="/image-policy/">'
        f'<img src="{E(src)}" alt="{E(alt)}" width="960" height="540" loading="lazy">'
        f'</a><figcaption><a href="/image-policy/">{E(caption)}</a></figcaption></figure>'
    )

def compare_box(title, links, lead=None):
    """Lookup/compare box for code and filter pages. links = [(href, label), ...]."""
    lead_html = f"<p>{E(lead)}</p>" if lead else ""
    items = "".join(f'<li><a href="{E(href)}">{E(label)}</a></li>' for href, label in links)
    return (
        f'<aside class="compare" aria-label="{E(title)}"><h2>{E(title)}</h2>'
        f"{lead_html}<ul>{items}</ul></aside>"
    )

def next_reads(items, heading="Keep reading", hid="nr-h"):
    """Related next-read cards. items = [(href, title, blurb, img_or_None), ...]."""
    if not items:
        return ""
    cards = []
    for href, title, blurb, img in items:
        thumb = ""
        if img:
            # The picture links to the image policy. The title link is the next read.
            thumb = (
                f'<a class="nr-thumb" href="/image-policy/">'
                f'<img src="{E(img)}" alt="AI-generated image" width="320" height="180" loading="lazy"></a>'
            )
        cards.append(
            f'<li>{thumb}<div><a href="{E(href)}"><strong>{E(title)}</strong></a>'
            f"<p>{E(blurb)}</p></div></li>"
        )
    return (
        f'<section class="next-reads" aria-labelledby="{E(hid)}"><h2 id="{E(hid)}">{E(heading)}</h2>'
        f'<ul>{"".join(cards)}</ul></section>'
    )

def slug_code(code):
    s = code.lower().replace(" ", "-").replace("/", "-").replace(":", "")
    s = "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in s)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")

def all_rows():
    out = []
    used = set()
    for brand, appl, rows in GROUPS:
        for r in rows:
            item = dict(r)
            item["brand"] = brand
            item["appl"] = appl
            # Case matters: GE uses DE for demo mode and dE for defrost.
            if r["code"] == "DE":
                slug = "demo"
            else:
                slug = slug_code(r["code"])
            base = slug
            n = 2
            while (brand, appl, slug) in used:
                slug = f"{base}-{n}"
                n += 1
            used.add((brand, appl, slug))
            item["slug"] = slug
            out.append(item)
    return out

ROWS = all_rows()

def listing_path(brand, appl):
    return f"/codes/{brand}/{appl}/"

def code_path(r):
    return f"/codes/{r['brand']}/{r['appl']}/{r['slug']}/"

def safety_for(r):
    extra = ""
    if r["brand"] == "samsung" and r["appl"] == "refrigerator":
        extra = "<p>Samsung's refrigerator code page says not to unplug the refrigerator, and not to press buttons to hide a code, unless the steps for that code tell you to. Unplugging can make the fault harder to diagnose. The unplug step in the box above is for checks that require you to move the cabinet or open a panel.</p>"
    return SAFETY + extra

def code_page(r, published=None, modified=None):
    d_pub = published or TODAY
    d_mod = modified or d_pub
    dh = _DATE_H.get(d_mod, TODAY_H)
    path = code_path(r)
    b, a = BNAME[r["brand"]], ANAME[r["appl"]]
    title = f"{b} {a} {r['code']} Error Code"
    if len(title) > 58:
        title = f"{b} {r['code']} {a} Code"
    desc = f"{b} {a.lower()} code {r['code']}: {r['meaning']} Safe checks from the manufacturer, and when to call a technician."
    aliases = ""
    if r["aliases"]:
        aliases = "<p>The same manufacturer page also lists " + E(", ".join(r["aliases"])) + ".</p>"
    checks = "".join(f"<li>{E(c)}</li>" for c in r["checks"])
    extra = f"<p>{E(r['extra'])}</p>" if r["extra"] else ""
    sibs = [x for x in ROWS if x["brand"] == r["brand"] and x["appl"] == r["appl"] and x["slug"] != r["slug"] and x["individual"]][:6]
    sib = "".join(f'<li><a href="{code_path(x)}">{E(x["code"])}</a>: {E(x["meaning"])}</li>' for x in sibs)
    more = f'<h2>More {E(b)} {E(a.lower())} codes</h2><ul>{sib}</ul>' if sib else ""
    water = ""
    if r["water"]:
        water = '<p>Related: <a href="/filters/">refrigerator water filter finder</a>. A sensor code is not a filter part number. Match the cartridge in the refrigerator to the manual.</p>'
    faqs = [
        (f"What does {b} {a.lower()} code {r['code']} mean?", r["meaning"] + (" " + r["extra"] if r["extra"] else "")),
        (f"What can I check on a {b} {a.lower()} showing {r['code']}?", " ".join(r["checks"]) + " Unplug the appliance or switch off its breaker before you move it or open a panel. If it uses gas, shut the gas off before any step the manufacturer did not publish."),
        (f"When should I call a technician for {r['code']}?", r["service"]),
    ]
    body = f'''<article class="prose wide"><h1>{E(b)} {E(a.lower())} code {E(r["code"])}</h1>
{byline(dh)}
<div class="answer"><p><strong>Meaning:</strong> {E(r["meaning"])}</p></div>
{aliases}{extra}
{safety_for(r)}
<h2>Checks the manufacturer publishes</h2><ul class="checks">{checks}</ul>
<h2>When to call a technician</h2><p>{E(r["service"])}</p>
{water}
{faq_html(faqs)}
{sources_html(r["sources"], f"Retrieved {dh}. Models differ. If your manual defines this code differently, the manual wins. {BRAND} is not affiliated with {E(b)}.")}
{more}
<p><a href="{listing_path(r["brand"], r["appl"])}">All {E(b)} {E(a.lower())} codes</a> · <a href="/brands/{r["brand"]}/">{E(b)}</a> · <a href="/appliances/{APLUR[r["appl"]]}/">{E(a)} brands</a> · <a href="/guides/safety/">Safety notes</a> · <a href="/codes/">All error codes</a></p>
</article>'''
    write(path, page(path, title, desc, body, [article_ld(f"{b} {a.lower()} code {r['code']}", path, f"{b} {r['code']}", published=d_pub, modified=d_mod), faq_ld(faqs)],
                    [("/", "Home"), ("/codes/", "Error codes"), (listing_path(r["brand"], r["appl"]), f"{b} {a}"), (path, r["code"])], lastmod=d_mod))

def listing_page(brand, appl, rows, new=False):
    d, dh = (TODAY2, TODAY2_H) if new else (TODAY, TODAY_H)
    path = listing_path(brand, appl)
    b, a = BNAME[brand], ANAME[appl]
    bits = []
    for r in rows:
        alias = f" Also listed as {', '.join(r['aliases'])}." if r["aliases"] else ""
        more = f' <a href="{code_path(r)}">Full page for {E(r["code"])}</a>.' if r["individual"] else ""
        checks = " ".join(r["checks"])
        bits.append(f'<h3 id="{r["slug"]}">{E(r["code"])}</h3><p>{E(r["meaning"])}{E(alias)} {E(checks)} {E(r["service"])}{more}</p>')
    faqs = [
        (f"Where do these {b} {a.lower()} codes come from?", f"Each code on this page is taken from the {b} support page linked in Sources. We do not add codes from repair blogs or from another brand."),
        (f"Does {rcode(rows)} mean the same thing on every {b} {a.lower()}?", "No. The manufacturer often says a code applies to some models only, or that the same letters mean something else on another model. Check the manual for your model number."),
        (f"What should I do before I open a panel on a {b} {a.lower()}?", "Unplug it or switch off the breaker. If it burns gas, shut the gas supply off before any step the manufacturer did not publish. If you smell gas, leave and call your gas utility."),
    ]
    gas = " This appliance may burn gas. Shut the gas off before any inspection past the published checks." if appl in ("dryer", "oven") else ""
    fridge_note = ""
    if brand == "samsung" and appl == "refrigerator":
        fridge_note = "<p>Samsung's refrigerator code page says not to unplug the refrigerator, and not to clear a code from the panel, unless the steps for that code say to. The unplug line above is for when you have to move the cabinet.</p>"
    body = f'''<article class="prose wide"><h1>{E(b)} {E(a.lower())} error codes</h1>
{byline(dh)}
<div class="answer"><p>These are the {E(b)} {E(a.lower())} codes we could verify on the manufacturer's own page. Each block says what the code means, the checks that page allows, and when it says to call a technician.</p></div>
{SAFETY}<p>{E(gas).strip()}</p>{fridge_note}
{"".join(bits)}
{faq_html(faqs)}
{sources_html(unique_sources(rows), f"Retrieved {dh}. {BRAND} is not affiliated with {E(b)}. Names identify the appliance only.")}
<p><a href="/brands/{brand}/">All {E(b)} pages</a> · <a href="/appliances/{APLUR[appl]}/">All {E(a.lower())} brands</a> · <a href="/filters/">Water filters</a></p>
</article>'''
    # fix empty gas paragraph
    body = body.replace("<p></p>", "")
    desc = f"{b} {a.lower()} error codes: what each code means, the safe checks the manufacturer publishes, and when to call a technician."
    write(path, page(path, f"{b} {a} Error Codes", desc, body,
                    [article_ld(f"{b} {a.lower()} error codes", path, f"{b} {a}", published=d, modified=d), faq_ld(faqs)],
                    [("/", "Home"), ("/codes/", "Error codes"), (path, f"{b} {a}")], lastmod=d))

def rcode(rows):
    return rows[0]["code"]

def unique_sources(rows):
    seen = []
    for r in rows:
        for s in r["sources"]:
            if s not in seen:
                seen.append(s)
    return seen

def brand_pages():
    cards = []
    for slug, name in BRANDS:
        items = []
        for appl, an, _ in APPLS:
            rows = [r for r in ROWS if r["brand"] == slug and r["appl"] == appl]
            if not rows:
                continue
            items.append(f'<li><a href="{listing_path(slug, appl)}">{E(an)} codes</a> ({len(rows)} verified)</li>')
        if not items:
            continue
        faqs = [
            (f"Which {name} appliance should I open?",
             f"Open the type printed on the machine. This page links only the {name} appliances whose codes we read on a {name} support page."),
            (f"Why is a {name} code missing?",
             "A code is missing when it was not on the manufacturer page we checked. We do not add codes from repair blogs or from another brand."),
        ]
        # ge gained an oven listing on 18 Nov 2026. Whirlpool's oven count changed 21 Nov 2026.
        if slug == "ge":
            dh, lm = TODAY2_H, TODAY2
        elif slug == "whirlpool":
            dh, lm = TODAY5_H, TODAY5
        else:
            dh, lm = None, None
        body = f'''<article class="prose"><h1>{E(name)} error codes</h1>
{byline(dh)}
<p class="answer">Pick the appliance. Every code is cited to a {E(name)} manual or support page. We leave out codes we have not checked on that page.</p>
<ul class="cols">{"".join(items)}</ul>
{faq_html(faqs)}
<p><a href="/brands/">All brands</a> · <a href="/codes/">All error codes</a> · <a href="/guides/safety/">Safety notes</a></p></article>'''
        path = f"/brands/{slug}/"
        covered = [ANAME[appl].lower() for appl, _, _ in APPLS if any(r["brand"] == slug and r["appl"] == appl for r in ROWS)]
        write(path, page(path, f"{name} Appliance Error Codes", f"{name} error codes we verified: {', '.join(covered)}. Each code is cited to a {name} support page.",
                        body, [article_ld(f"{name} error codes", path, name, modified=lm), faq_ld(faqs)],
                        [("/", "Home"), ("/brands/", "Brands"), (path, name)], lastmod=lm))
    cards = []
    for slug, name in BRANDS:
        labels = []
        for appl, an, _ in APPLS:
            if any(r["brand"] == slug and r["appl"] == appl for r in ROWS):
                labels.append(f'<a href="{listing_path(slug, appl)}">{E(an)}</a>')
        if labels:
            cards.append(f'<li class="card"><h2><a href="/brands/{slug}/">{E(name)}</a></h2><p>{", ".join(labels)}</p></li>')
    faqs = [
        ("Which brand should I pick?",
         "Pick the name printed on the appliance. A code is published here only after we read it on that manufacturer's support page or manual."),
        ("Which brands or machines are missing?",
         "Frigidaire pages are not in this version. We did not find a Frigidaire.com code list we could cite code by code. Bosch ranges, refrigerators, and dryers, and KitchenAid washers and dryers are in the same gap."),
    ]
    # Content changed 18 Nov 2026: the GE oven gap note was removed from this hub.
    body = f'''<article class="prose"><h1>Error codes by brand</h1>
{byline(TODAY2_H)}
<p class="answer">Choose a brand. We publish a code only after reading it on that manufacturer's support page or manual.</p>
<ul class="cards">{"".join(cards)}</ul>
<p>Frigidaire pages are not in this version. We did not find a Frigidaire.com code list we could cite code by code. Bosch ranges, refrigerators, and dryers, and KitchenAid washers and dryers are in the same gap.</p>
{faq_html(faqs)}
<p><a href="/codes/">All error codes</a> · <a href="/appliances/">By appliance</a> · <a href="/guides/safety/">Safety notes</a></p></article>'''
    write("/brands/", page("/brands/", f"Appliance Error Codes by Brand | {BRAND}", "Samsung, LG, GE Appliances, Whirlpool, Maytag, KitchenAid, and Bosch error codes, each cited to the manufacturer.",
                          body, [article_ld("Error codes by brand", "/brands/", modified=TODAY2), faq_ld(faqs)],
                          [("/", "Home"), ("/brands/", "Brands")], lastmod=TODAY2))

def _oven_reads(items, heading, hid):
    """Next-read cards. Oven articles pass OVEN_THUMB; an empty path draws no image."""
    packed = []
    for href, title, blurb in items:
        img = OVEN_THUMB if OVEN_THUMB and "/oven" in href else None
        packed.append((href, title, blurb, img))
    return next_reads(packed, heading, hid)

def whirlpool_oven_table(rows):
    body = []
    for r in rows:
        code_cell = f'<a href="{code_path(r)}">{E(r["code"])}</a>' if r["individual"] else E(r["code"])
        step = E(r["extra"]) if r["extra"] else "Breaker reset only."
        body.append(f'<tr id="{E(r["slug"])}"><td>{code_cell}</td><td>{E(r["meaning"])}</td><td>{step}</td></tr>')
    return ('<div class="tablewrap"><table class="list"><thead><tr>'
            "<th>Code</th><th>What that Whirlpool page says</th><th>Anything besides the reset</th>"
            "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>")

def whirlpool_oven_pages():
    """21 Nov 2026: range F codes opened on Whirlpool Product Help. Hub plus two full pages."""
    rows = [r for r in ROWS if r["brand"] == "whirlpool" and r["appl"] == "oven"]
    path = "/codes/whirlpool/oven/"
    index_src = ("Whirlpool Product Help: range codes that start with F",
                 "https://producthelp.whirlpool.com/Cooking/Wall_Ovens_and_Ranges/Ranges/Error_Codes/Starts_with_F")
    faqs = [
        ("What does a Whirlpool oven F code mean?",
         "It depends on the rest of the code. On the range pages opened 21 Nov 2026, Whirlpool gives almost every code the same owner step, a 1 minute breaker reset, and then names a different part. F1 E1 names the oven control. F2 E1 starts by asking whether the grates sit level. F3 E1 names the oven temperature sensor."),
        ("Should I replace the part Whirlpool names?",
         "No. Those pages tell you to reset power and to schedule service if the code comes back. They do not publish a procedure for replacing a control, a sensor, a latch, a fan, or an element. Unplug the appliance or switch off the breaker before you move the range. Shut the gas off before any inspection past the published reset."),
        ("Does this table cover a Whirlpool wall oven?",
         "No. This is the freestanding and slide-in range list. Whirlpool publishes wall oven codes separately, and that list was not opened on 21 Nov 2026. Use the manual for a wall oven."),
    ]
    mid = _oven_reads([
        ("/codes/whirlpool/oven/f2-e1/", "Whirlpool F2 E1", "The one F code that starts with the cooktop grates, while the range is cool."),
        ("/codes/whirlpool/oven/f1-e1/", "Whirlpool F1 E1", "Oven control or wiring. The same sentence as several other F1 codes, and not the sensor."),
        ("/codes/ge/oven/", "GE oven codes", "GE's F2 is an over-temperature code. GE's F0 and F1 name the keypanel."),
        ("/codes/samsung/oven/c-24/", "Samsung C-24", "Samsung's fast temperature rise is usually a blocked vent, not an F code."),
    ], "Open one of these next", "nr-mid")
    end = _oven_reads([
        ("/appliances/ovens/", "Oven codes by brand", "How Whirlpool, GE, and Samsung name different faults with similar letters."),
        ("/codes/ge/oven/loc-door/", "GE Loc Door", "A self-clean latch display with its own reset. Whirlpool's latch codes do not use those steps."),
        ("/guides/safety/", "Safety notes", "Unplug before you move a range. Shut the gas off before you go past the published check."),
        ("/brands/whirlpool/", "Whirlpool hub", "Washer, dryer, dishwasher, and refrigerator codes, separate from this range list."),
    ], "Keep reading", "nr-end")
    compare = compare_box(
        "Check another oven",
        [
            ("/codes/whirlpool/oven/f2-e1/", "Whirlpool F2 E1, the grate check"),
            ("/codes/whirlpool/oven/f1-e1/", "Whirlpool F1 E1, the oven control"),
            ("/codes/ge/oven/", "GE Appliances oven codes"),
            ("/codes/samsung/oven/", "Samsung oven codes"),
            ("/appliances/ovens/", "All oven brands"),
            ("/brands/lg/", "LG brand hub"),
        ],
        "A Whirlpool range code does not transfer to a GE oven, a Samsung oven, or an LG appliance.",
    )
    body = f'''<article class="prose wide"><h1>Whirlpool oven F codes</h1>
{byline(TODAY5_H)}
{article_thumb(OVEN_THUMB, "Unbranded oven control panel in ordinary indoor light")}
<div class="answer"><p>On the range pages Whirlpool publishes, an F code is not one fault. The owner step on nearly every page is the same: turn the breaker off for 1 minute, turn it back on, and watch for 1 minute. What changes is the part the page names. <a href="/codes/whirlpool/oven/f1-e1/">F1 E1</a> names the oven control. <a href="/codes/whirlpool/oven/f2-e1/">F2 E1</a> first asks whether the cooktop grates sit level. <a href="#f3-e1">F3 E1</a> names the oven temperature sensor. If the code returns, Whirlpool says to schedule service.</p></div>
{SAFETY}
<h2>The reset, written once</h2>
<p>Whirlpool's wording on these pages is: power the unit down by turning off the circuit breaker for one minute, power it back up, monitor the oven for one minute so the code does not display again, and verify that the oven operates. That is a control reset, not a repair. Do not open the control, the keypad, a temperature sensor, a door latch, a fan, a bake or broil element, or any wiring. If the range burns gas, shut the gas supply off before any inspection past that reset. If you smell gas, leave and call the gas utility. The <a href="/guides/safety/">safety notes</a> cover the same stop point, including the anti-tip bracket before you pull a range out.</p>
{mid}
<h2>The letter does not tell you the part</h2>
<p>F1 is a family, not a meaning. F1 E1, F1 E0, F1 E2, F1 E5, F1-7, F1-9, F1-E, F3, and F6 all say there may be a problem with the oven control or the associated wiring. F1 E7 and F1 E9 name the appliance control board instead. F03 and F04 say electronic oven control. F06 says electronic control. F0 E0 says a component of the oven control system. Treat those as different sentences, because Whirlpool wrote them that way.</p>
<p>The sensor sentence is a different group, and it includes codes that do not start with F3. F01, F02, F1, F1-1, F1-2, F1-3, F1-H, F1-L, F2, F3-1, F3 E0, and F3 E1 all name the oven temperature sensor, the control, or the wiring. F3 E2 adds the warming drawer sensor on a range that has one. F3 E3 names the sensor or the wiring and does not mention the control. A reader who only remembers "F3 means the sensor" will misread F3, which is the control sentence, and will miss F1 and F2, which are the sensor sentence.</p>
<p><a href="/codes/ge/oven/">GE's oven page</a> does not match this map. GE's F0, F1, F6, and F7 share one meaning, a keypanel problem, and GE says the keypanel often needs to be replaced. GE's F3 and F4 name the oven sensor. GE's F2 means the oven temperature exceeded a preset threshold. <a href="/codes/samsung/oven/">Samsung</a> does not use this F list at all. Samsung's <a href="/codes/samsung/oven/c-24/">C-24</a> is a temperature that rises faster than normal, and Samsung says that is generally a blocked vent. Use the brand printed on the appliance. The <a href="/appliances/ovens/">oven hub</a> puts those three side by side. <a href="/brands/lg/">LG's other appliances</a> are a separate list. This site does not have an LG oven page.</p>
<h2>Two checks that are not only the breaker</h2>
<p><a href="/codes/whirlpool/oven/f2-e1/">F2 E1</a> is the grate page. When the range is cool, rock each grate corner to corner and side to side. If it wobbles, it may be installed backwards, so switch the grates, then cycle power. The same page still names the user interface or keypad, the control, or the wiring. F2 E0 and F2 E2 through F2 E6 name that keypad sentence and skip the grates. Do not rock a hot grate.</p>
<p><a href="#f3-e4">F3 E4</a> and <a href="#f8">F8</a> are the meat probe. Both pages say to verify the probe is securely inserted in the receptacle, and both say the location may vary. Then do the breaker reset. F8 is not the cooling fan. The fan codes are F7 E5, F7 E6, F8 E0, and F8 E2. F8 E0 says the cooling fan speed is too low and mentions an airflow restriction. F8 E2 says the speed is too high and does not mention a restriction. Neither page tells you to open the fan.</p>
<h2>Door, heat, and Wi-Fi</h2>
<p>Latch wording is not identical, so the table keeps it. F5 names the oven door latch assembly and the door latch switches. F5 E1, F5 E2, and F5 E3 say main oven door latch assembly and the door switch. F7 E1 names only the door switch. F7 E0 names the latch assembly and does not name the switch. F9-1, F9-2, F9-3, F1-A, and F1-C name the oven door latch and the door lock switch. None of those pages publish the button sequence on the <a href="/codes/ge/oven/loc-door/">GE Loc Door</a> page. Do not force a locked door.</p>
<p><a href="#f5-e5">F5 E5</a> says the oven has not reached self-clean temperature after 30 minutes, and that there may be a problem with the door hinges or the door gasket. The only owner step is still the breaker reset. Do not take the door off. <a href="#fee6">FEE6</a> names the main cavity bake element. <a href="#fee7">FEE7</a> names the broil element. <a href="#fee8">FEE8</a> publishes the reset and names no part, so do not borrow the bake or broil meaning.</p>
<p><a href="#fc-e1">FC E1</a> says the range could not connect to the router, and that there is no link between the Wi-Fi module and the router. The page adds a router reset: if another Wi-Fi device works at the range, disconnect router power for 2 minutes, reconnect it, then disconnect the range for 2 minutes and reconnect. If the signal there is weak, Whirlpool says you can move the router, use a compatible extender, or contact the internet provider. <a href="#fc-e7">FC E7</a> says the missing link is between the Wi-Fi module and the internet, and it tells you to start a cycle after the breaker reset. <a href="#fc-e8">FC E8</a> is a registration error: enter the SAID number again, and select the right appliance type and model. The other FC codes on Whirlpool's index were not opened on 21 Nov 2026 and are not in the table.</p>
{compare}
<h2>Every range page opened on 21 Nov 2026</h2>
<p>Full pages exist only for <a href="/codes/whirlpool/oven/f1-e1/">F1 E1</a> and <a href="/codes/whirlpool/oven/f2-e1/">F2 E1</a>. F1 E1 already had a URL here. F2 E1 is the code with a check the others do not share. The rest stay in this table. Publishing a separate page for each breaker reset would be the same article with the code swapped. Whirlpool's index also lists FBE1 and FBE2. Those two pages were not opened, so they are not given a meaning here.</p>
{whirlpool_oven_table(rows)}
{faq_html(faqs)}
{sources_html([index_src] + unique_sources(rows), f"Each linked page was opened {TODAY5_H}. Wall oven codes, FBE1, FBE2, and the FC codes missing from the table were not opened. {BRAND} is not affiliated with Whirlpool.")}
{end}
<p><a href="/brands/whirlpool/">All Whirlpool pages</a> · <a href="/appliances/ovens/">All oven brands</a> · <a href="/codes/ge/oven/">GE oven codes</a> · <a href="/codes/samsung/oven/">Samsung oven codes</a> · <a href="/guides/safety/">Safety notes</a></p>
</article>'''
    desc = "Whirlpool range F codes opened 21 Nov 2026. F1 E1 is the oven control. F2 E1 checks the grates. F3 E1 is the sensor."
    write(path, page(path, "Whirlpool Oven F Codes: What Each One Names", desc, body,
                    [article_ld("Whirlpool oven F codes", path, "Whirlpool oven", published=TODAY, modified=TODAY5), faq_ld(faqs)],
                    [("/", "Home"), ("/codes/", "Error codes"), (path, "Whirlpool oven")], lastmod=TODAY5))
    _wp_f1e1_page()
    _wp_f2e1_page()

def _wp_f1e1_page():
    path = "/codes/whirlpool/oven/f1-e1/"
    r = next(x for x in ROWS if x["brand"] == "whirlpool" and x["appl"] == "oven" and x["code"] == "F1 E1")
    faqs = [
        ("What does Whirlpool oven F1 E1 mean?",
         "Whirlpool's range page says there may be a problem with the oven control, or the associated wiring. The same sentence is on F1 E0, F1 E2, F1 E5, F1-7, F1-9, F1-E, F3, and F6."),
        ("What should I do for F1 E1?",
         "Turn the breaker off for 1 minute, turn it back on, watch for 1 minute, and confirm the oven operates. Unplug the appliance before you move it. If the code returns, schedule service. Do not open the control."),
        ("Is F1 E1 the temperature sensor?",
         "No. The sensor sentence is on F3 E1 and on several codes that do not look like F3, including F1 and F2. F1 E1 is the control sentence. F2 E1 is the grate check."),
    ]
    mid = _oven_reads([
        ("/codes/whirlpool/oven/f2-e1/", "Whirlpool F2 E1", "Check the grates while the range is cool, then reset power."),
        ("/codes/whirlpool/oven/#f3-e1", "Whirlpool F3 E1", "The sensor sentence, in the range table. It is not this page."),
        ("/codes/ge/oven/", "GE F0 and F1", "GE groups F0 and F1 as a keypanel fault and often a keypanel replacement."),
        ("/codes/samsung/oven/c-f0/", "Samsung C-F0", "A communication error, with a firmware note on three induction model families."),
    ], "Codes people mix up with F1 E1", "nr-mid")
    end = _oven_reads([
        ("/codes/whirlpool/oven/", "All Whirlpool range F codes", "The table of every range page opened 21 Nov 2026, including the ones that share this sentence."),
        ("/appliances/ovens/", "Oven codes by brand", "Whirlpool, GE, and Samsung do not share an F-code dictionary."),
        ("/guides/safety/", "Safety notes", "Shut the gas off before you go past a published reset on a gas range."),
        ("/brands/whirlpool/", "Whirlpool hub", "The washer drain codes are a different article."),
    ], "Keep reading", "nr-end")
    compare = compare_box(
        "Check a different code",
        [
            ("/codes/whirlpool/oven/f2-e1/", "F2 E1, grates then keypad"),
            ("/codes/whirlpool/oven/#f3-e1", "F3 E1, temperature sensor"),
            ("/codes/whirlpool/oven/#f1-e7", "F1 E7, appliance control board"),
            ("/codes/ge/oven/", "GE oven codes"),
            ("/codes/samsung/oven/", "Samsung oven codes"),
        ],
        "Same brand, different part. Then a different brand entirely, if the name on the oven is not Whirlpool.",
    )
    body = f'''<article class="prose wide"><h1>Whirlpool oven code F1 E1</h1>
{byline(TODAY5_H)}
{article_thumb(OVEN_THUMB, "Unbranded oven control panel in ordinary indoor light")}
<div class="answer"><p><strong>Meaning:</strong> Whirlpool's range page says there may be a problem with the oven control, or the associated wiring. Reset the breaker for 1 minute. If F1 E1 returns, schedule service. This is not the temperature sensor, and it is not the grate check.</p></div>
{SAFETY}
<h2>The check Whirlpool publishes</h2>
<ul class="checks"><li>Turn the circuit breaker off for 1 minute, then turn it back on.</li>
<li>Watch for 1 minute. Confirm F1 E1 stays off, then confirm the oven operates.</li></ul>
<p>That is the whole owner procedure on the F1 E1 page. Whirlpool then says to schedule service. Do not open the control or the wiring to see which one it is. On a gas range, shut the gas supply off before any inspection past this reset. The same control sentence, checked the same day, is on F1 E0, F1 E2, F1 E5, F1-7, F1-9, F1-E, bare F3, and bare F6. Those stay on the <a href="/codes/whirlpool/oven/">range table</a> rather than as copies of this page. F1 E7 and F1 E9 are close but not the same: they name the appliance control board.</p>
{mid}
<h2>Codes that look related and are not</h2>
<p><a href="/codes/whirlpool/oven/f2-e1/">F2 E1</a> starts with the cooktop grates, and only then names the keypad, the control, or the wiring. <a href="/codes/whirlpool/oven/#f3-e1">F3 E1</a> names the oven temperature sensor, the control, or the wiring. So does bare F1, which is easy to confuse with F1 E1 if the display is hard to read. Write down the full code before you pick a row. <a href="/codes/ge/oven/">GE</a> uses F1 for the keypanel, often as a replacement, after a 1 to 2 minute breaker reset. <a href="/codes/samsung/oven/c-f0/">Samsung C-F0</a> is a communication error, and on three induction model families Samsung publishes a SmartThings firmware update. None of those steps are on Whirlpool's F1 E1 page.</p>
{compare}
<h2>When to call a technician</h2>
<p>{E(r["service"])}</p>
{faq_html(faqs)}
{sources_html(r["sources"] + [("Whirlpool Product Help: range codes that start with F", "https://producthelp.whirlpool.com/Cooking/Wall_Ovens_and_Ranges/Ranges/Error_Codes/Starts_with_F")], f"F1 E1 and the sibling control pages were opened {TODAY5_H}. GE oven pages were last read {TODAY2_H}. Samsung C-F0 was last read {TODAY_H}. {BRAND} is not affiliated with Whirlpool.")}
{end}
<p><a href="/codes/whirlpool/oven/">All Whirlpool oven F codes</a> · <a href="/appliances/ovens/">Oven brands</a> · <a href="/brands/whirlpool/">Whirlpool</a> · <a href="/guides/safety/">Safety notes</a></p>
</article>'''
    desc = "Whirlpool range F1 E1 is the oven control or its wiring. Breaker off for 1 minute. Not the sensor and not the grates."
    ld = article_ld("Whirlpool oven code F1 E1", path, "Whirlpool F1 E1", published=TODAY, modified=TODAY5)
    if OVEN_THUMB:
        ld["image"] = url(OVEN_THUMB)
    write(path, page(path, "Whirlpool F1 E1: Oven Control, Not the Sensor", desc, body, [ld, faq_ld(faqs)],
                    [("/", "Home"), ("/codes/", "Error codes"), ("/codes/whirlpool/oven/", "Whirlpool oven"), (path, "F1 E1")], lastmod=TODAY5))

def _wp_f2e1_page():
    path = "/codes/whirlpool/oven/f2-e1/"
    r = next(x for x in ROWS if x["brand"] == "whirlpool" and x["appl"] == "oven" and x["code"] == "F2 E1")
    faqs = [
        ("What does Whirlpool oven F2 E1 mean?",
         "Whirlpool asks first whether the cooktop grates are installed properly and level. If a cool grate wobbles, it may be in backwards. The same page then says there may be a problem with the user interface or keypad, the control, or the wiring."),
        ("What should I check before I call for F2 E1?",
         "With the range cool, rock each grate corner to corner and side to side. Switch any grate that wobbles, then turn the breaker off for 1 minute and back on. Watch for 1 minute. Unplug the appliance before you move the range."),
        ("Is Whirlpool F2 E1 the same as GE F2?",
         "No. GE's F2 page says the oven temperature exceeded a preset threshold, and the owner step there is a breaker reset. GE does not mention the grates."),
    ]
    mid = _oven_reads([
        ("/codes/whirlpool/oven/f1-e1/", "Whirlpool F1 E1", "Oven control or wiring, with no grate check."),
        ("/codes/whirlpool/oven/#f2-e0", "Whirlpool F2 E0", "The keypad sentence without the grate step. It lives in the range table."),
        ("/codes/ge/oven/", "GE oven F2", "GE's F2 is an over-temperature code, not a grate code."),
        ("/codes/samsung/oven/door/", "Samsung door code", "A different oven, and a plunger check rather than cooktop grates."),
    ], "What to open if F2 E1 is not your code", "nr-mid")
    end = _oven_reads([
        ("/codes/whirlpool/oven/", "Whirlpool range F-code table", "Every range page opened 21 Nov 2026, with the part each one names."),
        ("/appliances/ovens/", "Oven codes by brand", "Start here if the brand on the oven is not Whirlpool."),
        ("/guides/safety/", "Safety notes", "Do not work over a hot grate. Shut the gas off past the published checks."),
        ("/codes/samsung/oven/", "Samsung oven codes", "C-24, the door plunger, and the other Samsung range codes on this site."),
    ], "Keep reading", "nr-end")
    compare = compare_box(
        "Check another code",
        [
            ("/codes/whirlpool/oven/f1-e1/", "Whirlpool F1 E1, oven control"),
            ("/codes/whirlpool/oven/#f2-e0", "Whirlpool F2 E0, keypad only"),
            ("/codes/whirlpool/oven/#f8", "Whirlpool F8, meat probe"),
            ("/codes/ge/oven/", "GE oven codes"),
            ("/appliances/ovens/", "All oven brands"),
        ],
        "F2 E1 is the grate page. The keypad-only F2 codes and the other brands are separate.",
    )
    body = f'''<article class="prose wide"><h1>Whirlpool oven code F2 E1</h1>
{byline(TODAY5_H)}
{article_thumb(OVEN_THUMB, "Unbranded oven control panel in ordinary indoor light")}
<div class="answer"><p><strong>Meaning:</strong> Whirlpool's first question is whether the cooktop grates are installed properly and sit level. A grate that wobbles, checked only when the range is cool, may be in backwards. If the code remains after you switch the grates and reset power, the same page names the user interface or keypad, the control, or the wiring, and says to schedule service.</p></div>
{SAFETY}
<h2>The grate check, then the reset</h2>
<ul class="checks">
<li>Wait until the range is cool. Do not rock a hot grate.</li>
<li>Rock each grate corner to corner and side to side. If it wobbles, Whirlpool says it may be installed backwards. Switch the grates so they sit level.</li>
<li>Cycle power: breaker off for 1 minute, then on. Watch for 1 minute and confirm the oven operates.</li>
</ul>
<p>F2 E0, F2 E2, F2 E3, F2 E4, F2 E5, and F2 E6 use the keypad sentence and do not ask about the grates. Those rows are on the <a href="/codes/whirlpool/oven/">range table</a>. Bare F2 is a different page again: it names the oven temperature sensor, the control, or the wiring. Read the full display. F2 and F2 E1 are not the same code.</p>
{mid}
<h2>What this is not</h2>
<p><a href="/codes/whirlpool/oven/f1-e1/">F1 E1</a> skips the grates and names the oven control. <a href="/codes/ge/oven/">GE's F2</a> says the oven temperature exceeded a preset threshold. The GE page's owner step is a 1 to 2 minute breaker reset, with service if it returns. It does not mention grates. <a href="/codes/samsung/oven/door/">Samsung's door code</a> is a plunger at the door, about three quarters of an inch when the door is open. Cooktop grates do not clear a Samsung door code, and a Samsung plunger check does not clear Whirlpool F2 E1.</p>
{compare}
<h2>When to call a technician</h2>
<p>{E(r["service"])}</p>
{faq_html(faqs)}
{sources_html(r["sources"] + [("Whirlpool Product Help: range codes that start with F", "https://producthelp.whirlpool.com/Cooking/Wall_Ovens_and_Ranges/Ranges/Error_Codes/Starts_with_F"), ("GE Appliances: range and wall oven error codes", "https://products.geappliances.com/appliance/gea-support-search-content?contentId=16238")], f"Whirlpool F2 E1 was opened {TODAY5_H}. The GE oven page was last read {TODAY2_H}. {BRAND} is not affiliated with Whirlpool.")}
{end}
<p><a href="/codes/whirlpool/oven/">All Whirlpool oven F codes</a> · <a href="/appliances/ovens/">Oven brands</a> · <a href="/codes/ge/oven/">GE oven codes</a> · <a href="/guides/safety/">Safety notes</a></p>
</article>'''
    desc = "Whirlpool range F2 E1: level the cool grates, then reset the breaker for 1 minute. The keypad is the next line on Whirlpool's page."
    ld = article_ld("Whirlpool oven code F2 E1", path, "Whirlpool F2 E1", published=TODAY5, modified=TODAY5)
    if OVEN_THUMB:
        ld["image"] = url(OVEN_THUMB)
    write(path, page(path, "Whirlpool F2 E1: Check the Grates First", desc, body, [ld, faq_ld(faqs)],
                    [("/", "Home"), ("/codes/", "Error codes"), ("/codes/whirlpool/oven/", "Whirlpool oven"), (path, "F2 E1")], lastmod=TODAY5))

def bosch_dishwasher_page():
    """21 Nov 2026 reread of Bosch's dishwasher code page. E22 gained drain steps."""
    path = "/codes/bosch/dishwasher/"
    rows = [r for r in ROWS if r["brand"] == "bosch" and r["appl"] == "dishwasher"]
    faqs = [
        ("What changed on the Bosch dishwasher page?",
         "On 21 Nov 2026 the E22 entry still starts with a blocked filter, and it also lists a blocked or loose drain pump cover, a kinked drain pump hose, and a clogged air gap or drain hose. E15, E16, E17, E18, E09, E12, and E14 still match the earlier reading."),
        ("What does Bosch E22 mean?",
         "The filter is blocked. Wash it under running water with mild soap and a soft brush and put it back. If the pump cover is loose or the pump is blocked, clear debris and click the cover shut. Straighten the drain pump hose. Then check the air gap and the drain hose."),
        ("What does Bosch E15 mean?",
         "The safety switch has detected water in the base, and leak protection has activated. Turn off the water inflow and contact Bosch. Do not keep using the dishwasher."),
    ]
    mid = next_reads([
        ("/codes/bosch/dishwasher/e22/", "Bosch E22", "Filter, drain pump cover, hose, and air gap. The individual page now carries the 21 Nov steps.", None),
        ("/codes/bosch/dishwasher/e15/", "Bosch E15", "Water in the base. Turn the inflow off and contact Bosch.", None),
        ("/codes/bosch/dishwasher/#e18", "Bosch E18", "Low water or poor pumping. Bosch states a 10 liter a minute supply.", None),
        ("/codes/kitchenaid/dishwasher/", "KitchenAid dishwasher codes", "F9E1 is a long drain. A different maker, and a different list.", None),
    ], "Dishwasher codes to open next", "nr-mid")
    end = next_reads([
        ("/codes/whirlpool/dishwasher/", "Whirlpool dishwasher codes", "A separate brand. Do not copy a Bosch step onto a Whirlpool display.", None),
        ("/appliances/dishwashers/", "Dishwasher codes by brand", "Samsung, LG, GE, Bosch, KitchenAid, and Whirlpool hubs.", None),
        ("/guides/safety/", "Safety notes", "Unplug before you move the dishwasher. Shut the water off on a leak code.", None),
        ("/brands/bosch/", "Bosch hub", "Washer codes are the other Bosch list on this site.", None),
    ], "Keep reading", "nr-end")
    compare = compare_box(
        "Check another dishwasher",
        [
            ("/codes/bosch/dishwasher/e22/", "Bosch E22"),
            ("/codes/bosch/dishwasher/e15/", "Bosch E15"),
            ("/codes/bosch/dishwasher/e16/", "Bosch E16 and E17"),
            ("/codes/kitchenaid/dishwasher/", "KitchenAid dishwasher codes"),
            ("/codes/samsung/dishwasher/", "Samsung dishwasher codes"),
            ("/appliances/dishwashers/", "All dishwasher brands"),
        ],
        "Stay with the brand on the door. E22 on this page is Bosch's wording.",
    )
    bits = []
    for r in rows:
        alias = f" Also listed as {', '.join(r['aliases'])}." if r["aliases"] else ""
        more = f' <a href="{code_path(r)}">Full page for {E(r["code"])}</a>.' if r["individual"] else ""
        bits.append(f'<h3 id="{r["slug"]}">{E(r["code"])}</h3><p>{E(r["meaning"])}{E(alias)} {" ".join(E(c) for c in r["checks"])} {E(r["service"])}{more}</p>')
    body = f'''<article class="prose wide"><h1>Bosch dishwasher error codes</h1>
{byline(TODAY5_H)}
<div class="answer"><p>Bosch's dishwasher code page was opened again on 21 Nov 2026. The change that matters is <a href="#e22">E22</a>. It still means a blocked filter, and the same entry now walks through the drain pump cover, the drain pump hose, and the air gap or drain hose. <a href="#e15">E15</a> is still water in the base: turn the inflow off and contact Bosch. The other codes already on this page still match.</p></div>
{SAFETY}
<h2>E22, reread 21 Nov 2026</h2>
<p>Bosch says the filter is where food particles collect and that it needs regular cleaning. Remove it, wash it under running water with mild soap and a soft brush, and reinstall it. Bosch links a longer filter article and a video. Those were not opened, so the steps above are the ones on the code page itself.</p>
<p>The same E22 entry then says the drain pump may be blocked or the cover loose. Remove the cover, clear standing water and loose debris, and replace the cover so it clicks. Check the drain pump hose for a kink or a sharp bend. For the air gap or the drain hose, turn the dishwasher off, check the air gap, disconnect the hose into a bucket, clear debris, reconnect it, and start a rinse. If E22 remains, Bosch points to a separate reset article. That article was not opened on 21 Nov 2026, so its steps are not copied here. Contact Bosch if the code is still there. Details also sit on the <a href="/codes/bosch/dishwasher/e22/">E22 page</a>.</p>
<p>Bosch gives <a href="#e24">E24</a> and E25, which this site does not publish as their own pages, the pump, hose, and air gap steps without the filter wash. E23 says the drain pump is blocked, clogged, or faulty, and it does not add those steps. Use the code on your display. Do not treat every drain code as E22.</p>
{mid}
<h2>The codes that still match</h2>
<p><a href="/codes/bosch/dishwasher/e15/">E15</a> means the safety switch detected water in the base and leak protection has activated. Turn off the water inflow and contact Bosch. Do not keep the dishwasher running. <a href="#e16">E16 and E17</a> mean water is not entering, or the filling system has a problem. Check that the inlet hose is not kinked or damaged, then contact Bosch. <a href="#e18">E18</a> is the flow into the dishwasher: the level is too low, or water is not being pumped correctly. Bosch says to check the inlet hose and to confirm the supply is on, and it states a flow of 10 liters a minute. <a href="#e09">E09</a> is a heat pump internal heater fault. The published step is a 30 second breaker reset, then support. Do not open the heater. <a href="#e12">E12</a> is limescale in the heat pump. Bosch says to descale, and to use softening salt if the dishwasher has a softener. <a href="#e14">E14</a> names a flow meter failure or a fill problem and does not add an owner procedure.</p>
{"".join(bits)}
{compare}
<p>E24 and E25 are mentioned above because the 21 Nov reread showed they share the drain steps. They are not separate pages here. A KitchenAid drain code such as the ones on the <a href="/codes/kitchenaid/dishwasher/">KitchenAid dishwasher hub</a>, or a Whirlpool dishwasher code, is a different manufacturer page. The <a href="/appliances/dishwashers/">dishwasher hub</a> is the brand list. Unplug the dishwasher before you pull it out. Shut the water off if water is reaching the floor. The <a href="/guides/safety/">safety notes</a> say the same thing.</p>
{faq_html(faqs)}
{sources_html(unique_sources(rows), f"Bosch's dishwasher error code page was opened {TODAY5_H}. The filter-cleaning article, the how-to video, and the separate reset article linked from that page were not opened, so their steps are not copied. {BRAND} is not affiliated with Bosch.")}
{end}
<p><a href="/brands/bosch/">All Bosch pages</a> · <a href="/appliances/dishwashers/">All dishwasher brands</a> · <a href="/guides/safety/">Safety notes</a></p>
</article>'''
    # The hand-written sections already explain E24. Drop the empty anchor promise if we never emit id e24.
    body = body.replace('<a href="#e24">E24</a>', "E24")
    desc = "Bosch dishwasher codes reread 21 Nov 2026. E22 adds the drain pump, hose, and air gap. E15 still means water in the base."
    write(path, page(path, "Bosch Dishwasher Codes, Reread for E22", desc, body,
                    [article_ld("Bosch dishwasher error codes", path, "Bosch dishwasher", published=TODAY, modified=TODAY5), faq_ld(faqs)],
                    [("/", "Home"), ("/codes/", "Error codes"), (path, "Bosch dishwasher")], lastmod=TODAY5))

def oven_appliance_page():
    """Comparison hub. Whirlpool rows are from 21 Nov 2026. GE and Samsung dates stay on their pages."""
    path = "/appliances/ovens/"
    faqs = [
        ("Which oven brand should I open?",
         "Open the brand printed on the oven. Whirlpool F1 E1 names the oven control. GE's F1 names the keypanel. Samsung does not use that F list."),
        ("Does F2 mean the same thing on Whirlpool and GE?",
         "No. Whirlpool F2 E1 starts with the cooktop grates. GE's F2 page says the oven temperature exceeded a preset threshold. Samsung's fast temperature code is C-24, and Samsung says it is generally a blocked vent."),
        ("Which checks are safe on an oven?",
         "Only the checks on that brand's page. Unplug the appliance or switch off the breaker before you move it. Shut the gas off before any step the manufacturer did not publish."),
    ]
    mid = _oven_reads([
        ("/codes/whirlpool/oven/", "Whirlpool range F codes", "Control, sensor, grates, latch, fan, and Wi-Fi, from the pages opened 21 Nov 2026."),
        ("/codes/ge/oven/", "GE oven codes", "Keypanel, sensor, over-temp, and the Loc Door reset. Last read 18 Nov 2026."),
        ("/codes/samsung/oven/", "Samsung oven codes", "C-24, the door plunger, bAd LinE, and the other codes last read 16 Nov 2026."),
        ("/codes/whirlpool/oven/f2-e1/", "Whirlpool F2 E1", "The grate check. Do not use it on a GE oven."),
    ], "Start with the brand on the oven", "nr-mid")
    end = _oven_reads([
        ("/codes/ge/oven/loc-door/", "GE Loc Door", "A flashing LOC DOOR with a reset that Whirlpool's latch pages do not publish."),
        ("/codes/samsung/oven/c-24/", "Samsung C-24", "Clear the vent. Opening and closing the door can clear it while cooking."),
        ("/guides/safety/", "Safety notes", "Gas shutoff, the anti-tip bracket, and when to stop."),
        ("/brands/lg/", "LG brand hub", "LG washer, dryer, dishwasher, and refrigerator codes. No LG oven page yet."),
    ], "Keep reading", "nr-end")
    compare = compare_box(
        "Check another oven",
        [
            ("/codes/whirlpool/oven/", "Whirlpool range F codes"),
            ("/codes/ge/oven/", "GE Appliances oven codes"),
            ("/codes/samsung/oven/", "Samsung oven codes"),
            ("/brands/lg/", "LG brand hub"),
            ("/codes/", "All error codes"),
        ],
        "Pick the name on the appliance. These three lists were not written as one code set.",
    )
    cards = []
    for slug, name in BRANDS:
        rows = [r for r in ROWS if r["brand"] == slug and r["appl"] == "oven"]
        if not rows:
            continue
        preview = ", ".join(r["code"] for r in rows[:6])
        cards.append(f'<li class="card"><h2><a href="{listing_path(slug, "oven")}">{E(name)} oven codes</a></h2><p>{E(preview)}</p></li>')
    sources = [
        ("Whirlpool Product Help: range codes that start with F", "https://producthelp.whirlpool.com/Cooking/Wall_Ovens_and_Ranges/Ranges/Error_Codes/Starts_with_F"),
        ("GE Appliances: range and wall oven error codes", "https://products.geappliances.com/appliance/gea-support-search-content?contentId=16238"),
        ("Samsung US support: range and wall oven error codes", "https://www.samsung.com/us/support/troubleshoot/TSG10003529/"),
    ]
    body = f'''<article class="prose"><h1>Oven error codes by brand</h1>
{byline(TODAY5_H)}
{article_thumb(OVEN_THUMB, "Unbranded oven control panel in ordinary indoor light")}
<p class="answer">The letters do not travel. <a href="/codes/whirlpool/oven/f1-e1/">Whirlpool F1 E1</a> names the oven control or its wiring. GE's F0, F1, F6, and F7 page names the keypanel, and GE says it often needs to be replaced. Samsung does not publish that F list. Start with the name on the oven, then the code.</p>
<h2>Three F-looking codes that are not the same fault</h2>
<p>Whirlpool's range pages were opened {TODAY5_H}. <a href="/codes/whirlpool/oven/f2-e1/">F2 E1</a> asks whether the cooktop grates sit level, and only then names the keypad or the control. GE's F2, on the page last read {TODAY2_H}, says the oven temperature exceeded a preset threshold. The GE owner step is a breaker reset of 1 to 2 minutes, then service if it returns. Samsung's <a href="/codes/samsung/oven/c-24/">C-24</a>, last read {TODAY_H}, is a temperature that rises faster than normal. Samsung says that is generally a blocked vent on the back of the cooktop, and that you can clear it while cooking by opening and closing the door a few times.</p>
<p>The sensor words diverge the same way. Whirlpool <a href="/codes/whirlpool/oven/#f3-e1">F3 E1</a> names the oven temperature sensor, the control, or the wiring, and so do F1 and F2, which do not look like sensor codes. GE's F3 and F4 share one line: the oven sensor usually needs to be replaced. A Whirlpool reset does not become a GE parts instruction, and a GE keypanel note does not become a Whirlpool repair.</p>
{mid}
<h2>Door displays</h2>
<p>Whirlpool's F5, F9-1, and F7 E1 pages name a latch or a door switch and then give the 1 minute breaker reset. They do not publish the motorized-switch steps on <a href="/codes/ge/oven/loc-door/">GE Loc Door</a>. Samsung's <a href="/codes/samsung/oven/door/">door code</a> is the round black plunger, which should stick out about three quarters of an inch when the door is open. Use the page that matches the brand. Do not force a door that is locked after self-clean.</p>
{compare}
<h2>Brand pages</h2>
<ul class="cards">{"".join(cards)}</ul>
<p>Whirlpool's table is the long one, because Whirlpool publishes a page per code and most of those pages share the breaker reset. GE and Samsung already had hubs. There is no LG oven page on this site yet. <a href="/brands/lg/">LG's brand hub</a> covers the washer, dryer, dishwasher, and refrigerator codes we have checked. If the code is missing, it is missing because that maker's page was not the source. Unplug the appliance before you move it. Shut the gas off before any step the cited page does not list. The <a href="/guides/safety/">safety notes</a> include the anti-tip bracket.</p>
{faq_html(faqs)}
{sources_html(sources, f"Whirlpool range index opened {TODAY5_H}. GE oven page last read {TODAY2_H}. Samsung oven page last read {TODAY_H}. Those earlier pages were not rewritten today. {BRAND} is not affiliated with these makers.")}
{end}
<p><a href="/appliances/">All appliance types</a> · <a href="/codes/">All error codes</a> · <a href="/codes/whirlpool/oven/">Whirlpool F codes</a></p>
</article>'''
    desc = "Oven codes by brand. Whirlpool F1 E1 is the control, F2 E1 checks the grates, and GE F2 is an over-temperature code."
    ld = article_ld("Oven error codes", path, "Oven", published=TODAY, modified=TODAY5)
    if OVEN_THUMB:
        ld["image"] = url(OVEN_THUMB)
    write(path, page(path, "Oven Codes: Whirlpool F2 E1 Is Not GE F2", desc, body, [ld, faq_ld(faqs)],
                    [("/", "Home"), ("/appliances/", "Appliances"), (path, "Ovens")], lastmod=TODAY5))

def washer_appliance_page():
    """20 Nov 2026 refresh of /appliances/washers/. Other appliance hubs stay on their old dates."""
    path = "/appliances/washers/"
    an = "Washer"
    items = []
    for slug, name in BRANDS:
        rows = [r for r in ROWS if r["brand"] == slug and r["appl"] == "washer"]
        if not rows:
            continue
        preview = ", ".join(r["code"] for r in rows[:6])
        items.append(f'<li class="card"><h2><a href="{listing_path(slug, "washer")}">{E(name)} washer codes</a></h2><p>{E(preview)}</p></li>')
    faqs = [
        ("Which brand should I pick for a washer code?",
         "Use the brand name on the washer. Samsung 4C is a fill code, LG OE is a drain code, and Whirlpool F9 E1 is a long drain. The same letters on another brand are a different page."),
        ("Are Whirlpool F9 E1 and F21 the same drain problem?",
         "They are related, and Whirlpool publishes them on two pages. F9 E1 is a long drain, with the hose no more than 4.5 inches into the standpipe and a 96 inch maximum height on the front load page. F21, also shown as F02, is drain time longer than expected. That page adds HE detergent and a Pause/Cancel or 5 minute unplug. It does not repeat the 4.5 inch measurement."),
        ("Which checks are safe on a washer?",
         "Only the checks written on that brand's page. Unplug the washer or switch off the breaker before you move it or open a panel. Let hot drain water cool before you open a pump filter."),
    ]
    mid = next_reads([
        ("/codes/whirlpool/washer/f9-e1/", "Whirlpool washer F9 E1", "Long drain: 4.5 inch hose limit, air gap, and the 96 inch height on Whirlpool's front load page.", None),
        ("/codes/whirlpool/washer/f21/", "Whirlpool washer F21", "Drain time longer than expected. Pause/Cancel, then a 5 minute unplug, and HE detergent only.", None),
        ("/codes/samsung/washer/4c/", "Samsung washer 4C", "Water is not entering. Hose match, open valves, and the 6 to 8 inch drain-hose depth Samsung states.", None),
        ("/codes/lg/washer/oe/", "LG washer OE", "The washer cannot drain. LG's spin-only listening check comes before the pump filter.", None),
    ], "Washer codes to open next", hid="nr-mid")
    end = next_reads([
        ("/codes/ge/washer/ie/", "GE washer IE", "No water entering, plus the 4 minute control lock that unplugging restarts.", None),
        ("/codes/bosch/washer/e18/", "Bosch washer E18", "Blocked or kinked drain hose. Bosch warns the water can still be very hot.", None),
        ("/codes/maytag/washer/lf/", "Maytag washer LF", "Slow fill. Maytag says both the hot and the cold faucets have to be open.", None),
        ("/guides/safety/", "Safety notes", "Unplug before you move the washer or open a panel. Shut the gas off on a gas dryer or range.", None),
    ], "Keep reading", hid="nr-end")
    compare = compare_box(
        "Check another appliance",
        [
            ("/appliances/ovens/", "Oven and range codes"),
            ("/codes/ge/oven/", "GE Appliances oven codes"),
            ("/codes/samsung/oven/", "Samsung oven codes"),
            ("/codes/whirlpool/oven/", "Whirlpool oven F codes"),
            ("/brands/lg/", "LG brand hub"),
            ("/appliances/dishwashers/", "Dishwasher codes"),
        ],
        "A washer code does not transfer to an oven or a dishwasher. Open the machine you actually have.",
    )
    sources = [
        ("Whirlpool Product Help: washer F9 E1", "https://producthelp.whirlpool.com/Laundry/Washers/Front_Load_Washers/Error_Codes/%22F%22_Error_Codes/F9_E1_-_Front_Load_Washer"),
        ("Whirlpool Product Help: washer F21 and F02", "https://producthelp.whirlpool.com/Laundry/Washers/Product_Info/Washer_Product_Assistance/What_is_an_F21_or_F02_Error_Code_on_a_Front_Load_Washer"),
        ("Samsung US support: washing machine error codes", "https://www.samsung.com/us/support/troubleshoot/TSG10000997/"),
        ("LG US support: front load washer error code list", "https://www.lg.com/us/support/help-library/lg-front-load-washer-error-code-list--20155069413456"),
        ("GE Appliances: washer Consumer Help Indicator", "https://products.geappliances.com/appliance/gea-support-search-content?contentId=35949"),
        ("Maytag Product Help: top load HE washer error codes", "https://producthelp.maytag.com/Laundry/Washers/Product_Info/Washer_Product_Assistance/Error_Codes_in_Top_Load_HE_Washers"),
        ("Bosch US support: washer error codes", "https://www.bosch-home.com/us/en/c/spotlight/blt341dacb48f00c362/owner-support/error-codes/washers"),
    ]
    body = f'''<article class="prose"><h1>Washer error codes</h1>
{byline(TODAY4_H)}
<p class="answer">Pick the brand printed on the washer. The letters are not a shared code. On the pages we have checked, <a href="/codes/samsung/washer/4c/">Samsung 4C</a> means water is not entering, <a href="/codes/lg/washer/oe/">LG OE</a> means the washer cannot drain, and <a href="/codes/whirlpool/washer/f9-e1/">Whirlpool F9 E1</a> means the drain is taking too long.</p>
<h2>Rechecked 20 Nov 2026: Whirlpool drain codes</h2>
<p>Whirlpool's front load <a href="https://producthelp.whirlpool.com/Laundry/Washers/Front_Load_Washers/Error_Codes/%22F%22_Error_Codes/F9_E1_-_Front_Load_Washer" rel="nofollow noopener" target="_blank">F9 E1 page</a> still calls that code a long drain. The hose must not extend more than 4.5 inches (113 mm) into the standpipe or laundry tub, because drained water can siphon back. The maximum height on that page is 96 inches from the bottom of the washer. Do not tape the hose into the pipe. There has to be an air gap. On models that have one, the drain pump filter is behind the bottom dispenser drawer, and the door seal has small drain holes that clog. Some top load displays show the same alert as drn. The full checks are on the <a href="/codes/whirlpool/washer/f9-e1/">F9 E1 page</a>.</p>
<p>Whirlpool's <a href="https://producthelp.whirlpool.com/Laundry/Washers/Product_Info/Washer_Product_Assistance/What_is_an_F21_or_F02_Error_Code_on_a_Front_Load_Washer" rel="nofollow noopener" target="_blank">F21 and F02 page</a> is a second article in the same family: drain time longer than expected. Straighten a kinked or clogged hose, use only HE detergent, and press Pause/Cancel. If that does not clear it, unplug the washer for 5 minutes, plug it back in, reselect the cycle, and press Start. That page does not repeat the 4.5 inch measurement. If the code stays, Whirlpool says to call for service. Details are on the <a href="/codes/whirlpool/washer/f21/">F21 page</a>.</p>
{mid}
<h2>Fill, drain, and door codes are not interchangeable</h2>
<p>This table is only the codes already on this site. It is not a full list of every code each maker publishes. A blank cell means we have not put that kind of code up for that brand, not that the maker has none.</p>
<div class="tablewrap"><table class="list"><thead><tr><th>Brand</th><th>Fill or supply</th><th>Drain</th><th>Door or lid</th></tr></thead><tbody>
<tr><td>Samsung</td><td><a href="/codes/samsung/washer/4c/">4C</a></td><td><a href="/codes/samsung/washer/5e/">5E</a></td><td><a href="/codes/samsung/washer/de/">dE</a></td></tr>
<tr><td>LG</td><td><a href="/codes/lg/washer/ie/">IE</a></td><td><a href="/codes/lg/washer/oe/">OE</a></td><td><a href="/codes/lg/washer/de/">dE</a></td></tr>
<tr><td>GE Appliances</td><td><a href="/codes/ge/washer/ie/">IE</a></td><td>Not on this hub</td><td><a href="/codes/ge/washer/de/">dE</a></td></tr>
<tr><td>Whirlpool</td><td>Not on the two pages cited here</td><td><a href="/codes/whirlpool/washer/f9-e1/">F9 E1</a>, <a href="/codes/whirlpool/washer/f21/">F21</a></td><td>Not on those pages</td></tr>
<tr><td>Maytag</td><td><a href="/codes/maytag/washer/lf/">LF</a></td><td><a href="/codes/maytag/washer/#drn">drn</a></td><td><a href="/codes/maytag/washer/lid/">lid</a></td></tr>
<tr><td>Bosch</td><td><a href="/codes/bosch/washer/e17/">E17</a></td><td><a href="/codes/bosch/washer/e18/">E18</a></td><td><a href="/codes/bosch/washer/#e16">E16</a></td></tr>
</tbody></table></div>
<p><a href="/codes/lg/washer/oe/">LG OE</a> is the page that tells you to run a spin-only cycle and listen for the pump before you open the filter. <a href="/codes/ge/washer/ie/">GE IE</a> adds a timer the others do not: when the message starts, the washer locks the controls for 4 minutes, and unplugging starts that timer over. <a href="/codes/bosch/washer/e17/">Bosch E17</a> is a blocked inlet filter or low pressure, and Bosch says the AquaStop hose contains an electric valve, so do not immerse it. <a href="/codes/maytag/washer/lf/">Maytag LF</a> is a slow fill, and Maytag says both the hot and the cold faucets have to be open. <a href="/brands/lg/">LG's other appliances</a> use a different list again. An oven code, including the ones on the <a href="/appliances/ovens/">oven hub</a>, is not a washer code.</p>
{compare}
<h2>Brand pages</h2>
<ul class="cards">{"".join(items)}</ul>
<p>If the code on your display is not in that brand's list, it is missing because we have not read it on the maker's page. Do not borrow a meaning from the column above. Unplug the washer before you pull it out or open a panel. The <a href="/guides/safety/">safety notes</a> cover that, and they cover the gas shutoff for a dryer or a range.</p>
{faq_html(faqs)}
{sources_html(sources, f"Whirlpool F9 E1 and F21 pages reread {TODAY4_H}. Samsung, LG, GE Appliances, Maytag, and Bosch washer pages were last read {TODAY_H} and were not rewritten in this refresh. Which Error Code is not affiliated with these makers.")}
{end}
<p><a href="/appliances/">All appliance types</a> · <a href="/codes/">All error codes</a> · <a href="/codes/ge/oven/">GE oven codes</a> · <a href="/codes/samsung/oven/">Samsung oven codes</a> · <a href="/codes/whirlpool/oven/">Whirlpool oven F codes</a></p></article>'''
    desc = "Washer error codes by brand. Samsung 4C fills, LG OE drains, Whirlpool F9 E1 is a long drain. Whirlpool pages rechecked 20 Nov 2026."
    write(path, page(path, "Washer Error Codes by Brand", desc, body,
                    [article_ld("Washer error codes", path, an, published=TODAY, modified=TODAY5), faq_ld(faqs)],
                    [("/", "Home"), ("/appliances/", "Appliances"), (path, "Washers")], lastmod=TODAY5))

def appliance_pages():
    for appl, an, plural in APPLS:
        if appl == "washer":
            washer_appliance_page()
            continue
        if appl == "oven":
            oven_appliance_page()
            continue
        items = []
        for slug, name in BRANDS:
            rows = [r for r in ROWS if r["brand"] == slug and r["appl"] == appl]
            if not rows:
                continue
            preview = ", ".join(r["code"] for r in rows[:6])
            items.append(f'<li class="card"><h2><a href="{listing_path(slug, appl)}">{E(name)} {E(an.lower())} codes</a></h2><p>{E(preview)}</p></li>')
        faqs = [
            (f"Which brand should I pick for a {an.lower()} code?",
             f"Use the brand name on the appliance. The same letters can mean different things on another brand. This page links only brands whose {an.lower()} codes we have checked."),
            (f"Which checks are safe on a {an.lower()}?",
             "Only the checks written on that brand's page, taken from the manufacturer. Unplug the appliance or switch off the breaker before you move it or open a panel. If it uses gas, shut the gas supply off before any step the manufacturer did not publish."),
        ]
        related = '<p>A filter part number is not an error code. <a href="/filters/">Which water filter fits</a> is a separate page.</p>' if appl == "refrigerator" else ""
        # the oven listing gained a GE card on 18 Nov 2026; the other appliance pages are unchanged.
        dh, lm = (TODAY2_H, TODAY2) if appl == "oven" else (None, None)
        body = f'''<article class="prose"><h1>{E(an)} error codes</h1>
{byline(dh)}
<p class="answer">Brand pages for {E(an.lower())} codes we verified. The same letters can mean different things on another brand, so start with the name on the appliance.</p>
<ul class="cards">{"".join(items)}</ul>
{related}
{faq_html(faqs)}
<p><a href="/appliances/">All appliance types</a> · <a href="/codes/">All error codes</a> · <a href="/guides/safety/">Unplug and gas shutoff</a></p></article>'''
        path = f"/appliances/{plural}/"
        write(path, page(path, f"{an} Error Codes by Brand", f"{an} error codes for the brands we have checked, with the manufacturer's meaning and the safe checks.",
                        body, [article_ld(f"{an} error codes", path, an, modified=lm), faq_ld(faqs)],
                        [("/", "Home"), ("/appliances/", "Appliances"), (path, plural.capitalize())], lastmod=lm))
    cards = "".join(f'<li class="card"><h2><a href="/appliances/{p}/">{E(n)}s</a></h2><p>Codes for {E(n.lower())}s, brand by brand.</p></li>' for _, n, p in APPLS)
    # Wait, ANAME already includes the noun "Washer" and plural path is washers. Card title "Washers" from path. Fix: use plural from path capitalized properly.
    cards = []
    for _, n, p in APPLS:
        cards.append(f'<li class="card"><h2><a href="/appliances/{p}/">{E(p.capitalize())}</a></h2><p>Verified {E(n.lower())} codes by brand.</p></li>')
    faqs = [
        ("Which appliance type should I open?",
         "Open the type that matches the machine: washer, dryer, dishwasher, refrigerator, or oven. Then pick the brand printed on it."),
        ("Do the same letters mean the same thing on every brand?",
         "No. Start with the brand name on the appliance. A code page for one brand does not apply to another."),
    ]
    body = f'''<article class="prose"><h1>Error codes by appliance</h1>
{byline()}
<p class="answer">Washers, dryers, dishwashers, refrigerators, and ovens. Open a type, then the brand printed on the appliance.</p>
<ul class="cards">{"".join(cards)}</ul>
{faq_html(faqs)}
<p><a href="/brands/">By brand</a> · <a href="/codes/">All error codes</a> · <a href="/filters/">Water filters</a></p></article>'''
    write("/appliances/", page("/appliances/", f"Error Codes by Appliance | {BRAND}", "Washer, dryer, dishwasher, refrigerator, and oven error codes, sorted by appliance type.",
                              body, [article_ld("Error codes by appliance", "/appliances/"), faq_ld(faqs)],
                              [("/", "Home"), ("/appliances/", "Appliances")]))

def codes_index(search_json):
    rows = []
    for r in ROWS:
        if not r["individual"]:
            continue
        rows.append(f'<li><a href="{code_path(r)}">{E(BNAME[r["brand"]])} {E(ANAME[r["appl"]].lower())} {E(r["code"])}</a></li>')
    faqs = [
        ("Which error code page should I open?",
         "Open the brand, then the appliance. Single code pages are the codes people look up most often. Other verified codes are on the brand and appliance listing."),
        ("Which source is a code based on?",
         "Each code page links the manufacturer page it was read from. If the code is not on that page, it is not on this site."),
    ]
    # A Loc Door link was added here 18 Nov 2026, so this hub's retrieved/modified date moves.
    body = f'''<article class="prose wide"><h1>Appliance error code pages</h1>
{byline(TODAY5_H)}
<p class="answer">One page for each brand and appliance we have checked, plus a page for the codes people look up most often. Search from the <a href="/">home page</a>. The <a href="/codes/whirlpool/oven/">Whirlpool range F-code table</a> was opened {TODAY5_H}.</p>
<h2>By brand</h2><ul class="cols">{"".join(f'<li><a href="/brands/{s}/">{E(n)}</a></li>' for s, n in BRANDS)}</ul>
<h2>By appliance</h2><ul class="cols">{"".join(f'<li><a href="/appliances/{p}/">{E(p.capitalize())}</a></li>' for _, _, p in APPLS)}</ul>
<h2>Single codes</h2><ul class="cols">{"".join(rows)}</ul>
<p class="note">Each code page links the manufacturer page it was read from. GE oven pages were added {TODAY2_H}. Whirlpool range F codes were opened {TODAY5_H}.</p>
<section class="sources"><h2>Sources</h2><ul><li><a href="https://www.samsung.com/us/support/troubleshoot/TSG10000997/" rel="nofollow noopener" target="_blank">Samsung washer error codes</a></li><li><a href="https://www.lg.com/us/support/help-library/lg-front-load-washer-error-code-list--20155069413456" rel="nofollow noopener" target="_blank">LG washer error codes</a></li><li><a href="https://products.geappliances.com/appliance/gea-support-search-content?contentId=16912" rel="nofollow noopener" target="_blank">GE Appliances refrigerator fault codes</a></li></ul><p class="note">The full citation list is on each code page.</p></section>
{faq_html(faqs)}</article>'''
    write("/codes/", page("/codes/", f"Appliance Error Code List | {BRAND}", "Browse verified washer, dryer, dishwasher, refrigerator, and oven error codes by brand.",
                         body, [article_ld("Appliance error code pages", "/codes/", published=TODAY, modified=TODAY5), faq_ld(faqs)],
                         [("/", "Home"), ("/codes/", "Error codes")], lastmod=TODAY5))

def home(search_json):
    faqs = [
        ("Which error code should I look up?",
         "Use the code on the appliance display. Search on this page, or open the brand and then the appliance type. Every code page comes from the manufacturer's support page or manual."),
        ("Which water filter should I pick?",
         "Read the part number on the cartridge you take out and the model number in the manual, then open the filter finder. A model is listed only when the manufacturer lists it."),
        ("When should I stop and call a technician?",
         "Stop when the code returns, when the manufacturer says service is required, or when the check is not on the cited page. Unplug the appliance before you move it or open a panel."),
    ]
    brand_cards = []
    for slug, name in BRANDS:
        links = [f'<a href="{listing_path(slug, appl)}">{E(ANAME[appl])}</a>' for appl, _, _ in APPLS if any(r["brand"] == slug and r["appl"] == appl for r in ROWS)]
        brand_cards.append(f'<li class="card"><h3><a href="/brands/{slug}/">{E(name)}</a></h3><p>{", ".join(links)}</p></li>')
    body = f'''<section class="hero"><h1>Which error code is on your appliance?</h1>
<p class="answer">Look up a washer, dryer, dishwasher, refrigerator, or oven code. Every code on this site comes from the manufacturer's support page or manual, with the safe checks that page allows and a clear point to stop and call a technician.</p>
<form class="search" role="search" action="/" method="get"><label for="code-search">Search a code</label>
<input id="code-search" name="code" type="search" inputmode="text" autocomplete="off" placeholder="Try 4C, OE, F9 E1, E15" enterkeyhint="search">
<ul id="code-results"></ul></form>
<script type="application/json" id="code-index">{search_json}</script>
<p class="btnrow"><a class="btn" href="/codes/">Browse all codes</a> <a class="btn alt" href="/filters/">Find a fridge water filter</a></p></section>
{SAFETY}
<h2>Brands</h2><ul class="cards">{"".join(brand_cards)}</ul>
<h2>Appliance types</h2><ul class="cols">{"".join(f'<li><a href="/appliances/{p}/">{E(p.capitalize())}</a></li>' for _, _, p in APPLS)}</ul>
<h2>Refrigerator water filters</h2><p>The filter pages list the official part number, the substitute the manufacturer names, and the brands or notes on that official page. We do not copy compatibility charts from other sites. <a href="/filters/">Open the filter finder</a>.</p>
<h2>How a page is built</h2><p>We open the manufacturer page, record the code and the checks written there, and link that page. If a code is not on the page, it is not here. Names are plain text. There are no logos and no claim that a brand sponsors this site. <a href="/methodology/">Sources and methods</a>.</p>
{faq_html(faqs)}'''
    desc = "Look up washer, dryer, dishwasher, refrigerator, and oven error codes, plus the official fridge water filter number. Cited to the manufacturer."
    # Search index gained the 21 Nov 2026 Whirlpool range codes, so this page's lastmod moves.
    write("/", page("/", f"{BRAND}: Appliance Error Codes and Water Filters", desc, body, faq_ld(faqs), lastmod=TODAY5))

def filter_pages():
    by = {f["slug"]: f for f in FILTERS}
    for f in FILTERS:
        path = f"/filters/{f['slug']}/"
        sib = "".join(f'<li><a href="/filters/{s}/">{E(by[s]["sku"])}</a></li>' for s in f["siblings"] if s in by)
        err = f'<p><a href="{listing_path(f["error_brand"], "refrigerator")}">{E(BNAME[f["error_brand"]])} refrigerator error codes</a></p>' if any(r["brand"] == f["error_brand"] and r["appl"] == "refrigerator" for r in ROWS) else ""
        faqs = [
            (f"Which filter is {f['sku']}?", f["lead"]),
            (f"Which refrigerators take {f['sku']}?", f["models"]),
            (f"How do I reset the filter light after installing {f['sku']}?", f["reset"]),
        ]
        body = f'''<article class="prose wide"><h1>{E(f["name"])}</h1>
{byline()}
<div class="answer"><p>{E(f["lead"])}</p><p>{E(f["substitute"])}</p></div>
{SAFETY}
<h2>Official details</h2>
<div class="tablewrap"><table class="stats"><tbody>
<tr><th scope="row">Official part number</th><td>{E(f["sku"])}</td></tr>
<tr><th scope="row">Official substitute</th><td>{E(f["substitute"])}</td></tr>
<tr><th scope="row">Refrigerators the manufacturer lists</th><td>{E(f["models"])}</td></tr>
<tr><th scope="row">Replace</th><td>{E(f["interval"])}</td></tr>
<tr><th scope="row">Last verified</th><td>{TODAY_H}</td></tr>
</tbody></table></div>
<h2>How to find the model number</h2>
<p>Use the model number the manufacturer asks for on its filter finder, and the part number printed on the cartridge you take out. The pages we checked do not share one sentence that locates the label on every refrigerator. If the manual says the label is inside the fridge or on the door frame, follow that wording for your model. Confirm the part on the old filter and in the manual before you buy. This is a guide, not a repair service. Filters sold as compatible are not listed here unless the manufacturer itself says they are approved.</p>
<h2>Filter light</h2><p>{E(f["reset"])}</p>
<p>{E(f["extra"])}</p>
{err}
{faq_html(faqs)}
{sources_html(f["sources"], f"Retrieved {TODAY_H}. {BRAND} is not affiliated with {E(f['brand'])}.")}
<h2>Other filters on this site</h2><ul>{sib}</ul>
<p><a href="/filters/">All filters</a> · <a href="/filters/reset-filter-light/">Filter light reset</a></p>
</article>'''
        desc = clip(f"{f['sku']} water filter: the official part, the substitute the manufacturer names, and how to confirm it fits.")
        write(path, page(path, f"{f['sku']} Water Filter: Which Fridges", desc, body,
                        [article_ld(f"{f['sku']} refrigerator water filter", path, f["sku"]), faq_ld(faqs)],
                        [("/", "Home"), ("/filters/", "Water filters"), (path, f["sku"])]))
    # hub
    cards = "".join(f'<li class="card"><h2><a href="/filters/{f["slug"]}/">{E(f["sku"])}</a></h2><p>{E(f["name"])}</p></li>' for f in FILTERS)
    faqs = [
        ("How do I find the right refrigerator water filter?", "Read the part number on the cartridge you remove, and the model number the manufacturer asks for. Then open that manufacturer's filter page. A chart on another website is not a source we use."),
        ("Where is the model number?", "The official filter pages ask you to enter the model. They do not all describe the same label location. Use the wording in your manual, which is often on a label inside the refrigerator or on the door frame."),
        ("Do you list compatible aftermarket filters?", "No. A third party filter is listed only if the manufacturer itself says it is approved. None of the pages in this version do that."),
    ]
    body = f'''<article class="prose wide"><h1>Which water filter fits this refrigerator?</h1>
{byline()}
<p class="answer">Start with the part number on the filter you take out, and the refrigerator model number. The cards below are official cartridges we verified. A model page is published only when the manufacturer lists that model.</p>
{SAFETY}
<h2>Verified cartridges</h2><ul class="cards">{cards}</ul>
<h2>Find the model number and the part number</h2>
<p>Take the old cartridge out and read the number printed on it. Then find the refrigerator model. Whirlpool, KitchenAid, and GE Appliances each ask for that model on their filter pages. We do not invent a location. If your manual says the label is inside the fresh food compartment or on the door frame, use that spot for your model and ignore a guess from a different brand.</p>
<p>These model pages are not in this version, because the official page we opened did not list that exact model: Whirlpool WRF535SWHZ, GE GSS25GSHSS, Samsung RF28R7351SR, LG LFXS26973S, Frigidaire FG4H2272UF, and KitchenAid KRFC302ESS. The same gap covers EDR2RXD1, EDR3RXD1, EDR4RXD1, HAF-CIN, HAF-QIN, LT1000P, LT800P, and EPTWFU01 until their current official pages are checked line by line.</p>
<p><a href="/filters/reset-filter-light/">Filter light reset, official steps only</a> · <a href="/appliances/refrigerators/">Refrigerator error codes</a></p>
{faq_html(faqs)}
{sources_html([
    ("Whirlpool water filters", "https://www.whirlpool.com/kitchen/refrigeration/water-filters.html"),
    ("KitchenAid refrigerator water filters", "https://www.kitchenaid.com/major-appliances/water-filters.html"),
    ("GE Appliances SmartWater filters", "https://products.geappliances.com/appliance/gea-support-search-content?contentId=16933"),
], f"Retrieved {TODAY_H}. Confirm the part on the old filter and in the manual. This is a guide, not a repair service.")}
</article>'''
    write("/filters/", page("/filters/", f"Refrigerator Water Filter Finder | {BRAND}", "Find the official refrigerator water filter by the part number on the cartridge and the model in the manual.",
                           body, [article_ld("Refrigerator water filter finder", "/filters/"), faq_ld(faqs)],
                           [("/", "Home"), ("/filters/", "Water filters")]))
    # reset
    faqs = [
        ("How do I reset a GE XWFE filter light?", "GE says a new XWFE filter makes the Filter Status LED flash 3 times and then turn off. That page does not add a button sequence."),
        ("How do I reset an MWFP or EDR1RXD1 filter light?", "The GE SmartWater article and the Whirlpool EDR1RXD1 page we checked do not publish one button sequence for every model. Use the owner's manual."),
        ("What if the light stays on?", "Confirm the cartridge is the one the manual names, and that it is seated. On XWFE models, GE says a wrong or non GE filter can show ERR and shut the water valve. Then use the manual or the manufacturer."),
    ]
    body = f'''<article class="prose"><h1>Refrigerator filter light reset</h1>
{byline()}
<p class="answer">Only the reset behavior published by the manufacturer is on this page. A button sequence from a video or another brand is not included.</p>
<h2>GE Appliances XWFE</h2>
<p>After you install a new XWFE filter, GE says the Filter Status LED flashes 3 times and the Filter Status indicator turns off. If the filter is dry, fill it with water first. A wet filter can shut the water valve. The bypass plug with RFID is WR17X33825, and GE says that plug does not detect leaks.</p>
<p><a href="/filters/xwfe/">XWFE details</a></p>
<h2>GE Appliances MWFP and MWF</h2>
<p>GE's SmartWater article explains which cartridge to buy. It does not print a filter light reset. Use the owner's manual for your model. <a href="/filters/mwfp/">MWFP</a> · <a href="/filters/mwf/">MWF</a></p>
<h2>Whirlpool EDR1RXD1</h2>
<p>The everydrop product page tells you to replace the filter every 6 months or 200 gallons. It does not print a light reset that covers every Whirlpool, Maytag, Amana, KitchenAid, and JennAir refrigerator. Use the manual. <a href="/filters/edr1rxd1/">EDR1RXD1</a></p>
<h2>Samsung, LG, and Frigidaire</h2>
<p>Reset steps for HAF-CIN, HAF-QIN, LT1000P, LT800P, and EPTWFU01 are not on this page yet. We will add them only after the official support page for that cartridge is checked.</p>
{faq_html(faqs)}
{sources_html(FILTERS[1]["sources"] + FILTERS[0]["sources"][:1], f"Retrieved {TODAY_H}.")}
<p><a href="/filters/">Back to the filter finder</a></p>
</article>'''
    write("/filters/reset-filter-light/", page("/filters/reset-filter-light/", f"Reset the Refrigerator Filter Light | {BRAND}", "Official refrigerator filter light reset steps only, starting with the GE XWFE indicator.",
                                             body, [article_ld("Reset the refrigerator filter light", "/filters/reset-filter-light/"), faq_ld(faqs)],
                                             [("/", "Home"), ("/filters/", "Water filters"), ("/filters/reset-filter-light/", "Filter light")]))

def guide_safety():
    faqs = [
        ("Should I unplug the appliance before I look up a code?", "You can read the code with the appliance on. Unplug it, or switch off the breaker, before you pull it out, remove a panel, or clean a filter."),
        ("When do I shut the gas off?", "Shut the gas supply off before any inspection past the checks the manufacturer published for that code. Do not open a gas valve, igniter, or gas line. If you smell gas, leave and call your gas utility."),
        ("Does a range need an anti-tip bracket?", "Yes for freestanding and slide-in ranges that ship with one. The U.S. Consumer Product Safety Commission (CPSC) says to confirm the bracket is fixed to the wall or floor and that the range stays engaged in it, and not to stand on an open oven door or put heavy items on it."),
        ("The code is not on this site. What now?", "Use the manual for your model or the manufacturer's support page. We would rather omit a code than guess. You can send us the model and the official page from the contact form."),
    ]
    mid_reads = next_reads([
        ("/appliances/ovens/", "Oven error codes by brand", "Samsung, GE Appliances, Whirlpool, and other oven hubs on this site.", None),
        ("/codes/ge/oven/", "GE Appliances oven codes", "F0, Loc Door, Bad Line, and the other GE oven codes we verified.", None),
        ("/codes/samsung/oven/", "Samsung oven codes", "C-24, C-F0, door, and the other Samsung range codes we verified.", None),
    ], "Related oven pages", hid="nr-mid")
    end_reads = next_reads([
        ("/codes/whirlpool/oven/", "Whirlpool oven F codes", "F1 E1 is the oven control. F2 E1 starts with the grates. Opened 21 Nov 2026.", None),
        ("/brands/lg/", "LG error codes", "LG washer, dryer, dishwasher, and refrigerator codes already on this site.", None),
        ("/codes/", "All error code pages", "Browse every brand and appliance listing we have checked.", None),
        ("/filters/", "Refrigerator water filter finder", "Official cartridge numbers only, cited to the manufacturer.", None),
    ], "Keep reading", hid="nr-end")
    compare = compare_box(
        "Check another appliance type",
        [
            ("/appliances/ovens/", "Oven and range codes"),
            ("/appliances/dryers/", "Dryer codes (gas shutoff notes)"),
            ("/appliances/washers/", "Washer codes"),
            ("/codes/", "All brands and codes"),
        ],
        "Safety steps differ by machine. Open the type that matches yours, then the brand printed on it.",
    )
    body = f'''<article class="prose"><h1>Safety notes for error codes</h1>
{byline(TODAY3_H)}
<p class="answer">Read the code, then do only the checks the manufacturer published. Unplug the appliance before you move it. Shut the gas off before you go further on a gas dryer or range. On a freestanding range, confirm the anti-tip bracket before you pull the unit out.</p>
{SAFETY}
<h2>Electricity</h2>
<p>Many resets on the cited pages are a short power cut at the plug or the breaker. That is a control reset, not a repair. Do not bypass a breaker or a lid lock. A washer or dishwasher that is full of water can still be dangerous after you unplug it. Let hot water cool before you open a drain filter. Samsung and Bosch both warn that drain water can still be hot.</p>
<h2>Gas</h2>
<p>Gas dryers and gas ranges need the supply valve shut off before any inspection past the published check. <a href="/brands/lg/">LG</a>'s gAS dryer code, for example, only tells you to confirm the valve is on and the line is not kinked. It does not tell you to open the burner. If you smell gas, do not look for the leak with a flame or a spark. Leave and call the gas utility.</p>
{compare}
<h2>Range tip-over (CPSC)</h2>
<p>Before you slide a freestanding or slide-in range out to read a label or clear a vent, check the anti-tip bracket. The <a href="https://www.cpsc.gov/s3fs-public/5007.pdf" rel="nofollow noopener" target="_blank">U.S. Consumer Product Safety Commission range tip-over alert (Publication 5007)</a> says the bracket should be fixed to the wall or floor and the range should stay held in it. CPSC also says not to leave children unsupervised in the kitchen, not to put heavy items on an open oven door, and not to use the open door as a step or to stand. If the bracket is missing, ask the range maker whether your model should have one. Some makers will send a replacement. This site does not publish gas line, sealed system, or electrical repair steps past the manufacturer checks on each code page.</p>
{mid_reads}
<h2>Water</h2>
<p>If a code means a leak or an overfill, shut the supply valve. Do not keep the cycle running. A filter part number is a separate question from a sensor code. Use the <a href="/filters/">filter finder</a> only for cartridges the manufacturer names.</p>
<h2>Refrigerators</h2>
<p>Samsung's refrigerator code page says not to unplug the refrigerator, and not to clear the code from the panel, unless the steps for that code say to. Food safety matters if the freezer is warm. Move food when a code such as GE FF says the temperature is rising.</p>
{faq_html(faqs)}
{sources_html([
    ("U.S. CPSC: Range Tipover Safety Alert (Publication 5007)", "https://www.cpsc.gov/s3fs-public/5007.pdf"),
    ("Samsung refrigerator error codes", "https://www.samsung.com/us/support/troubleshoot/TSG10007315/"),
    ("LG dryer error codes, including gAS", "https://www.lg.com/us/support/help-library/lg-dryer-error-code-list--20154710772482"),
    ("Samsung washer will not drain", "https://www.samsung.com/us/support/troubleshoot/TSG10007110/"),
], f"Retrieved {TODAY3_H}. CPSC Publication 5007 checked {TODAY3_H}.")}
{end_reads}
<p><a href="/codes/">Browse error codes</a> · <a href="/appliances/ovens/">Oven brands</a> · <a href="/methodology/">Sources and methods</a></p>
</article>'''
    write("/guides/safety/", page("/guides/safety/", f"Appliance Error Code Safety | {BRAND}", "Unplug, shut off gas, and check the range anti-tip bracket before you go past the manufacturer's published checks.",
                                 body, [article_ld("Appliance error code safety", "/guides/safety/", published=TODAY, modified=TODAY5), faq_ld(faqs)],
                                 [("/", "Home"), ("/guides/safety/", "Safety")], lastmod=TODAY5))

def simple(path, title, desc, h1, inner, crumb, faqs=None, published=None, modified=None, lastmod=None):
    ld = [article_ld(h1, path, published=published, modified=modified)]
    extra = ""
    if faqs:
        extra = faq_html(faqs)
        ld.append(faq_ld(faqs))
    body = f'<article class="prose"><h1>{E(h1)}</h1>{inner}{extra}</article>'
    write(path, page(path, title, desc, body, ld, [("/", "Home"), (path, crumb)], lastmod=lastmod))

def about_legal():
    simple("/about/", f"About {BRAND}", "What Which Error Code is and how the pages are checked.", "About Which Error Code", f'''
{byline()}
<p>{BRAND} is an independent guide to home appliance error codes and to the official refrigerator water filter number. The question on every code page is the same: what does this code mean, which checks did the manufacturer publish, and when should you call a technician?</p>
<h2>What we cover</h2>
<p>Washers, dryers, dishwashers, refrigerators, and ovens from Samsung, LG, GE Appliances, Whirlpool, Maytag, KitchenAid, and Bosch, where we have read an official page. Filter pages cover cartridges whose official product page we have read.</p>
<h2>Independence</h2>
<p>{BRAND} is not affiliated with, endorsed by, or sponsored by any appliance maker. Brand names are plain text. We do not show logos.</p>
<p>See <a href="/methodology/">sources and methods</a>. Send a correction from the <a href="/contact/">contact page</a>.</p>''', "About")
    simple("/methodology/", f"Sources and Methods | {BRAND}", "How Which Error Code checks error codes and water filter numbers.", "Sources and methods", f'''
{byline()}
<h2>Error codes</h2>
<p>A code is added only when it appears on the manufacturer's support page or in the manufacturer's manual. The page on this site names that source. We paraphrase the steps. We do not copy the manual. If the official page says the code means different things on different models, we say that and stop.</p>
<h2>What we leave out</h2>
<p>Repair blogs, parts sellers, and videos are not sources for a code or a part number. A code that is missing here is missing on purpose. Frigidaire, several Bosch and KitchenAid appliance types, and several filter model numbers are in that gap for this version.</p>
<h2>Filters</h2>
<p>A filter page uses the manufacturer's product page or performance sheet. We do not copy a compatibility chart from another site. A refrigerator model is listed only when the official page lists it. Third party compatible filters are omitted unless the manufacturer says they are approved.</p>
<h2>Safety</h2>
<p>The unplug and gas notes are our safety framing. They are separate from the manufacturer's steps, and the page says so when the manufacturer gives a different instruction, as Samsung does for many refrigerator codes.</p>
<h2>Dates</h2>
<p>Last verified is the date we read the source, {TODAY_H}. We change that date when the content changes, not on every rebuild.</p>
<p><a href="/contact/">Report an error</a>.</p>''', "Sources and methods")
    simple("/image-policy/", f"Image Policy | {BRAND}", "How Which Error Code handles images and trademarks.", "Image policy", f'''
<p>Last updated {TODAY5_H}.</p>
<h2>Images</h2>
<p>The mark in the header, the favicon, and the social image are original graphics we made. They are not photographs of appliances and they are not brand logos.</p>
<h2>Article photographs</h2>
<p>A code article may show one photograph. When it does, the picture is an AI-generated image of an unbranded control panel in ordinary light. It shows no real person, no logo, and no readable brand name. The caption says AI-generated image and links to this page. A page with no photograph is text only. We do not use illustrated or glossy renderings, and we do not present the picture as a photo of a specific person's appliance.</p>
<h2>Logos and trademarks</h2>
<p>We do not display appliance brand logos. Names are used only to identify the product.</p>
<p>See <a href="/copyright/">copyright</a> or <a href="/contact/">contact</a> if you believe an image uses your work.</p>''', "Image policy", published=TODAY, modified=TODAY5, lastmod=TODAY5)
    contact = f'''{byline()}
<p>Questions and corrections go to <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>. Include the page address, the code or part number, and a link to the manufacturer page if you have one.</p>
<h2>Send a message</h2>
<p class="form-status" id="contact-status" role="status" hidden></p>
<form class="contact" id="contact-form" action="{FORM_ENDPOINT}" method="POST">
<input type="hidden" name="_subject" value="Which Error Code contact">
<input type="hidden" name="_template" value="table">
<input type="hidden" name="_next" value="{BASE}contact/?sent=1">
<input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
<input type="hidden" name="_captcha" value="false">
<label for="name">Name</label><input id="name" type="text" name="name" required autocomplete="name">
<label for="email">Email</label><input id="email" type="email" name="email" required autocomplete="email">
<label for="message">Message</label><textarea id="message" name="message" rows="6" required></textarea>
<button class="btn" type="submit">Send message</button></form>
<p class="note">The form is delivered by FormSubmit to {CONTACT_EMAIL}. You can also use the email link above. See the <a href="/privacy/">privacy policy</a>.</p>'''
    simple("/contact/", f"Contact {BRAND}", "Contact Which Error Code at joshuaofisrael@gmail.com with a correction or a question.", "Contact us", contact, "Contact")
    D = TODAY_H
    legal = {
        "/terms/": ("Terms of Use", f'''<p>Last updated {D}. These terms govern your use of whicherrorcode.com, operated under the name Which Error Code. {LEGAL_LINE} By using the site you agree to these terms.</p>
<h2>Information only</h2><p>The site gives general information from cited manufacturer pages. It is not a repair service, and it is not engineering or professional advice. Appliance makers change codes and part numbers. Follow the manual for your model, and hire a qualified technician for repairs.</p>
<h2>Accuracy</h2><p>We cite our sources and we omit what we cannot verify. We do not warrant that a page is complete or current.</p>
<h2>Acceptable use</h2><p>You may link to pages for personal, non commercial use. You may not scrape the site in bulk, republish our original text, misuse the contact form, or try to disrupt the site.</p>
<h2>Intellectual property</h2><p>Original text, design, and compilations belong to Joshua Israel Ventures LLC. Appliance names and trademarks belong to their owners and are used only to identify products. That use does not imply affiliation or endorsement.</p>
<h2>Third party services</h2><p>We link to manufacturer sites and we use GitHub Pages, Cloudflare, and FormSubmit. If you accept analytics on the launch site, Google Analytics 4 loads as well. We are not responsible for their content or practices.</p>
<h2>Disclaimer of warranties and limitation of liability</h2><p>The site is provided as is and as available. To the fullest extent permitted by law, Joshua Israel Ventures LLC disclaims all warranties and will not be liable for indirect, incidental, special, consequential, or punitive damages, or for a loss from your use of the site or from a repair you attempt. Our total liability for any claim relating to the site is limited to 100 US dollars.</p>
<h2>Indemnity</h2><p>You agree to indemnify Joshua Israel Ventures LLC against claims arising from your misuse of the site or your breach of these terms.</p>
<h2>Governing law</h2><p>These terms are governed by the laws of the State of Florida, United States, without regard to conflict of law rules. Courts in Florida have jurisdiction, and you consent to it.</p>
<h2>Changes</h2><p>We may update these terms. The date above is the latest version. Questions: <a href="/contact/">contact</a>.</p>'''),
        "/privacy/": ("Privacy Policy", f'''<p>Last updated {TODAY3_H}. This policy explains how Which Error Code, whicherrorcode.com, handles information. {LEGAL_LINE}</p>
<h2 id="analytics">Analytics</h2><p>When the site is on its own domain, launch pages can load two analytics tools.</p>
<p>Cloudflare Web Analytics counts page views. It does not use cookies and it does not track you across other sites. The beacon loads with each launch page.</p>
<p>Google Analytics 4 (GA4) stays off until you accept the banner. Consent Mode v2 starts with analytics storage, ad storage, ad user data, and ad personalization denied. The GA4 script is requested only after you accept. Reject leaves that script unloaded. Cookie settings in the footer opens the same choice. Accept allows analytics storage on this site only. Ad storage, ad user data, and ad personalization stay denied until we show ad units that need them. The preview build does not include the Cloudflare beacon or the GA4 script. The site owner pastes the measurement id into the launch build before those hits are sent.</p>
<h2>Contact</h2><p>If you email {CONTACT_EMAIL} or use the contact form, we receive your name, email address, and message so we can reply. The form is handled by FormSubmit. We keep messages only as long as we need them to respond.</p>
<h2 id="advertising">Advertising</h2><p>Which Error Code uses Google AdSense for future display advertising. Launch pages include the AdSense account meta tag and the AdSense script for publisher verification (publisher id {ADSENSE_CLIENT}). This version does not place ad units on the page, so you should not see ads in the article body yet.</p>
<h2>Google advertising cookies and your choices</h2><p>Third-party vendors, including Google, use cookies to serve ads based on a user's prior visits to this website or other websites. Google's use of advertising cookies enables it and its partners to serve ads based on your visit to this site and/or other sites on the Internet. You may opt out of personalized advertising by visiting <a href="https://adssettings.google.com/" rel="nofollow noopener">Google Ads Settings</a>. Alternatively, you can opt out of a third-party vendor's use of cookies for personalized advertising at <a href="https://www.aboutads.info/choices/" rel="nofollow noopener">aboutads.info/choices</a>. For more information, see <a href="https://policies.google.com/technologies/partner-sites" rel="nofollow noopener">how Google uses information from sites or apps that use its services</a>.</p>
<p>When ad units go live, Consent Mode will keep ad storage denied until you accept advertising cookies where the law requires that choice. You can opt out of personalized advertising at Google Ads Settings and aboutads.info. See the <a href="/ad-disclosure/">advertising disclosure</a> and the site <a href="/ads.txt">ads.txt</a> file.</p>
<h2>Cookies</h2><p>These pages do not set their own cookies. Cloudflare Web Analytics does not use cookies. Your banner choice is stored in this browser's local storage, not in a cookie. If you accept Google Analytics 4, Google may set analytics cookies for this site. Choose Reject, or open Cookie settings and reject later, and the GA4 script is not requested. The AdSense verification script may still load; it does not show ad units on this version.</p>
<h2>Hosting</h2><p>The site is hosted on GitHub Pages, which may log IP addresses for security.</p>
<h2>Your rights</h2><p>You can ask us to access, correct, or delete personal information we hold. Use the <a href="/contact/">contact page</a>. Residents of some states and countries have additional rights, which we will honor.</p>
<h2>Children</h2><p>The site is a general audience site and is not directed at children under 13. We do not knowingly collect personal information from children.</p>
<h2>Changes</h2><p>We will post changes on this page with a new date.</p>'''),
        "/disclaimer/": ("Disclaimer", f'''<p>Last updated {D}. {LEGAL_LINE}</p>
<h2>Not affiliated with any appliance maker</h2><p>Which Error Code is independent. It is not affiliated with, endorsed by, or sponsored by Samsung, LG, GE Appliances, Whirlpool, Maytag, KitchenAid, Bosch, Frigidaire, or any other maker. Names are used only to identify products.</p>
<h2>Not a repair manual</h2><p>Pages repeat the checks a manufacturer has published and tell you when that page says to stop. They are not instructions to disassemble an appliance. Unplug power and shut off the gas before any inspection past those checks. If you smell gas, leave and call your gas utility.</p>
<h2>Models differ</h2><p>A code can mean two things on two models. The manual for your model number wins over this site. Filter fit must be confirmed on the cartridge you remove and in the manual.</p>
<h2>Corrections</h2><p>Report a mistake on the <a href="/contact/">contact page</a>. We correct a verified mistake and we update the verified date.</p>
<h2>Limitation of liability</h2><p>To the extent permitted by law, Joshua Israel Ventures LLC is not liable for a loss that comes from relying on this site. See the <a href="/terms/">terms of use</a>.</p>'''),
        "/copyright/": ("Copyright and DMCA Policy", f'''<p>Last updated {D}. Original text, design, and compilations on Which Error Code are owned by Joshua Israel Ventures LLC. Facts are cited to their sources. {LEGAL_LINE} See the <a href="/image-policy/">image policy</a>.</p>
<h2>Reporting infringement</h2><p>If you believe material on this site infringes your copyright, use the <a href="/contact/">contact form</a> and include your name and contact details, a description of the work, the URL on our site, a statement that you have a good faith belief the use is not authorized, a statement under penalty of perjury that the notice is accurate and that you are the owner or authorized to act, and your physical or electronic signature. We will review notices and remove or disable material when that is the right step.</p>
<h2>Counter notice</h2><p>If your material was removed and you believe that was a mistake, you may send a counter notice through the contact form with the details required by 17 U.S.C. section 512(g).</p>
<h2>Repeat infringement</h2><p>We will act against repeat infringement when that is appropriate.</p>'''),
        "/ad-disclosure/": ("Advertising and Affiliate Disclosure", f'''<p>Last updated {TODAY3_H}. {LEGAL_LINE} Which Error Code is free to use. The site has no affiliate links.</p>
<h2>Google AdSense</h2><p>Launch pages include the Google AdSense publisher script and account meta tag ({ADSENSE_CLIENT}) so the site can be reviewed for AdSense. This version does not place ad units in the article body. When units are added, ads will be labeled as advertising, and this page will say so. See <a href="/ads.txt">ads.txt</a> and the <a href="/privacy/#advertising">privacy policy advertising section</a>.</p>
<h2>Editorial independence</h2><p>No appliance maker pays for a code to be added or removed. Questions: <a href="/contact/">contact</a>.</p>'''),
    }
    for p, (t, inner) in legal.items():
        body = f'<article class="prose"><h1>{E(t)}</h1>{inner}<p class="legal-line">{LEGAL_LINE}</p></article>'
        lm = TODAY3 if p in ("/privacy/", "/ad-disclosure/") else None
        write(p, page(p, f"{t} | {BRAND}", clip(f"{t} for Which Error Code, an independent guide to appliance error codes and water filters."), body,
                      article_ld(t, p, published=TODAY, modified=lm or TODAY), [("/", "Home"), (p, t)], lastmod=lm))

def not_found():
    body = '<h1>Page not found</h1><p>That page is not on this site. Try the <a href="/codes/">error code list</a> or the <a href="/filters/">water filter finder</a>.</p>'
    html_page = page("/404.html", f"Page not found | {BRAND}", "That page is not on Which Error Code.", body, noindex=True)
    with open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8") as f:
        f.write(html_page)

def png(path, w, h, rgb):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw.extend(rgb(x, y))
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    blob = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(blob)

def images():
    def logo_px(x, y):
        # 64 view scaled to 256
        nx, ny = x / 256, y / 256
        if 0.08 < nx < 0.92 and 0.08 < ny < 0.92:
            if 0.22 < nx < 0.78 and 0.22 < ny < 0.62:
                return (230, 244, 241)
            if 0.22 < nx < 0.78 and 0.70 < ny < 0.80:
                return (255, 179, 71)
            return (11, 57, 84)
        return (11, 57, 84)
    png(os.path.join(ROOT, "logo.png"), 256, 256, logo_px)
    def og_px(x, y):
        if y < 80 or y > 550:
            return (11, 57, 84)
        if 180 < x < 1020 and 160 < y < 470:
            return (230, 244, 241)
        return (247, 251, 251)
    png(os.path.join(ROOT, "og.png"), 1200, 630, og_px)
    svg = LOGO.replace('width="34" height="34" ', 'xmlns="http://www.w3.org/2000/svg" ').replace(' aria-hidden="true" focusable="false"', "")
    with open(os.path.join(ROOT, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(svg)

def extras():
    with open(os.path.join(ROOT, "CNAME"), "w", encoding="utf-8") as f:
        f.write("whicherrorcode.com\n")
    with open(os.path.join(ROOT, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)
    # AdSense ads.txt (publisher verification). Not a sitemap URL.
    with open(os.path.join(ROOT, "ads.txt"), "w", encoding="utf-8") as f:
        f.write(f"google.com, pub-{ADSENSE_CLIENT.split('ca-pub-')[-1]}, DIRECT, f08c47fec0942fa0\n")
    bots = ["*", "Googlebot", "Bingbot", "Mediapartners-Google", "OAI-SearchBot", "ChatGPT-User", "GPTBot",
            "PerplexityBot", "Perplexity-User", "ClaudeBot", "Claude-SearchBot", "Claude-User",
            "Google-Extended", "Applebot", "Applebot-Extended", "DuckAssistBot", "Amazonbot", "CCBot", "Bytespider"]
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots) + f"Sitemap: {BASE}sitemap.xml\n")
    # stable order
    pages = sorted(set(PAGES), key=lambda p: p[0])
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for p, m in pages:
            f.write(f"<url><loc>{url(p)}</loc><lastmod>{m}</lastmod></url>\n")
        f.write("</urlset>\n")
    lines = [f"# {BRAND}", "",
             f"> Which Error Code (whicherrorcode.com) explains home appliance error codes and official refrigerator water filter numbers. Every code is cited to the manufacturer. Whirlpool range F codes were opened {TODAY5_H}. Earlier pages keep the date printed on the page.",
             "",
             "Independent. Not affiliated with any appliance maker. Unplug the appliance and shut off the gas before any inspection past the published checks.",
             "",
             "## Start here",
             f"- [Home]({url('/')})",
             f"- [All error codes]({url('/codes/')})",
             f"- [Water filters]({url('/filters/')})",
             f"- [Safety]({url('/guides/safety/')})",
             f"- [Sources and methods]({url('/methodology/')})",
             "",
             "## Brand and appliance pages"]
    for brand, appl, rows in GROUPS:
        lines.append(f"- [{BNAME[brand]} {ANAME[appl].lower()} codes]({url(listing_path(brand, appl))})")
    lines.append("")
    lines.append("## Single codes")
    for r in ROWS:
        if r["individual"]:
            lines.append(f"- [{BNAME[r['brand']]} {ANAME[r['appl']].lower()} {r['code']}]({url(code_path(r))})")
    lines.append("")
    lines.append("## Filters")
    lines.append(f"- [Filter finder]({url('/filters/')})")
    for f in FILTERS:
        lines.append(f"- [{f['sku']}]({url('/filters/' + f['slug'] + '/')})")
    lines.append(f"- [Filter light reset]({url('/filters/reset-filter-light/')})")
    with open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(ROOT, "_config.yml"), "w", encoding="utf-8") as f:
        f.write("include: [CNAME]\nexclude: [README.md, LAUNCH-NOTES.md, _build, deploy.sh, indexnow.sh, legal, .gitignore]\n")

def search_index():
    data = []
    for r in ROWS:
        data.append({
            "code": r["code"],
            "aliases": " ".join(r["aliases"]),
            "brand": BNAME[r["brand"]],
            "appliance": ANAME[r["appl"]],
            "meaning": r["meaning"],
            "path": code_path(r) if r["individual"] else listing_path(r["brand"], r["appl"]) + "#" + r["slug"],
        })
    return json.dumps(data, ensure_ascii=False)

def main():
    # The ge/oven group and its Loc Door page were added 18 Nov 2026; they are brand new
    # URLs and use TODAY2 for published/modified/lastmod. Every other page is unchanged
    # from the 16 Nov 2026 build and keeps the original TODAY date.
    for r in ROWS:
        if r["individual"]:
            if r["brand"] == "whirlpool" and r["appl"] == "oven":
                continue
            published = modified = None
            if r["brand"] == "ge" and r["appl"] == "oven":
                published = modified = TODAY2
            elif r["brand"] == "bosch" and r["appl"] == "dishwasher" and r["code"] == "E22":
                published, modified = TODAY, TODAY5
            code_page(r, published=published, modified=modified)
    seen = []
    for brand, appl, rows in GROUPS:
        enriched = []
        for row in rows:
            match = next(r for r in ROWS if r["brand"] == brand and r["appl"] == appl and r["code"] == row["code"])
            enriched.append(match)
        if brand == "whirlpool" and appl == "oven":
            whirlpool_oven_pages()
        elif brand == "bosch" and appl == "dishwasher":
            bosch_dishwasher_page()
        else:
            listing_page(brand, appl, enriched, new=(brand == "ge" and appl == "oven"))
        seen.append((brand, appl))
    brand_pages()
    appliance_pages()
    idx = search_index()
    codes_index(idx)
    home(idx)
    filter_pages()
    guide_safety()
    about_legal()
    not_found()
    images()
    extras()
    n = len(set(p for p, _ in PAGES))
    print(n, "sitemap urls", "LAUNCH" if LAUNCH else "PREVIEW noindex")
    if LAUNCH and not re.fullmatch(r"G-[A-Z0-9]+", GA4_ID or ""):
        print("GA4_ID is empty. check.py --launch fails until it is a G- measurement id.")

if __name__ == "__main__":
    main()
