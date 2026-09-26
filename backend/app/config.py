"""Runtime config — env-driven, fixture-backed fallbacks for demo survival."""
import os

WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./attestation.db")
MOCK_LLM = os.getenv("MOCK_LLM", "false").lower() == "true"
ARTIFACT_DIR = os.getenv("ARTIFACT_DIR", "./artifacts")
