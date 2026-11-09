"""1단계: 후보 발견 (토큰 0). RSS·Google News RSS·arXiv·OpenAlex.

개별 소스 실패는 [WARN]으로 남기고 계속한다. 결과와 함께 소스별 상태(coverage)를 반환한다.
"""
import hashlib
import re
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

import feedparser
import requests

import config

UA = "2027MobilityUpdates/1.0 (+github pages archive)"
TIMEOUT = 20

TRACKING = re.compile(r"^(utm_|fbclid|gclid|ref$|cmpid|ocid)")


def norm_url(url: str) -> str:
    p = urllib.parse.urlsplit(url.strip())
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if not TRACKING.match(k)]
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower().removeprefix("www."),
                                    p.path.rstrip("/"), urllib.parse.urlencode(q), ""))


def uid(url: str) -> str:
    return hashlib.sha1(norm_url(url).encode()).hexdigest()[:12]


def _get(url: str):
    for attempt in range(2):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
            r.raise_for_status()
            return r
        except Exception as e:  # noqa: BLE001
            if attempt == 1:
                raise e
            time.sleep(2)


def _entry_time(e):
    for k in ("published_parsed", "updated_parsed"):
        if e.get(k):
            return datetime(*e[k][:6], tzinfo=timezone.utc)
    return None


def _clean(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def _parse_feed(text, *, source, region, country, kind, cutoff):
    out = []
    for e in feedparser.parse(text).entries[: config.MAX_PER_QUERY]:
        t = _entry_time(e)
        if t and t < cutoff:
            continue
        link = e.get("link", "")
        if not link:
            continue
        publisher = source
        if kind == "gnews" and e.get("source"):
            publisher = e["source"].get("title", source)
        title = _clean(e.get("title", ""))
        if kind == "gnews" and publisher and title.endswith(" - " + publisher):
            title = title[: -len(" - " + publisher)]
        out.append({
            "id": uid(link), "url": link, "title": title,
            "snippet": _clean(e.get("summary", ""))[:400],
            "publisher": publisher, "region": region, "country": country,
            "published": t.isoformat() if t else None, "kind": kind,
        })
    return out


def gnews_url(query, hl, gl, ceid):
    q = urllib.parse.quote(f"{query} when:1d")
    return f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"


def fetch_all(now=None):
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=config.LOOKBACK_HOURS)
    items, status = [], []

    for region, countries in config.REGIONS.items():
        for country, hl, gl, ceid, queries in countries:
            for q in queries:
                name = f"Google News {country}: {q}"
                try:
                    r = _get(gnews_url(q, hl, gl, ceid))
                    got = _parse_feed(r.content, source="Google News", region=region,
                                      country=country, kind="gnews", cutoff=cutoff)
                    items += got
                    status.append({"source": name, "region": region, "country": country, "ok": True, "n": len(got)})
                except Exception as e:  # noqa: BLE001
                    print(f"[WARN] {name}: {e}")
                    status.append({"source": name, "region": region, "country": country, "ok": False, "n": 0, "error": str(e)[:120]})
                time.sleep(0.5)

    for name, url, region, country in config.DIRECT_FEEDS:
        try:
            r = _get(url)
            got = _parse_feed(r.content, source=name, region=region, country=country, kind="rss", cutoff=cutoff)
            items += got
            status.append({"source": name, "region": region, "country": country, "ok": True, "n": len(got)})
        except Exception as e:  # noqa: BLE001
            print(f"[WARN] {name}: {e}")
            status.append({"source": name, "region": region, "country": country, "ok": False, "n": 0, "error": str(e)[:120]})

    items += _arxiv(cutoff, status)
    items += _openalex(now, status)

    # URL 기준 중복 제거 (같은 기사가 여러 쿼리에 걸린 경우)
    uniq = {}
    for it in items:
        uniq.setdefault(it["id"], it)
    return list(uniq.values()), status


def _arxiv(cutoff, status):
    url = ("http://export.arxiv.org/api/query?search_query=" + urllib.parse.quote(config.ARXIV_QUERY)
           + "&sortBy=submittedDate&sortOrder=descending&max_results=50")
    try:
        r = _get(url)
        got = []
        for e in feedparser.parse(r.content).entries:
            t = _entry_time(e)
            if t and t < cutoff - timedelta(days=2):  # arXiv 공개 지연 감안
                continue
            got.append({
                "id": uid(e.link), "url": e.link, "title": _clean(e.title),
                "snippet": _clean(e.get("summary", ""))[:900], "publisher": "arXiv",
                "region": "글로벌", "country": "글로벌", "published": t.isoformat() if t else None,
                "kind": "paper", "authors": ", ".join(a.name for a in e.get("authors", [])[:6]),
            })
        status.append({"source": "arXiv", "region": "글로벌", "country": "글로벌", "ok": True, "n": len(got)})
        return got
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] arXiv: {e}")
        status.append({"source": "arXiv", "region": "글로벌", "country": "글로벌", "ok": False, "n": 0, "error": str(e)[:120]})
        return []


def _openalex(now, status):
    since = (now - timedelta(days=3)).date().isoformat()
    got = []
    for s in config.OPENALEX_SEARCHES:
        url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(s)
               + f"&filter=from_publication_date:{since},type:article|preprint|proceedings-article"
               + "&per-page=25&select=id,doi,title,publication_date,authorships,primary_location,abstract_inverted_index")
        try:
            for w in _get(url).json().get("results", []):
                link = w.get("doi") or w["id"]
                abstract = ""
                inv = w.get("abstract_inverted_index") or {}
                if inv:
                    pos = sorted((p, word) for word, ps in inv.items() for p in ps)
                    abstract = " ".join(word for _, word in pos)[:900]
                venue = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or "OpenAlex"
                got.append({
                    "id": uid(link), "url": link, "title": w.get("title") or "", "snippet": abstract,
                    "publisher": venue, "region": "글로벌", "country": "글로벌",
                    "published": w.get("publication_date"), "kind": "paper",
                    "authors": ", ".join(a["author"]["display_name"] for a in w.get("authorships", [])[:6]),
                })
        except Exception as e:  # noqa: BLE001
            print(f"[WARN] OpenAlex {s}: {e}")
            status.append({"source": f"OpenAlex: {s}", "region": "글로벌", "country": "글로벌", "ok": False, "n": 0, "error": str(e)[:120]})
    status.append({"source": "OpenAlex", "region": "글로벌", "country": "글로벌", "ok": True, "n": len(got)})
    return got
