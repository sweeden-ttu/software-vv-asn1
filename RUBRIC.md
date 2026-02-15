# CS5374 Software Verification and Validation — Project Rubric

## Spring 2026 | Texas Tech University

---

## Overview

This rubric establishes the guidelines by which remote students shall accomplish and submit the examples given for the class. Students must first complete the class exercises and assignments, then apply the principles and topics discussed in lectures to their initial project design. The final deliverable is a "legal-luminary" agent that accomplishes the goals set forth in the project specification.

---

## Part 1: Class Exercise Prerequisites

Before beginning the project, students must complete and submit:

### 1.1 Vague Specification Agent (Quiz 1)
- **File:** `quiz1_vague_spec_agent.py`
- **Requirements:**
  - Build a LangGraph agent that classifies specifications as vague or precise
  - Transform vague specs into precise testable requirements
  - Generate test case specifications from the refined requirements
- **Submission:** Python code + sample outputs for 5 test inputs

### 1.2 Functional & Structural Testing (Part 2A)
- **Requirements:**
  - Perform Equivalence Partitioning (EP) analysis on provided code
  - Design minimum 20 functional test cases using EP methodology
  - Achieve ≥80% statement coverage with EP tests
  - Add structural tests to reach ≥95% coverage
- **Submission:** Test files + coverage reports

### 1.3 LangSmith Tracing (Part 2B)
- **Requirements:**
  - Enable LangSmith tracing on the Quiz 1 agent
  - Demonstrate traceable chain execution
  - Document all nodes and LLM calls
- **Submission:** Traced outputs + screenshots from LangSmith dashboard

---

## Part 2: Project — Legal Luminary Agent

### 2.1 Project Objectives

The legal-luminary agent validates legal and governmental content by:

1. **Verifying court documents** against authoritative sources (CourtListener, PACER)
2. **Validating laws/statutes** via Congress.gov API
3. **Confirming judge credentials** through CourtListener
4. **Checking elected officials** via FEC and Congress.gov
5. **Verifying elections** against official records
6. **Validating templates/forms** against official registries

### 2.2 Architecture Requirements

| Component | Description | Points |
|-----------|-------------|--------|
| **Pipeline** | LangGraph-based validation pipeline with 7 validator routes | 15 |
| **Validators** | 7 independent validator agents (news, judge, official, election, law, court doc, template) | 10 |
| **State Management** | Centralized PipelineState with provenance metadata | 5 |
| **Texas Data Crawler** | LangGraph pipeline crawling data.texas.gov for ground-truth datasets | 5 |
| **Site Content Verifier** | Automated verification of legalluminary.com content against authoritative sources | 5 |

### 2.3 Technical Stack

- **Framework:** LangGraph (agentic workflow)
- **Orchestration:** LangGraph (state-based deterministic workflow)
- **LLM (Cloud):** OpenAI GPT-4o-mini (temperature=0 for deterministic testing)
- **LLM (Local/HPCC):** Ollama running granite-code:34b on Texas Tech HPCC (V100 GPU)
- **Tracing / Observability:** LangSmith for full node-by-node observability
- **APIs:** CourtListener, Congress.gov, FEC, NewsGuard, Socrata SODA (data.texas.gov)
- **Testing:** pytest with pytest-cov
- **Automation:** GitHub Actions (CI/CD test driver)
- **Compute:** Texas Tech HPCC (Slurm, matador partition, V100 GPU)

---

## Part 3: Grading Rubric

### 3.1 Component Breakdown

