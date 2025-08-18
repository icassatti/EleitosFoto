# Eleitos Foto

Ferramenta para coleta e processamento de fotos de candidatos eleitos.

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

1. Clone este repositório
2. Instale as dependências necessárias:

```bash
pip install requests
pip install Pillow
pip install svgwrite
```

### 3. Conta PicWish
1. Acesse [PicWish](https://picwish.com/)
2. Crie uma conta gratuita
3. Vá para [API Key](https://picwish.com/my-account?subRoute=api-key)
4. Copie sua API Key

## Configuração

1. Copie o arquivo `config.template.json` para `config.json`
2. Edite o arquivo `config.json` e adicione sua API key do PicWish

```json
{
    "picwish_api_key": "sua_api_key_aqui"
}
```

## Funcionalidades

- Download de fotos de candidatos eleitos do TSE
- Processamento opcional de imagens com IA (PicWish)
- Geração de tarjetas com informações dos candidatos
- Exportação para formatos CSV, JSON e SVG

## Uso

Execute o script principal:

```bash
python eleitos_download.py
```

O programa irá solicitar:
- Informações da eleição (ano, tipo, região, UF, município)
- Opções de processamento de imagem (IA, remoção de fundo, formato 3x4)
- Opção para geração de tarjetas

## Estrutura de Diretórios

```
DADOS/
├── [REGIÃO]/
│   ├── [UF]/
│   │   ├── [MUNICÍPIO]/
│   │   │   ├── imagens/
│   │   │   ├── imagens_processadas/
│   │   │   ├── tarjetas/
│   │   │   ├── candidatos_eleitos_[UF]_[MUNICÍPIO].csv
│   │   │   └── candidatos_eleitos_[UF]_[MUNICÍPIO].json
```
                    └── Vereador/
```

### Arquivos Gerados

- **CSV/JSON**: Contém dados dos candidatos eleitos
- **imagens/**: Fotos originais do TSE
- **imagens_processadas/**: Fotos após melhorias com IA
  - Sufixo `_processed`: Apenas melhoria de qualidade
  - Sufixo `_processed_no_bg`: Com remoção de fundo
  - Sufixo `_processed_3x4`: Formato 3x4
  - Sufixo `_processed_no_bg_3x4`: Remoção de fundo e formato 3x4

## Observações

- As imagens são organizadas por cargo
- O processamento pode demorar dependendo do número de candidatos
- A API do PicWish tem limites de uso gratuito
- As imagens processadas são salvas em JPG ou PNG (quando há remoção de fundo)
