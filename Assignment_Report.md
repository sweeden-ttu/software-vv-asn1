# Software Verification & Validation — Assignment Report

**Author:** Scott Weeden (sweeden@ttu.edu)
**Date:** February 15, 2026

---

## Part 1: LangGraph Vague Specification Agent

### Overview

A LangGraph agent was built that takes a short specification, classifies it as vague or not vague using an LLM, and either transforms it first (if vague) or directly generates a test case specification.

**File:** `part1_vague_spec_agent.py`

### Architecture

The agent uses a 3-node LangGraph workflow with conditional routing:

```
classify_specification → [VAGUE?] → transform_to_precise → generate_test_case → END
                         [NOT VAGUE?] ──────────────────→ generate_test_case → END
```

### How to Run

```bash
export OPENAI_API_KEY="your-key-here"
python part1_vague_spec_agent.py
```

### Five Test Inputs

1. "The system shall allow for fast, easy data entry"
2. "Install high-quality flooring"
3. "The application must be secure"
4. "The report will include, as appropriate, investigation findings"
5. "The project will be completed in a timely manner"

> **Note:** Screenshots of outputs should be captured when running with a valid OpenAI API key. Each input is expected to be classified as VAGUE, transformed to a precise spec, and then a test case is generated.

---

## Part 2A: Designing and Implementing Functional/Structural Tests

### Repository

Source: https://github.com/AutomationPanda/shopping-cart-unit-tests
Project: Shopping Cart (Order) system in Python
File: `shopping_cart/orders.py`

### Step 1: Code Installation

The repository was cloned and explored. It contains:

- `orders.py` — Main source (60 statements): `calculate_total()` function, `Item` class, `Order` class, `DynamicallyPricedItem` class
- `tests/test_orders.py` — Existing test suite (29 tests)

### Step 2: Existing Test Execution

All 29 existing tests pass:

```
tests/test_orders.py::test_calculate_total[90-10-20-0.05-84.0]           PASSED
tests/test_orders.py::test_calculate_total[0-10-5-0.05-5.25]             PASSED
tests/test_orders.py::test_calculate_total[90-0-20-0.05-73.5]            PASSED
tests/test_orders.py::test_calculate_total[90-10-0-0.05-105.0]           PASSED
tests/test_orders.py::test_calculate_total[90-10-20-0-80.0]              PASSED
tests/test_orders.py::test_calculate_total[10-5-5-0.0875-10.88]          PASSED
tests/test_orders.py::test_calculate_total[10-5-5-0.0733-10.73]          PASSED
tests/test_orders.py::test_calculate_total[10-10-20-0.05-0.0]            PASSED
tests/test_orders.py::test_calculate_total[10-5-20-0.05-0.0]             PASSED
tests/test_orders.py::test_calculate_total_negatives[-90-10-20-0.05-subtotal]  PASSED
tests/test_orders.py::test_calculate_total_negatives[90--10-20-0.05-shipping]  PASSED
tests/test_orders.py::test_calculate_total_negatives[90-10--20-0.05-discount]  PASSED
tests/test_orders.py::test_calculate_total_negatives[90-10-20--0.05-tax_percent]  PASSED
tests/test_orders.py::test_Item_init                                      PASSED
tests/test_orders.py::test_Item_init_default_quantity                     PASSED
tests/test_orders.py::test_Item_calculate_item_total[12.34-1-12.34]       PASSED
tests/test_orders.py::test_Item_calculate_item_total[12.34-3-37.02]       PASSED
tests/test_orders.py::test_Item_calculate_item_total[12.34-0-0]           PASSED
tests/test_orders.py::test_Item_calculate_item_total[0-1-0]               PASSED
tests/test_orders.py::test_Order_init                                     PASSED
tests/test_orders.py::test_Order_add_item_to_empty                        PASSED
tests/test_orders.py::test_Order_add_item_to_existing                     PASSED
tests/test_orders.py::test_Order_calculate_subtotal_for_multiple_items    PASSED
tests/test_orders.py::test_Order_calculate_order_total                    PASSED
tests/test_orders.py::test_Order_get_reward_points                        PASSED
tests/test_orders.py::test_DynamicallyPricedItem_calculate_item_total[12.34-1-12.34]  PASSED
tests/test_orders.py::test_DynamicallyPricedItem_calculate_item_total[12.34-3-37.02]  PASSED
tests/test_orders.py::test_DynamicallyPricedItem_calculate_item_total[12.34-0-0]      PASSED
tests/test_orders.py::test_DynamicallyPricedItem_calculate_item_total[0-1-0]          PASSED

29 passed in 0.10s
```

