import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def list_available_models():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Erro: GOOGLE_API_KEY não encontrada no .env")
        return

    client = genai.Client(api_key=api_key)
    print("Buscando modelos disponíveis...")
    
    try:
        models = client.models.list()
        for model in models:
            print(f"Model ID: {model.name}")
            # print(f"Supported methods: {getattr(model, 'supported_generation_methods', 'N/A')}")
    except Exception as e:
        print(f"Erro ao listar modelos: {e}")

if __name__ == "__main__":
    list_available_models()
