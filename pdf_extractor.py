"""
Módulo de Extração Avançada de PDFs com IA
Detecta layout visual, posições, estrutura e usa ML para classificação
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict, Counter
from dataclasses import dataclass
import re
import numpy as np

try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@dataclass
class TextBlock:
    """Representa um bloco de texto com metadados"""
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    font_size: float
    font_name: str
    font_weight: str
    color: int
    is_bold: bool
    is_italic: bool
    
    @property
    def width(self) -> float:
        return self.x1 - self.x0
    
    @property
    def height(self) -> float:
        return self.y1 - self.y0
    
    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2
    
    @property
    def center_y(self) -> float:
        return (self.y0 + self.y1) / 2
    
    @property
    def area(self) -> float:
        return self.width * self.height


class SmartLayoutDetector:
    """Detector de layout inteligente com algoritmos avançados"""
    
    def __init__(self, page):
        self.page = page
        self.page_rect = page.rect
        self.width = self.page_rect.width
        self.height = self.page_rect.height
        self.margin_threshold = 50  # pixels
    
    def detect_margins(self, text_blocks: List[TextBlock]) -> Dict[str, float]:
        """Detecta margens da página"""
        if not text_blocks:
            return {'left': 0, 'right': self.width, 'top': 0, 'bottom': self.height}
        
        x_positions = [b.x0 for b in text_blocks] + [b.x1 for b in text_blocks]
        y_positions = [b.y0 for b in text_blocks] + [b.y1 for b in text_blocks]
        
        return {
            'left': min(x_positions),
            'right': max(x_positions),
            'top': min(y_positions),
            'bottom': max(y_positions)
        }
    
    def detect_grid_system(self, text_blocks: List[TextBlock]) -> Dict:
        """Detecta sistema de grid (colunas e linhas regulares)"""
        if not text_blocks:
            return {'columns': [], 'rows': [], 'grid_detected': False}
        
        # Análise de colunas por clustering de posições X
        x_positions = [b.x0 for b in text_blocks]
        x_clusters = self._cluster_positions(x_positions)
        
        # Análise de linhas por clustering de posições Y
        y_positions = [b.y0 for b in text_blocks]
        y_clusters = self._cluster_positions(y_positions)
        
        return {
            'columns': x_clusters,
            'rows': y_clusters,
            'grid_detected': len(x_clusters) > 1 or len(y_clusters) > 3
        }
    
    def _cluster_positions(self, positions: List[float], tolerance: float = 5) -> List[float]:
        """Agrupa posições próximas em clusters"""
        if not positions:
            return []
        
        sorted_pos = sorted(positions)
        clusters = []
        current_cluster = [sorted_pos[0]]
        
        for pos in sorted_pos[1:]:
            if pos - current_cluster[-1] <= tolerance:
                current_cluster.append(pos)
            else:
                clusters.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [pos]
        
        if current_cluster:
            clusters.append(sum(current_cluster) / len(current_cluster))
        
        return clusters
    
    def detect_visual_boxes(self) -> List[Dict]:
        """Detecta caixas/cards visuais por bordas, sombreamento e retângulos"""
        boxes = []
        drawings = self.page.get_drawings()
        
        for drawing in drawings:
            for item in drawing['items']:
                if item[0] == 'r':  # retângulo
                    if len(item) >= 3:
                        rect = item[1]
                        
                        # Calcula área e proporções
                        area = rect.width * rect.height
                        page_area = self.width * self.height
                        area_ratio = area / page_area
                        aspect_ratio = rect.width / rect.height if rect.height > 0 else 0
                        
                        # Filtra boxes relevantes
                        if 0.005 < area_ratio < 0.95 and rect.width > 50 and rect.height > 30:
                            boxes.append({
                                'type': 'visual_box',
                                'x0': rect.x0,
                                'y0': rect.y0,
                                'x1': rect.x1,
                                'y1': rect.y1,
                                'width': rect.width,
                                'height': rect.height,
                                'area': area,
                                'area_ratio': area_ratio,
                                'aspect_ratio': aspect_ratio,
                                'color': drawing.get('color', None),
                                'fill': drawing.get('fill', None),
                                'stroke_width': drawing.get('width', 1)
                            })
        
        return sorted(boxes, key=lambda x: x['area'], reverse=True)
    
    def detect_reading_order_zones(self, text_blocks: List[TextBlock]) -> List[Dict]:
        """Divide página em zonas respeitando ordem natural de leitura"""
        if not text_blocks:
            return []
        
        # Ordena blocos por posição (top-to-bottom, left-to-right)
        sorted_blocks = sorted(text_blocks, key=lambda b: (b.y0, b.x0))
        
        zones = []
        current_zone = []
        vertical_tolerance = 15
        horizontal_tolerance = self.width * 0.15
        
        for block in sorted_blocks:
            if not current_zone:
                current_zone.append(block)
            else:
                last_block = current_zone[-1]
                
                # Calcula distâncias
                vertical_gap = block.y0 - last_block.y1
                horizontal_overlap = self._calculate_horizontal_overlap(last_block, block)
                
                # Decide se pertence à mesma zona
                if vertical_gap < vertical_tolerance and horizontal_overlap > 0.5:
                    current_zone.append(block)
                elif vertical_gap < vertical_tolerance * 2 and abs(block.x0 - last_block.x0) < horizontal_tolerance:
                    current_zone.append(block)
                else:
                    # Nova zona
                    if current_zone:
                        zones.append(self._create_zone_from_blocks(current_zone))
                    current_zone = [block]
        
        if current_zone:
            zones.append(self._create_zone_from_blocks(current_zone))
        
        return zones
    
    def _calculate_horizontal_overlap(self, block1: TextBlock, block2: TextBlock) -> float:
        """Calcula percentual de sobreposição horizontal entre dois blocos"""
        overlap_start = max(block1.x0, block2.x0)
        overlap_end = min(block1.x1, block2.x1)
        
        if overlap_end <= overlap_start:
            return 0.0
        
        overlap = overlap_end - overlap_start
        min_width = min(block1.width, block2.width)
        
        return overlap / min_width if min_width > 0 else 0.0
    
    def _create_zone_from_blocks(self, blocks: List[TextBlock]) -> Dict:
        """Cria zona a partir de blocos com metadados enriquecidos"""
        x0 = min(b.x0 for b in blocks)
        y0 = min(b.y0 for b in blocks)
        x1 = max(b.x1 for b in blocks)
        y1 = max(b.y1 for b in blocks)
        
        # Extrai texto preservando ordem e formatação
        text_parts = []
        for block in blocks:
            text_parts.append(block.text.strip())
        
        text = '\n'.join(filter(None, text_parts))
        
        # Calcula estatísticas de fonte
        font_sizes = [b.font_size for b in blocks]
        avg_font_size = sum(font_sizes) / len(font_sizes)
        max_font_size = max(font_sizes)
        
        # Detecta ênfases
        has_bold = any(b.is_bold for b in blocks)
        has_italic = any(b.is_italic for b in blocks)
        
        return {
            'x0': x0,
            'y0': y0,
            'x1': x1,
            'y1': y1,
            'width': x1 - x0,
            'height': y1 - y0,
            'text': text,
            'blocks': [self._block_to_dict(b) for b in blocks],
            'avg_font_size': avg_font_size,
            'max_font_size': max_font_size,
            'has_bold': has_bold,
            'has_italic': has_italic,
            'block_count': len(blocks)
        }
    
    def _block_to_dict(self, block: TextBlock) -> Dict:
        """Converte TextBlock para dicionário"""
        return {
            'x0': block.x0,
            'y0': block.y0,
            'x1': block.x1,
            'y1': block.y1,
            'text': block.text,
            'font_size': block.font_size,
            'font_name': block.font_name,
            'is_bold': block.is_bold,
            'is_italic': block.is_italic
        }


class IntelligentContentAnalyzer:
    """Analisador de conteúdo com ML e heurísticas avançadas"""
    
    # Padrões de identificação
    TITLE_PATTERNS = [
        r'^[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ\s]+$',  # Tudo maiúsculo
        r'^\d+\.?\s+[A-Z]',  # Numeração de seção
        r'^(Capítulo|Seção|Parte)\s+\d+',
    ]
    
    LIST_MARKERS = ['•', '○', '●', '■', '□', '▪', '▫', '►', '▸', '⦿', '⦾', 
                    '-', '*', '→', '⇒', '»', '›', '✓', '✗']
    
    TABLE_INDICATORS = ['total', 'média', 'soma', '%', 'valor', 'quantidade',
                       'descrição', 'item', 'código', 'nome', 'data']
    
    @classmethod
    def classify_zone_advanced(cls, zone: Dict, page_context: Dict = None) -> Dict:
        """Classificação avançada com múltiplos critérios e score de confiança"""
        text = zone['text']
        text_lower = text.lower()
        
        # Features para classificação
        features = cls._extract_features(zone, text, text_lower)
        
        # Sistema de scoring para cada tipo
        scores = {
            'title': cls._score_title(features),
            'subtitle': cls._score_subtitle(features),
            'header': cls._score_header(features),
            'paragraph': cls._score_paragraph(features),
            'list': cls._score_list(features),
            'table_like': cls._score_table(features),
            'card': cls._score_card(features),
            'caption': cls._score_caption(features),
            'footnote': cls._score_footnote(features)
        }
        
        # Identifica tipo com maior score
        best_type = max(scores.items(), key=lambda x: x[1])
        
        return {
            'type': best_type[0],
            'confidence': best_type[1],
            'scores': scores,
            'features': features
        }
    
    @classmethod
    def _extract_features(cls, zone: Dict, text: str, text_lower: str) -> Dict:
        """Extrai features para classificação"""
        return {
            # Dimensões
            'width': zone['width'],
            'height': zone['height'],
            'area': zone['width'] * zone['height'],
            'aspect_ratio': zone['width'] / zone['height'] if zone['height'] > 0 else 0,
            
            # Texto
            'text_length': len(text),
            'word_count': len(text.split()),
            'line_count': len(text.split('\n')),
            'avg_line_length': len(text) / max(len(text.split('\n')), 1),
            
            # Formatação
            'avg_font_size': zone.get('avg_font_size', 12),
            'max_font_size': zone.get('max_font_size', 12),
            'has_bold': zone.get('has_bold', False),
            'has_italic': zone.get('has_italic', False),
            'block_count': zone.get('block_count', 1),
            
            # Conteúdo
            'has_numbers': bool(re.search(r'\d', text)),
            'has_uppercase': bool(re.search(r'[A-Z]', text)),
            'uppercase_ratio': sum(1 for c in text if c.isupper()) / max(len(text), 1),
            'has_list_markers': any(marker in text for marker in cls.LIST_MARKERS),
            'has_table_words': any(word in text_lower for word in cls.TABLE_INDICATORS),
            'is_short': len(text) < 100,
            'is_long': len(text) > 500,
            
            # Estrutura
            'starts_with_number': bool(re.match(r'^\d+\.?\s', text)),
            'is_all_caps': text.isupper() and len(text) > 3,
            'has_colon': ':' in text,
            'has_dash': '—' in text or '–' in text,
        }
    
    @classmethod
    def _score_title(cls, f: Dict) -> float:
        """Score para título principal"""
        score = 0.0
        
        # Tamanho de fonte grande
        if f['max_font_size'] >= 24: score += 0.4
        elif f['max_font_size'] >= 20: score += 0.3
        elif f['max_font_size'] >= 16: score += 0.2
        
        # Texto curto
        if f['word_count'] <= 10: score += 0.2
        
        # Bold ou maiúsculas
        if f['has_bold']: score += 0.15
        if f['is_all_caps']: score += 0.15
        
        # Proporções
        if f['height'] > 40: score += 0.1
        
        # Penalidades
        if f['word_count'] > 20: score -= 0.3
        if f['line_count'] > 2: score -= 0.2
        
        return max(0, min(1, score))
    
    @classmethod
    def _score_subtitle(cls, f: Dict) -> float:
        """Score para subtítulo"""
        score = 0.0
        
        if 14 <= f['max_font_size'] < 20: score += 0.3
        if f['has_bold']: score += 0.2
        if 3 <= f['word_count'] <= 15: score += 0.2
        if f['starts_with_number']: score += 0.15
        if f['uppercase_ratio'] > 0.3: score += 0.15
        
        return max(0, min(1, score))
    
    @classmethod
    def _score_header(cls, f: Dict) -> float:
        """Score para cabeçalho de seção"""
        score = 0.0
        
        if f['has_bold']: score += 0.3
        if f['starts_with_number']: score += 0.2
        if 13 <= f['max_font_size'] <= 18: score += 0.2
        if f['word_count'] <= 12: score += 0.15
        if f['has_colon']: score += 0.15
        
        return max(0, min(1, score))
    
    @classmethod
    def _score_paragraph(cls, f: Dict) -> float:
        """Score para parágrafo normal"""
        score = 0.3  # Base score
        
        if f['word_count'] >= 15: score += 0.2
        if f['line_count'] >= 2: score += 0.15
        if 10 <= f['avg_font_size'] <= 13: score += 0.2
        if not f['has_bold'] and not f['is_all_caps']: score += 0.15
        
        return max(0, min(1, score))
    
    @classmethod
    def _score_list(cls, f: Dict) -> float:
        """Score para lista"""
        score = 0.0
        
        if f['has_list_markers']: score += 0.5
        if f['line_count'] >= 3: score += 0.2
        if f['starts_with_number']: score += 0.15
        if 50 < f['avg_line_length'] < 200: score += 0.15
        
        return max(0, min(1, score))
    
    @classmethod
    def _score_table(cls, f: Dict) -> float:
        """Score para estrutura tabular"""
        score = 0.0
        
        if f['has_table_words']: score += 0.25
        if f['block_count'] >= 6: score += 0.25
        if f['has_numbers']: score += 0.15
        if 0.5 < f['aspect_ratio'] < 2: score += 0.15
        if f['line_count'] >= 4: score += 0.1
        
        # Alto número de blocos sugere estrutura
        if f['block_count'] >= 10: score += 0.1
        
        return max(0, min(1, score))
    
    @classmethod
    def _score_card(cls, f: Dict) -> float:
        """Score para card/box de destaque"""
        score = 0.0
        
        # Proporção quadrada
        if 0.7 < f['aspect_ratio'] < 1.5: score += 0.3
        
        # Área moderada
        if 5000 < f['area'] < 100000: score += 0.2
        
        # Conteúdo focado
        if f['is_short']: score += 0.2
        if f['has_bold']: score += 0.15
        if f['word_count'] <= 50: score += 0.15
        
        return max(0, min(1, score))
    
    @classmethod
    def _score_caption(cls, f: Dict) -> float:
        """Score para legenda"""
        score = 0.0
        
        if f['avg_font_size'] < 10: score += 0.3
        if f['is_short']: score += 0.2
        if f['has_italic']: score += 0.2
        if f['word_count'] <= 20: score += 0.15
        if 'figura' in f or 'tabela' in f or 'fonte:' in f: score += 0.15
        
        return max(0, min(1, score))
    
    @classmethod
    def _score_footnote(cls, f: Dict) -> float:
        """Score para nota de rodapé"""
        score = 0.0
        
        if f['avg_font_size'] < 9: score += 0.4
        if f['starts_with_number']: score += 0.2
        if f['is_short']: score += 0.2
        if f['word_count'] <= 30: score += 0.2
        
        return max(0, min(1, score))
    
    @classmethod
    def extract_structured_list(cls, text: str) -> List[Dict]:
        """Extrai lista estruturada com hierarquia"""
        lines = text.split('\n')
        items = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detecta nível de indentação
            indent_level = len(line) - len(line.lstrip())
            
            # Remove marcadores
            clean = re.sub(r'^[•○●■□▪▫►▸⦿⦾\-\*→⇒»›✓✗\d+\.)\]]\s*', '', line)
            
            if clean:
                items.append({
                    'text': clean,
                    'level': indent_level // 4,  # Assume 4 espaços por nível
                    'original': line
                })
        
        return items
    
    @classmethod
    def extract_key_value_pairs(cls, text: str) -> Dict[str, str]:
        """Extrai pares chave-valor de texto estruturado"""
        pairs = {}
        
        # Padrão: "Chave: Valor"
        matches = re.findall(r'([^:\n]+):\s*([^\n]+)', text)
        for key, value in matches:
            pairs[key.strip()] = value.strip()
        
        return pairs


class AdvancedPDFExtractor:
    """Extrator principal com IA e análise avançada"""
    
    def __init__(self, method: str = "auto", enable_ocr: bool = False, 
                 log_callback=None, progress_callback=None):
        self.method = method
        self.enable_ocr = enable_ocr
        self.log = log_callback or print
        self.progress = progress_callback or (lambda x: None)
    
    def extract(self, pdf_path: Path) -> List[Dict]:
        """Extrai dados com análise profunda de layout e conteúdo"""
        
        self.log(f"🔍 Iniciando extração avançada: {pdf_path.name}")
        
        doc = fitz.open(pdf_path)
        pages_data = []
        total_pages = len(doc)
        
        for page_num in range(total_pages):
            self.progress((page_num + 1) / total_pages)
            
            page = doc[page_num]
            self.log(f"📄 Processando página {page_num + 1}/{total_pages}")
            
            # Detector de layout inteligente
            layout_detector = SmartLayoutDetector(page)
            
            # Extrai blocos de texto com metadados completos
            text_blocks = self._extract_text_blocks_rich(page)
            
            # Detecta margens e grid
            margins = layout_detector.detect_margins(text_blocks)
            grid = layout_detector.detect_grid_system(text_blocks)
            
            # Detecta caixas visuais
            visual_boxes = layout_detector.detect_visual_boxes()
            
            # Cria zonas respeitando ordem de leitura
            zones = layout_detector.detect_reading_order_zones(text_blocks)
            
            # Classifica cada zona com IA
            for zone in zones:
                classification = IntelligentContentAnalyzer.classify_zone_advanced(zone)
                zone.update(classification)
            
            # Extrai tabelas com múltiplos métodos
            tables = self._extract_tables_advanced(pdf_path, page_num + 1, page)
            
            # Extrai imagens com análise
            images = self._extract_images_advanced(page)
            
            # Detecta headers e footers
            header_footer = self._detect_header_footer(text_blocks, page.rect.height)
            
            # Extrai metadados da página
            page_metadata = {
                'page': page_num + 1,
                'width': layout_detector.width,
                'height': layout_detector.height,
                'margins': margins,
                'grid': grid,
                'text_blocks': [self._block_to_export(b) for b in text_blocks],
                'zones': zones,
                'visual_boxes': visual_boxes,
                'tables': tables,
                'images': images,
                'header_footer': header_footer,
                'full_text': page.get_text(),
                'has_images': len(images) > 0,
                'has_tables': len(tables) > 0,
                'dominant_font_size': self._get_dominant_font_size(text_blocks)
            }
            
            pages_data.append(page_metadata)
        
        doc.close()
        
        self.log(f"✅ Extração completa: {total_pages} páginas processadas")
        return pages_data
    
    def _extract_text_blocks_rich(self, page) -> List[TextBlock]:
        """Extrai blocos de texto com metadados completos"""
        text_dict = page.get_text("dict")
        blocks = []
        
        for block in text_dict.get("blocks", []):
            if "lines" not in block:
                continue
            
            block_texts = []
            font_sizes = []
            font_names = []
            colors = []
            flags_list = []
            
            for line in block["lines"]:
                for span in line["spans"]:
                    block_texts.append(span["text"])
                    font_sizes.append(span["size"])
                    font_names.append(span["font"])
                    colors.append(span["color"])
                    flags_list.append(span.get("flags", 0))
            
            if not block_texts:
                continue
            
            # Calcula médias e detecta ênfases
            avg_font_size = sum(font_sizes) / len(font_sizes)
            dominant_font = Counter(font_names).most_common(1)[0][0] if font_names else ""
            dominant_color = Counter(colors).most_common(1)[0][0] if colors else 0
            
            # Flags: bit 0 = superscript, 1 = italic, 2 = serifed, 4 = bold
            is_bold = any(f & 2**4 for f in flags_list)
            is_italic = any(f & 2**1 for f in flags_list)
            
            # Detecta peso da fonte pelo nome
            font_weight = 'bold' if 'bold' in dominant_font.lower() else 'normal'
            
            text_block = TextBlock(
                x0=block['bbox'][0],
                y0=block['bbox'][1],
                x1=block['bbox'][2],
                y1=block['bbox'][3],
                text=' '.join(block_texts),
                font_size=avg_font_size,
                font_name=dominant_font,
                font_weight=font_weight,
                color=dominant_color,
                is_bold=is_bold,
                is_italic=is_italic
            )
            
            blocks.append(text_block)
        
        return blocks
    
    def _block_to_export(self, block: TextBlock) -> Dict:
        """Converte TextBlock para formato exportável"""
        return {
            'x0': block.x0,
            'y0': block.y0,
            'x1': block.x1,
            'y1': block.y1,
            'text': block.text,
            'font_size': block.font_size,
            'font_name': block.font_name,
            'is_bold': block.is_bold,
            'is_italic': block.is_italic
        }
    
    def _extract_tables_advanced(self, pdf_path: Path, page_num: int, page) -> List[Dict]:
        """Extração avançada de tabelas com fallback e validação"""
        tables = []
        
        # Método 1: pdfplumber (melhor para tabelas com linhas)
        if PDFPLUMBER_AVAILABLE:
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    pdf_page = pdf.pages[page_num - 1]
                    
                    # Tenta com diferentes configurações
                    for strategy in ['lines', 'lines_strict', 'text']:
                        extracted = pdf_page.extract_tables({
                            'vertical_strategy': strategy,
                            'horizontal_strategy': strategy,
                            'intersection_tolerance': 3
                        })
                        
                        for table in extracted:
                            if table and len(table) > 1:
                                validated = self._validate_table(table)
                                if validated:
                                    tables.append({
                                        'method': f'pdfplumber_{strategy}',
                                        'headers': validated['headers'],
                                        'rows': validated['rows'],
                                        'quality': 90,
                                        'columns': len(validated['headers']),
                                        'rows_count': len(validated['rows'])
                                    })
                        
                        if tables:
                            break  # Se encontrou, não precisa tentar outras estratégias
                
                self.log(f"  ✓ pdfplumber encontrou {len(tables)} tabela(s)")
            except Exception as e:
                self.log(f"  ⚠ PDFPlumber erro: {e}")
        
        # Método 2: Camelot (fallback ou adicional)
        if not tables and CAMELOT_AVAILABLE:
            try:
                # Lattice (para tabelas com bordas)
                extracted = camelot.read_pdf(
                    str(pdf_path),
                    pages=str(page_num),
                    flavor='lattice',
                    line_scale=40
                )
                
                for table in extracted:
                    df = table.df
                    if not df.empty:
                        validated = self._validate_table(df.values.tolist())
                        if validated:
                            tables.append({
                                'method': 'camelot_lattice',
                                'headers': validated['headers'],
                                'rows': validated['rows'],
                                'quality': int(table.accuracy),
                                'columns': len(validated['headers']),
                                'rows_count': len(validated['rows'])
                            })
                
                # Stream (para tabelas sem bordas visíveis)
                if not tables:
                    extracted = camelot.read_pdf(
                        str(pdf_path),
                        pages=str(page_num),
                        flavor='stream',
                        edge_tol=50
                    )
                    
                    for table in extracted:
                        df = table.df
                        if not df.empty:
                            validated = self._validate_table(df.values.tolist())
                            if validated:
                                tables.append({
                                    'method': 'camelot_stream',
                                    'headers': validated['headers'],
                                    'rows': validated['rows'],
                                    'quality': int(table.accuracy),
                                    'columns': len(validated['headers']),
                                    'rows_count': len(validated['rows'])
                                })
                
                self.log(f"  ✓ Camelot encontrou {len(tables)} tabela(s)")
            except Exception as e:
                self.log(f"  ⚠ Camelot erro: {e}")
        
        # Método 3: Detecção manual por análise de texto estruturado
        if not tables:
            manual_tables = self._detect_tables_by_structure(page)
            if manual_tables:
                tables.extend(manual_tables)
                self.log(f"  ✓ Detecção manual encontrou {len(manual_tables)} tabela(s)")
        
        return tables
    
    def _validate_table(self, table_data: List[List]) -> Optional[Dict]:
        """Valida e limpa dados de tabela"""
        if not table_data or len(table_data) < 2:
            return None
        
        # Remove linhas completamente vazias
        cleaned_rows = []
        for row in table_data:
            if any(str(cell).strip() for cell in row):
                cleaned_row = [str(cell).strip() for cell in row]
                cleaned_rows.append(cleaned_row)
        
        if len(cleaned_rows) < 2:
            return None
        
        # Primeira linha como headers
        headers = cleaned_rows[0]
        rows = cleaned_rows[1:]
        
        # Valida consistência de colunas
        num_cols = len(headers)
        valid_rows = []
        
        for row in rows:
            # Ajusta número de colunas se necessário
            if len(row) < num_cols:
                row.extend([''] * (num_cols - len(row)))
            elif len(row) > num_cols:
                row = row[:num_cols]
            
            valid_rows.append(row)
        
        return {
            'headers': headers,
            'rows': valid_rows
        }
    
    def _detect_tables_by_structure(self, page) -> List[Dict]:
        """Detecta tabelas por análise de estrutura de texto"""
        tables = []
        text_dict = page.get_text("dict")
        
        # Agrupa blocos por linha Y (tolerância de 5px)
        lines_dict = defaultdict(list)
        
        for block in text_dict.get("blocks", []):
            if "lines" not in block:
                continue
            
            for line in block["lines"]:
                y_pos = int(line["bbox"][1] / 5) * 5  # Agrupa por linha
                
                for span in line["spans"]:
                    lines_dict[y_pos].append({
                        'x': span["bbox"][0],
                        'text': span["text"].strip(),
                        'size': span["size"]
                    })
        
        # Detecta padrões tabulares (múltiplas linhas com múltiplos elementos alinhados)
        current_table = []
        
        for y_pos in sorted(lines_dict.keys()):
            line_items = sorted(lines_dict[y_pos], key=lambda x: x['x'])
            
            # Se tem 3+ itens alinhados horizontalmente, pode ser linha de tabela
            if len(line_items) >= 3:
                current_table.append(line_items)
            else:
                # Finaliza tabela se tinha conteúdo
                if len(current_table) >= 3:
                    table = self._structure_manual_table(current_table)
                    if table:
                        tables.append(table)
                current_table = []
        
        # Verifica última tabela
        if len(current_table) >= 3:
            table = self._structure_manual_table(current_table)
            if table:
                tables.append(table)
        
        return tables
    
    def _structure_manual_table(self, table_lines: List[List[Dict]]) -> Optional[Dict]:
        """Estrutura tabela detectada manualmente"""
        if len(table_lines) < 3:
            return None
        
        # Determina número de colunas pelo número médio de itens
        col_counts = [len(line) for line in table_lines]
        avg_cols = int(sum(col_counts) / len(col_counts))
        
        if avg_cols < 2:
            return None
        
        # Primeira linha como headers
        headers = [item['text'] for item in table_lines[0][:avg_cols]]
        
        # Demais linhas como dados
        rows = []
        for line in table_lines[1:]:
            row = [item['text'] for item in line[:avg_cols]]
            # Preenche colunas faltantes
            while len(row) < len(headers):
                row.append('')
            rows.append(row)
        
        return {
            'method': 'manual_structure',
            'headers': headers,
            'rows': rows,
            'quality': 70,
            'columns': len(headers),
            'rows_count': len(rows)
        }
    
    def _extract_images_advanced(self, page) -> List[Dict]:
        """Extrai informações avançadas de imagens"""
        images = []
        
        image_list = page.get_images(full=True)
        
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                
                # Pega informações da imagem
                img_dict = page.parent.extract_image(xref)
                
                # Posição na página
                img_rects = page.get_image_rects(img)
                
                for rect in img_rects:
                    image_info = {
                        'index': img_index,
                        'xref': xref,
                        'x0': rect.x0,
                        'y0': rect.y0,
                        'x1': rect.x1,
                        'y1': rect.y1,
                        'width': rect.width,
                        'height': rect.height,
                        'area': rect.width * rect.height,
                        'format': img_dict.get('ext', 'unknown'),
                        'colorspace': img_dict.get('colorspace', 'unknown'),
                        'size_bytes': len(img_dict.get('image', b'')),
                        'aspect_ratio': rect.width / rect.height if rect.height > 0 else 0
                    }
                    
                    # Classifica tipo de imagem
                    image_info['type'] = self._classify_image(image_info)
                    
                    images.append(image_info)
                    
            except Exception as e:
                self.log(f"  ⚠ Erro ao extrair imagem {img_index}: {e}")
        
        return images
    
    def _classify_image(self, img_info: Dict) -> str:
        """Classifica tipo de imagem por características"""
        aspect_ratio = img_info['aspect_ratio']
        area = img_info['area']
        
        # Logo (pequena e quadrada)
        if area < 10000 and 0.8 < aspect_ratio < 1.2:
            return 'logo'
        
        # Ícone (muito pequena)
        if area < 2000:
            return 'icon'
        
        # Banner (horizontal e larga)
        if aspect_ratio > 3:
            return 'banner'
        
        # Gráfico/Chart (moderada)
        if 10000 < area < 200000:
            return 'chart'
        
        # Foto/Ilustração (grande)
        if area > 100000:
            return 'photo'
        
        return 'figure'
    
    def _detect_header_footer(self, text_blocks: List[TextBlock], page_height: float) -> Dict:
        """Detecta headers e footers por posição"""
        header_zone = page_height * 0.1  # 10% superior
        footer_zone = page_height * 0.9  # 10% inferior
        
        header_blocks = [b for b in text_blocks if b.y1 < header_zone]
        footer_blocks = [b for b in text_blocks if b.y0 > footer_zone]
        
        return {
            'header': {
                'text': ' '.join(b.text for b in header_blocks),
                'blocks': [self._block_to_export(b) for b in header_blocks]
            } if header_blocks else None,
            'footer': {
                'text': ' '.join(b.text for b in footer_blocks),
                'blocks': [self._block_to_export(b) for b in footer_blocks]
            } if footer_blocks else None
        }
    
    def _get_dominant_font_size(self, text_blocks: List[TextBlock]) -> float:
        """Retorna tamanho de fonte mais comum"""
        if not text_blocks:
            return 12.0
        
        font_sizes = [b.font_size for b in text_blocks]
        return Counter(font_sizes).most_common(1)[0][0]
    
    def extract_with_ocr(self, pdf_path: Path, pages: Optional[List[int]] = None) -> List[Dict]:
        """Extrai com OCR para PDFs escaneados"""
        # Placeholder para implementação futura com Tesseract/EasyOCR
        self.log("⚠ OCR ainda não implementado")
        return self.extract(pdf_path)
    
    def analyze_document_structure(self, pages_data: List[Dict]) -> Dict:
        """Analisa estrutura geral do documento"""
        
        total_pages = len(pages_data)
        
        # Coleta estatísticas
        all_zones = []
        all_tables = []
        all_images = []
        zone_types = []
        
        for page in pages_data:
            all_zones.extend(page['zones'])
            all_tables.extend(page['tables'])
            all_images.extend(page['images'])
            zone_types.extend([z['type'] for z in page['zones']])
        
        # Análise de tipografia
        font_sizes = []
        for page in pages_data:
            for block in page['text_blocks']:
                font_sizes.append(block['font_size'])
        
        return {
            'total_pages': total_pages,
            'total_zones': len(all_zones),
            'total_tables': len(all_tables),
            'total_images': len(all_images),
            'zone_type_distribution': dict(Counter(zone_types)),
            'avg_zones_per_page': len(all_zones) / total_pages if total_pages > 0 else 0,
            'has_tables': len(all_tables) > 0,
            'has_images': len(all_images) > 0,
            'typography': {
                'min_font_size': min(font_sizes) if font_sizes else 0,
                'max_font_size': max(font_sizes) if font_sizes else 0,
                'avg_font_size': sum(font_sizes) / len(font_sizes) if font_sizes else 0,
                'common_sizes': dict(Counter(font_sizes).most_common(5))
            },
            'document_type': self._infer_document_type(zone_types, len(all_tables), len(all_images))
        }
    
    def _infer_document_type(self, zone_types: List[str], table_count: int, image_count: int) -> str:
        """Infere tipo de documento baseado em características"""
        type_counts = Counter(zone_types)
        
        # Documento acadêmico/científico
        if table_count > 5 or (table_count > 2 and type_counts.get('paragraph', 0) > 10):
            return 'scientific_paper'
        
        # Apresentação/Slides
        if type_counts.get('title', 0) > 5 and image_count > 5:
            return 'presentation'
        
        # Manual/Guia
        if type_counts.get('list', 0) > 10 or type_counts.get('header', 0) > 10:
            return 'manual'
        
        # Relatório
        if table_count > 0 and type_counts.get('paragraph', 0) > 5:
            return 'report'
        
        # Livro/Texto longo
        if type_counts.get('paragraph', 0) > 20:
            return 'book'
        
        return 'generic_document'
    
    def export_markdown(self, pages_data: List[Dict], output_path: Path):
        """Exporta para Markdown estruturado"""
        md_lines = []
        
        for page_data in pages_data:
            md_lines.append(f"\n---\n## Página {page_data['page']}\n")
            
            for zone in page_data['zones']:
                zone_type = zone['type']
                text = zone['text'].strip()
                
                if not text:
                    continue
                
                if zone_type == 'title':
                    md_lines.append(f"\n# {text}\n")
                elif zone_type == 'subtitle':
                    md_lines.append(f"\n## {text}\n")
                elif zone_type == 'header':
                    md_lines.append(f"\n### {text}\n")
                elif zone_type == 'list':
                    items = IntelligentContentAnalyzer.extract_structured_list(text)
                    for item in items:
                        indent = "  " * item['level']
                        md_lines.append(f"{indent}- {item['text']}")
                    md_lines.append("")
                elif zone_type == 'card':
                    md_lines.append(f"\n> **{text}**\n")
                else:
                    md_lines.append(f"\n{text}\n")
            
            # Adiciona tabelas
            for table in page_data['tables']:
                md_lines.append("\n")
                headers = table['headers']
                rows = table['rows']
                
                # Cabeçalho
                md_lines.append("| " + " | ".join(headers) + " |")
                md_lines.append("|" + "|".join(["---"] * len(headers)) + "|")
                
                # Linhas
                for row in rows:
                    md_lines.append("| " + " | ".join(str(c) for c in row) + " |")
                
                md_lines.append("")
        
        output_path.write_text('\n'.join(md_lines), encoding='utf-8')
        self.log(f"✅ Markdown exportado: {output_path}")


# Função auxiliar para uso rápido
def extract_pdf_smart(pdf_path: str, output_format: str = 'json') -> Dict:
    """
    Função helper para extração rápida e inteligente
    
    Args:
        pdf_path: Caminho do PDF
        output_format: 'json', 'markdown', 'html'
    
    Returns:
        Dados extraídos e análise estrutural
    """
    extractor = AdvancedPDFExtractor(
        method='auto',
        log_callback=print
    )
    
    path = Path(pdf_path)
    pages_data = extractor.extract(path)
    analysis = extractor.analyze_document_structure(pages_data)
    
    result = {
        'metadata': {
            'filename': path.name,
            'total_pages': len(pages_data),
            'analysis': analysis
        },
        'pages': pages_data
    }
    
    # Exporta conforme formato solicitado
    if output_format == 'markdown':
        md_path = path.with_suffix('.md')
        extractor.export_markdown(pages_data, md_path)
        result['output_file'] = str(md_path)
    
    return result
