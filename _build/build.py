#!/usr/bin/env python3
"""Which Error Code static site builder. Run from the repo root.

  python3 _build/build.py            # pre launch: noindex on every page, root paths, CNAME
  python3 _build/build.py --launch   # domain live: indexable, Cloudflare beacon

NOINDEX is the single pre launch flag. Paths are always root relative.
Canonicals always use https://whicherrorcode.com/.
"""
import os, sys, json, html, zlib, struct
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
INDEXNOW_KEY = "e5e7fc4f0a0e96a11d330aa8cf3cba1c"
CF_BEACON_TOKEN = "eac63f2b5dbc4539a2d95249baab6472"
FORM_ENDPOINT = "https://formsubmit.co/joshuaofisrael@gmail.com"
CONTACT_EMAIL = "joshuaofisrael@gmail.com"
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

def page(path, title, desc, body, jsonld=None, crumbs=None, noindex=False, robots_extra=False):
    desc = clip(desc)
    canon = url(path if path != "/404.html" else "/")
    if path == "/404.html":
        canon = url("/404.html")
    force_no = noindex or NOINDEX
    # Real pages stay in the sitemap. The noindex flag is separate and flips at launch.
    # 404 and other utility pages pass noindex=True and stay out.
    if path != "/404.html" and not noindex:
        PAGES.append((path, TODAY))
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
    if jsonld:
        ld += jsonld if isinstance(jsonld, list) else [jsonld]
    ldh = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    nav = "".join(f'<a href="{p}"' + (' aria-current="page"' if p == path else "") + f'>{n}</a>' for p, n in NAV)
    bc = ""
    if crumbs:
        bc = '<nav class="crumbs" aria-label="Breadcrumb"><ol>' + "".join(
            (f'<li><a href="{p}">{E(n)}</a></li>' if i < len(crumbs) - 1 else f'<li aria-current="page">{E(n)}</li>')
            for i, (p, n) in enumerate(crumbs)) + "</ol></nav>"
    robots = "noindex, follow" if force_no else "index, follow, max-image-preview:large"
    beacon = (f"<!-- Cloudflare Web Analytics --><script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{\"token\": \"{CF_BEACON_TOKEN}\"}}'></script><!-- End Cloudflare Web Analytics -->") if LAUNCH else "<!-- cf-beacon: added by launch build -->"
    flag = "on" if NOINDEX else "off"
    legal = ""
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{canon}">
<meta name="robots" content="{robots}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{BRAND}"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{canon}"><meta property="og:image" content="{url('/og.png')}"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/style.css?v=1">{ldh}
</head><body><a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap"><a class="brand" href="/">{LOGO}<span>{BRAND}</span></a><nav class="main" aria-label="Main">{nav}</nav></div></header>
<main id="main" class="wrap">{bc}{body}<!-- ad-slot: below-content (reserved; no ad code) --></main>
<footer class="site"><div class="wrap"><p class="fbrand"><strong>{BRAND}</strong> explains home appliance error codes and refrigerator water filter numbers from the manufacturer pages we cite. We are independent. Names are used only to identify the appliance. Codes and part numbers change by model, so check the manual for yours.</p>
<p class="flinks"><a href="/about/">About</a> | <a href="/methodology/">Sources and methods</a> | <a href="/image-policy/">Image policy</a> | <a href="/terms/">Terms of use</a> | <a href="/privacy/">Privacy</a> | <a href="/disclaimer/">Disclaimer</a> | <a href="/ad-disclosure/">Advertising disclosure</a> | <a href="/copyright/">Copyright and DMCA</a> | <a href="/contact/">Contact</a></p>
{legal}</div></footer>
<script src="/assets/site.js?v=1" defer></script>{beacon}
<!-- noindex-flag: {flag} -->
</body></html>'''

def article_ld(headline, path, about=None):
    data = {"@context": "https://schema.org", "@type": "Article", "headline": headline,
            "datePublished": TODAY, "dateModified": TODAY,
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

def byline():
    return f'<p class="byline">By {BRAND}. Last verified {TODAY_H}.</p>'

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

def code_page(r):
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
    water = ""
    if r["water"]:
        water = '<p>Related: <a href="/filters/">refrigerator water filter finder</a>. A sensor code is not a filter part number. Match the cartridge in the refrigerator to the manual.</p>'
    faqs = [
        (f"What does {b} {a.lower()} code {r['code']} mean?", r["meaning"] + (" " + r["extra"] if r["extra"] else "")),
        (f"What can I check on a {b} {a.lower()} showing {r['code']}?", " ".join(r["checks"]) + " Unplug the appliance or switch off its breaker before you move it or open a panel. If it uses gas, shut the gas off before any step the manufacturer did not publish."),
        (f"When should I call a technician for {r['code']}?", r["service"]),
    ]
    body = f'''<article class="prose wide"><h1>{E(b)} {E(a.lower())} code {E(r["code"])}</h1>
{byline()}
<div class="answer"><p><strong>Meaning:</strong> {E(r["meaning"])}</p></div>
{aliases}{extra}
{safety_for(r)}
<h2>Checks the manufacturer publishes</h2><ul class="checks">{checks}</ul>
<h2>When to call a technician</h2><p>{E(r["service"])}</p>
{water}
{faq_html(faqs)}
{sources_html(r["sources"], f"Retrieved {TODAY_H}. Models differ. If your manual defines this code differently, the manual wins. {BRAND} is not affiliated with {E(b)}.")}
<h2>More {E(b)} {E(a.lower())} codes</h2><ul>{sib}</ul>
<p><a href="{listing_path(r["brand"], r["appl"])}">All {E(b)} {E(a.lower())} codes</a> · <a href="/guides/safety/">Safety notes</a> · <a href="/codes/">All brands</a></p>
</article>'''
    write(path, page(path, title, desc, body, [article_ld(f"{b} {a.lower()} code {r['code']}", path, f"{b} {r['code']}"), faq_ld(faqs)],
                    [("/", "Home"), ("/codes/", "Error codes"), (listing_path(r["brand"], r["appl"]), f"{b} {a}"), (path, r["code"])]))

def listing_page(brand, appl, rows):
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
{byline()}
<div class="answer"><p>These are the {E(b)} {E(a.lower())} codes we could verify on the manufacturer's own page. Each block says what the code means, the checks that page allows, and when it says to call a technician.</p></div>
{SAFETY}<p>{E(gas).strip()}</p>{fridge_note}
{"".join(bits)}
{faq_html(faqs)}
{sources_html(unique_sources(rows), f"Retrieved {TODAY_H}. {BRAND} is not affiliated with {E(b)}. Names identify the appliance only.")}
<p><a href="/brands/{brand}/">All {E(b)} pages</a> · <a href="/appliances/{APLUR[appl]}/">All {E(a.lower())} brands</a> · <a href="/filters/">Water filters</a></p>
</article>'''
    # fix empty gas paragraph
    body = body.replace("<p></p>", "")
    desc = f"{b} {a.lower()} error codes: what each code means, the safe checks the manufacturer publishes, and when to call a technician."
    write(path, page(path, f"{b} {a} Error Codes", desc, body,
                    [article_ld(f"{b} {a.lower()} error codes", path, f"{b} {a}"), faq_ld(faqs)],
                    [("/", "Home"), ("/codes/", "Error codes"), (path, f"{b} {a}")]))

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
        body = f'''<h1>{E(name)} error codes</h1>
{byline()}
<p class="answer">Pick the appliance. Every code is cited to a {E(name)} manual or support page. We leave out codes we have not checked on that page.</p>
<ul class="cols">{"".join(items)}</ul>
<p><a href="/codes/">All brands</a> · <a href="/guides/safety/">Safety notes</a></p>'''
        path = f"/brands/{slug}/"
        covered = [ANAME[appl].lower() for appl, _, _ in APPLS if any(r["brand"] == slug and r["appl"] == appl for r in ROWS)]
        write(path, page(path, f"{name} Appliance Error Codes", f"{name} error codes we verified: {', '.join(covered)}. Each code is cited to a {name} support page.",
                        body, None, [("/", "Home"), ("/brands/", "Brands"), (path, name)]))
    cards = []
    for slug, name in BRANDS:
        labels = []
        for appl, an, _ in APPLS:
            if any(r["brand"] == slug and r["appl"] == appl for r in ROWS):
                labels.append(f'<a href="{listing_path(slug, appl)}">{E(an)}</a>')
        if labels:
            cards.append(f'<li class="card"><h2><a href="/brands/{slug}/">{E(name)}</a></h2><p>{", ".join(labels)}</p></li>')
    body = f'''<h1>Error codes by brand</h1>
<p class="answer">Choose a brand. We publish a code only after reading it on that manufacturer's support page or manual.</p>
<ul class="cards">{"".join(cards)}</ul>
<p>Frigidaire pages are not in this version. We did not find a Frigidaire.com code list we could cite code by code. Bosch ranges, refrigerators, and dryers, KitchenAid washers and dryers, and GE ovens are in the same gap.</p>'''
    write("/brands/", page("/brands/", f"Appliance Error Codes by Brand | {BRAND}", "Samsung, LG, GE Appliances, Whirlpool, Maytag, KitchenAid, and Bosch error codes, each cited to the manufacturer.",
                          body, None, [("/", "Home"), ("/brands/", "Brands")]))

