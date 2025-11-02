# shared/config.py
from crewai.llm import LLM
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv()

# --- THIS IS THE ONLY PLACE WHERE THE LLM AND ENV VARS ARE DEFINED ---
# You can adjust model parameters here for both the Data Collection Crew and the Auto Analyst.
crewai_LLM_MODEL = os.getenv("crewai_LLM_MODEL")

langgraph_LLM_MODEL = os.getenv("langgraph_LLM_MODEL")

BASE_URL = os.getenv("BASE_URL")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Enhanced LLM Configuration for Data Collection Crew
def get_llm() -> LLM:
    """Creates and configures the Language Model for the crew."""
    # The 'llm_params' dictionary is where you control the model's behavior.
    llm_params = {
        "temperature": 0.0,
    }

    return LLM(
        model=crewai_LLM_MODEL,
        base_url=BASE_URL,
        api_key=OPENROUTER_API_KEY,
        model_kwargs=llm_params 
    )

# Enhanced LLM Configuration for Auto Analyst
llm_model = ChatOpenAI(
    model=langgraph_LLM_MODEL,
    base_url=BASE_URL,
    api_key=OPENROUTER_API_KEY
)

# --- Static Configuration (Always Loaded) ---

# Destination Vector DB Connection (PostgreSQL)
VECTOR_DB_HOST = os.getenv("VECTOR_DB_HOST")
VECTOR_DB_NAME = os.getenv("VECTOR_DB_NAME")
VECTOR_DB_USER = os.getenv("VECTOR_DB_USER")
VECTOR_DB_PASSWORD = os.getenv("VECTOR_DB_PASSWORD")