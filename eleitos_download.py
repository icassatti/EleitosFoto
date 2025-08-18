import requests
import csv
import json
import os
from picwish import PicWishProcessor
from geradortarget import process_candidates

# Códigos dos cargos
CARGOS = {
    11: "Prefeito",
    12: "Vice-prefeito",
    13: "Vereador"
}

def obter_id_eleicao(ano, tipo):
    tipo = tipo.lower()
    abrangencia = "M" if tipo == "municipal" else "F"
    url = "https://divulgacandcontas.tse.jus.br/divulga/rest/v1/ata/ordinarias"
    try:
        response = requests.get(url)
        response.raise_for_status()
        eleicoes = response.json()
        for eleicao in eleicoes:
            if str(eleicao.get("ano")) == str(ano) and eleicao.get("tipoAbrangencia") == abrangencia:
                return eleicao.get("id")
    except requests.RequestException as e:
        print(f"Erro ao acessar o endpoint de eleições: {e}")
    return None

def obter_ufs_por_regiao(id_eleicao):
    url = f"https://divulgacandcontas.tse.jus.br/divulga/rest/v1/eleicao/eleicao-atual?idEleicao={id_eleicao}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        dados = response.json()
        ues = dados.get("ues", [])
        regioes = {}
        for ue in ues:
            regiao = ue.get("regiao")
            sigla = ue.get("sigla")
            nome = ue.get("nome")
            if regiao and sigla and sigla != "BR":
                if regiao not in regioes:
                    regioes[regiao] = []
                regioes[regiao].append({"sigla": sigla, "nome": nome})
        return regioes
    except requests.RequestException as e:
        print(f"Erro ao acessar dados da eleição atual: {e}")
    return {}

def buscar_codigo_municipio(uf, id_eleicao, nome_municipio):
    url = f"https://divulgacandcontas.tse.jus.br/divulga/rest/v1/eleicao/buscar/{uf}/{id_eleicao}/municipios"
    try:
        response = requests.get(url)
        response.raise_for_status()
        municipios = response.json()
        
        # Handle case where municipios is a string
        if isinstance(municipios, str):
            print(f"Resposta inesperada do servidor: {municipios}")
            return None
            
        # Handle case where municipios is a dict with nested data
        if isinstance(municipios, dict):
            municipios = municipios.get('municipios', [])
            
        for municipio in municipios:
            if isinstance(municipio, dict) and municipio.get("nome", "").strip().lower() == nome_municipio.strip().lower():
                return municipio.get("codigo")
        
        print(f"Município '{nome_municipio}' não encontrado em {uf}")
        return None
    except requests.RequestException as e:
        print(f"Erro ao buscar municípios: {e}")
        return None
    except (KeyError, TypeError) as e:
        print(f"Erro ao processar dados dos municípios: {e}")
        return None

def obter_candidatos_eleitos(id_eleicao, codigo_municipio, codigo_cargo):
    url = f"https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/listar/2024/{codigo_municipio}/{id_eleicao}/{codigo_cargo}/candidatos"
    try:
        response = requests.get(url)
        response.raise_for_status()
        dados = response.json()
        candidatos = dados.get("candidatos", [])
        eleitos = []
        for candidato in candidatos:
            totalizacao = candidato.get("descricaoTotalizacao", "")
            if "Eleito" in totalizacao:
                id_candidato = candidato.get("id")
                imagem_url = f"https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/{id_eleicao}/{id_candidato}/{codigo_municipio}"
                eleitos.append({
                    "Nome Completo": candidato.get("nomeCompleto"),
                    "Nome de Urna": candidato.get("nomeUrna"),
                    "Número na Urna": candidato.get("numero"),
                    "Partido": candidato.get("partido", {}).get("sigla"),
                    "Cargo": CARGOS[codigo_cargo],
                    "Código do Cargo": codigo_cargo,
                    "Código do Município": codigo_municipio,
                    "Reeleição": "Sim" if candidato.get("st_REELEICAO") else "Não",
                    "Imagem Oficial": imagem_url
                })
        return eleitos
    except requests.RequestException as e:
        print(f"Erro ao acessar candidatos do cargo {codigo_cargo}: {e}")
    return []

def criar_estrutura_diretorios(regiao, uf, municipio):
    """Cria a estrutura de diretórios se não existir e retorna o caminho completo"""
    # Converte todos os nomes para maiúsculas e remove espaços extras
    regiao = regiao.strip().upper()
    uf = uf.strip().upper()
    municipio = municipio.strip().upper()
    
    # Obtém o diretório atual do script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Define o caminho base relativo ao script e cria a estrutura
    caminho_completo = os.path.join(script_dir, "DADOS", regiao, uf, municipio)
    
    # Cria os diretórios se não existirem
    os.makedirs(caminho_completo, exist_ok=True)
    
    return caminho_completo

