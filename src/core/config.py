import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "RapidBoard AI"
    # Añadir más configuraciones aquí (DB, LangSmith, etc.)

settings = Settings()
