# Which Error Code (whicherrorcode.com): launch checklist

Status 16 Nov 2026: the committed site is still the preview build, with a robots `noindex` meta on every page. Repo branch `main`, folder `/`. CNAME file is `whicherrorcode.com`. The domain is not bought in this step. $0 spent. `GA4_ID` in `_build/build.py` is an empty string until you paste a `G-XXXXXXXXXX` measurement id.

Do these steps in order after the domain is bought.

## 1. Buy the domain
Needs a yes on the exact price. Log the cost as an LLC expense.

## 2. DNS
- A records on @ for GitHub Pages: 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
- CNAME www to joshuaofisrael.github.io
- Add the Search Console TXT record at the same time.

## 3. Switch the repo to launch mode

Paste the Google Analytics 4 measurement id into `GA4_ID` in `_build/build.py` (`G-XXXXXXXXXX`). While that constant is empty, `python3 _build/check.py --launch` exits 1 and prints `ga4-id-empty`. It also exits 1 if any page is missing the Cloudflare Web Analytics beacon or the GA4 loader.

Exact launch command, from the repo root, after `GA4_ID` is set:

```
python3 _build/build.py --launch
python3 _build/check.py --launch
python3 _build/legal_gate.py check
```

`./deploy.sh --launch` runs those three commands and does not push. The launch build removes `noindex` from the robots meta tag, keeps root-relative paths and the `whicherrorcode.com` CNAME, and keeps the sitemap (with `lastmod`), robots.txt, llms.txt, and the IndexNow key file. Google Analytics 4 is requested only after the visitor accepts the consent banner. Then commit and push.

## 4. GitHub Pages custom domain
- Confirm `https_certificate` and enforce HTTPS when the certificate is approved.
- The robots meta should be indexable. `curl -s https://whicherrorcode.com/ | grep -o '<meta name="robots" content="[^"]*"'` should not contain `noindex`. A raw grep for the word noindex still matches the `noindex-flag` comment, so that count is not the test.
- Homepage, sitemap, and robots should return 200.

## 5. Analytics, Search Console, Bing
- Cloudflare Web Analytics loads on every launch page and does not use cookies. Add the host to the traffic list.
- Google Analytics 4 loads only after Accept on the banner. Consent Mode v2 starts denied. Cookie settings in the footer opens the banner again. The privacy policy names Google Analytics 4 and Cloudflare Web Analytics.
- Verify the domain property and submit https://whicherrorcode.com/sitemap.xml.
- Bing import needs a Microsoft sign in. After launch, `./indexnow.sh` pings the sitemap URLs.

## 6. Still open in the content
See the filter finder for cartridges and models that were not on an official list we could cite. Do not invent those pages.

## What v1 contains
Error code pages for Samsung, LG, GE Appliances, Whirlpool, Maytag, KitchenAid, and Bosch, limited to codes read on the manufacturer page. Filter pages for EDR1RXD1, XWFE, MWFP, and MWF, plus a filter light page that only repeats published reset behavior. Legal pages, sitemap, robots, and llms.txt.
