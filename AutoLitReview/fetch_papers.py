"""
fetch_papers.py - offline retrieval step for the AutoLitReview chatbot.

The chatbot generates concepts and hands you a command; you run this locally
(it calls the OpenAlex API, which the chatbot's environment cannot reach), then
paste the JSON it prints back into the chat. The chatbot resumes from there.

It is a trimmed copy of AutoLitReview.py's OpenAlex collector: same filters
(has_abstract, year range, optional --domain field, optional --core-only venue),
same DOI/title dedup. No LLM calls happen here.

Output: a JSON array on stdout, one object per unique paper:
  {"title", "abstract", "year", "source", "venue", "venue_quality"}
Progress goes to stderr, so `python fetch_papers.py ... > papers.json` (or piping
to your clipboard) yields a clean paste.

Requirements:
  pip install requests
  export OPENALEX_API_KEY=...        # OPTIONAL but recommended (higher rate limits); free at openalex.org/settings/api

Usage:
  python fetch_papers.py "open-source intelligence" "attribute inference" \
      "user profiling" "social engineering" \
      --per-concept 10 --year-from 2024 --year-to 2026 --domain cybersecurity

  # straight to clipboard (macOS):
  python fetch_papers.py "OSINT" "attribute inference" | pbcopy
"""
import os
import sys
import json
import argparse
import requests

OPENALEX_KEY = os.environ.get("OPENALEX_API_KEY", "")

# OpenAlex field IDs (level-2 of Domain->Field->Subfield->Topic), used by --domain
# as a hard server-side filter (primary_topic.field.id). Mirrors AutoLitReview.py.
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
        log(f"  searching: {c}")
        try:
            results = search_concept(c, per_concept, year_from, year_to,
                                     field_id, core_only)
        except requests.HTTPError as e:
            log(f"    (OpenAlex search failed for '{c}': {e})")
            continue
        for p in results:
            key = p["doi"] or p["title"].strip().lower()
            if key and key not in seen:
                seen.add(key)
                papers.append(p)
    return papers


def parse_args():
    p = argparse.ArgumentParser(
        description="Offline OpenAlex retrieval for the AutoLitReview chatbot. "
                    "Prints paste-ready JSON to stdout.")
    p.add_argument("concepts", nargs="+", help="one or more search concepts (quoted)")
    p.add_argument("--per-concept", type=int, default=10,
                   help="papers fetched per concept (default 10)")
    p.add_argument("--year-from", type=int, default=2024,
                   help="earliest publication year (default 2024)")
    p.add_argument("--year-to", type=int, default=2026,
                   help="latest publication year (default 2026)")
    p.add_argument("--domain", default=None,
                   help="restrict to an OpenAlex field, e.g. 'cybersecurity'. "
                        "Known: " + ", ".join(sorted(DOMAIN_FIELDS)))
    p.add_argument("--core-only", action="store_true",
                   help="keep only 'core' (reputable) venues; excludes preprints "
                        "like arXiv")
    p.add_argument("--out", default=None,
                   help="also write the JSON to this file")
    return p.parse_args()


def main():
    a = parse_args()
    if not OPENALEX_KEY:
        log("Tip: set OPENALEX_API_KEY for higher, stable rate limits "
            "(free key at openalex.org/settings/api). Continuing without it.")
    year_from, year_to = a.year_from, a.year_to
    if year_from > year_to:
        log(f"year-from ({year_from}) after year-to ({year_to}); swapping.")
        year_from, year_to = year_to, year_from

    field_id = None
    if a.domain:
        d = a.domain.lower().strip()
        if d.isdigit():
            field_id = int(d)                       # numeric OpenAlex field id, e.g. 17
            log(f"Domain filter: OpenAlex field id {field_id}")
        else:
            field_id = DOMAIN_FIELDS.get(d)
            if field_id is None:
                log(f"Unknown domain '{a.domain}' - searching without a field filter. "
                    f"Pass a numeric field id, or one of: {', '.join(sorted(DOMAIN_FIELDS))}")
            else:
                log(f"Domain filter: {a.domain} (OpenAlex field id {field_id})")
    if a.core_only:
        log("Venue filter: core sources only (excludes preprints like arXiv)")

    papers = collect(a.concepts, a.per_concept, year_from, year_to,
                     field_id, a.core_only)
    log(f"Collected {len(papers)} unique papers")
    if not papers:
        log("No papers found. Widen --year-from, relax --domain, drop --core-only, "
            "or check OPENALEX_API_KEY.")

    # Drop the internal doi key from the paste payload; keep the schema the chatbot expects.
    payload = [{k: p[k] for k in
                ("title", "abstract", "year", "source", "venue", "venue_quality")}
               for p in papers]
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    print(text)                       # stdout = clean JSON for copy-paste
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
        log(f"Wrote {a.out}")


if __name__ == "__main__":
    main()
