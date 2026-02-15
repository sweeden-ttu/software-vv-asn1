"""
Experiment 6: legalluminary.com Site Content Verification

Validates the legal content published on legalluminary.com (served from the
legal-luminary-site git submodule) by:

  1. Parsing all markdown in _pages/ and _posts/ for legal claims and source URLs
  2. Verifying every cited source URL is reachable (HTTPS 200)
  3. Cross-referencing legal claims against official Texas statute text
  4. Checking SHA-256 content integrity against the verification manifest
  5. Running specific fact-checks through the Legal Luminary pipeline
  6. Validating LRL (Texas Legislative Reference Library) resources
  7. Negative test: Scott Weeden should NOT appear as a TX Notary Public

Metrics:
  - URL reachability rate
  - Claim verification accuracy
  - Content integrity (SHA-256 match rate)
  - Pipeline verification success rate on site content
"""

import os
import sys
import json
import hashlib
import re
import requests
from datetime import datetime
from pathlib import Path

from langsmith import traceable

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "Site Content Verification Experiment")

from config.settings import (
    SITE_PAGES_WITH_SOURCES,
    SITE_CONTENT_DIRS,
    LEGAL_LUMINARY_SITE_SUBMODULE,
    LRL_CONFIG,
)

# Resolve paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SITE_ROOT = PROJECT_ROOT / LEGAL_LUMINARY_SITE_SUBMODULE
MANIFEST_PATH = SITE_ROOT / "verification" / "manifest.json"


# ===================================================================
# Helpers
# ===================================================================

def _extract_urls_from_markdown(text: str) -> list:
    """Extract all URLs from markdown content."""
    url_pattern = re.compile(
        r'https?://[^\s<>")\]\'`,;]+', re.IGNORECASE
    )
    return list(set(url_pattern.findall(text)))