### Step 3: Initial Statement Coverage

```
Name        Stmts   Miss  Cover   Missing
-----------------------------------------
orders.py      60      4    93%   86-89
-----------------------------------------
TOTAL          60      4    93%
```

Lines 86-89 are `DynamicallyPricedItem.get_latest_price()` (makes HTTP API call, tested only via mocked `calculate_item_total`).

### Step 4: Equivalence Partitioning — 20 Functional Test Designs

#### Equivalence Classes Identified

| EC# | Source | EP Class | Valid/Invalid |
|-----|--------|----------|---------------|
| EC1 | calculate_total.subtotal | subtotal = 0 | Valid (boundary) |
| EC2 | calculate_total.subtotal | subtotal > 0 | Valid |
| EC3 | calculate_total.subtotal | subtotal < 0 | Invalid |
| EC4 | calculate_total.shipping | shipping = 0 | Valid (boundary) |
| EC5 | calculate_total.shipping | shipping > 0 | Valid |
| EC6 | calculate_total.shipping | shipping < 0 | Invalid |
| EC7 | calculate_total.discount | discount = 0 | Valid (boundary) |
| EC8 | calculate_total.discount | 0 < discount ≤ subtotal+shipping | Valid |
| EC9 | calculate_total.discount | discount > subtotal+shipping | Valid (clamped to 0) |
| EC10 | calculate_total.discount | discount < 0 | Invalid |
| EC11 | calculate_total.tax_percent | tax_percent = 0 | Valid (boundary) |
| EC12 | calculate_total.tax_percent | 0 < tax_percent < 1 | Valid |
| EC13 | calculate_total.tax_percent | tax_percent < 0 | Invalid |
| EC14 | Item.unit_price | unit_price = 0 | Valid (boundary) |
| EC15 | Item.unit_price | unit_price > 0 | Valid |
| EC16 | Item.quantity | quantity = 0 | Valid (boundary) |
| EC17 | Item.quantity | quantity = 1 (default) | Valid |
| EC18 | Item.quantity | quantity > 1 | Valid |
| EC19 | Order.items | empty order (0 items) | Valid (boundary) |
| EC20 | Order.items | 1 item | Valid |
| EC21 | Order.items | multiple items (>1) | Valid |
| EC22 | Order.reward_points | total < 1000 | Valid (no bonus) |
| EC23 | Order.reward_points | total ≥ 1000 | Valid (bonus +10) |
| EC24 | DynamicallyPricedItem.qty | quantity = 1 (default) | Valid |
| EC25 | DynamicallyPricedItem.qty | quantity > 1 | Valid |

#### 20 Functional Test Case Specifications

