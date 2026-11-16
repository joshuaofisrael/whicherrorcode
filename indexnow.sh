#!/bin/bash
# Ping IndexNow after whicherrorcode.com is live. Do not run while the domain is unpublished.
KEY=e5e7fc4f0a0e96a11d330aa8cf3cba1c
cd "$(dirname "$0")"
if [ $# -gt 0 ]; then URLS=$(printf '"%s",' "$@"); else URLS=$(grep -o '<loc>[^<]*' sitemap.xml | sed 's/<loc>//' | sed 's/.*/"&"/' | paste -sd, -); fi
curl -s -o /dev/null -w "IndexNow HTTP %{http_code}\n" -H "Content-Type: application/json; charset=utf-8" https://api.indexnow.org/indexnow \
 -d "{\"host\":\"whicherrorcode.com\",\"key\":\"$KEY\",\"keyLocation\":\"https://whicherrorcode.com/$KEY.txt\",\"urlList\":[${URLS%,}]}"
