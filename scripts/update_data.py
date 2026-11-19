"""Refreshes data/portfolio/stats.json and news.json.
Sources: US EIA (Brent), UNHCR (displacement), World Bank (trade), UN News (headlines).
Nothing is invented: if a source fails, its entry is left out and the site shows 'No verified data'."""
import gzip, json, os, urllib.request, urllib.parse, datetime as dt, xml.etree.ElementTree as ET

BROWSER = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

def get(url, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": BROWSER,
        "Accept": "application/json, application/rss+xml, application/xml;q=0.9, */*;q=0.8",
        "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    return data

def num(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
stats = {}

# 1. Brent crude (US EIA)
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

# 2. Displaced people originating from Syria and Yemen (UNHCR)
try:
    for year in (2025, 2024, 2023):
        q = urllib.parse.urlencode([("cf_type", "ISO"), ("coo", "SYR,YEM"),
                                    ("coo_all", "true"), ("year[]", str(year))])
        items = json.loads(get("https://api.unhcr.org/population/v1/population/?" + q)).get("items", [])
        if items:
            total = sum(num(i.get(k)) for i in items
                        for k in ("refugees", "asylum_seekers", "idps", "oip"))
            if total > 0:
                stats["displaced"] = {"value": total,
                    "source": "UNHCR, refugees, asylum-seekers, IDPs and others needing protection, originating from Syria and Yemen",
                    "observed": "end of %d" % year, "updated": now, "status": "annual dataset"}
                break
    if "displaced" not in stats:
        print("Displaced: no data returned")
except Exception as e:
    print("Displaced failed:", e)

# 3. Regional trade (World Bank: trade as % of GDP, Middle East & North Africa)
for code in ("MEA", "MNA"):
    try:
        url = ("https://api.worldbank.org/v2/country/%s/indicator/NE.TRD.GNFS.ZS"
               "?format=json&mrnev=1&per_page=1" % code)
        row = json.loads(get(url))[1][0]
        if row.get("value") is not None:
            stats["trade"] = {"value": float(row["value"]), "suffix": "% of GDP",
                "source": "World Bank, trade in goods and services, Middle East & North Africa",
                "observed": str(row["date"]), "updated": now, "status": "annual dataset"}
            break
    except Exception as e:
        print("Trade failed (%s):" % code, e)

# 4. Headlines (UN News, Middle East)
news = []
raw = b""
try:
    raw = get("https://news.un.org/feed/subscribe/en/news/region/middle-east/feed/rss.xml")
    root = ET.fromstring(raw.lstrip(b"\xef\xbb\xbf").strip())
    for it in root.iter("item"):
        d = it.findtext("pubDate", "")
        try: d = dt.datetime.strptime(d[:25], "%a, %d %b %Y %H:%M:%S").strftime("%Y-%m-%d")
        except Exception: pass
        news.append({"title": it.findtext("title", "").strip(), "url": it.findtext("link", ""),
                     "source": "UN News", "date": d})
        if len(news) >= 15: break
except Exception as e:
    print("News failed:", e)
    print("First bytes received:", raw[:200])

os.makedirs("data/portfolio", exist_ok=True)
json.dump(stats, open("data/portfolio/stats.json", "w"), indent=2)
json.dump(news, open("data/portfolio/news.json", "w"), indent=2)
print("stats:", list(stats), "news:", len(news))