| TC# | Source Code .py | EP Classes | Valid/Invalid? | Test Inputs | Expected Output | Status |
|-----|----------------|------------|----------------|-------------|-----------------|--------|
| TC01 | orders.py (calculate_total) | EC1, EC5, EC8, EC12 | Valid | subtotal=0, shipping=15, discount=5, tax=0.10 | 11.00 | PASS |
| TC02 | orders.py (calculate_total) | EC2, EC4, EC7, EC12 | Valid | subtotal=50, shipping=0, discount=0, tax=0.08 | 54.00 | PASS |
| TC03 | orders.py (calculate_total) | EC2, EC5, EC8, EC11 | Valid | subtotal=100, shipping=10, discount=20, tax=0 | 90.00 | PASS |
| TC04 | orders.py (calculate_total) | EC2, EC5, EC9, EC12 | Valid | subtotal=20, shipping=5, discount=50, tax=0.10 | 0.00 | PASS |
| TC05 | orders.py (calculate_total) | EC3 | Invalid | subtotal=-10, shipping=5, discount=3, tax=0.05 | ValueError("subtotal cannot be negative") | PASS |
| TC06 | orders.py (calculate_total) | EC6 | Invalid | subtotal=50, shipping=-5, discount=3, tax=0.05 | ValueError("shipping cannot be negative") | PASS |
| TC07 | orders.py (calculate_total) | EC10 | Invalid | subtotal=50, shipping=5, discount=-10, tax=0.05 | ValueError("discount cannot be negative") | PASS |
| TC08 | orders.py (calculate_total) | EC13 | Invalid | subtotal=50, shipping=5, discount=3, tax=-0.05 | ValueError("tax_percent cannot be negative") | PASS |
| TC09 | orders.py (calculate_total) | EC1, EC4, EC7, EC11 | Valid | subtotal=0, shipping=0, discount=0, tax=0 | 0.00 | PASS |
| TC10 | orders.py (calculate_total) | EC2, EC5, EC8, EC12 | Valid | subtotal=10000, shipping=500, discount=1000, tax=0.15 | 10925.00 | PASS |
| TC11 | orders.py (Item) | EC14, EC18 | Valid | name="free sample", price=0, qty=5 | item_total=0 | PASS |
| TC12 | orders.py (Item) | EC15, EC17 | Valid | name="book", price=29.99, qty=default(1) | item_total=29.99 | PASS |
| TC13 | orders.py (Item) | EC15, EC18 | Valid | name="pen", price=1.50, qty=10 | item_total=15.00 | PASS |
| TC14 | orders.py (Item) | EC15, EC16 | Valid | name="eraser", price=2.50, qty=0 | item_total=0 | PASS |
| TC15 | orders.py (Order) | EC19 | Valid | Order(ship=5, disc=0, tax=0.10), no items | subtotal=0, total=5.50 | PASS |
| TC16 | orders.py (Order) | EC20 | Valid | Order(ship=10, disc=5, tax=0.07) + 1 item(25.00×2) | subtotal=50, total=58.85 | PASS |
| TC17 | orders.py (Order) | EC21 | Valid | Order(ship=0, disc=0, tax=0.05) + 3 items | subtotal=10, total=10.50 | PASS |
| TC18 | orders.py (Order) | EC22 | Valid | Order + item(99.99×1), total < 1000 | reward_points=99 | PASS |
| TC19 | orders.py (Order) | EC23 | Valid | Order + item(1000×1), total ≥ 1000 | reward_points=1010 | PASS |
| TC20 | orders.py (DynamicItem) | EC24, EC25 | Valid | DynItem(id=101, qty=default) + DynItem(202, qty=4) | totals: 49.99, 40.00 | PASS |

### Step 5: EP Test Implementation and Execution

**File:** `shopping_cart/tests/test_ep_functional.py`

All 20 EP tests pass:

