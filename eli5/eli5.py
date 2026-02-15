from langchain_ollama import ChatOllama
from langsmith import traceable
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun


# Load environment variables
load_dotenv(dotenv_path=".env", override=True)


# Initialize web search tool (DuckDuckGo - free, no API key needed)
web_search_tool = DuckDuckGoSearchRun()

# Define prompt template
prompt = """You are a professor and expert in explaining complex topics in a way that is easy to understand. 
Your job is to answer the provided question so that even a 5 year old can understand it. 
You have provided with relevant background context to answer the question.

Question: {question} 

Context: {context}

Answer:"""
# print("Prompt Template: ", prompt)


# Create Application with Ollama
ollama_client = ChatOllama(
    model="llama3.2:1b",
    base_url="http://localhost:11434",
    temperature=0.7,
)

@traceable
def search(question):
    try:
        web_results = web_search_tool.invoke(question)
        return web_results
    except Exception as e:
        return f"Search error: {str(e)}"
    
@traceable
def explain(question, context):
    formatted = prompt.format(question=question, context=context)
    
    response = ollama_client.invoke([
        {"role": "system", "content": formatted},
        {"role": "user", "content": question},
    ])
    return response.content

@traceable
def eli5(question):
    context = search(question)
    answer = explain(question, context)
    return answer

# Run the application
question = "What is trustcall?"
print(eli5(question))
