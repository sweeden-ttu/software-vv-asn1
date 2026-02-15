"""
Part 2B: LangSmith Tracing for Quiz 1 (Vague Specification Agent)

This script implements the same vague specification agent from Quiz 1
with LangSmith tracing enabled to observe and debug chain execution.

Setup:
    1. Sign up at https://smith.langchain.com
    2. Create an API key
    3. Set environment variables:
        export LANGCHAIN_TRACING_V2=true
        export LANGCHAIN_API_KEY="your-langsmith-key"
        export LANGCHAIN_PROJECT="quiz1-vague-spec-agent"
        export OPENAI_API_KEY="your-openai-key"

Usage:
    python assignment1_langsmith_tracing.py
"""

import os

# ============================================================================
# LangSmith Tracing Configuration
# ============================================================================

# Enable LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
# Set your LangSmith API key (or set via environment variable before running)
# os.environ["LANGCHAIN_API_KEY"] = "your-langsmith-api-key"
os.environ["LANGCHAIN_PROJECT"] = "quiz1-vague-spec-agent"

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable


# ============================================================================
# State Definition
# ============================================================================

class SpecState(TypedDict):
    """State that flows through the graph."""
    input_spec: str
    is_vague: bool
    vagueness_reasoning: str
    precise_spec: str
    test_case: str


# ============================================================================
# LLM Initialization
# ============================================================================

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# ============================================================================
# Node Functions (with LangSmith tracing decorators)
# ============================================================================

@traceable(name="classify_specification")
def classify_specification(state: SpecState) -> SpecState:
    """
    Node 1: Classify the specification as vague or not vague.
    """
    spec = state["input_spec"]

    messages = [
        SystemMessage(content="""You are a software quality assurance expert specializing in
requirements analysis. Your task is to classify a specification as VAGUE or NOT VAGUE.

A specification is VAGUE if it:
- Uses subjective terms without measurable criteria (e.g., "fast", "easy", "high-quality")
- Lacks specific numeric thresholds, standards, or protocols
- Is open to multiple interpretations
- Does not define clear acceptance criteria

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
    print(f"CLASSIFICATION: {'VAGUE' if is_vague else 'NOT VAGUE'}")
    print(f"REASONING: {reasoning}")

    return {
        **state,
        "is_vague": is_vague,
        "vagueness_reasoning": reasoning,
    }


@traceable(name="transform_to_precise")
def transform_to_precise(state: SpecState) -> SpecState:
    """
    Node 2: Transform a vague specification into a precise one.
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

Provide the precise specification directly."""),
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


@traceable(name="generate_test_case")
def generate_test_case(state: SpecState) -> SpecState:
    """
    Node 3: Generate a test case based on the specification.
    """
    if state.get("is_vague") and state.get("precise_spec"):
        spec_to_test = state["precise_spec"]
        print(f"\n--- GENERATING TEST CASE (from transformed precise spec) ---")
    else:
        spec_to_test = state["input_spec"]
        print(f"\n--- GENERATING TEST CASE (from original spec) ---")

    messages = [
        SystemMessage(content="""You are a software test engineer.
Generate a detailed test case specification.

Format:
TEST CASE ID: TC-001
TEST CASE TITLE: <title>
PRECONDITIONS: <preconditions>
TEST STEPS:
  1. <step 1>
  2. <step 2>
TEST DATA: <data>
EXPECTED RESULT: <result>
PASS/FAIL CRITERIA: <criteria>"""),
        HumanMessage(content=f"Generate a test case for:\n\n\"{spec_to_test}\"")
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
# Routing
# ============================================================================

def route_based_on_vagueness(state: SpecState) -> Literal["transform_to_precise", "generate_test_case"]:
    if state.get("is_vague"):
        return "transform_to_precise"
    else:
        return "generate_test_case"


# ============================================================================
# Graph Construction
# ============================================================================

def build_graph():
    workflow = StateGraph(SpecState)

    workflow.add_node("classify_specification", classify_specification)
    workflow.add_node("transform_to_precise", transform_to_precise)
    workflow.add_node("generate_test_case", generate_test_case)

    workflow.set_entry_point("classify_specification")

    workflow.add_conditional_edges(
        "classify_specification",
        route_based_on_vagueness,
        {
            "transform_to_precise": "transform_to_precise",
            "generate_test_case": "generate_test_case",
        }
    )

    workflow.add_edge("transform_to_precise", "generate_test_case")
    workflow.add_edge("generate_test_case", END)

    return workflow.compile()


# ============================================================================
# Main Execution with Tracing
# ============================================================================

@traceable(name="quiz1_vague_spec_pipeline")
def run_agent_with_tracing(spec: str) -> dict:
    """Run the agent with LangSmith tracing enabled."""
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
    print("=" * 70)
    print("QUIZ 1 - LANGSMITH TRACED EXECUTION")
    print("=" * 70)
    print(f"Tracing enabled: {os.environ.get('LANGCHAIN_TRACING_V2', 'false')}")
    print(f"Project: {os.environ.get('LANGCHAIN_PROJECT', 'default')}")
    print()

    # Run with one of the vague specifications as a demonstration
    test_spec = "The system shall allow for fast, easy data entry"

    print(f"Running agent with spec: \"{test_spec}\"")
    result = run_agent_with_tracing(test_spec)

    print("\n" + "=" * 70)
    print("EXECUTION COMPLETE")
    print("=" * 70)
    print(f"\nView traces at: https://smith.langchain.com")
    print(f"Project: {os.environ.get('LANGCHAIN_PROJECT', 'default')}")
    print(f"\nNumber of chains executed:")
    print(f"  - 1 top-level pipeline (quiz1_vague_spec_pipeline)")
    if result.get("is_vague"):
        print(f"  - 3 nodes: classify_specification → transform_to_precise → generate_test_case")
        print(f"  - 3 LLM calls total")
    else:
        print(f"  - 2 nodes: classify_specification → generate_test_case")
        print(f"  - 2 LLM calls total")
