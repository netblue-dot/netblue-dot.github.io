"""Refreshes data/portfolio/stats.json (Brent, EIA) and data/portfolio/news.json (UN News RSS).
Keys come from environment variables (GitHub Actions secrets). Nothing is invented:
if a source fails, its entry is left out and the site shows 'No verified data'."""
import json, os, urllib.request, urllib.parse, datetime as dt, xml.etree.ElementTree as ET

def get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "portfolio-data-bot"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
stats = {}

key = os.environ.get("EIA_API_KEY")
if key:
    try:
        q = urllib.parse.urlencode({
            "api_key": key, "frequency": "daily", "data[0]": "value",
            "facets[series][]": "RBRTE", "sort[0][column]": "period",
            "sort[0][direction]": "desc", "length": "1"})
        row = json.loads(get("https://api.eia.gov/v2/petroleum/pri/spt/data/?" + q))["response"]["data"][0]
        stats["brent"] = {"value": float(row["value"]), "prefix": "$", "suffix": "/bbl",
            "source": "US EIA, Europe Brent spot price", "observed": row["period"],
            "updated": now, "status": "delayed dataset"}
    except Exception as e:
        print("Brent failed:", e)

news = []
try:
    root = ET.fromstring(get("https://news.un.org/feed/subscribe/en/news/region/middle-east/feed/rss.xml"))
    for it in root.iter("item"):
        d = it.findtext("pubDate", "")
        try: d = dt.datetime.strptime(d[:25], "%a, %d %b %Y %H:%M:%S").strftime("%Y-%m-%d")
        except Exception: pass
        news.append({"title": it.findtext("title", "").strip(), "url": it.findtext("link", ""),
                     "source": "UN News", "date": d})
        if len(news) >= 15: break
except Exception as e:
    print("News failed:", e)

os.makedirs("data/portfolio", exist_ok=True)
json.dump(stats, open("data/portfolio/stats.json", "w"), indent=2)
json.dump(news, open("data/portfolio/news.json", "w"), indent=2)
print("stats:", list(stats), "news:", len(news))
