"""
Part 1: LangGraph Agent for Vague Specification Detection and Test Case Generation

This agent:
1. Takes a short specification as input
2. Classifies it as VAGUE or NOT VAGUE using an LLM
3. If VAGUE: transforms to a precise specification, then generates a test case
4. If NOT VAGUE: directly generates a test case specification

Reference: LangGraph_Demo2.py pattern (conditional routing with LLM nodes)

Usage:
    export OPENAI_API_KEY="your-key-here"
    python part1_vague_spec_agent.py
"""

import os
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


# ============================================================================
# State Definition
# ============================================================================

class SpecState(TypedDict):
    """State that flows through the graph."""
    input_spec: str              # Original specification from user
    is_vague: bool               # Whether the spec is vague
    vagueness_reasoning: str     # Why the spec is/isn't vague
    precise_spec: str            # Transformed precise specification (if vague)
    test_case: str               # Generated test case specification


# ============================================================================
# LLM Initialization
# ============================================================================

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# ============================================================================
# Node Functions
# ============================================================================

def classify_specification(state: SpecState) -> SpecState:
    """
    Node 1: Classify the specification as vague or not vague.
    Uses the LLM to analyze the specification for vagueness.
    """
    spec = state["input_spec"]

    messages = [
        SystemMessage(content="""You are a software quality assurance expert specializing in
requirements analysis. Your task is to classify a specification as VAGUE or NOT VAGUE.

A specification is VAGUE if it:
- Uses subjective terms without measurable criteria (e.g., "fast", "easy", "high-quality", "secure", "timely", "as appropriate")
- Lacks specific numeric thresholds, standards, or protocols
- Is open to multiple interpretations
- Does not define clear acceptance criteria

A specification is NOT VAGUE if it:
- Contains specific measurable criteria
- References concrete standards, protocols, or thresholds
- Has unambiguous acceptance criteria

Respond with EXACTLY this format:
CLASSIFICATION: VAGUE or NOT_VAGUE
REASONING: <brief explanation of why>"""),
        HumanMessage(content=f"Classify this specification:\n\n\"{spec}\"")
    ]

    response = llm.invoke(messages)
    response_text = response.content.strip()

    is_vague = "VAGUE" in response_text.split("\n")[0] and "NOT_VAGUE" not in response_text.split("\n")[0]
    reasoning = response_text.split("REASONING:")[-1].strip() if "REASONING:" in response_text else response_text

    print(f"\n{'='*70}")
    print(f"INPUT SPECIFICATION: \"{spec}\"")
    print(f"{'='*70}")
    print(f"CLASSIFICATION: {'VAGUE' if is_vague else 'NOT VAGUE'}")
    print(f"REASONING: {reasoning}")

    return {
        **state,
        "is_vague": is_vague,
        "vagueness_reasoning": reasoning,
    }


def transform_to_precise(state: SpecState) -> SpecState:
    """
    Node 2 (conditional): Transform a vague specification into a precise one.
    Only called when the specification is classified as vague.
    """
    spec = state["input_spec"]
    reasoning = state["vagueness_reasoning"]

    messages = [
        SystemMessage(content="""You are a software quality assurance expert.
Transform the given VAGUE specification into a PRECISE specification by:
1. Replacing subjective terms with measurable criteria
2. Adding specific numeric thresholds or standards
3. Defining clear acceptance criteria
4. Making it testable and unambiguous

Provide the precise specification directly, without any preamble."""),
        HumanMessage(content=f"""Original vague specification: \"{spec}\"
Vagueness analysis: {reasoning}

Transform this into a precise, testable specification:""")
    ]

    response = llm.invoke(messages)
    precise = response.content.strip()

    print(f"\n--- TRANSFORMED PRECISE SPECIFICATION ---")
    print(precise)

    return {
        **state,
        "precise_spec": precise,
    }


def generate_test_case(state: SpecState) -> SpecState:
    """
    Node 3: Generate a test case based on the specification.
    Uses the precise spec (if available) or the original spec.
    """
    # Use precise spec if the original was vague, otherwise use original
    if state.get("is_vague") and state.get("precise_spec"):
        spec_to_test = state["precise_spec"]
        print(f"\n--- GENERATING TEST CASE (from transformed precise spec) ---")
    else:
        spec_to_test = state["input_spec"]
        print(f"\n--- GENERATING TEST CASE (from original spec) ---")

    messages = [
        SystemMessage(content="""You are a software test engineer.
Generate a detailed test case specification based on the given requirement.

Format the test case as follows:
TEST CASE ID: TC-001
TEST CASE TITLE: <descriptive title>
PRECONDITIONS: <what must be true before testing>
TEST STEPS:
  1. <step 1>
  2. <step 2>
  ...
TEST DATA: <specific test data to use>
EXPECTED RESULT: <what should happen>
PASS/FAIL CRITERIA: <how to determine pass or fail>"""),
        HumanMessage(content=f"Generate a test case for this specification:\n\n\"{spec_to_test}\"")
    ]

    response = llm.invoke(messages)
    test_case = response.content.strip()

    print(test_case)
    print(f"\n{'='*70}\n")

    return {
        **state,
        "test_case": test_case,
    }


# ============================================================================
# Routing Function
# ============================================================================

def route_based_on_vagueness(state: SpecState) -> Literal["transform_to_precise", "generate_test_case"]:
    """
    Conditional edge: route to transformation if vague, else directly to test generation.
    """
    if state.get("is_vague"):
        return "transform_to_precise"
    else:
        return "generate_test_case"


# ============================================================================
# Graph Construction
# ============================================================================

def build_graph():
    """Build and compile the LangGraph workflow."""
    workflow = StateGraph(SpecState)

    # Add nodes
    workflow.add_node("classify_specification", classify_specification)
    workflow.add_node("transform_to_precise", transform_to_precise)
    workflow.add_node("generate_test_case", generate_test_case)

    # Set entry point
    workflow.set_entry_point("classify_specification")

    # Add conditional edge from classify → either transform or generate
    workflow.add_conditional_edges(
        "classify_specification",
        route_based_on_vagueness,
        {
            "transform_to_precise": "transform_to_precise",
            "generate_test_case": "generate_test_case",
        }
    )

    # After transformation, always go to test case generation
    workflow.add_edge("transform_to_precise", "generate_test_case")

    # Test case generation is the final node
    workflow.add_edge("generate_test_case", END)

    return workflow.compile()


# ============================================================================
# Main Execution
# ============================================================================

def run_agent(spec: str) -> dict:
    """Run the agent with a given specification."""
    graph = build_graph()
    initial_state: SpecState = {
        "input_spec": spec,
        "is_vague": False,
        "vagueness_reasoning": "",
        "precise_spec": "",
        "test_case": "",
    }
    result = graph.invoke(initial_state)
    return result


if __name__ == "__main__":
    # Five test inputs from the assignment
    test_specifications = [
        # 1. Software Development (vague)
        "The system shall allow for fast, easy data entry",

        # 2. Construction (vague)
        "Install high-quality flooring",

        # 3. Performance (vague)
        "The application must be secure",

        # 4. Reporting (vague)
        "The report will include, as appropriate, investigation findings",

        # 5. Project Timeline (vague)
        "The project will be completed in a timely manner",
    ]

    print("=" * 70)
    print("LANGGRAPH VAGUE SPECIFICATION DETECTION & TEST CASE GENERATOR")
    print("=" * 70)

    for i, spec in enumerate(test_specifications, 1):
        print(f"\n{'#'*70}")
        print(f"# TEST INPUT {i} of {len(test_specifications)}")
        print(f"{'#'*70}")
        result = run_agent(spec)
