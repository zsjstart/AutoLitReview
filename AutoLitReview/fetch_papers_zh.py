"""
fetch_papers.py —— AutoLitReview 聊天助手的离线检索步骤。

聊天助手负责生成概念并给你一条命令；你在本地运行本脚本（它调用 OpenAlex API，
而聊天助手的环境无法访问），再把它打印的 JSON 粘贴回聊天框，助手便从这里继续。

它是 AutoLitReview.py 中 OpenAlex 收集器的精简版：相同的过滤条件
（has_abstract、年份区间、可选的 --domain 学科、可选的 --core-only 期刊/会议），
相同的 DOI/标题去重。本脚本不调用任何大模型。

输出：stdout 上的一个 JSON 数组，每篇唯一论文一个对象：
  {"title", "abstract", "year", "source", "venue", "venue_quality"}
进度信息写入 stderr，因此 `python fetch_papers.py ... > papers.json`
（或用管道送入剪贴板）得到的就是干净、可直接粘贴的内容。

环境要求：
  pip install requests
  export OPENALEX_API_KEY=...        # 可选但推荐（更高速率上限）；免费：openalex.org/settings/api

用法：
  python fetch_papers.py "open-source intelligence" "attribute inference" \
      "user profiling" "social engineering" \
      --per-concept 10 --year-from 2024 --year-to 2026 --domain cybersecurity

  # 直接送入剪贴板（macOS）：
  python fetch_papers.py "OSINT" "attribute inference" | pbcopy
"""
import os
import sys
import json
import argparse
import requests

OPENALEX_KEY = os.environ.get("OPENALEX_API_KEY", "")

# OpenAlex 学科字段 ID（Domain->Field->Subfield->Topic 的第二层），供 --domain
# 作为服务端硬过滤使用（primary_topic.field.id）。与 AutoLitReview.py 保持一致。
DOMAIN_FIELDS = {
    "cybersecurity": 17, "computer science": 17, "cs": 17,
    "engineering": 22, "materials science": 25, "mathematics": 26,
    "physics": 31, "biology": 13, "chemistry": 16,
    "medicine": 27, "psychology": 32, "social sciences": 33,
    "economics": 20, "neuroscience": 28, "environmental science": 23,
}


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def reconstruct_abstract(inverted_index):
    if not inverted_index:
        return ""
    words = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[i] for i in sorted(words))


def venue_quality(is_core, is_doaj):
    if is_core:
        return "Core"
    if is_doaj:
        return "DOAJ"
    return "Other"


def search_concept(concept, per_concept, year_from, year_to,
                   field_id=None, core_only=False):
    filters = ["has_abstract:true", f"publication_year:{year_from}-{year_to}"]
    if field_id:
        filters.append(f"primary_topic.field.id:{field_id}")
    if core_only:
        filters.append("primary_location.source.is_core:true")
    params = {
        "search": concept,
        "per-page": per_concept,
        "filter": ",".join(filters),
        "sort": "relevance_score:desc",
    }
    if OPENALEX_KEY:
        params["api_key"] = OPENALEX_KEY
    resp = requests.get("https://api.openalex.org/works", params=params, timeout=30)
    resp.raise_for_status()
    out = []
    for w in resp.json().get("results", [])[:per_concept]:
        loc = w.get("primary_location") or {}
        source_obj = loc.get("source") or {}
        src = (w.get("doi") or loc.get("landing_page_url")
               or source_obj.get("homepage_url") or "")
        is_core = bool(source_obj.get("is_core"))
        is_doaj = bool(source_obj.get("is_in_doaj"))
        out.append({
            "doi": (w.get("doi") or "").lower(),
            "title": w.get("title") or "",
            "abstract": reconstruct_abstract(w.get("abstract_inverted_index")),
            "year": w.get("publication_year") or "",
            "source": src,
            "venue": source_obj.get("display_name") or "",
            "venue_quality": venue_quality(is_core, is_doaj),
        })
    return out


def collect(concepts, per_concept, year_from, year_to, field_id, core_only):
    seen, papers = set(), []
    for c in concepts:
        log(f"  正在检索：{c}")
        try:
            results = search_concept(c, per_concept, year_from, year_to,
                                     field_id, core_only)
        except requests.HTTPError as e:
            log(f"    （概念 '{c}' 检索失败：{e}）")
            continue
        for p in results:
            key = p["doi"] or p["title"].strip().lower()
            if key and key not in seen:
                seen.add(key)
                papers.append(p)
    return papers


def parse_args():
    p = argparse.ArgumentParser(
        description="AutoLitReview 聊天助手的离线 OpenAlex 检索脚本，"
                    "把可直接粘贴的 JSON 打印到 stdout。")
    p.add_argument("concepts", nargs="+", help="一个或多个检索概念（用引号括起）")
    p.add_argument("--per-concept", type=int, default=10,
                   help="每个概念抓取的论文数（默认 10）")
    p.add_argument("--year-from", type=int, default=2024,
                   help="最早发表年份（默认 2024）")
    p.add_argument("--year-to", type=int, default=2026,
                   help="最晚发表年份（默认 2026）")
    p.add_argument("--domain", default=None,
                   help="限定到某个 OpenAlex 学科，例如 'cybersecurity'。"
                        "可选：" + "、".join(sorted(DOMAIN_FIELDS)))
    p.add_argument("--core-only", action="store_true",
                   help="只保留 'core'（权威）来源；会排除 arXiv 等预印本")
    p.add_argument("--out", default=None,
                   help="同时把 JSON 写入该文件")
    return p.parse_args()


def main():
    a = parse_args()
    if not OPENALEX_KEY:
        log("提示：设置 OPENALEX_API_KEY 可获得更高、更稳定的速率上限"
            "（免费密钥：openalex.org/settings/api）。当前将不带密钥继续。")
    year_from, year_to = a.year_from, a.year_to
    if year_from > year_to:
        log(f"year-from（{year_from}）晚于 year-to（{year_to}），已自动交换。")
        year_from, year_to = year_to, year_from

    field_id = None
    if a.domain:
        d = a.domain.lower().strip()
        if d.isdigit():
            field_id = int(d)                       # numeric OpenAlex field id, e.g. 17
            log(f"学科过滤：OpenAlex 字段 id {field_id}")
        else:
            field_id = DOMAIN_FIELDS.get(d)
            if field_id is None:
                log(f"未知学科 '{a.domain}'，将不加学科过滤进行检索。"
                    f"可传入数字字段 id，或用：{'、'.join(sorted(DOMAIN_FIELDS))}")
            else:
                log(f"学科过滤：{a.domain}（OpenAlex 字段 id {field_id}）")
    if a.core_only:
        log("来源过滤：仅 core 来源（排除 arXiv 等预印本）")

    papers = collect(a.concepts, a.per_concept, year_from, year_to,
                     field_id, a.core_only)
    log(f"共收集到 {len(papers)} 篇唯一论文")
    if not papers:
        log("未找到论文。可放宽 --year-from、去掉 --domain、移除 --core-only，"
            "或检查 OPENALEX_API_KEY。")

    # 丢弃内部使用的 doi 键，输出聊天助手期望的 schema。
    payload = [{k: p[k] for k in
                ("title", "abstract", "year", "source", "venue", "venue_quality")}
               for p in papers]
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    print(text)                       # stdout = 干净的 JSON，可直接复制
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
        log(f"已写入 {a.out}")


if __name__ == "__main__":
    main()