| # | Component | Deliverable | Points | Deadline |
|---|-----------|-------------|--------|----------|
| 1 | Project Proposal | Written proposal with hypothesis, experiments, architecture | 5 | Week 3 |
| 2 | Source Code — Pipeline | LangGraph validation pipeline (`pipeline.py`) with 7 validator agents | 15 | Week 5 |
| 3 | Source Code — Validators | 7 validator modules: news, judge, official, election, law, court doc, template | 10 | Week 5 |
| 4 | Experiment 1 | Baseline hallucination rate measurement (10 ground-truth citations) | 10 | Week 7 |
| 5 | Experiment 2 | Pipeline effectiveness — precision, recall, hallucination rate | 10 | Week 8 |
| 6 | Experiment 3 | LangGraph node validation vs post-hoc verification comparison | 10 | Week 9 |
| 7 | Experiment 4 | Security red-team evaluation (10 adversarial tests) | 10 | Week 10 |
| 8a | Experiment 5 | Texas Data Pipeline — ground-truth discovery from data.texas.gov | 5 | Week 11 |
| 8b | Experiment 6 | legalluminary.com site content verification (SHA-256, URL reachability, legal claims, notary negative test) | 5 | Week 12 |
| 9 | EP Functional Tests | 20+ EP test cases with tabular design + implementation | 10 | Week 6 |
| 9 | Structural Tests | Minimum 40 tests achieving 80%+ coverage | 5 | Week 6 |
| 10 | Coverage Report | Statement coverage ≥80% (target: 95%+) | 5 | Week 6 |
| 11 | LangSmith Tracing | Full tracing enabled across all validators and pipeline | 5 | Week 5 |
| 12 | Blog Posts | 3 conceptual blog posts exploring theoretical foundations | 5 | Week 11 |
| **TOTAL** | | | **100** | |

### 3.2 Grading Standards

| Grade | Points | Requirements |
|-------|--------|--------------|
| A | 90-100 | All components complete + ≥95% coverage + 4 experiments documented |
| B | 80-89 | All components complete + ≥85% coverage + 3 experiments documented |
| C | 70-79 | Core pipeline + validators + ≥80% coverage |
| D | 60-69 | Partial pipeline + ≥70% coverage |
| F | <60 | Incomplete submission |

---

## Part 4: Class Topics Applied

### 4.1 Verification vs. Validation

**Verification** ensures you are _"building the thing right"_ — the system follows its specifications. **Validation** ensures you are _"building the right thing"_ — the system meets user needs.

| Concept | Definition | Application in Legal Luminary |
|---------|------------|-------------------------------|
| **Verification** (process-oriented) | Are we following the spec correctly? | Structural tests checking code paths, coverage analysis, SHA-256 content integrity checks, allow-list domain matching |
| **Validation** (product-oriented) | Does the product meet user needs? | EP functional tests, pipeline smoke tests on real Texas statutes, site content reachability checks, LLM quality evaluations |

### 4.2 The Test Oracle

A **Test Oracle** is a source of expected results against which actual outputs are compared. In the Legal Luminary pipeline:

| Oracle | Implementation | Location |
|--------|----------------|----------|
| **Official Allow List** | Trusted domain sets for news, courts, legislation | `config/settings.py` |
| **Site Allow List** | Per-host allowlist with categories (government, news, vendor) | `legal-luminary-site/verification/allowlist.yml` |
| **Verification Manifest** | SHA-256 hashes + URL reachability for every content file | `legal-luminary-site/verification/manifest.json` |
| **Ground Truth Citations** | 10 landmark legal cases with known-correct citations | `experiments/exp1_baseline.py` |
| **Texas Government Data** | Official TDCJ, TCEQ, TDLR datasets from data.texas.gov | `texas_data_crawler.py` |

The orchestrator's **Node 2 (Evidence Verification)** implements the oracle check as a conditional edge — content proceeds only if every cited source passes the allow list.

### 4.3 Functional Testing Strategies

#### Equivalence Partitioning (EP)

EP divides the input space into classes where the software behaves similarly. For each partition, select at least one representative element.

**Legal Luminary EP Classes:**

| Partition | Valid Class (Allow-Listed) | Invalid Class (Unauthorized) |
|-----------|---------------------------|------------------------------|
| News Source URLs | `*.texas.gov`, `*.bellcountytx.com`, `apnews.com` | `fakenews.example.com`, `texas-gov.phishing.net` |
| Court Domains | `txcourts.gov`, `uscourts.gov`, `courtlistener.com` | `txcourts.net.evil.com`, `fakecourt.org` |
| Statute References | `statutes.capitol.texas.gov/Docs/PE/htm/PE.22.htm` | `statutes.capitol.texas.gov.fake.com/PE.22.htm` |
| Official Names | Real: "Chief Justice John Roberts" | Fabricated: "Justice Marcus Thornberry" |
| Confidence Scores | ≥ 0.7 (VERIFIED) | < 0.7 (UNVERIFIED/PENDING) |

**Reaching the 20-case requirement:** If Input₁ yields 8 cases (5 EP + 3 BVA), move to Input₂ and repeat. Continue across validators until ≥20 unique functional test cases are defined.

#### Boundary Value Analysis (BVA)

