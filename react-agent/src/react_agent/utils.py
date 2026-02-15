"""Utility & helper functions."""

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama


def get_message_text(msg: BaseMessage) -> str:
    """Get the text content of a message."""
    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        return content.get("text", "")
    else:
        txts = [c if isinstance(c, str) else (c.get("text") or "") for c in content]
        return "".join(txts).strip()


def load_chat_model(fully_specified_name: str) -> BaseChatModel:
    """Load a chat model from a fully specified name.

    Args:
        fully_specified_name (str): String in the format 'provider/model'.
            For Ollama, use 'ollama/model-name' (e.g., 'ollama/llama3.1:1b')
    """
    provider, model = fully_specified_name.split("/", maxsplit=1)
    
    # Special handling for Ollama to use local models
    if provider.lower() == "ollama":
        return ChatOllama(
            model=model,
            base_url="http://localhost:11434",  # Default Ollama URL
            temperature=0.7,
        )
    
    # For other providers, use the default init_chat_model
    return init_chat_model(model, model_provider=provider)
