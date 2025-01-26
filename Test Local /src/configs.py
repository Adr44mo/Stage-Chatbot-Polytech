from dotenv import dotenv_values

venv = dotenv_values(".env")

OPENAI_API_KEY = venv.get("OPENAI_API_KEY")