BVA extends EP by focusing on the _edges_ of each class — where defects are most likely to appear. This parallels ML uncertainty: a classifier is most uncertain at the 0.5 decision boundary.

**BVA selection strategy for each boundary:**
1. The **exact lower bound** (e.g., confidence = 0.7)
2. The **exact upper bound** (e.g., confidence = 1.0)
3. **Just below** the lower bound (e.g., confidence = 0.699)
4. **Just above** the upper bound (e.g., retry_count = MAX_RETRIES + 1)
5. A **middle/risk-free** interior value (e.g., confidence = 0.85)

**Legal Luminary BVA Examples:**

| Boundary | Below | At | Above | Interior |
|----------|-------|----|-------|----------|
| Confidence threshold (0.7) | 0.699 → UNVERIFIED | 0.7 → VERIFIED | 0.701 → VERIFIED | 0.85 |
| Retry limit (3) | 2 → retry | 3 → escalate | 4 → should not reach | 1 |
| URL similarity (homograph) | `txcourts.gov` ✓ | `txcоurts.gov` (Cyrillic о) ✗ | `txcourts.gov.evil.com` ✗ | `search.txcourts.gov` ✓ |
| Empty input | `""` → reject | `" "` → reject | `"a"` → classify | `"Brown v. Board"` |

#### Extreme Value Analysis

Extension of BVA testing system maximums:
- Memory: Large dataset payloads from data.texas.gov (87eh-wyyj has 100K+ records)
- String length: URLs exceeding 2048 characters
- Concurrency: Multiple validators executing simultaneously

#### Syntax Checking

Lexical-level analysis on generated markdown ensures required tokens and formatting:
- Front matter has `verified_at:` date, `source_url:` or `sources:` list
- URLs follow `https://` scheme (no bare `http://`)
- Statute citations match pattern `§ \d+` or `Chapter \d+`
- SHA-256 hash matches manifest for unmodified content

### 4.4 Testing Methodologies Summary

| Method | Implementation |
|--------|----------------|
| **Equivalence Partitioning** | 20 EP test cases covering valid/invalid inputs per validator |
| **Boundary Value Analysis** | Testing thresholds (confidence ≥0.7, retries, URL similarity) |
| **Structural Testing** | Achieving ≥95% statement coverage via pytest-cov |
| **Red-Team Testing** | Adversarial tests for prompt injection, source spoofing |
| **Syntax Checking** | Markdown front-matter validation, URL scheme checks |

### 4.5 Agentic AI Testing

| Concept | Implementation |
|---------|----------------|
| **LangGraph Workflow** | Pipeline: classify → route → validate → aggregate → retry/escalate |
| **Orchestrator Agent** | Extract → verify evidence (allow list) → generate/flag → evaluate → report |
| **LangSmith Tracing** | Full observability across all nodes, every LLM call traced |
| **Test Oracle** | Allow list + verification manifest + ground-truth citations |
| **Black-Box Testing** | Each validator is an independent testable node |
| **Sensitivity Analysis** | Vary one validator weight while holding others constant (ablation) |
| **Uncertainty Analysis** | Confidence scores + retry logic = Bayesian-style assurance at each step |

### 4.6 Enabling LangSmith Tracing

**Step 1: Install libraries**
```bash
pip install langgraph langchain langsmith langchain_ollama python-dotenv
```

**Step 2: Configure environment variables**
```bash
export LANGCHAIN_TRACING_V2=true          # Primary toggle
export LANGCHAIN_API_KEY="lsv2_pt_..."    # From smith.langchain.com
export LANGCHAIN_PROJECT="Legal Luminary"  # Organizes traces
export LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
```

**Step 3: Backend LLM setup**
- Cloud: OpenAI GPT-4o-mini (temperature=0 for determinism)
- Local/HPCC: Ollama running granite-code:34b or Llama 3.2

**Step 4: Code integration (~3-4 lines at script top)**
```python
import os
from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "Legal Luminary")
```

All `@traceable()` decorated functions and LangGraph nodes are then automatically profiled — capturing latency, token usage, inputs/outputs for each chain.

**What LangSmith captures per run:**
- Node-by-node execution trace (extract → verify → evaluate)
- LLM call inputs, outputs, and token counts
- Latency per node and total pipeline
- Conditional edge routing decisions
- Error traces for failed validations

---

## Part 5: Experiment Guidelines