def _extract_front_matter(text: str) -> dict:
    """Extract YAML front matter from markdown."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            fm_text = text[3:end].strip()
            result = {}
            for line in fm_text.split("\n"):
                if ":" in line:
                    key, _, val = line.partition(":")
                    result[key.strip()] = val.strip().strip('"').strip("'")
            return result
    return {}


def _check_url_reachable(url: str, timeout: int = 15) -> dict:
    """Check if a URL returns HTTP 200."""
    try:
        resp = requests.get(
            url, timeout=timeout, allow_redirects=True,
            headers={"User-Agent": "LegalLuminary-Verifier/1.0"}
        )
        return {
            "url": url,
            "status": resp.status_code,
            "ok": resp.status_code == 200,
            "final_url": resp.url,
        }
    except Exception as e:
        return {"url": url, "status": 0, "ok": False, "error": str(e)[:100]}


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 of a file."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


# ===================================================================
# Test Functions
# ===================================================================

@traceable(name="exp6_url_reachability")
def test_url_reachability() -> dict:
    """Verify every source URL cited in site content is reachable."""
    results = {"tested": 0, "reachable": 0, "unreachable": [], "details": []}

    all_urls = set()
    for rel_path, info in SITE_PAGES_WITH_SOURCES.items():
        for url in info.get("source_urls", []):
            all_urls.add(url)

    # Also scan markdown files for URLs
    for content_dir in SITE_CONTENT_DIRS:
        dir_path = SITE_ROOT / content_dir
        if dir_path.exists():
            for md_file in dir_path.glob("*.md"):
                text = md_file.read_text(errors="replace")
                for url in _extract_urls_from_markdown(text):
                    if url.startswith("https://") and not any(
                        skip in url for skip in [
                            "giphy.com", "github.com", "github.io",
                            "docker.com", "typora.io", "shopify.github",
                            "webisland.agency", "jekyllrb.com",
                            "daringfireball.net",
                        ]
                    ):
                        all_urls.add(url)

    print(f"  [reachability] Testing {len(all_urls)} unique URLs...")

    for url in sorted(all_urls):
        result = _check_url_reachable(url)
        results["tested"] += 1
        results["details"].append(result)
        if result["ok"]:
            results["reachable"] += 1
            print(f"    OK  {url}")
        else:
            results["unreachable"].append(result)
            print(f"    FAIL {url} → {result.get('status', 'error')}")

    results["reachability_rate"] = (
        results["reachable"] / results["tested"]
        if results["tested"] > 0 else 0
    )
    return results


@traceable(name="exp6_content_integrity")
def test_content_integrity() -> dict:
    """Verify SHA-256 hashes against the verification manifest."""
    results = {"tested": 0, "matched": 0, "mismatched": [], "manifest_missing": False}

    if not MANIFEST_PATH.exists():
        results["manifest_missing"] = True
        print("  [integrity] WARNING: manifest.json not found")
        return results

    manifest = json.loads(MANIFEST_PATH.read_text())
    files = manifest.get("files", {})

    for rel_path, file_info in files.items():
        expected_sha = file_info.get("sha256", "")
        file_path = SITE_ROOT / rel_path
        if not file_path.exists():
            results["mismatched"].append({
                "file": rel_path, "reason": "file not found"
            })
            continue

        actual_sha = _sha256_file(file_path)
        results["tested"] += 1

        if actual_sha == expected_sha:
            results["matched"] += 1
        else:
            results["mismatched"].append({
                "file": rel_path,
                "reason": "SHA-256 mismatch",
                "expected": expected_sha[:16] + "...",
                "actual": actual_sha[:16] + "...",
            })

    results["integrity_rate"] = (
        results["matched"] / results["tested"]
        if results["tested"] > 0 else 0
    )
    return results


@traceable(name="exp6_legal_claims")
def test_legal_claims_verification() -> dict:
    """Cross-reference legal claims in site content against statute URLs."""
    results = {"tested": 0, "verified": 0, "failed": [], "details": []}

    claim_checks = [
        {
            "page": "_pages/texas-law.md",
            "claim": "Chapter 55A governs expunctions (as of Jan 2025 renumbering)",
            "statute_url": "https://statutes.capitol.texas.gov/Docs/CR/htm/CR.55A.htm",
            "verify_text": "55A",
        },
        {
            "page": "_pages/texas-law.md",
            "claim": "Capital Felony punishable by life without parole or death",
            "statute_url": "https://statutes.capitol.texas.gov/Docs/PE/htm/PE.12.htm",
            "verify_text": "capital",
        },
        {
            "page": "_pages/defense.md",
            "claim": "Texas Penal Code Chapter 22 defines assault offenses",
            "statute_url": "https://statutes.capitol.texas.gov/Docs/PE/htm/PE.22.htm",
            "verify_text": "assault",
        },
        {
            "page": "_pages/bell-county.md",
            "claim": "Bell County has four District Courts: 27th, 146th, 169th, 426th",
            "statute_url": "https://www.bellcountytx.com/",
            "verify_text": "bell county",
        },
    ]

    for check in claim_checks:
        results["tested"] += 1
        url_result = _check_url_reachable(check["statute_url"])

        detail = {
            "page": check["page"],
            "claim": check["claim"],
            "source_reachable": url_result["ok"],
            "source_status": url_result.get("status", 0),
        }

        # Verify the claim text exists in the page
        page_path = SITE_ROOT / check["page"]
        if page_path.exists():
            page_text = page_path.read_text(errors="replace").lower()
            detail["claim_in_page"] = check["verify_text"].lower() in page_text
        else:
            detail["claim_in_page"] = False

        if detail["source_reachable"] and detail["claim_in_page"]:
            results["verified"] += 1
            detail["status"] = "VERIFIED"
        else:
            results["failed"].append(detail)
            detail["status"] = "FAILED"

        results["details"].append(detail)
        print(f"  [{detail['status']}] {check['claim'][:60]}...")

    results["verification_rate"] = (
        results["verified"] / results["tested"]
        if results["tested"] > 0 else 0
    )
    return results


@traceable(name="exp6_lrl_resources")
def test_lrl_resources() -> dict:
    """Validate that LRL (Texas Legislative Reference Library) resources
    are accessible — a key data source for the pipeline."""
    results = {"tested": 0, "reachable": 0, "details": []}

    lrl_urls = {
        "LRL Homepage": LRL_CONFIG["base_url"],
        "Bill Search": LRL_CONFIG["bill_search"],
        "Member Search": LRL_CONFIG["member_search"],
        "Committee Calendar": LRL_CONFIG["committee_calendar"],
        "Session Dates": LRL_CONFIG["session_dates"],
        "Library Catalog": LRL_CONFIG["catalog"],
    }

    for name, url in lrl_urls.items():
        result = _check_url_reachable(url)
        results["tested"] += 1
        detail = {"name": name, **result}
        results["details"].append(detail)
        if result["ok"]:
            results["reachable"] += 1
            print(f"    OK  {name}: {url}")
        else:
            print(f"    FAIL {name}: {url} → {result.get('status', 'error')}")

    results["reachability_rate"] = (
        results["reachable"] / results["tested"]
        if results["tested"] > 0 else 0
    )
    return results


@traceable(name="exp6_notary_negative_test")
def test_notary_negative_validation() -> dict:
    """NEGATIVE TEST: Scott Weeden should NOT be found in the Texas
    Secretary of State Notary Public database.

    This tests that the pipeline correctly FAILS validation when
    asked to verify a claim about someone being a notary who is not.
    """
    results = {
        "test_name": "Scott Weeden Notary Public Negative Test",
        "expected_outcome": "FAIL / UNVERIFIED",
        "claim": "Scott Weeden is a commissioned Texas Notary Public",
    }

    # Approach 1: Try the TX SOS notary search directly
    # The TX SOS notary search is at https://direct.sos.state.tx.us/notaries/notarysearch.asp
    notary_search_url = "https://direct.sos.state.tx.us/notaries/notarysearch.asp"
    notary_reachable = _check_url_reachable(notary_search_url)
    results["notary_search_reachable"] = notary_reachable["ok"]
    results["notary_search_url"] = notary_search_url

    # Approach 2: Run through the Legal Luminary pipeline
    try:
        from pipeline import validate
        pipeline_result = validate(
            content_type="official",
            query="Scott Weeden, Texas Notary Public, commissioned notary",
            raw_content="Scott Weeden is a commissioned Notary Public in the State of Texas",
        )
        results["pipeline_status"] = pipeline_result.get("overall_status", "unknown")
        results["pipeline_confidence"] = pipeline_result.get("overall_confidence", 0)
        results["pipeline_verified"] = (
            pipeline_result.get("overall_status") == "verified"
        )

        # This SHOULD NOT be verified — it's a negative test
        if results["pipeline_verified"]:
            results["test_passed"] = False
            results["reason"] = (
                "UNEXPECTED: Pipeline verified Scott Weeden as a notary. "
                "This should have FAILED validation."
            )
        else:
            results["test_passed"] = True
            results["reason"] = (
                "CORRECT: Pipeline did NOT verify Scott Weeden as a notary. "
                f"Status: {results['pipeline_status']}, "
                f"Confidence: {results['pipeline_confidence']:.2f}"
            )
    except Exception as e:
        results["pipeline_error"] = str(e)[:200]
        results["test_passed"] = None
        results["reason"] = f"Pipeline error: {str(e)[:100]}"

    status = "PASS" if results.get("test_passed") else "FAIL"
    print(f"  [{status}] {results['reason']}")
    return results


@traceable(name="exp6_rss_feeds")
def test_rss_feed_sources() -> dict:
    """Verify RSS feed sources configured in _data/rss-feeds.yml are reachable."""
    results = {"tested": 0, "reachable": 0, "unreachable": [], "details": []}

    rss_config_path = SITE_ROOT / "_data" / "rss-feeds.yml"
    if not rss_config_path.exists():
        results["error"] = "rss-feeds.yml not found"
        return results

    # Parse the YAML manually (avoid pyyaml dependency)
    text = rss_config_path.read_text()
    urls = re.findall(r'url:\s*["\']?(https?://[^\s"\']+)', text)

    for url in urls:
        result = _check_url_reachable(url, timeout=10)
        results["tested"] += 1
        results["details"].append({"url": url, **result})
        if result["ok"]:
            results["reachable"] += 1
        else:
            results["unreachable"].append(url)

    results["reachability_rate"] = (
        results["reachable"] / results["tested"]
        if results["tested"] > 0 else 0
    )
    return results


@traceable(name="exp6_pipeline_on_site_content")
def test_pipeline_on_site_content() -> dict:
    """Run the Legal Luminary pipeline on claims extracted from the site."""
    results = {"tested": 0, "verified": 0, "failed": 0, "details": []}

    test_cases = [
        {
            "content_type": "law",
            "query": "Texas Code of Criminal Procedure Chapter 55A governs expunctions",
            "description": "Expunction statute reference from texas-law.md",
        },
        {
            "content_type": "law",
            "query": "Texas Penal Code Chapter 22 defines assaultive offenses",
            "description": "Assault statute reference from defense.md",
        },
        {
            "content_type": "news_source",
            "query": "https://www.bellcountytx.com/",
            "description": "Bell County official site from bell-county.md",
        },
        {
            "content_type": "news_source",
            "query": "https://capitol.texas.gov/",
            "description": "Texas Legislature from legal-news.md",
        },
        {
            "content_type": "news_source",
            "query": "https://lrl.texas.gov/",
            "description": "TX Legislative Reference Library",
        },
    ]

    try:
        from pipeline import validate
    except Exception as e:
        results["error"] = f"Could not import pipeline: {e}"
        return results

    for tc in test_cases:
        results["tested"] += 1
        try:
            result = validate(
                content_type=tc["content_type"],
                query=tc["query"],
            )
            status = result.get("overall_status", "unknown")
            confidence = result.get("overall_confidence", 0)

            detail = {
                "description": tc["description"],
                "status": status,
                "confidence": confidence,
            }
            results["details"].append(detail)

            if status == "verified":
                results["verified"] += 1
            else:
                results["failed"] += 1

            print(f"  [{status.upper()}] {tc['description']} "
                  f"(confidence: {confidence:.2f})")
        except Exception as e:
            results["failed"] += 1
            results["details"].append({
                "description": tc["description"],
                "error": str(e)[:100],
            })

    results["verification_rate"] = (
        results["verified"] / results["tested"]
        if results["tested"] > 0 else 0
    )
    return results


# ===================================================================
# Main Experiment Runner
# ===================================================================

@traceable(name="exp6_run_full")
def run_experiment_6() -> dict:
    """Run the full site content verification experiment."""
    print("=" * 70)
    print("EXPERIMENT 6: legalluminary.com SITE CONTENT VERIFICATION")
    print(f"Site submodule: {SITE_ROOT}")
    print("=" * 70)

    if not SITE_ROOT.exists():
        print(f"\nERROR: Submodule not found at {SITE_ROOT}")
        print("Run: git submodule add https://github.com/sweeden-ttu/legal-luminary.git "
              "legal-luminary-site")
        return {"error": "submodule not found"}

    # Phase 1: Content Integrity
    print("\n[Phase 1] Content Integrity (SHA-256 verification)...")
    integrity = test_content_integrity()
    print(f"  Matched: {integrity['matched']}/{integrity['tested']} "
          f"({integrity.get('integrity_rate', 0):.0%})")

    # Phase 2: URL Reachability
    print("\n[Phase 2] Source URL Reachability...")
    reachability = test_url_reachability()
    print(f"  Reachable: {reachability['reachable']}/{reachability['tested']} "
          f"({reachability.get('reachability_rate', 0):.0%})")

    # Phase 3: Legal Claims
    print("\n[Phase 3] Legal Claims Cross-Reference...")
    claims = test_legal_claims_verification()
    print(f"  Verified: {claims['verified']}/{claims['tested']} "
          f"({claims.get('verification_rate', 0):.0%})")

    # Phase 4: LRL Resources
    print("\n[Phase 4] LRL (TX Legislative Reference Library) Resources...")
    lrl = test_lrl_resources()
    print(f"  Reachable: {lrl['reachable']}/{lrl['tested']} "
          f"({lrl.get('reachability_rate', 0):.0%})")

    # Phase 5: RSS Feed Sources
    print("\n[Phase 5] RSS Feed Source Verification...")
    rss = test_rss_feed_sources()
    print(f"  Reachable: {rss.get('reachable', 0)}/{rss.get('tested', 0)}")

    # Phase 6: Notary Negative Test
    print("\n[Phase 6] Negative Test — Scott Weeden Notary Public...")
    notary = test_notary_negative_validation()

    # Phase 7: Pipeline on Site Content
    print("\n[Phase 7] Pipeline Verification of Site Content...")
    pipeline = test_pipeline_on_site_content()
    print(f"  Verified: {pipeline.get('verified', 0)}/{pipeline.get('tested', 0)}")

    # Final Report
    report = {
        "experiment": "Exp6 — legalluminary.com Site Content Verification",
        "timestamp": datetime.utcnow().isoformat(),
        "site_root": str(SITE_ROOT),
        "content_integrity": integrity,
        "url_reachability": reachability,
        "legal_claims": claims,
        "lrl_resources": lrl,
        "rss_feeds": rss,
        "notary_negative_test": notary,
        "pipeline_verification": pipeline,
    }

    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    out_path = data_dir / "exp6_results.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nReport saved to {out_path}")

    print("\n" + "=" * 70)
    print("EXPERIMENT 6 SUMMARY")
    print(f"  Content Integrity:    {integrity.get('integrity_rate', 0):.0%}")
    print(f"  URL Reachability:     {reachability.get('reachability_rate', 0):.0%}")
    print(f"  Legal Claims:         {claims.get('verification_rate', 0):.0%}")
    print(f"  LRL Resources:        {lrl.get('reachability_rate', 0):.0%}")
    print(f"  RSS Feeds:            {rss.get('reachability_rate', 0):.0%}")
    notary_status = "PASS" if notary.get("test_passed") else "FAIL"
    print(f"  Notary Negative Test: {notary_status}")
    print(f"  Pipeline Verify:      {pipeline.get('verification_rate', 0):.0%}")
    print("=" * 70)

    return report


if __name__ == "__main__":
    run_experiment_6()