def appliance_pages():
    for appl, an, plural in APPLS:
        items = []
        for slug, name in BRANDS:
            rows = [r for r in ROWS if r["brand"] == slug and r["appl"] == appl]
            if not rows:
                continue
            preview = ", ".join(r["code"] for r in rows[:6])
            items.append(f'<li class="card"><h2><a href="{listing_path(slug, appl)}">{E(name)} {E(an.lower())} codes</a></h2><p>{E(preview)}</p></li>')
        body = f'''<h1>{E(an)} error codes</h1>
<p class="answer">Brand pages for {E(an.lower())} codes we verified. The same letters can mean different things on another brand, so start with the name on the appliance.</p>
<ul class="cards">{"".join(items)}</ul>
<p><a href="/codes/">All error codes</a> · <a href="/guides/safety/">Unplug and gas shutoff</a></p>'''
        path = f"/appliances/{plural}/"
        write(path, page(path, f"{an} Error Codes by Brand", f"{an} error codes for the brands we have checked, with the manufacturer's meaning and the safe checks.",
                        body, None, [("/", "Home"), ("/appliances/", "Appliances"), (path, plural.capitalize())]))
    cards = "".join(f'<li class="card"><h2><a href="/appliances/{p}/">{E(n)}s</a></h2><p>Codes for {E(n.lower())}s, brand by brand.</p></li>' for _, n, p in APPLS)
    # Wait, ANAME already includes the noun "Washer" and plural path is washers. Card title "Washers" from path. Fix: use plural from path capitalized properly.
    cards = []
    for _, n, p in APPLS:
        cards.append(f'<li class="card"><h2><a href="/appliances/{p}/">{E(p.capitalize())}</a></h2><p>Verified {E(n.lower())} codes by brand.</p></li>')
    body = f'<h1>Error codes by appliance</h1><p class="answer">Washers, dryers, dishwashers, refrigerators, and ovens. Open a type, then the brand printed on the appliance.</p><ul class="cards">{"".join(cards)}</ul>'
    write("/appliances/", page("/appliances/", f"Error Codes by Appliance | {BRAND}", "Washer, dryer, dishwasher, refrigerator, and oven error codes, sorted by appliance type.",
                              body, None, [("/", "Home"), ("/appliances/", "Appliances")]))