### 5.1 Experiment 1: Baseline Hallucination Rate
- **Objective:** Measure LLM hallucination rate without verification
- **Method:** Test 10 ground-truth legal citations against GPT-4o-mini
- **Metric:** Proportion of hallucinated/incorrect citations

### 5.2 Experiment 2: Pipeline Effectiveness
- **Objective:** Measure precision, recall, and hallucination rate WITH pipeline
- **Method:** Run same 10 citations through validator pipeline
- **Compare:** Pre-pipeline vs post-pipeline hallucination rates

### 5.3 Experiment 3: LangGraph vs Post-Hoc
- **Objective:** Compare two verification architectures
- **Method:** 
  - (A) LangGraph with retry logic
  - (B) Simple LLM + post-hoc self-verification
- **Metrics:** Accuracy, latency, false positive/negative rates

### 5.4 Experiment 4: Security Red-Team
- **Objective:** Evaluate robustness against adversarial attacks
- **Test Cases:**
  1. Prompt injection attempts
  2. Source spoofing (homograph attacks)
  3. Fabricated court case citations
  4. Fake elected official names
  5. Non-existent statutes
  6. Historical manipulation (wrong dates)
  7. Domain impersonation
  8. Data exfiltration attempts
  9. Token manipulation
  10. Race condition attacks

### 5.5 Experiment 5: Texas Data Pipeline — Ground Truth Discovery
- **Objective:** Crawl data.texas.gov and classify datasets for use as ground-truth evidence
- **Method:**
  - Use Socrata SODA API to discover and sample Texas government datasets
  - Classify each as LAW_VERIFICATION, NEWS, or ATTORNEY_RESOURCE via Ollama LLM
  - Measure classification accuracy against human-labeled expectations
  - Evaluate ground-truth quality (record counts, identifier fields, confidence scores)
- **Datasets Include:** TDCJ inmate records, TCEQ civil judgments/administrative orders, TDLR licenses, insurance complaints, CPS investigations
- **Metrics:** API reachability rate, classification accuracy, ground-truth quality score

### 5.6 Experiment 6: legalluminary.com Site Content Verification
- **Objective:** Validate legal content published on legalluminary.com against authoritative sources
- **Method:**
  - Parse all markdown in `_pages/` and `_posts/` from the `legal-luminary-site` submodule
  - Verify SHA-256 content integrity against the verification manifest
  - Check every cited source URL for HTTPS 200 reachability
  - Cross-reference legal claims (statute numbers, court classifications, penalty ranges) against official Texas statute text
  - Run site content through the Legal Luminary validation pipeline
  - Validate LRL (Texas Legislative Reference Library) resources are accessible
  - Verify RSS feed sources from `_data/rss-feeds.yml` are reachable
- **Negative Test:** Scott Weeden should NOT be found in the TX Secretary of State Notary Public database — the pipeline must correctly FAIL this validation
- **Metrics:** Content integrity rate, URL reachability rate, legal claim verification rate, pipeline verification rate

---

## Part 5B: Presentation and Demonstration

### 5B.1 Presentation Content: The Foundations of V&V

The presentation establishes the theoretical framework based on software engineering standards:

- **Defining V&V:** Verification ensures you are "building the thing right" (following specifications). Validation ensures you are "building the right thing" (meeting user needs).
- **The Test Oracle:** The Official Allow List of sites and contacts serves as the source of expected results. This is codified in `config/settings.py` (trusted domain lists) and `verification/allowlist.yml` in the site submodule.
- **Functional Testing Strategies:**
  - **Equivalence Partitioning (EP):** Categorize sources into "Valid" (allow-listed) and "Invalid" (unauthorized) classes.
  - **Boundary Value Analysis (BVA):** Test edges such as URLs nearly identical to official sources but with subtle errors (e.g., homograph attacks in Experiment 4).
- **Syntax Checking:** Lexical-level analysis on generated markdown to ensure required tokens and formatting are present.

### 5B.2 Demonstration: The LangGraph Validation Pipeline

The demonstration shows a deterministic workflow processing content through a series of nodes:

- **Node 1: Extract Content** — An agent extracts data from a target website (e.g., legalluminary.com) and stores it in a shared `State` class.
- **Node 2: Evidence Verification (The Router)** — A Conditional Edge acts as a gatekeeper. It cross-references extracted information against the Official Allow List.
  - **Logic:** If the source is on the allow list, proceed to content generation; if not, flag as "Invalid Input" and halt.
