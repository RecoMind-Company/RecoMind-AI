"""
llm_config.py
=============
إعدادات نموذج Groq عبر LangChain-Groq.
"""

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

MODEL_NAME  = "llama-3.3-70b-versatile"
MAX_TOKENS  = 2048
TEMPERATURE = 0.0

def get_llm() -> ChatGroq:
    return ChatGroq(
        model=MODEL_NAME,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )