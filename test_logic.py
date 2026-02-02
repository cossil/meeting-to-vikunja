import os
from logic import TaskProcessor, GeminiService, VikunjaClient
from dotenv import load_dotenv

load_dotenv()

def test_extraction():
    print("--- Testando Extração de Texto ---")
    text = TaskProcessor.extract_text_from_file("sample_meeting.txt")
    print(f"Texto extraído ({len(text)} caracteres):")
    print(text[:100] + "...")
    assert len(text) > 0

def test_fuzzy_matching():
    print("\n--- Testando Fuzzy Matching ---")
    mock_users = [
        {"id": 1, "name": "João Silva", "username": "joao"},
        {"id": 2, "name": "Maria Oliveira", "username": "maria"},
        {"id": 3, "name": "Pedro Santos", "username": "pedro"}
    ]
    
    match1 = TaskProcessor.match_assignee("João", mock_users)
    print(f"Match para 'João': {match1} (Esperado: 1)")
    assert match1 == 1
    
    match2 = TaskProcessor.match_assignee("Maria", mock_users)
    print(f"Match para 'Maria': {match2} (Esperado: 2)")
    assert match2 == 2
    
    match3 = TaskProcessor.match_assignee("Desconhecido", mock_users)
    print(f"Match para 'Desconhecido': {match3} (Esperado: None)")
    assert match3 is None

if __name__ == "__main__":
    test_extraction()
    test_fuzzy_matching()
    print("\nTestes básicos concluídos com sucesso!")