- **Node 3: Content Generation** — Only verified evidence is used to populate markdown files.
- **Node 4: Evaluator Node** — Use an LLM to assess cohesiveness, relevancy, and toxicity of the generated output.

### 5B.3 GitHub Workflow Actions (The Test Driver)

GitHub Actions serves as the automated Test Driver, running verification on every code push or content update:

- **Trigger:** Workflow triggered by `pull_request` to markdown files.
- **Environment Setup:** Action sets up virtual environment, installs `langgraph`, `langchain`, `langsmith`.
- **Execution:** Runs the Python validation script. If the Adequacy Criterion (e.g., 100% of links verified against the oracle) is not met, the CI/CD build fails, preventing unauthorized content from being merged.
- **Secrets Management:** GitHub Secrets securely handle LangSmith API keys and other environment variables.

### 5B.4 Observability and Evidence with LangSmith

LangSmith provides the "documented evidence" required for high-degree assurance:

- **Tracing:** Node-by-node trace of a successful verification run proves the system checked the allow list before generating content.
- **Evaluation Results:** "Datasets & Experiments" view shows how the pipeline scores generated content against ground-truth data.
- **Error Analysis:** LangSmith tracks failing test cases, identifying exactly why evidence was rejected (non-matching domain, high toxicity score, etc.).

### 5B.5 Demonstration Hardware/Software Summary

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Automation** | GitHub Actions | CI/CD Test Driver |
| **Orchestration** | LangGraph | State-based deterministic workflow |
| **Observability** | LangSmith | Tracing and Evaluation |
| **LLM (HPCC)** | Ollama (granite-code:34b) | Deterministic, cost-effective testing on V100 GPU |
| **LLM (Local)** | Ollama (Llama 3.2) | Local development and rapid iteration |
| **LLM (Cloud)** | OpenAI GPT-4o-mini | Production classification (temperature=0) |
| **Data Source** | data.texas.gov (Socrata SODA API) | Ground-truth Texas government datasets |
| **Site Under Test** | legalluminary.com (GitHub Pages) | Content verification target |

---

## Part 6: Submission Requirements

### 6.1 Directory Structure

```
software-vv-asn1/
├── .github/
│   └── workflows/
│       └── legal-luminary-ci.yml   # GitHub Actions CI/CD (Test Driver)
├── legal-luminary/                 # Main pipeline code
│   ├── pipeline.py                 # Main LangGraph validation pipeline
│   ├── orchestrator.py             # Orchestrator agent (extract → verify → evaluate)
│   ├── texas_data_crawler.py       # data.texas.gov LangGraph crawler
│   ├── state.py                    # PipelineState, ValidationResult schemas
│   ├── config/
│   │   └── settings.py             # API keys, trusted domains (all verified), thresholds
│   ├── validators/
│   │   ├── news_validator.py       # News source validation
│   │   ├── judge_validator.py      # Judge verification
│   │   ├── official_validator.py   # Elected official validation
│   │   ├── election_validator.py   # Election validation
│   │   ├── law_validator.py        # Statute validation
│   │   ├── court_doc_validator.py  # Court document validation
│   │   └── template_validator.py   # Official form validation
│   ├── experiments/
│   │   ├── exp1_baseline.py                  # Baseline hallucination rate
│   │   ├── exp2_pipeline_effectiveness.py    # Pipeline effectiveness
│   │   ├── exp3_validator_vs_posthoc.py      # LangGraph vs post-hoc
│   │   ├── exp4_security_redteam.py          # Security red-team
│   │   ├── exp5_texas_data_pipeline.py       # Texas data ground-truth discovery
│   │   └── exp6_site_content_verification.py # legalluminary.com content verification
│   ├── tests/
│   │   ├── test_ep_functional.py   # 20 EP functional test cases
│   │   ├── test_structural.py      # 40+ structural coverage tests
│   │   └── test_texas_crawler.py   # Texas data crawler tests
│   └── data/                       # Generated results (gitignored)
├── legal-luminary-site/            # Git submodule: legalluminary.com Jekyll site
│   ├── _pages/                     # Legal content pages (texas-law, defense, etc.)
│   ├── _posts/                     # Blog posts and news articles
│   ├── _data/                      # RSS feed config, news-feed.json
│   ├── verification/
│   │   ├── manifest.json           # SHA-256 hashes + URL reachability (the oracle)
│   │   └── allowlist.yml           # Official allow list of trusted domains
│   └── verifier/                   # Site verification scripts
└── RUBRIC.md                       # This file
```