```
tests/test_ep_functional.py::test_TC01_calculate_total_zero_subtotal       PASSED [  5%]
tests/test_ep_functional.py::test_TC02_calculate_total_no_shipping_no_discount PASSED [ 10%]
tests/test_ep_functional.py::test_TC03_calculate_total_zero_tax             PASSED [ 15%]
tests/test_ep_functional.py::test_TC04_calculate_total_discount_exceeds_amount PASSED [ 20%]
tests/test_ep_functional.py::test_TC05_calculate_total_negative_subtotal    PASSED [ 25%]
tests/test_ep_functional.py::test_TC06_calculate_total_negative_shipping    PASSED [ 30%]
tests/test_ep_functional.py::test_TC07_calculate_total_negative_discount    PASSED [ 35%]
tests/test_ep_functional.py::test_TC08_calculate_total_negative_tax         PASSED [ 40%]
tests/test_ep_functional.py::test_TC09_calculate_total_all_zeros            PASSED [ 45%]
tests/test_ep_functional.py::test_TC10_calculate_total_large_values         PASSED [ 50%]
tests/test_ep_functional.py::test_TC11_item_zero_price_multiple_quantity    PASSED [ 55%]
tests/test_ep_functional.py::test_TC12_item_default_quantity                PASSED [ 60%]
tests/test_ep_functional.py::test_TC13_item_multiple_quantity               PASSED [ 65%]
tests/test_ep_functional.py::test_TC14_item_zero_quantity                   PASSED [ 70%]
tests/test_ep_functional.py::test_TC15_order_empty                          PASSED [ 75%]
tests/test_ep_functional.py::test_TC16_order_single_item                    PASSED [ 80%]
tests/test_ep_functional.py::test_TC17_order_multiple_items                 PASSED [ 85%]
tests/test_ep_functional.py::test_TC18_order_reward_points_below_threshold  PASSED [ 90%]
tests/test_ep_functional.py::test_TC19_order_reward_points_above_threshold  PASSED [ 95%]
tests/test_ep_functional.py::test_TC20_dynamic_item_default_and_multi_quantity PASSED [100%]

20 passed in 0.04s
```

### Step 6: Coverage After EP Tests

```
Name        Stmts   Miss  Cover   Missing
-----------------------------------------
orders.py      60      4    93%   86-89
-----------------------------------------
TOTAL          60      4    93%
```

Coverage remains at 93%. The 4 uncovered lines (86-89) are in `DynamicallyPricedItem.get_latest_price()` which requires mocking the HTTP layer.

### Step 7: Structural Tests for Increased Coverage

**File:** `shopping_cart/tests/test_structural.py`

5 structural tests were designed to cover lines 86-89 by mocking `requests.get`:

1. `test_structural_get_latest_price_normal` — Normal API response
2. `test_structural_get_latest_price_string_id` — String ID in URL construction
3. `test_structural_dynamic_item_in_order` — Integration with Order
4. `test_structural_get_latest_price_zero_price` — API returns zero price
5. `test_structural_order_mixed_items` — Mixed Item + DynamicallyPricedItem in Order

### Step 8: Final Coverage After Structural Tests

```
Name        Stmts   Miss  Branch  BrPart  Cover   Missing
---------------------------------------------------------
orders.py      60      0      14       0   100%
---------------------------------------------------------
TOTAL          60      0      14       0   100%

54 passed in 0.10s
```

**100% statement coverage and 100% branch coverage achieved** across all 54 tests (29 original + 20 EP + 5 structural).

---

## Part 2B: LangSmith Tracing

### Overview

The vague specification agent from Quiz 1 was implemented with LangSmith tracing enabled.

**File:** `part2b_langsmith_tracing.py`

### How to Run

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY="your-langsmith-key"
export LANGCHAIN_PROJECT="quiz1-vague-spec-agent"
export OPENAI_API_KEY="your-openai-key"
python part2b_langsmith_tracing.py
```

### Expected Chains Executed (per run)

For a **vague** specification:

- 1 top-level pipeline (`quiz1_vague_spec_pipeline`)
- 3 chain nodes: `classify_specification` → `transform_to_precise` → `generate_test_case`
- 3 LLM calls total

For a **non-vague** specification:

- 1 top-level pipeline
- 2 chain nodes: `classify_specification` → `generate_test_case`
- 2 LLM calls total

> **Note:** Screenshots of the LangSmith trace dashboard should be captured from https://smith.langchain.com after execution.

---

## File Summary

| File | Description |
|------|-------------|
| `part1_vague_spec_agent.py` | Part 1: LangGraph agent for vague spec detection |
| `part2b_langsmith_tracing.py` | Part 2B: LangSmith-traced version of Quiz 1 |
| `shopping_cart/tests/test_ep_functional.py` | Part 2A: 20 EP functional tests |
| `shopping_cart/tests/test_structural.py` | Part 2A: 5 structural tests for 100% coverage |
| `shopping_cart/tests/test_orders.py` | Original 29 tests from repository |
| `shopping_cart/orders.py` | Source code under test |
