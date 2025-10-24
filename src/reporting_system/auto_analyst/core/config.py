# auto_analyst/core/config.py

from langchain_openai import ChatOpenAI
from crewai.llm import LLM
import os

# --- THIS IS THE ONLY PLACE WHERE THE LLM AND ENV VARS ARE DEFINED ---
langgraph_LLM_MODEL = "z-ai/glm-4.5-air:free" 

# Enhanced LLM Configuration
llm_model = ChatOpenAI(
    model=langgraph_LLM_MODEL,
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)