import json
import time
import requests
import os
from urllib.parse import urlparse
from log_config import setup_logger

def carregar_config():
    """Carrega configurações do arquivo config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

class PicWishProcessor:
    def __init__(self, api_key=None):
        self.logger = setup_logger('PicWishProcessor', os.path.join(os.path.dirname(__file__), 'picwish_processor.log'))
        self.logger.info("Iniciando PicWishProcessor")
        
        if api_key is None:
            config = carregar_config()
            api_key = config.get('picwish_api_key')
        self.logger.info(f"API Key configurada: {api_key[:4]}..." if api_key else "API Key não configurada")
        self.api_key = api_key
        
    def download_image(self, url, save_path):
        """Download da imagem original"""
        try:
            self.logger.info(f"Baixando imagem de {url}")
            response = requests.get(url)
            response.raise_for_status()
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(response.content)
            self.logger.info(f"Imagem salva em {save_path}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao baixar imagem: {e}")
            return False

    def process_image_with_picwish(self, image_url):
        """Processa a imagem usando a API PicWish"""
        if not self.api_key:
            self.logger.error("API Key não configurada!")
            self.logger.info("Configure uma API Key válida no arquivo config.json")
            return None

        headers = {'X-API-KEY': self.api_key}
        data = {'sync': '0', 'image_url': image_url}
        url = 'https://techhk.aoscdn.com/api/tasks/visual/scale'

        try:
            self.logger.info(f"Enviando requisição para PicWish API...")
            response = requests.post(url, headers=headers, data=data)
            response_json = response.json()
            self.logger.info(f"Status da requisição: {response.status_code}")
            
            if response.status_code == 401:
                self.logger.error("API Key inválida ou expirada!")
                self.logger.info("1. Acesse https://picwish.com/my-account?subRoute=api-key")
                self.logger.info("2. Copie sua API key válida")
                self.logger.info("3. Atualize o arquivo config.json")
                self.logger.info("4. Execute o programa novamente")
                return None
                
            self.logger.debug(f"Resposta completa: {response_json}")
            
            if response_json.get('status') == 200 and 'data' in response_json:
                task_id = response_json['data'].get('task_id')
                if task_id:
                    self.logger.info(f"Task ID obtido: {task_id}")
                    return task_id
                else:
                    self.logger.warning("Task ID não encontrado na resposta")
            else:
                self.logger.error(f"Erro na resposta: {response_json.get('message', 'Sem mensagem de erro')}")
        except Exception as e:
            self.logger.error(f"Erro ao processar imagem: {e}")
        return None

    def get_processed_image(self, task_id, timeout=30):
        """Obtém o resultado do processamento"""
        headers = {'X-API-KEY': self.api_key}
        url = f'https://techhk.aoscdn.com/api/tasks/visual/scale/{task_id}'
        
        self.logger.info(f"Iniciando polling para task_id: {task_id}")
        for i in range(timeout):
            if i > 0:
                self.logger.info(f"Tentativa {i+1} de {timeout}")
                time.sleep(1)
            try:
                response = requests.get(url, headers=headers)
                data = response.json()
                self.logger.info(f"Status da resposta: {response.status_code}")
                
                if data.get('status') == 200 and 'data' in data:
                    task_data = data['data']
                    state = task_data.get('state')
                    state_detail = task_data.get('state_detail', '')
                    self.logger.info(f"Estado da tarefa: {state}")
                    self.logger.info(f"Detalhe do estado: {state_detail}")
                    
                    # Verifica se o processamento está completo
                    if state == 1 and 'image' in task_data:  # Removido state_detail == 'Complete'
                        processed_url = task_data['image']
                        self.logger.info(f"URL da imagem processada: {processed_url}")
                        return processed_url
                    elif state < 0:
                        self.logger.error(f"Erro no processamento: {data}")
                        break
                    elif state == 2:  # Estado "Preparing"
                        self.logger.info("Preparando o processamento...")
                    else:
                        self.logger.info("Processamento ainda em andamento...")
            except Exception as e:
                self.logger.error(f"Erro ao obter resultado: {e}")
                break
        self.logger.warning("Timeout ou erro ao aguardar processamento")
        return None

    def process_remove_background(self, image_url):
        """Processa a imagem para remover o fundo"""
        headers = {'X-API-KEY': self.api_key}
        data = {'sync': '0', 'image_url': image_url}
        url = 'https://techhk.aoscdn.com/api/tasks/visual/segmentation'

        try:
            self.logger.info(f"Enviando requisição para remover fundo...")
            response = requests.post(url, headers=headers, data=data)
            response_json = response.json()
            self.logger.info(f"Status da requisição: {response.status_code}")
            self.logger.debug(f"Resposta completa: {response_json}")
            
            if response_json.get('status') == 200 and 'data' in response_json:
                task_id = response_json['data'].get('task_id')
                if task_id:
                    self.logger.info(f"Task ID obtido para remoção de fundo: {task_id}")
                    return task_id
                else:
                    self.logger.warning("Task ID não encontrado na resposta")
            else:
                self.logger.error(f"Erro na resposta: {response_json.get('message', 'Sem mensagem de erro')}")
        except Exception as e:
            self.logger.error(f"Erro ao processar remoção de fundo: {e}")
        return None

    def get_background_removed_image(self, task_id, timeout=30):
        """Obtém o resultado do processamento de remoção de fundo"""
        headers = {'X-API-KEY': self.api_key}
        url = f'https://techhk.aoscdn.com/api/tasks/visual/segmentation/{task_id}'
        
        self.logger.info(f"Iniciando polling para remoção de fundo task_id: {task_id}")
        for i in range(timeout):
            if i > 0:
                self.logger.info(f"Tentativa {i+1} de {timeout}")
                time.sleep(1)
            try:
                response = requests.get(url, headers=headers)
                data = response.json()
                
                if data.get('status') == 200 and 'data' in data:
                    task_data = data['data']
                    state = task_data.get('state')
                    self.logger.info(f"Estado da tarefa: {state}")
                    
                    if state == 1 and 'image' in task_data:
                        processed_url = task_data['image']
                        self.logger.info(f"URL da imagem sem fundo: {processed_url}")
                        return processed_url
                    elif state < 0:
                        self.logger.error(f"Erro no processamento: {data}")
                        break
                    else:
                        self.logger.info("Processamento ainda em andamento...")
            except Exception as e:
                self.logger.error(f"Erro ao obter resultado: {e}")
                break
        self.logger.warning("Timeout ou erro ao aguardar processamento")
        return None

    def process_id_photo(self, image_url):
        """Processa a imagem para formato 3x4"""
        headers = {'X-API-KEY': self.api_key}
        data = {'sync': '0', 'image_url': image_url}
        url = 'https://techhk.aoscdn.com/api/tasks/visual/idphoto'

        try:
            self.logger.info(f"Enviando requisição para formato 3x4...")
            response = requests.post(url, headers=headers, data=data)
            response_json = response.json()
            self.logger.info(f"Status da requisição: {response.status_code}")
            self.logger.debug(f"Resposta completa: {response_json}")
            
            if response_json.get('status') == 200 and 'data' in response_json:
                task_id = response_json['data'].get('task_id')
                if task_id:
                    self.logger.info(f"Task ID obtido para foto 3x4: {task_id}")
                    return task_id
        except Exception as e:
            self.logger.error(f"Erro ao processar foto 3x4: {e}")
        return None

    def get_id_photo_result(self, task_id, timeout=30):
        """Obtém o resultado do processamento 3x4"""
        headers = {'X-API-KEY': self.api_key}
        url = f'https://techhk.aoscdn.com/api/tasks/visual/idphoto/{task_id}'
        
        for i in range(timeout):
            if i > 0:
                time.sleep(1)
            try:
                response = requests.get(url, headers=headers)
                data = response.json()
                
                if data.get('status') == 200 and 'data' in data:
                    task_data = data['data']
                    state = task_data.get('state')
                    
                    if state == 1 and 'image' in task_data:
                        return task_data['image']
                    elif state < 0:
                        self.logger.error(f"Erro no processamento 3x4: {data}")
                        break
            except Exception as e:
                self.logger.error(f"Erro ao obter resultado 3x4: {e}")
                break
        return None

    def get_processed_filename(self, nome, remove_background, make_id_photo):
        """Gera o nome do arquivo baseado nos processos aplicados"""
        parts = [nome]
        
        # Sempre adiciona o sufixo processed
        parts.append("processed")
        
        # Adiciona indicadores para cada processo extra
        if remove_background:
            parts.append("no_bg")
        if make_id_photo:
            parts.append("3x4")
            
        # Junta as partes com underscore e define a extensão
        filename = "_".join(parts)
        extension = ".png" if remove_background else ".jpg"
        
        return f"{filename}{extension}"

    def process_candidate(self, candidate_data, base_dir, scale_iterations=1, remove_background=False, make_id_photo=False):
        """Processa um único candidato"""
        nome = candidate_data['Nome de Urna'].replace(' ', '_')
        cargo = candidate_data['Cargo']
        url_original = candidate_data['Imagem Oficial']
        
        self.logger.info(f"Processando candidato: {nome}")
        self.logger.info(f"URL original: {url_original}")
        
        # Criar estrutura de pastas
        images_dir = os.path.join(base_dir, 'imagens')
        processed_dir = os.path.join(base_dir, 'imagens_processadas')
        cargo_dir = os.path.join(images_dir, cargo)
        processed_cargo_dir = os.path.join(processed_dir, cargo)
        
        # Criar todas as pastas necessárias
        os.makedirs(cargo_dir, exist_ok=True)
        os.makedirs(processed_cargo_dir, exist_ok=True)

        # Baixar imagem original primeiro
        original_path = os.path.join(cargo_dir, f"{nome}.jpg")
        if not self.download_image(url_original, original_path):
            self.logger.warning(f"Falha ao baixar imagem original para {nome}")
            return False

        self.logger.info(f"Imagem original salva em: {original_path}")
        
        # Processar imagem
        current_url = url_original
        processed_success = False
        
        # Aplicar melhorias de qualidade
        for iteration in range(scale_iterations):
            task_id = self.process_image_with_picwish(current_url)
            if task_id and (improved_url := self.get_processed_image(task_id)):
                current_url = improved_url
                processed_success = True
            else:
                break
        
        # Remover fundo se solicitado
        if remove_background and current_url:
            if task_id := self.process_remove_background(current_url):
                if final_url := self.get_background_removed_image(task_id):
                    current_url = final_url
                    processed_success = True

        # Processar para 3x4 se solicitado
        if make_id_photo and current_url:
            if task_id := self.process_id_photo(current_url):
                if final_url := self.get_id_photo_result(task_id):
                    current_url = final_url
                    processed_success = True

        # Salvar resultado apenas se houve processamento bem-sucedido
        if processed_success and current_url != url_original:
            filename = self.get_processed_filename(nome, remove_background, make_id_photo)
            processed_path = os.path.join(processed_cargo_dir, filename)
            if self.download_image(current_url, processed_path):
                self.logger.info(f"Imagem processada salva em: {processed_path}")
                return True
            else:
                self.logger.warning(f"Falha ao salvar imagem processada para {nome}")
        else:
            self.logger.info(f"Nenhum processamento foi concluído com sucesso para {nome}")
        
        return False

    def process_candidates_list(self, candidates_data, base_dir, scale_iterations=1, remove_background=False, make_id_photo=False):
        """Processa uma lista de candidatos"""
        results = []
        for candidate in candidates_data:
            success = self.process_candidate(
                candidate,
                base_dir,
                scale_iterations=scale_iterations,
                remove_background=remove_background,
                make_id_photo=make_id_photo
            )
            results.append({
                'nome': candidate['Nome de Urna'],
                'cargo': candidate['Cargo'],
                'sucesso': success
            })
        return results

    def download_candidates_list(self, candidates_data, base_dir):
        """Apenas baixa as imagens originais dos candidatos"""
        results = []
        for candidate in candidates_data:
            nome = candidate['Nome de Urna'].replace(' ', '_')
            cargo = candidate['Cargo']
            url_original = candidate['Imagem Oficial']
            
            # Criar estrutura de pastas
            images_dir = os.path.join(base_dir, 'imagens')
            cargo_dir = os.path.join(images_dir, cargo)
            os.makedirs(cargo_dir, exist_ok=True)
            
            # Baixar imagem original
            original_path = os.path.join(cargo_dir, f"{nome}.jpg")
            success = self.download_image(url_original, original_path)
            
            if success:
                self.logger.info(f"Imagem de {nome} salva em: {original_path}")
            
            results.append({
                'nome': candidate['Nome de Urna'],
                'cargo': candidate['Cargo'],
                'sucesso': success
            })
        return results

if __name__ == "__main__":
    # Caminho para o arquivo JSON dos candidatos
    json_file = os.path.join(os.path.dirname(__file__), "DADOS", "SUL", "SC", "SOMBRIO", "candidatos_eleitos_SC_SOMBRIO.json")
    
    # Ler o arquivo JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        candidatos = json.load(f)

    base_dir = os.path.dirname(json_file)
    
    processor = PicWishProcessor()
    processor.process_candidates_list(
        candidatos,
        base_dir,
        scale_iterations=1,  # Número de vezes que vai melhorar a qualidade
        remove_background=False,  # Se deve remover o fundo
        make_id_photo=False  # Se deve processar para formato 3x4
    )