def codes_index(search_json):
    rows = []
    for r in ROWS:
        if not r["individual"]:
            continue
        rows.append(f'<li><a href="{code_path(r)}">{E(BNAME[r["brand"]])} {E(ANAME[r["appl"]].lower())} {E(r["code"])}</a></li>')
    body = f'''<h1>Appliance error code pages</h1>
<p class="answer">One page for each brand and appliance we have checked, plus a page for the codes people look up most often. Search from the <a href="/">home page</a>.</p>
<h2>By brand</h2><ul class="cols">{"".join(f'<li><a href="/brands/{s}/">{E(n)}</a></li>' for s, n in BRANDS)}</ul>
<h2>By appliance</h2><ul class="cols">{"".join(f'<li><a href="/appliances/{p}/">{E(p.capitalize())}</a></li>' for _, _, p in APPLS)}</ul>
<h2>Single codes</h2><ul class="cols">{"".join(rows)}</ul>
<p class="note">Each code page links the manufacturer page it was read from. Retrieved {TODAY_H}.</p>
<section class="sources"><h2>Sources</h2><ul><li><a href="https://www.samsung.com/us/support/troubleshoot/TSG10000997/" rel="nofollow noopener" target="_blank">Samsung washer error codes</a></li><li><a href="https://www.lg.com/us/support/help-library/lg-front-load-washer-error-code-list--20155069413456" rel="nofollow noopener" target="_blank">LG washer error codes</a></li><li><a href="https://products.geappliances.com/appliance/gea-support-search-content?contentId=16912" rel="nofollow noopener" target="_blank">GE Appliances refrigerator fault codes</a></li></ul><p class="note">The full citation list is on each code page.</p></section>'''
    write("/codes/", page("/codes/", f"Appliance Error Code List | {BRAND}", "Browse verified washer, dryer, dishwasher, refrigerator, and oven error codes by brand.",
                         body, None, [("/", "Home"), ("/codes/", "Error codes")]))

