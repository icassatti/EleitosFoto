import os
import json
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import svgwrite
from svgwrite import cm, mm
from corelmanager import CorelDrawManager
from log_config import setup_logger

class TarjetaGenerator:
    def __init__(self, output_dir="tarjetas"):
        self.output_dir = output_dir
        self.logger = setup_logger('TarjetaGenerator', os.path.join(os.path.dirname(__file__), 'tarjeta_generator.log'))
        self.logger.info("Iniciando TarjetaGenerator")
        self.largura = 600
        self.altura = 400
        self.font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        self.font_size = 20
        try:
            self.font = ImageFont.truetype(self.font_path, self.font_size)
        except OSError:
            # Fallback para fonte padrão se não encontrar a DejaVu
            print("Fonte DejaVu não encontrada, usando fonte padrão")
            self.font = ImageFont.load_default()
        os.makedirs(output_dir, exist_ok=True)
        
    def gerar_tarjeta(self, candidato):
        """Gera uma tarjeta individual"""
        self.logger.info(f"Gerando tarjeta para candidato: {candidato.get('Nome de Urna')}")
        nome_arquivo = f"{candidato.get('Nome de Urna')}_{candidato.get('Código do Município')}"
        
        # Gerar versão PNG
        png_path = os.path.join(self.output_dir, f"{nome_arquivo}.png")
        self._gerar_tarjeta_png(candidato, png_path)
        
        # Gerar versão SVG
        svg_path = os.path.join(self.output_dir, f"{nome_arquivo}.svg")
        self._gerar_tarjeta_svg(candidato, svg_path)
        
        return png_path, svg_path

    def _gerar_tarjeta_png(self, candidato, output_path):
        try:
            self.logger.info(f"Gerando PNG para {candidato.get('Nome de Urna')}")
            """Gera versão PNG da tarjeta"""
            tarjeta = Image.new("RGB", (self.largura, self.altura), "white")
            draw = ImageDraw.Draw(tarjeta)

            # Download and paste candidate image
            imagem_url = candidato.get("Imagem Oficial")
            try:
                response = requests.get(imagem_url)
                foto = Image.open(BytesIO(response.content)).convert("RGB")
                foto = foto.resize((200, 200))
                tarjeta.paste(foto, ((self.largura - 200) // 2, 20))
            except Exception as e:
                self.logger.warning(f"Erro ao baixar imagem de {candidato.get('Nome Completo')}: {e}")

            # Prepare text lines
            texto = [
                f"Nome: {candidato.get('Nome Completo')}",
                f"Urna: {candidato.get('Nome de Urna')}",
                f"Número: {candidato.get('Número na Urna')}",
                f"Partido: {candidato.get('Partido')}",
                f"Cargo: {candidato.get('Cargo')}",
                f"Reeleição: {candidato.get('Reeleição')}",
                f"Cidade/UF: {candidato.get('Código do Município')}"
            ]

            # Draw text below the image
            y_text = 240
            for line in texto:
                draw.text((30, y_text), line, font=self.font, fill="black")
                y_text += 30

            tarjeta.save(output_path)
            self.logger.info(f"PNG gerado com sucesso: {output_path}")
        except Exception as e:
            self.logger.error(f"Erro ao gerar PNG: {e}")
            raise

    def _gerar_tarjeta_svg(self, candidato, output_path):
        """Gera versão SVG da tarjeta (preparação para CorelDraw)"""
        dwg = svgwrite.Drawing(output_path, size=(f"{self.largura}px", f"{self.altura}px"))
        
        # Adicionar elementos
        dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill='white'))
        
        # Adicionar imagem do candidato
        imagem_url = candidato.get("Imagem Oficial")
        # Usando um elemento image do SVG para a foto
        dwg.add(dwg.image(href=imagem_url,
                         insert=((self.largura - 200) // 2, 20),
                         size=(200, 200)))
        
        # Texto
        texts = [
            f"Nome: {candidato.get('Nome Completo')}",
            f"Urna: {candidato.get('Nome de Urna')}",
            f"Número: {candidato.get('Número na Urna')}",
            f"Partido: {candidato.get('Partido')}",
            f"Cargo: {candidato.get('Cargo')}",
            f"Reeleição: {candidato.get('Reeleição')}"
        ]
        
        y = 240
        for text in texts:
            dwg.add(dwg.text(text, insert=(30, y), 
                           font_family="DejaVu Sans",
                           font_size=self.font_size,
                           fill='black'))  # Adicionado fill para garantir texto visível
            y += 30
            
        dwg.save()

    def gerar_arquivo_corel(self, candidatos):
        """Gera arquivo CorelDraw com todas as tarjetas"""
        # Criar SVG master que será convertido para CDR
        master_svg = os.path.join(self.output_dir, "tarjetas_master.svg")
        dwg = svgwrite.Drawing(master_svg, size=('297mm', '210mm'))  # A4 landscape
        
        # Organizar tarjetas em grid
        x, y = 10, 10
        for candidato in candidatos:
            _, svg_path = self.gerar_tarjeta(candidato)
            # Adicionar SVG como grupo
            dwg.add(dwg.use(svg_path, insert=(f"{x}mm", f"{y}mm")))
            
            # Calcular próxima posição
            x += self.largura + 10
            if x > 277:  # A4 width - margin
                x = 10
                y += self.altura + 10
                
        dwg.save()
        
        # TODO: Adicionar conversão de SVG para CDR
        # Isso requer uma ferramenta externa ou biblioteca específica
        print(f"Arquivo master SVG gerado em: {master_svg}")
        print("Para usar no CorelDraw, importe o arquivo SVG")

def process_candidates(candidatos_data, gerar_tarjetas=False):
    """Função para ser chamada do eleitos_download.py"""
    if not gerar_tarjetas:
        return
    
    try:
        corel = CorelDrawManager()
        output_dir = "tarjetas"
        os.makedirs(output_dir, exist_ok=True)
        
        # Gerar arquivo CDR
        output_path = os.path.join(output_dir, "tarjetas_eleitos.cdr")
        corel.create_template(candidatos_data, output_path)
        print(f"Arquivo CorelDraw gerado em: {output_path}")
        
    finally:
        corel.quit()

