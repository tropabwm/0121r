"""
Gerenciador de Configurações
Salva preferências e histórico
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class ConfigManager:
    """Gerencia configurações e histórico da aplicação"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".pdf_converter"
        self.config_file = self.config_dir / "config.json"
        self.history_file = self.config_dir / "history.json"
        
        # Criar diretório se não existir
        self.config_dir.mkdir(exist_ok=True)
        
        # Inicializar arquivos
        self._init_files()
    
    def _init_files(self):
        """Inicializa arquivos de configuração"""
        if not self.config_file.exists():
            self.save_settings({})
        
        if not self.history_file.exists():
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def save_settings(self, settings: Dict):
        """Salva configurações"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
    
    def load_settings(self) -> Optional[Dict]:
        """Carrega configurações salvas"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
        
        return None
    
    def save_to_history(self, conversion_data: Dict):
        """Adiciona conversão ao histórico"""
        try:
            history = self.get_history()
            history.append(conversion_data)
            
            # Manter apenas últimas 50 conversões
            if len(history) > 50:
                history = history[-50:]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            print(f"Erro ao salvar histórico: {e}")
    
    def get_history(self) -> List[Dict]:
        """Retorna histórico de conversões"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar histórico: {e}")
        
        return []
    
    def clear_history(self):
        """Limpa histórico"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    def get_default_settings(self) -> Dict:
        """Retorna configurações padrão"""
        return {
            'extraction_method': 'auto',
            'design_theme': 'premium',
            'include_toc': True,
            'responsive_design': True,
            'animations': True,
            'dark_mode': True,
            'language': 'pt-BR'
        }
