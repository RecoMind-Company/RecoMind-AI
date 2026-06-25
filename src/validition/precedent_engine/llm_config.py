import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

print("GROQ_API_KEY:", os.getenv("GROQ_API_KEY"))

llm = LLM(
    model="groq/llama-3.1-8b-instant",
    provider="groq",      
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)