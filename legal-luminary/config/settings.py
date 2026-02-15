"""
Configuration and environment settings for the Legal Luminary pipeline.

All API keys and tracing config are loaded from environment variables.
"""

import os


# ============================================================================
# LangSmith Tracing (enabled project-wide)
# ============================================================================

os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "Software Validation and Verification")
os.environ.setdefault("LANGSMITH_TRACING", "true")
os.environ.setdefault("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")


# ============================================================================
# API Keys (set via environment variables before running)
# ============================================================================

# Keys are read from environment variables.
# On macOS, set these in ~/.zprofile so they're available to all shells:
#   export OPENAI_API_KEY="sk-..."
#   export LANGSMITH_API_KEY="lsv2_pt_..."
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
LANGSMITH_API_KEY = os.environ.get("LANGSMITH_API_KEY", "") or os.environ.get(
    "LANGCHAIN_API_KEY", ""
)

# CourtListener (free API for court documents)
COURTLISTENER_API_KEY = os.environ.get("COURTLISTENER_API_KEY", "")
COURTLISTENER_BASE_URL = "https://www.courtlistener.com/api/rest/v4"

# NewsGuard (media trust ratings)
NEWSGUARD_API_KEY = os.environ.get("NEWSGUARD_API_KEY", "")

# Congress.gov API (free, for federal officials and legislation)
CONGRESS_GOV_API_KEY = os.environ.get("CONGRESS_GOV_API_KEY", "")
CONGRESS_GOV_BASE_URL = "https://api.congress.gov/v3"

# Federal Election Commission (free API)
FEC_API_KEY = os.environ.get("FEC_API_KEY", "")
FEC_BASE_URL = "https://api.open.fec.gov/v1"

# PACER (court electronic filing — requires paid account)
PACER_USERNAME = os.environ.get("PACER_USERNAME", "")
PACER_PASSWORD = os.environ.get("PACER_PASSWORD", "")


# ============================================================================
# Trusted Domain Lists
# ============================================================================

TRUSTED_NEWS_DOMAINS = {
    # Government sources
    "supremecourt.gov",
    "uscourts.gov",
    "congress.gov",
    "whitehouse.gov",
    "justice.gov",
    "ftc.gov",
    "sec.gov",
    "fec.gov",
    # Major legal news
    "law.cornell.edu",
    "scotusblog.com",
    "courtlistener.com",
    "pacer.gov",
    "govinfo.gov",
    # Texas legal resources
    "texaslawhelp.org",
    "texascourthelp.gov",
    "texasbar.com",
    # Texas law blogs
    "edtexweblog.com",
    # Verified news
    "reuters.com",
    "apnews.com",
    "npr.org",
    # Major law firms
    "allenoverry.com",
    "cliffordchance.com",
    "freshfields.com",
    "linklaters.com",
    "slaughterandmay.com",
}

TRUSTED_COURT_DOMAINS = {
    "uscourts.gov",
    "supremecourt.gov",
    "courtlistener.com",
    "pacer.gov",
    "law.cornell.edu",
    "govinfo.gov",
    # Texas courts
    "texascourthelp.gov",
    "txcourts.gov",
    "txcourts.net",
}

TRUSTED_LEGISLATION_DOMAINS = {
    "congress.gov",
    "govinfo.gov",
    "law.cornell.edu",
    "legiscan.com",
    "ncsl.org",
    # Texas legal resources
    "texaslawhelp.org",
    "texasbar.com",
    # Major law firms
    "allenoverry.com",
    "cliffordchance.com",
    "freshfields.com",
    "linklaters.com",
    "slaughterandmay.com",
}


# ============================================================================
# Validation Thresholds
# ============================================================================

# Minimum confidence for a source to be considered verified
MIN_CONFIDENCE_THRESHOLD = 0.7

# Maximum retries for a validator node before escalating
MAX_VALIDATOR_RETRIES = 3

# Hallucination rate threshold for pipeline acceptance
HALLUCINATION_RATE_THRESHOLD = 0.05  # 5%
