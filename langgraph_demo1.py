from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

# Optional (only if you use Ollama)
from langchain_ollama import ChatOllama


class State(TypedDict):
    text: str
    answer: str
    payload: list[dict]


# --- Node 1: extract text from payload ---
def extract_content(state: State):
    return {"text": state["payload"][0]["customer_remark"]}


# --- Router: decide which node to go to next ---
def route_question_or_compliment(state: State):
    # simple heuristic: '?' => question, otherwise compliment
    return "question" if "?" in state["text"] else "compliment"


# --- Node 2a: handle compliment ---
def run_compliment_code(state: State):
    return {"answer": "Thanks for the compliment."}


# --- Node 2b: handle question ---
def run_question_code(state: State):
    return {"answer": "Thanks for your question. We will look into it."}


# --- Node 3: beautify (optionally using an LLM) ---
def beautify(state: State):
    # If you want: uncomment Ollama call to rewrite the answer nicely.
    # llm = ChatOllama(model="llama3.2:1b", temperature=0)
    # prompt = f"Rewrite this politely in one sentence: {state['answer']}"
    # pretty = llm.invoke(prompt).content
    # return {"answer": pretty}

    return {"answer": state["answer"] + " (beautified)"}


def build_graph():
    graph_builder = StateGraph(State)

    graph_builder.add_node("extract_content", extract_content)
    graph_builder.add_node("run_question_code", run_question_code)
    graph_builder.add_node("run_compliment_code", run_compliment_code)
    graph_builder.add_node("beautify", beautify)

    graph_builder.add_edge(START, "extract_content")

    graph_builder.add_conditional_edges(
        "extract_content",
        route_question_or_compliment,
        {
            "compliment": "run_compliment_code",
            "question": "run_question_code",
        },
    )

    graph_builder.add_edge("run_question_code", "beautify")
    graph_builder.add_edge("run_compliment_code", "beautify")
    graph_builder.add_edge("beautify", END)

    return graph_builder.compile()


if __name__ == "__main__":
    graph = build_graph()

    png_bytes = graph.get_graph().draw_mermaid_png()
    with open("langgraph_diagram.png", "wb") as f:
        f.write(png_bytes)
    print("Diagram saved as: langgraph_diagram.png")
    example_payload = [
        {
            "time_of_comment": "2025-01-20",
            "customer_remark": "Why has the packaging changed?",
            "social_media_channel": "facebook",
            "number_of_likes": 100,
        }
    ]

    result = graph.invoke({"payload": example_payload})
    print("\nFINAL RESULT:\n", result)

    print("\nSTEP-BY-STEP STREAM:\n")
    for step in graph.stream({"payload": example_payload}):
        print(step)
