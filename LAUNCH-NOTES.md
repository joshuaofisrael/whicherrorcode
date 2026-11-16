# Which Error Code (whicherrorcode.com): launch checklist

Status 16 Nov 2026: v1 built with noindex on every page. Repo branch `main`, folder `/`. CNAME file is `whicherrorcode.com`. The domain is not bought in this step. $0 spent.

Do these steps in order after the domain is bought.

## 1. Buy the domain
Needs a yes on the exact price. Log the cost as an LLC expense.

## 2. DNS
- A records on @ for GitHub Pages: 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
- CNAME www to joshuaofisrael.github.io
- Add the Search Console TXT record at the same time.

## 3. Switch the repo to launch mode
```
./deploy.sh --launch
```
This removes noindex, adds the Cloudflare beacon, and keeps root paths and the CNAME file. Then commit and push.

## 4. GitHub Pages custom domain
- Confirm `https_certificate` and enforce HTTPS when the certificate is approved.
- `curl -s https://whicherrorcode.com/ | grep -c noindex` should be 0.
- Homepage, sitemap, and robots should return 200.

## 5. Analytics, Search Console, Bing
- Confirm the shared analytics beacon loads, then add the host to the traffic list.
- Verify the domain property and submit https://whicherrorcode.com/sitemap.xml.
- Bing import needs a Microsoft sign in. After launch, `./indexnow.sh` pings the sitemap URLs.

## 6. Still open in the content
See the filter finder for cartridges and models that were not on an official list we could cite. Do not invent those pages.

## What v1 contains
Error code pages for Samsung, LG, GE Appliances, Whirlpool, Maytag, KitchenAid, and Bosch, limited to codes read on the manufacturer page. Filter pages for EDR1RXD1, XWFE, MWFP, and MWF, plus a filter light page that only repeats published reset behavior. Legal pages, sitemap, robots, and llms.txt.
