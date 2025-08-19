import win32com.client
import os
from log_config import setup_logger

class CorelDrawManager:
    # Constants from mdMain
    CONST_PAGE = {
        'WIDTH': 550,  # SizeWidthPage in mm
        'HEIGHT': 329  # SizeHeightPage in mm
    }
    
    CONST_LAYOUT = {
        'MIN_WIDTH_OUTLINE': 0.0762,
        'DISTANCE_BETWEEN_COLUMNS': 124,
        'DISTANCE_BETWEEN_ROWS': -19.823,
        'FIRST_COLUMN_CENTER_X': 73.453,
        'FIRST_ROW_CENTER_Y': 303.268,
        'MAX_TEXT_WIDTH': 93
    }
    
    CONST_RECTANGLE = {
        'HEIGHT': 19.3,
        'WIDTH': 101.4
    }
    
    CONST_TEXT = {
        'NAME_Y_OFFSET': 2.687,
        'BASE_NAME_LENGTH': 10,
        'BASE_NAME_WIDTH': 84,
        'BASE_NAME_HEIGHT': 7.29,
        'NAME_WIDTH_UNIT': 0.391304348,
        'NAME_HEIGHT_UNIT': -0.121052632,
        'INFO_Y_OFFSET': -5.064
    }

    def __init__(self):
        """Initialize CorelDraw Manager and setup logging"""
        self.logger = setup_logger('CorelDrawManager', os.path.join(os.path.dirname(__file__), 'corel_manager.log'))
        self.logger.info("Iniciando CorelDraw Manager")
        try:
            self.app = win32com.client.Dispatch('CorelDRAW.Application')
            self.app.Visible = False
            self.logger.info("CorelDraw Application iniciado com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao iniciar CorelDraw: {e}")
            raise

    def create_document(self, output_path):
        """Creates a new CorelDraw document with standard settings"""
        try:
            self.logger.info("Criando novo documento CorelDraw")
            doc = self.app.CreateDocument()
            doc.Unit = 3  # cdrMillimeter
            page = doc.ActivePage
            page.SizeWidth = self.CONST_PAGE['WIDTH']
            page.SizeHeight = self.CONST_PAGE['HEIGHT']
            self.logger.info(f"Documento criado com dimensões: {self.CONST_PAGE['WIDTH']}x{self.CONST_PAGE['HEIGHT']}mm")
            return doc
        except Exception as e:
            self.logger.error(f"Erro ao criar documento: {e}")
            raise

    def create_tarjeta(self, doc, candidate_data, col, row):
        """Creates a single tarjeta for a candidate"""
        try:
            self.logger.info(f"Criando tarjeta para {candidate_data['Nome de Urna']} na posição ({col}, {row})")
            layer = doc.ActivePage.ActiveLayer
            
            # Calculate position
            x = self.CONST_LAYOUT['FIRST_COLUMN_CENTER_X'] + (col * self.CONST_LAYOUT['DISTANCE_BETWEEN_COLUMNS'])
            y = self.CONST_LAYOUT['FIRST_ROW_CENTER_Y'] + (row * self.CONST_LAYOUT['DISTANCE_BETWEEN_ROWS'])
            
            # Create rectangle
            self.logger.debug(f"Criando retângulo na posição (x={x}, y={y})")
            rect = layer.CreateRectangle(
                x - (self.CONST_RECTANGLE['WIDTH'] / 2),
                y - (self.CONST_RECTANGLE['HEIGHT'] / 2),
                x + (self.CONST_RECTANGLE['WIDTH'] / 2),
                y + (self.CONST_RECTANGLE['HEIGHT'] / 2)
            )
            rect.Outline.Width = self.CONST_LAYOUT['MIN_WIDTH_OUTLINE']
            
            # Create name text
            self.logger.debug("Criando textos da tarjeta")
            name_text = layer.CreateArtisticText(
                x - (self.CONST_RECTANGLE['WIDTH'] / 2),
                y + self.CONST_TEXT['NAME_Y_OFFSET'],
                candidate_data['Nome de Urna'],
                'Cooper Black',
                22.154
            )
            self._format_name_text(name_text, x, y)
            
            # Create info text
            info = f"{candidate_data['Número na Urna']} - {candidate_data['Partido']} - {candidate_data['Cargo']}"
            info_text = layer.CreateArtisticText(
                x - (self.CONST_RECTANGLE['WIDTH'] / 2),
                y + self.CONST_TEXT['INFO_Y_OFFSET'],
                info,
                'Arial',
                9.934
            )
            self._format_info_text(info_text, x, y)
            self.logger.info(f"Tarjeta criada com sucesso para {candidate_data['Nome de Urna']}")
        except Exception as e:
            self.logger.error(f"Erro ao criar tarjeta para {candidate_data.get('Nome de Urna', 'Nome não encontrado')}: {e}")
            raise

    def _format_name_text(self, text_shape, center_x, center_y):
        """Formats the candidate name text object"""
        text_shape.Text.Story.Fill.UniformColor.RGBAssign(220, 0, 0)  # Red
        text_shape.Outline.Width = 1
        text_shape.Outline.Color.RGBAssign(255, 255, 255)  # White
        text_shape.Outline.BehindFill = True
        text_shape.CenterX = center_x
        text_shape.CenterY = center_y + self.CONST_TEXT['NAME_Y_OFFSET']

    def _format_info_text(self, text_shape, center_x, center_y):
        """Formats the candidate info text object"""
        text_shape.Text.Story.Fill.UniformColor.RGBAssign(0, 0, 0)  # Black
        text_shape.Text.Story.Bold = True
        text_shape.Outline.Width = 1
        text_shape.Outline.Color.RGBAssign(255, 255, 255)  # White
        text_shape.Outline.BehindFill = True
        text_shape.CenterX = center_x
        text_shape.CenterY = center_y + self.CONST_TEXT['INFO_Y_OFFSET']

    def create_template(self, candidates_data, output_path):
        """Creates a complete template with all candidates"""
        try:
            self.logger.info(f"Iniciando criação do template com {len(candidates_data)} candidatos")
            doc = self.create_document(output_path)
            
            col = 0
            row = 0
            max_rows = 15
            
            for i, candidate in enumerate(candidates_data, 1):
                if row >= max_rows:
                    row = 0
                    col += 1
                if col >= 4:
                    self.logger.warning("Limite máximo de colunas atingido (4 colunas)")
                    break
                    
                self.logger.info(f"Processando candidato {i}/{len(candidates_data)}")
                self.create_tarjeta(doc, candidate, col, row)
                row += 1
            
            self.logger.info(f"Salvando arquivo em: {output_path}")
            doc.SaveAs(output_path)
            doc.Close()
            self.logger.info("Template criado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao criar template: {e}")
            raise

    def quit(self):
        """Closes CorelDraw application"""
        try:
            self.logger.info("Fechando CorelDraw Application...")
            self.app.Quit()
            self.logger.info("CorelDraw Application fechado com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao fechar CorelDraw: {e}")
            raise
            self.logger.error(f"Erro ao criar template: {e}")
            raise

    def quit(self):
        """Closes CorelDraw application"""
        try:
            self.logger.info("Fechando CorelDraw Application...")
            self.app.Quit()
            self.logger.info("CorelDraw Application fechado com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao fechar CorelDraw: {e}")
            raise
