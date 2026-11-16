#!/usr/bin/env python3
"""Pre-publish legal hold gate for Which Error Code.
Adapted from the Which Cabin gate. Usage: legal_gate.py check [--no-queue]
Exit 0 when every page passes. Exit 3 when a page is HOLD_REVIEW.
"""
import sys, os, re, json, hashlib, datetime, glob, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "whicherrorcode.com"
BOT = "Which Error Code build"
CR = os.environ.get("CONTENT_REVIEW_DIR", "/workspace/content-review")
Q = CR + "/queue.jsonl"
DR = CR + "/drafts/whicherrorcode"
REPO_LISTS = os.path.join(ROOT, "legal")
HIGH = {1, 2, 6, 8}
OBJECTIVE = {3, 4}
LEGAL_PAGES = ("privacy", "terms", "contact", "disclaimer", "copyright", "ad-disclosure", "about", "image-policy", "methodology")
KW = {
    1: r"\b(fraud\w*|scam\w*|corrupt(ion|ly)?|embezzl\w*|arrested|indicted|charged with|convicted|lawsuits?|sued|suing|misconduct|abus(e|ed|ive)|dishonest\w*|cover[ -]?up|criminal|bribe\w*|negligen\w*|cheat(s|ed|ing)?|rip[ -]?off)\b",
    5: r"\b(guaranteed returns?|tax advice|legal advice|medical advice|you should (sue|claim compensation)|take \d+ ?mg)\b",
    6: r"\b(election|ballot|polling (place|station)|voter registration|vote by|voting day|certified results?|electoral)\b",
    7: r"\b(official partner|endorsed by|in partnership with|certified by|approved by the|100% (safe|accurate)|guaranteed (best|quiet|fix))\b",
    8: r"\b(embargo(ed)?|cease and desist|dmca|takedown notice|legal notice|reporting restriction|correction request)\b",
}

def lines(name):
    out = []
    for p in (os.path.join(CR, name), os.path.join(REPO_LISTS, name)):
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out

def approved(h):
    return any(j.get("site") == SITE and j.get("sha256") == h and str(j.get("approved_by", "")).lower().startswith("joshua") for j in lines("approvals.jsonl"))

def cleared(h):
    return any(j.get("site") == SITE and j.get("sha256") == h and str(j.get("chatgpt_verdict", "")).upper().startswith("SAFE") for j in lines("moderate-clearances.jsonl"))

def visible(raw):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip()

def scan(raw, rel):
    text = visible(raw)
    top = rel.split("/")[0]
    legal = top in LEGAL_PAGES
    R = []
    for n, rx in KW.items():
        for m in re.finditer(rx, text, re.I):
            if n == 8 and m.group(0).lower() == "dmca" and (top == "copyright" or text[max(0, m.start() - 14):m.end()] == "Copyright and DMCA"):
                continue
            if n in (5, 7) and re.search(r"\b(not|never|no|nor|isn'?t|aren'?t|without)\b[^.]{0,40}$", text[max(0, m.start() - 55):m.start()], re.I):
                continue
            R.append((n, m.group(0), "keyword tripwire; review"))
            break
    if not legal:
        m = re.search(r"[\w.+-]+@[\w-]+\.[a-z][\w.]+", text)
        if m:
            R.append((2, m.group(0), "email address"))
        m = re.search(r"(?<![\w/.:,-])(\+\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?![\w-])", text)
        if m:
            R.append((2, m.group(0).strip(), "possible phone number"))
        m = re.search(r"\b\d{1,5}\s+[A-Z][a-z]+(\s[A-Z][a-z]+)*\s(Street|St|Road|Rd|Drive|Dr|Avenue|Ave|Lane|Ln|Court|Ct|Boulevard|Blvd)\b", text)
        if m:
            R.append((2, m.group(0), "possible street address"))
    for u in re.findall(r"""<(?:img|source|video)[^>]+src=["'](https?://[^"']+)""", raw, re.I):
        R.append((3, u, "remote image or video; self host it or drop it"))
        break
    if top in ("codes", "filters", "guides") and "index.html" in rel:
        sec = re.search(r'<section class="sources".*?</section>', raw, re.S)
        if not sec or not re.search(r'href="https?://', sec.group(0)):
            R.append((4, "(no source URLs)", "page cites no source actually accessed"))
    return text, R

def sev(R):
    return "HIGH" if any(n in HIGH for n, _, _ in R) else ("MODERATE" if R else None)

def verdict(R, h):
    if not R:
        return "PASS"
    if approved(h):
        return "PASS (Joshua approved hash)"
    if sev(R) == "MODERATE" and not any(n in OBJECTIVE for n, _, _ in R) and cleared(h):
        return "PASS (MODERATE, cleared hash)"
    return "HOLD_REVIEW"

def main(a):
    if not a or a[0] != "check":
        print(__doc__)
        return 2
    noq = "--no-queue" in a
    bad = n = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "**/*.html"), recursive=True)):
        if "/_build/" in f:
            continue
        rel = os.path.relpath(f, ROOT)
        raw = open(f, encoding="utf-8").read()
        text, R = scan(raw, rel)
        h = hashlib.sha256(text.encode()).hexdigest()
        v = verdict(R, h)
        n += 1
        if v == "HOLD_REVIEW":
            bad += 1
            print("HOLD_REVIEW", sev(R), rel, "sha256", h[:12])
            for rule, excerpt, why in R:
                print(f"  rule {rule}: {excerpt!r} {why}")
            if not noq:
                os.makedirs(os.path.dirname(Q), exist_ok=True)
                os.makedirs(DR, exist_ok=True)
                dp = os.path.join(DR, rel.replace("/", "__") + ".HOLD_REVIEW.html")
                open(dp, "w", encoding="utf-8").write(raw)
                title = (re.search(r"<title>(.*?)</title>", raw) or [None, rel])[1]
                open(Q, "a", encoding="utf-8").write(json.dumps({
                    "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                    "site": SITE, "bot": BOT, "title": html.unescape(title),
                    "flagged": "; ".join(f"[{r}] {x}" for r, x, _ in R),
                    "rule": sorted(set(r for r, _, _ in R)),
                    "sources": re.findall(r'href="(https?://[^"]+)"', raw)[:20],
                    "suggestion": "; ".join(sorted(set(s for _, _, s in R))),
                    "severity": sev(R), "draft_path": dp, "sha256": h, "status": "HOLD_REVIEW",
                }, ensure_ascii=False) + "\n")
        elif R:
            print(v, rel)
    print(f"legal gate: {n} pages checked, {bad} HOLD_REVIEW")
    return 3 if bad else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
