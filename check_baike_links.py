#!/usr/bin/env python3
"""Check whether terms in data/baike.yaml are reachable on Baidu Baike.

Usage:
    python3 check_baike_links.py              # check all terms
    python3 check_baike_links.py --term DFT   # check a single term
    python3 check_baike_links.py --strict     # treat warnings as failures
    python3 check_baike_links.py --delay 2    # seconds between requests

Exit code is non-zero when any term fails (or, with --strict, warns).

Dependencies (install into the python that runs this script):
    pip install pyyaml curl_cffi
curl_cffi mimics a browser TLS fingerprint and is required to pass Baidu's
anti-bot checks; without it most requests are answered with HTTP 403.
"""
import argparse
import re
import sys
import time

try:
    import yaml
except ImportError:
    sys.exit("缺少 PyYAML 库，请先安装: pip install pyyaml")

try:
    from curl_cffi import requests as http
    TRANSPORT = "curl_cffi (模拟浏览器指纹)"
except ImportError:
    try:
        import requests as http
        TRANSPORT = "requests"
    except ImportError:
        sys.exit("缺少 HTTP 库，请先安装: pip install requests（建议 curl_cffi，可绕过百度反爬）")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def get(url, timeout):
    if TRANSPORT.startswith("curl_cffi"):
        return http.get(url, headers=HEADERS, impersonate="chrome", timeout=timeout)
    return http.get(url, headers=HEADERS, timeout=timeout)


def load_terms(path):
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    terms = []
    for item in data.get("terms", []):
        if isinstance(item, str):
            terms.append({"name": item.strip(), "url": None})
        elif isinstance(item, dict) and item.get("name"):
            terms.append(
                {"name": str(item["name"]).strip(), "url": item.get("url")}
            )
    return terms


def build_url(term):
    if term["url"]:
        return term["url"]
    return "https://baike.baidu.com/item/" + term["name"]


def check_term(term, timeout, retries):
    name, url = term["name"], build_url(term)
    for attempt in range(retries + 1):
        try:
            resp = get(url, timeout)
        except Exception as e:
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            return name, url, "fail", f"请求失败: {e}"
        final = resp.url
        m = TITLE_RE.search(resp.text)
        title = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        if "anticrawl" in final or "captcha" in final:
            if attempt < retries:
                time.sleep(3 * (attempt + 1))
                continue
            return name, url, "blocked", f"被百度反爬验证码拦截，请稍后重试: {final}"
        if resp.status_code == 404 or "error.html" in final:
            return name, url, "fail", "词条不存在（404），请在 data/baike.yaml 中配置 url 指向正确词条"
        if resp.status_code != 200:
            if attempt < retries:
                time.sleep(3 * (attempt + 1))
                continue
            return name, url, "blocked", f"HTTP {resp.status_code}，疑似被反爬拦截: {final}"
        if not final.startswith("https://baike.baidu.com/"):
            return name, url, "fail", f"跳转离开百度百科: {final}"
        if "/search" in final or "/searchword" in final:
            return name, url, "fail", f"跳转到搜索页（词条不存在）: {final}"
        if name in title:
            return name, url, "ok", f"词条存在（标题含术语）: {final}"
        if "_百度百科" in title:
            return name, url, "ok", f"词条页面正常（标题: {title}）: {final}"
        if name in resp.text:
            return name, url, "warn", f"标题未含术语，但页面正文出现（可能是未收录页）: {final}"
        return name, url, "fail", f"页面中未找到术语（可能是未收录页）: {final}"
    return name, url, "blocked", "重试次数用尽"


def main():
    parser = argparse.ArgumentParser(description="检查百度百科术语链接")
    parser.add_argument("--data", default="data/baike.yaml", help="术语数据文件")
    parser.add_argument("--term", action="append", help="只检查指定术语（可多次指定）")
    parser.add_argument("--delay", type=float, default=1.0, help="请求间隔秒数")
    parser.add_argument("--timeout", type=float, default=15.0, help="单次请求超时")
    parser.add_argument("--strict", action="store_true", help="警告也视为失败")
    parser.add_argument("--retries", type=int, default=2, help="反爬拦截时重试次数")
    args = parser.parse_args()

    terms = load_terms(args.data)
    if not terms:
        sys.exit(f"{args.data} 中没有找到任何术语")
    if args.term:
        wanted = set(args.term)
        known = {t["name"] for t in terms}
        extra = [{"name": n, "url": None} for n in wanted - known]
        terms = [t for t in terms if t["name"] in wanted] + extra
        if not terms:
            sys.exit("指定的术语在数据文件中不存在")

    counts = {"ok": 0, "warn": 0, "fail": 0, "blocked": 0}
    print(f"传输方式: {TRANSPORT}")
    for i, term in enumerate(terms):
        name, url, status, detail = check_term(term, args.timeout, args.retries)
        counts[status] += 1
        marks = {"ok": "[OK]   ", "warn": "[WARN] ", "fail": "[FAIL] ", "blocked": "[BLOCK]"}
        print(f"{marks[status]}{name} -> {url}\n        {detail}")
        if i < len(terms) - 1 and args.delay > 0:
            time.sleep(args.delay)

    print(
        f"\n汇总: {counts['ok']} 通过, {counts['warn']} 警告, "
        f"{counts['fail']} 失败, {counts['blocked']} 被拦截"
    )
    bad = counts["fail"] + (counts["warn"] + counts["blocked"] if args.strict else 0)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