### 6.2 How to Run

```bash
# Set environment variables (or use GitHub Secrets in CI)
export OPENAI_API_KEY="sk-..."
export LANGSMITH_API_KEY="lsv2_pt_..."
export LANGCHAIN_TRACING_V2=true

# Install dependencies
pip install -r requirements.txt

# Initialize the site submodule
git submodule update --init --recursive

# Run all tests with coverage
cd legal-luminary
python -m pytest tests/ -v --cov=validators --cov=config --cov=. --cov-report=term-missing

# Run pipeline demo
python pipeline.py

# Run the orchestrator agent (processes legalluminary.com content)
python orchestrator.py --pages-only

# Run the Texas data crawler
python texas_data_crawler.py --max 5

# Run experiments 1-6
python experiments/exp1_baseline.py
python experiments/exp2_pipeline_effectiveness.py
python experiments/exp3_validator_vs_posthoc.py
python experiments/exp4_security_redteam.py
python experiments/exp5_texas_data_pipeline.py --max 5
python experiments/exp6_site_content_verification.py
```

### 6.3 How to Run with Ollama (HPCC or Local)

```bash
# Set Ollama environment
export USE_OLLAMA=true
export OLLAMA_BASE_URL="http://localhost:43411"  # or SSH-tunneled port
export OLLAMA_MODEL="granite-code:34b"

# Run orchestrator with Ollama backend
cd legal-luminary
python orchestrator.py --pages-only

# Run crawler with Ollama
python texas_data_crawler.py --ollama-url http://localhost:43411 --model granite-code:34b

# On HPCC via sbatch
AGENT_PROMPT="Verify legalluminary.com content" sbatch ~/ollama_agent_job.sh
# Or with the fixed script:
export AGENT_PROMPT="your prompt here"
sbatch ~/ollama_agent_job.sh
```

### 6.4 GitHub Actions CI/CD

The workflow at `.github/workflows/legal-luminary-ci.yml` runs automatically on push/PR:

**Required GitHub Secrets:**
| Secret | Description |
|--------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o-mini |
| `LANGSMITH_API_KEY` | LangSmith API key for tracing |

**Jobs:**
1. **Lint & Structure** — Verify imports, pipeline compilation, domain counts
2. **Tests & Coverage** — pytest with coverage report (≥80% required)
3. **Site Content Verification** — SHA-256 integrity + URL reachability (≥90% required)
4. **Pipeline Validation** — LangGraph smoke tests + Exp6 site verification
5. **Texas Data Crawl** — Manual trigger only; runs Exp5 against data.texas.gov

### 6.5 Verifying the `legal-luminary-site` Submodule

The `legal-luminary-site` submodule contains the legalluminary.com Jekyll site. To verify its content:

1. **Content Integrity:** SHA-256 hashes in `verification/manifest.json` must match all `_pages/*.md` and `_posts/*.md` files
2. **Allow List:** All outbound URLs must appear in `verification/allowlist.yml`
3. **Source Citations:** Pages with `sources:` or `source_url:` front matter must reference reachable, authoritative URLs
4. **Legal Claims:** Statute references (e.g., Chapter 55A, Penal Code Chapter 22) must link to official `statutes.capitol.texas.gov` pages
5. **Negative Tests:** The pipeline must correctly FAIL validation for unverifiable claims (e.g., "Scott Weeden is a TX Notary Public")

---

## Part 7: Trusted Domains (All Verified HTTPS 200 on 2026-02-15)

### 7.1 Texas State Government

| Domain | Description | Verified |
|--------|-------------|----------|
| `data.texas.gov` | Texas Open Data Portal (Socrata SODA API) | 200 |
| `capitol.texas.gov` | Texas Capitol / Legislature | 200 |
| `statutes.capitol.texas.gov` | Texas Statutes full text | 200 |
| `www.texasattorneygeneral.gov` | TX Attorney General | 200 |
| `gov.texas.gov` | Texas Governor | 200 |
| `comptroller.texas.gov` | TX Comptroller | 200 |
| `www.sos.state.tx.us` | TX Secretary of State (TX Register, TX Admin Code) | 200 |
| `www.lbb.texas.gov` | TX Legislative Budget Board | 200 |
| `www.sunset.texas.gov` | TX Sunset Advisory Commission | 200 |
| `tidc.texas.gov` | TX Indigent Defense Commission | 200 |
| `scjc.texas.gov` | State Commission on Judicial Conduct | 200 |
| `ble.texas.gov` | TX Board of Law Examiners | 200 |
| `spa.texas.gov` | State Prosecuting Attorney | 200 |
| `texaschildrenscommission.gov` | TX Children's Commission | 200 |
| `texasjcmh.gov` | TX Judicial Commission on Mental Health | 200 |