def home(search_json):
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
<h2>How a page is built</h2><p>We open the manufacturer page, record the code and the checks written there, and link that page. If a code is not on the page, it is not here. Names are plain text. There are no logos and no claim that a brand sponsors this site. <a href="/methodology/">Sources and methods</a>.</p>'''
    desc = "Look up washer, dryer, dishwasher, refrigerator, and oven error codes, plus the official fridge water filter number. Cited to the manufacturer."
    write("/", page("/", f"{BRAND}: Appliance Error Codes and Water Filters", desc, body))

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
<p><a href="/filters/reset-filter-light/">Filter light reset, official steps only</a></p>
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
        ("The code is not on this site. What now?", "Use the manual for your model or the manufacturer's support page. We would rather omit a code than guess. You can send us the model and the official page from the contact form."),
    ]
    body = f'''<article class="prose"><h1>Safety notes for error codes</h1>
{byline()}
<p class="answer">Read the code, then do only the checks the manufacturer published. Unplug the appliance before you move it. Shut the gas off before you go further on a gas dryer or range.</p>
{SAFETY}
<h2>Electricity</h2>
<p>Many resets on the cited pages are a short power cut at the plug or the breaker. That is a control reset, not a repair. Do not bypass a breaker or a lid lock. A washer or dishwasher that is full of water can still be dangerous after you unplug it. Let hot water cool before you open a drain filter. Samsung and Bosch both warn that drain water can still be hot.</p>
<h2>Gas</h2>
<p>Gas dryers and gas ranges need the supply valve shut off before any inspection past the published check. LG's gAS code, for example, only tells you to confirm the valve is on and the line is not kinked. It does not tell you to open the burner. If you smell gas, do not look for the leak with a flame or a spark. Leave and call the gas utility.</p>
<h2>Water</h2>
<p>If a code means a leak or an overfill, shut the supply valve. Do not keep the cycle running. A filter part number is a separate question from a sensor code. Use the <a href="/filters/">filter finder</a> only for cartridges the manufacturer names.</p>
<h2>Refrigerators</h2>
<p>Samsung's refrigerator code page says not to unplug the refrigerator, and not to clear the code from the panel, unless the steps for that code say to. Food safety matters if the freezer is warm. Move food when a code such as GE FF says the temperature is rising.</p>
{faq_html(faqs)}
{sources_html([
    ("Samsung refrigerator error codes", "https://www.samsung.com/us/support/troubleshoot/TSG10007315/"),
    ("LG dryer error codes, including gAS", "https://www.lg.com/us/support/help-library/lg-dryer-error-code-list--20154710772482"),
    ("Samsung washer will not drain", "https://www.samsung.com/us/support/troubleshoot/TSG10007110/"),
], f"Retrieved {TODAY_H}.")}
<p><a href="/codes/">Browse error codes</a></p>
</article>'''
    write("/guides/safety/", page("/guides/safety/", f"Appliance Error Code Safety | {BRAND}", "Unplug the appliance and shut off the gas before you go past the manufacturer's published checks.",
                                 body, [article_ld("Appliance error code safety", "/guides/safety/"), faq_ld(faqs)],
                                 [("/", "Home"), ("/guides/safety/", "Safety")]))

def simple(path, title, desc, h1, inner, crumb, faqs=None):
    body = f'<article class="prose"><h1>{E(h1)}</h1>{inner}</article>'
    ld = None
    if faqs:
        body = f'<article class="prose"><h1>{E(h1)}</h1>{inner}{faq_html(faqs)}</article>'
        ld = [article_ld(h1, path), faq_ld(faqs)]
    write(path, page(path, title, desc, body, ld, [("/", "Home"), (path, crumb)]))

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
<p>Last updated {TODAY_H}.</p>
<h2>Images</h2>
<p>The mark in the header, the favicon, and the social image are original graphics we made. They are not photographs of appliances and they are not brand logos.</p>
<h2>AI generated images</h2>
<p>This version uses no AI generated photographs. If we add one, the caption will say AI generated image, it will not show a real person, and it will not be presented as a photo of a real appliance.</p>
<h2>Logos and trademarks</h2>
<p>We do not display appliance brand logos. Names are used only to identify the product.</p>
<p>See <a href="/copyright/">copyright</a> or <a href="/contact/">contact</a> if you believe an image uses your work.</p>''', "Image policy")
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
<h2>Third party services</h2><p>We link to manufacturer sites and we use GitHub Pages, Cloudflare, and FormSubmit. We are not responsible for their content or practices.</p>
<h2>Disclaimer of warranties and limitation of liability</h2><p>The site is provided as is and as available. To the fullest extent permitted by law, Joshua Israel Ventures LLC disclaims all warranties and will not be liable for indirect, incidental, special, consequential, or punitive damages, or for a loss from your use of the site or from a repair you attempt. Our total liability for any claim relating to the site is limited to 100 US dollars.</p>
<h2>Indemnity</h2><p>You agree to indemnify Joshua Israel Ventures LLC against claims arising from your misuse of the site or your breach of these terms.</p>
<h2>Governing law</h2><p>These terms are governed by the laws of the State of Florida, United States, without regard to conflict of law rules. Courts in Florida have jurisdiction, and you consent to it.</p>
<h2>Changes</h2><p>We may update these terms. The date above is the latest version. Questions: <a href="/contact/">contact</a>.</p>'''),
        "/privacy/": ("Privacy Policy", f'''<p>Last updated {D}. This policy explains how Which Error Code, whicherrorcode.com, handles information. {LEGAL_LINE}</p>
