# Which Error Code (whicherrorcode.com)

Home appliance error codes and official refrigerator water filter numbers. Static site, GitHub Pages (branch `main`, folder `/`).

- Status 16 Nov 2026: v1 is a preview. Every page carries `noindex` until `python3 _build/build.py --launch`. The domain whicherrorcode.com is named in `CNAME` and is not treated as live until DNS exists.
- Build: `python3 _build/build.py` (noindex, root paths, CNAME, no analytics beacon) or `python3 _build/build.py --launch` (indexable, beacon on). Then `python3 _build/check.py [--launch]` and `python3 _build/legal_gate.py check`.
- `./deploy.sh [--launch]` runs build, check, and the legal gate. It does not push.
- Canonicals, sitemap, robots, llms.txt, and JSON-LD use https://whicherrorcode.com/. The single noindex flag is `NOINDEX` in `_build/build.py` (on unless `--launch`).
- Data lives in `_build/codes.py` and `_build/filters.py`. Add a code only when the manufacturer's page states it. Add a filter model only when the official page lists that model.
- IndexNow key: `e5e7fc4f0a0e96a11d330aa8cf3cba1c`. `./indexnow.sh` is for after the domain resolves.
- Contact: joshuaofisrael@gmail.com (mailto and the contact form).
- Launch steps are in LAUNCH-NOTES.md.