### 7.2 Texas Legislature & Law Library

| Domain | Description | Verified |
|--------|-------------|----------|
| `www.legis.texas.gov` | Texas Legislature Online (TLO) | 200 |
| `lrl.texas.gov` | **TX Legislative Reference Library** (key resource) | 200 |
| `lrlcatalog.lrl.texas.gov` | LRL Library Catalog | 200 |
| `sll.texas.gov` | State Law Library | 200 |
| `tas-public.lrl.texas.gov` | TX Appointment System | 200 |
| `dirpub.dir.texas.gov` | Capitol Complex Directory | 200 |

### 7.3 Texas Courts

| Domain | Description | Verified |
|--------|-------------|----------|
| `txcourts.gov` | Texas Judicial Branch | 200 |
| `search.txcourts.gov` | TX Court case search | 200 |
| `card.txcourts.gov` | TX Court Activity Database | 200 |
| `bail.txcourts.gov` | TX Public Safety Report System | 200 |
| `efiletexas.gov` | Texas eFiling portal | 200 |
| `ocfw.texas.gov` | Office of Capital and Forensic Writs | 200 |
| `www.txwd.uscourts.gov` | US District Court Western District of TX | 200 |
| `texasbar.com` | State Bar of Texas | 200 |

### 7.4 Bell County Local Government

| Domain | Description | Verified |
|--------|-------------|----------|
| `www.bellcountytx.com` | Bell County official site | 200 |
| `www.killeentexas.gov` | City of Killeen | 200 |
| `www.templetx.gov` | City of Temple | 200 |
| `www.beltontexas.gov` | City of Belton | 200 |

### 7.5 Local & State News

| Domain | Description | Verified |
|--------|-------------|----------|
| `kdhnews.com` | Killeen Daily Herald | 200 |
| `www.kwtx.com` | KWTX News (Waco/Temple/Killeen) | 200 |
| `www.tdtnews.com` | Temple Daily Telegram | 200 |
| `www.statesman.com` | Austin American-Statesman | 200 |

### 7.6 LRL Points of Interest (as of Feb 2026)

The **Texas Legislative Reference Library** (`lrl.texas.gov`) provides:

- **89th Legislature, 2nd Called Session** (Aug 15 – Sep 4, 2025)
- **Bill Search** — Legislative Archive System with direct and advanced search
- **Member Directory** — Searchable across all legislative sessions
- **Committee Calendar** — Today's meetings and upcoming schedules
- **Session Dates & Bill Effective Dates** — 89th, 88th, 87th legislatures
- **Library Catalog** — Full catalog at `lrlcatalog.lrl.texas.gov`
- **Historical Statutes** — 1920 Complete TX Statutes, 1856 Codes, Paschal's Digest
- **Recent Blog Posts:**
  - Feb 13, 2026: New & Noteworthy Books and Reports
  - Feb 12, 2026: Current Articles & Research Resources
  - Feb 5, 2026: Current Articles & Research Resources
  - Feb 4, 2026: Interim Hearings — Week of February 9

---

## References

- **NIST AI Risk Management Framework:** Seven pillars of Trustworthy AI
- **LangChain/LangGraph:** Agentic workflow documentation
- **LangSmith:** Tracing, evaluation, and datasets platform
- **CourtListener API:** Court document verification
- **Congress.gov API:** Legislation verification
- **FEC API:** Election official verification
- **Socrata SODA API:** Texas Open Data Portal (`data.texas.gov`)
- **Texas Legislative Reference Library:** `lrl.texas.gov` — bills, members, sessions, committees
- **Texas Statutes:** `statutes.capitol.texas.gov` — full text of Texas law
- **GitHub Actions:** CI/CD test driver for automated verification
- **Ollama:** Local/HPCC LLM inference for deterministic, cost-effective testing

---

**Last Updated:** February 15, 2026
**Course:** CS5374 Software Verification and Validation — Texas Tech University
**Author:** Scott Weeden
