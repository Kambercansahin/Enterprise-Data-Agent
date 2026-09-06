from langchain_google_genai import ChatGoogleGenerativeAI,GoogleGenerativeAI
from dotenv import load_dotenv


load_dotenv()

def get_models(model_name="gemini-2.5-flash-lite",temperature=0.2):
    return ChatGoogleGenerativeAI(
        model = model_name,
        temperature = temperature
    )
