# Eleitos Foto

Sistema para download e processamento de imagens de candidatos eleitos do TSE com melhorias usando IA.

## Pré-requisitos

### 1. Python
- Faça download do Python em [python.org](https://www.python.org/downloads/)
- Durante a instalação, marque a opção "Add Python to PATH"
- Verifique a instalação abrindo o terminal e digitando:
```bash
python --version
```

### 2. Bibliotecas Python
Abra o terminal e instale as bibliotecas necessárias:
```bash
pip install requests
```

### 3. Conta PicWish
1. Acesse [PicWish](https://picwish.com/)
2. Crie uma conta gratuita
3. Vá para [API Key](https://picwish.com/my-account?subRoute=api-key)
4. Copie sua API Key

## Configuração

1. Clone ou baixe este repositório
2. Copie o arquivo `config.template.json` para `config.json`
3. Abra `config.json` e substitua "your_api_key_here" pela sua API Key do PicWish

## Uso

1. Abra o terminal na pasta do projeto
2. Execute o programa:
```bash
python eleitos_download.py
```
3. Siga as instruções na tela para informar:
   - Ano da eleição
   - Tipo (municipal/federal)
   - Região
   - UF
   - Município
   - Configurações de processamento de imagem

## Estrutura de Arquivos Gerada

```
EleitosFoto/
└── DADOS/
    └── REGIAO/          # Ex: SUL
        └── UF/          # Ex: SC
            └── MUNICIPIO/   # Ex: SOMBRIO
                ├── candidatos_eleitos_UF_MUNICIPIO.csv
                ├── candidatos_eleitos_UF_MUNICIPIO.json
                ├── imagens/
                │   ├── Prefeito/
                │   ├── Vice-prefeito/
                │   └── Vereador/
                └── imagens_processadas/
                    ├── Prefeito/
                    ├── Vice-prefeito/
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