<h2>Analytics</h2><p>When the site is on its own domain, we use Cloudflare Web Analytics to count page views. It does not use cookies and it does not track you across other sites. The preview build does not include the analytics script.</p>
<h2>Contact</h2><p>If you email {CONTACT_EMAIL} or use the contact form, we receive your name, email address, and message so we can reply. The form is handled by FormSubmit. We keep messages only as long as we need them to respond.</p>
<h2>Advertising</h2><p>The site shows no ads today. If we add ads later, we will update this policy first. You would be able to opt out of personalized advertising at Google Ads Settings and aboutads.info. Where the law requires it, we will ask for consent before advertising cookies are set.</p>
<h2>Cookies</h2><p>Which Error Code itself sets no cookies. The site works if your browser blocks cookies.</p>
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
        "/ad-disclosure/": ("Advertising and Affiliate Disclosure", f'''<p>Last updated {D}. {LEGAL_LINE} Which Error Code is free to use. The site shows no ads and it has no affiliate links. Later we may show advertising or add a link to a seller for an official part number. If we do, the link will be labeled and this page will change.</p>
<h2>Editorial independence</h2><p>No appliance maker pays for a code to be added or removed. Questions: <a href="/contact/">contact</a>.</p>'''),
    }
    for p, (t, inner) in legal.items():
        body = f'<article class="prose"><h1>{E(t)}</h1>{inner}<p class="legal-line">{LEGAL_LINE}</p></article>'
        write(p, page(p, f"{t} | {BRAND}", clip(f"{t} for Which Error Code, an independent guide to appliance error codes and water filters."), body, None, [("/", "Home"), (p, t)]))

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
             f"> Which Error Code (whicherrorcode.com) explains home appliance error codes and official refrigerator water filter numbers. Every code is cited to the manufacturer. Last verified {TODAY_H}.",
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
    for r in ROWS:
        if r["individual"]:
            code_page(r)
    seen = []
    for brand, appl, rows in GROUPS:
        enriched = []
        for row in rows:
            match = next(r for r in ROWS if r["brand"] == brand and r["appl"] == appl and r["code"] == row["code"])
            enriched.append(match)
        listing_page(brand, appl, enriched)
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

if __name__ == "__main__":
    main()