def exportar_para_csv_json(dados, uf, municipio, regiao):
    """Exporta os dados para CSV e JSON na estrutura de pastas correta"""
    # Obtém o caminho completo para salvar os arquivos
    caminho_pasta = criar_estrutura_diretorios(regiao, uf, municipio)
    base_nome = f"candidatos_eleitos_{uf.upper()}_{municipio.upper().replace(' ', '_')}"
    
    try:
        # Cria os caminhos completos para os arquivos
        caminho_csv = os.path.join(caminho_pasta, f"{base_nome}.csv")
        caminho_json = os.path.join(caminho_pasta, f"{base_nome}.json")
        
        # Salva o arquivo CSV
        with open(caminho_csv, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=dados[0].keys())
            writer.writeheader()
            writer.writerows(dados)
            
        # Salva o arquivo JSON
        with open(caminho_json, mode="w", encoding="utf-8") as jsonfile:
            json.dump(dados, jsonfile, ensure_ascii=False, indent=2)
            
        print(f"Dados exportados para:\n{caminho_csv}\n{caminho_json}")
    except Exception as e:
        print(f"Erro ao exportar arquivos: {e}")

def carregar_config():
    """Carrega configurações do arquivo config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    template_path = os.path.join(os.path.dirname(__file__), 'config.template.json')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"\nERRO: Arquivo de configuração não encontrado!")
        print(f"1. Copie o arquivo {template_path}")
        print(f"2. Renomeie para config.json")
        print(f"3. Atualize a chave 'picwish_api_key' com sua API key do PicWish")
        exit(1)

def obter_parametros():
    """Obtém os parâmetros de execução via input do usuário"""
    config = carregar_config()
    
    print("\n=== Configuração da Coleta de Dados ===")
    ano = input("Ano da eleição (Ex: 2024): ").strip()
    tipo = input("Tipo da eleição (municipal/federal): ").strip()
    regiao = input("Região (SUL/SUDESTE/NORTE/NORDESTE/CENTRO-OESTE): ").strip().upper()
    uf = input("UF (Ex: SC/PR/RS/SP): ").strip().upper()
    municipio = input("Nome do Município: ").strip()
    
    print("\n=== Configuração do Processamento de Imagens ===")
    usar_ia = input("Deseja melhorar as fotos com IA? (s/N): ").strip().lower() == 's'
    
    params = {
        'ano': ano,
        'tipo': tipo,
        'regiao': regiao,
        'uf': uf,
        'municipio': municipio,
        'usar_ia': usar_ia,
        'api_key': None,
        'scale_iterations': 0,
        'remove_background': False,
        'make_id_photo': False
    }
    
    if usar_ia:
        params['api_key'] = config.get('picwish_api_key')
        scale_iter = input("Número de iterações de melhoria (Enter para 1): ").strip()
        params['scale_iterations'] = int(scale_iter) if scale_iter.isdigit() else 1
        
        remove_bg = input("Remover fundo? (s/N): ").strip().lower()
        params['remove_background'] = remove_bg == 's'
        
        make_3x4 = input("Processar para 3x4? (s/N): ").strip().lower()
        params['make_id_photo'] = make_3x4 == 's'
    
    print("\n=== Configuração de Tarjetas ===")
    gerar_tarjetas = input("Deseja gerar tarjetas? (s/N): ").strip().lower() == 's'
    params['gerar_tarjetas'] = gerar_tarjetas
    
    return params

# === Fluxo principal com variáveis fixas ===
if __name__ == "__main__":
    # Obter parâmetros via input
    params = obter_parametros()
    
    id_eleicao = obter_id_eleicao(params['ano'], params['tipo'])
    if id_eleicao:
        regioes = obter_ufs_por_regiao(id_eleicao)
        ufs = regioes.get(params['regiao'])
        if ufs and any(uf["sigla"] == params['uf'] for uf in ufs):
            codigo_municipio = buscar_codigo_municipio(params['uf'], id_eleicao, params['municipio'])
            if codigo_municipio:
                todos_eleitos = []
                for codigo_cargo in CARGOS:
                    eleitos = obter_candidatos_eleitos(id_eleicao, codigo_municipio, codigo_cargo)
                    todos_eleitos.extend(eleitos)
                if todos_eleitos:
                    # Exportar dados
                    caminho_base = criar_estrutura_diretorios(params['regiao'], params['uf'], params['municipio'])
                    exportar_para_csv_json(todos_eleitos, params['uf'], params['municipio'], params['regiao'])
                    
                    # Processar imagens
                    processor = PicWishProcessor(api_key=params['api_key'])
                    if params['usar_ia']:
                        resultados = processor.process_candidates_list(
                            todos_eleitos,
                            caminho_base,
                            scale_iterations=params['scale_iterations'],
                            remove_background=params['remove_background'],
                            make_id_photo=params['make_id_photo']
                        )
                    else:
                        resultados = processor.download_candidates_list(todos_eleitos, caminho_base)
                    
                    # Mostrar resultados do processamento
                    for resultado in resultados:
                        status = "sucesso" if resultado['sucesso'] else "falha"
                        print(f"{'Processamento' if params['usar_ia'] else 'Download'} de {resultado['nome']} ({resultado['cargo']}): {status}")
                    
                    # Gerar tarjetas se solicitado
                    if params['gerar_tarjetas']:
                        process_candidates(todos_eleitos, True)
                else:
                    print("Nenhum candidato eleito encontrado.")
            else:
                print("Município não encontrado.")
        else:
            print("UF não encontrada na região selecionada.")
    else:
        print("Eleição não encontrada.")