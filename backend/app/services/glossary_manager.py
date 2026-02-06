import json
import os
from typing import Dict, List

class GlossaryManager:
    """Gerencia o glossário de termos para correção de STT."""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.seed_data = {
            "Hankell": ["Rankel", "Ranquel", "Hanke", "Rank", "Hankel", "Hanquel"],
            "Cenize": ["Senize", "Semize", "Zenize"],
            "Roquelina": ["Rock", "Roque", "Roc", "Hock"],
            "APN": ["PN", "A pena", "Apn", "A.P.N."],
            "Intelbras": ["Inteoubras", "Intel", "Inteobras"],
            "Datatem": ["Data tem", "Dataten", "Data ten"],
            "Odoo": ["Odo", "Hoodoo", "Odum"]
        }
        # In V2 we might expect the file to exist or handle it silently
        # For now, keeping logic close to original but respecting the injected path
        if not os.path.exists(self.file_path):
            # Ensure directory exists before writing
            os.makedirs(os.path.dirname(os.path.abspath(self.file_path)), exist_ok=True)
            self.save(self.seed_data)

    def load(self) -> Dict:
        try:
            if not os.path.exists(self.file_path):
                return self.seed_data
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar glossário: {e}")
            return self.seed_data

    def save(self, data: Dict):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar glossário: {e}")

    def get_prompt_rules(self) -> str:
        data = self.load()
        rules = []
        for correct, variations in data.items():
            vars_str = ", ".join(variations)
            rules.append(f"- Se ouvir: {vars_str} -> Escreva: {correct}")
        return "\n".join(rules)
