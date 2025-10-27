"""
Gerador de HTML com Design Neumórfico Dark + Neon Blue
Inspirado em layouts profissionais de documentação médica
"""

from typing import List, Dict
import re


class HTMLGenerator:
    """Gera HTML profissional estilo documentação médica"""
    
    def __init__(self, theme='neumorphic_dark', include_toc=True, responsive=True, 
                 animations=True, dark_mode=False):
        self.theme = theme
        self.include_toc = include_toc
        self.responsive = responsive
        self.animations = animations
        self.dark_mode = dark_mode
        self.toc_items = []
    
    def generate(self, pages_data: List[Dict]) -> str:
        """Gera HTML completo"""
        
        # Reseta TOC
        self.toc_items = []
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="pt-BR">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '    <title>Psicofármacos na Prática - Guia Profissional</title>',
            self._generate_css(),
            '</head>',
            '<body>'
        ]
        
        # Header
        html_parts.append(self._generate_header())
        
        # Container principal
        html_parts.append('<div class="main-container">')
        
        # Sidebar com TOC (se habilitado)
        if self.include_toc:
            html_parts.append('<aside class="sidebar">')
            html_parts.append(self._generate_toc_placeholder())
            html_parts.append('</aside>')
        
        # Conteúdo principal
        html_parts.append('<main class="content">')
        
        # Processa páginas
        for page_data in pages_data:
            html_parts.append(self._process_page(page_data))
        
        html_parts.append('</main>')
        html_parts.append('</div>')
        
        # Footer
        html_parts.append(self._generate_footer())
        
        # Scripts
        html_parts.append(self._generate_scripts())
        
        html_parts.extend(['</body>', '</html>'])
        
        # Pós-processamento: adiciona TOC real
        html = '\n'.join(html_parts)
        if self.include_toc:
            html = html.replace('<!-- TOC_PLACEHOLDER -->', self._generate_toc())
        
        return html
    
    def _process_page(self, page_data: Dict) -> str:
        """Processa uma página completa"""
        html_parts = [f'<article class="page" data-page="{page_data["page"]}">']
        
        zones = page_data.get('zones', [])
        tables = page_data.get('tables', [])
        images = page_data.get('images', [])
        
        # Se tem tabelas, processa com prioridade
        if tables:
            for table in tables:
                html_parts.append(self._generate_table(table, page_data['page']))
        
        # Processa zonas de conteúdo
        for zone in zones:
            zone_type = zone.get('type', 'paragraph')
            
            if zone_type == 'title':
                html_parts.append(self._generate_title(zone))
            elif zone_type == 'list':
                html_parts.append(self._generate_list(zone))
            elif zone_type == 'card':
                html_parts.append(self._generate_card(zone))
            elif zone_type == 'table_like':
                html_parts.append(self._generate_grid(zone))
            else:
                html_parts.append(self._generate_paragraph(zone))
        
        html_parts.append('</article>')
        
        return '\n'.join(html_parts)
    
    def _generate_title(self, zone: Dict) -> str:
        """Gera título/heading"""
        text = zone['text'].strip()
        
        # Determina nível baseado em tamanho
        font_size = zone['blocks'][0].get('font_size', 12) if zone['blocks'] else 12
        
        if font_size >= 24:
            level = 1
        elif font_size >= 18:
            level = 2
        else:
            level = 3
        
        # Adiciona ao TOC
        toc_id = self._generate_id(text)
        self.toc_items.append({
            'id': toc_id,
            'text': text,
            'level': level
        })
        
        return f'''
<div class="section-header">
    <h{level} class="section-title" id="{toc_id}">{text}</h{level}>
</div>
'''
    
    def _generate_paragraph(self, zone: Dict) -> str:
        """Gera parágrafo de texto"""
        text = zone['text'].strip()
        
        if not text:
            return ''
        
        # Divide em parágrafos se tiver múltiplas linhas
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        html = '<div class="text-block">\n'
        for para in paragraphs:
            html += f'    <p>{para}</p>\n'
        html += '</div>\n'
        
        return html
    
    def _generate_list(self, zone: Dict) -> str:
        """Gera lista com marcadores"""
        text = zone['text']
        items = []
        
        # Extrai itens
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Remove marcadores
            clean = re.sub(r'^[•\-→▪◦]\s*', '', line)
            if clean:
                items.append(clean)
        
        if not items:
            return ''
        
        html = '<div class="list-block">\n    <ul class="styled-list">\n'
        for item in items:
            html += f'        <li>{item}</li>\n'
        html += '    </ul>\n</div>\n'
        
        return html
    
    def _generate_card(self, zone: Dict) -> str:
        """Gera card destacado"""
        text = zone['text'].strip()
        
        # Tenta identificar título do card
        lines = text.split('\n')
        title = lines[0] if lines else ''
        content = '\n'.join(lines[1:]) if len(lines) > 1 else ''
        
        return f'''
<div class="info-card">
    <div class="card-title">{title}</div>
    <div class="card-content">{content}</div>
</div>
'''
    
    def _generate_grid(self, zone: Dict) -> str:
        """Gera grid de informações"""
        blocks = zone.get('blocks', [])
        
        html = '<div class="info-grid">\n'
        
        for block in blocks:
            text = block['text'].strip()
            if text:
                html += f'    <div class="grid-item">{text}</div>\n'
        
        html += '</div>\n'
        
        return html
    
    def _generate_table(self, table: Dict, page_num: int) -> str:
        """Gera tabela profissional"""
        headers = table.get('headers', [])
        rows = table.get('rows', [])
        
        if not headers or not rows:
            return ''
        
        # ID único para tabela
        table_id = f"table-p{page_num}"
        
        html = f'''
<div class="table-container">
    <div class="table-wrapper">
        <table class="data-table" id="{table_id}">
            <thead>
                <tr>
'''
        
        # Cabeçalhos
        for header in headers:
            header_text = str(header).strip()
            html += f'                    <th>{header_text}</th>\n'
        
        html += '''                </tr>
            </thead>
            <tbody>
'''
        
        # Linhas
        for row in rows:
            html += '                <tr>\n'
            for cell in row:
                cell_text = str(cell).strip()
                html += f'                    <td>{cell_text}</td>\n'
            html += '                </tr>\n'
        
        html += '''            </tbody>
        </table>
    </div>
</div>
'''
        
        return html
    
    def _generate_header(self) -> str:
        """Gera cabeçalho da página"""
        return '''
<header class="page-header">
    <div class="header-content">
        <div class="logo-section">
            <div class="logo-icon">
                <img src="logo.png" alt="Logo" onerror="this.style.display='none'">
            </div>
            <div class="logo-text">
                <h1>Psicofármacos na Prática</h1>
                <p>Guia Profissional 2025</p>
            </div>
        </div>
        <button class="print-btn" onclick="window.print()">
            <span>&#128424;</span> Imprimir
        </button>
    </div>
</header>
'''
    
    def _generate_footer(self) -> str:
        """Gera rodapé"""
        return '''
<footer class="page-footer">
    <div class="footer-content">
        <p>NPG | Neuropsiquiatria Geriátrica | @neuropsigeri</p>
        <p>Versão: Junho 2025</p>
    </div>
</footer>
'''
    
    def _generate_toc_placeholder(self) -> str:
        """Gera placeholder para TOC"""
        return '<!-- TOC_PLACEHOLDER -->'
    
    def _generate_toc(self) -> str:
        """Gera índice navegável"""
        html = '''
<nav class="toc">
    <h2 class="toc-title">Índice</h2>
    <ul class="toc-list">
'''
        
        for item in self.toc_items:
            indent = 'toc-level-' + str(item['level'])
            html += f'        <li class="{indent}">'
            html += f'<a href="#{item["id"]}">{item["text"]}</a></li>\n'
        
        html += '''    </ul>
</nav>
'''
        
        return html
    
    def _generate_id(self, text: str) -> str:
        """Gera ID único a partir de texto"""
        # Remove caracteres especiais e espaços
        id_text = re.sub(r'[^\w\s-]', '', text.lower())
        id_text = re.sub(r'[-\s]+', '-', id_text)
        return id_text[:50]  # Limita tamanho
    
    def _generate_css(self) -> str:
        """Gera CSS completo com tema Neumórfico Dark"""
        
        return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
        
        :root {
            /* Neumorphic Dark Colors */
            --bg-base: #1a1d29;
            --bg-elevated: #1f2233;
            --bg-sunken: #15171f;
            
            /* Neon Blue */
            --neon-blue: #00d4ff;
            --neon-blue-dark: #0099cc;
            --neon-blue-light: #5de4ff;
            --neon-glow: rgba(0, 212, 255, 0.5);
            
            /* Text Colors */
            --text-primary: #e8edf4;
            --text-secondary: #a8b3cf;
            --text-tertiary: #6b7794;
            
            /* Neumorphic Shadows */
            --shadow-light: rgba(255, 255, 255, 0.05);
            --shadow-dark: rgba(0, 0, 0, 0.5);
            --shadow-inset-light: rgba(255, 255, 255, 0.03);
            --shadow-inset-dark: rgba(0, 0, 0, 0.3);
            
            /* Spacing */
            --radius-sm: 12px;
            --radius-md: 16px;
            --radius-lg: 24px;
            
            --spacing-xs: 8px;
            --spacing-sm: 12px;
            --spacing-md: 16px;
            --spacing-lg: 24px;
            --spacing-xl: 32px;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: var(--text-primary);
            background: var(--bg-base);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }
        
        /* Header */
        .page-header {
            background: var(--bg-elevated);
            padding: var(--spacing-lg) var(--spacing-xl);
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 
                8px 8px 16px var(--shadow-dark),
                -4px -4px 12px var(--shadow-light);
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo-section {
            display: flex;
            align-items: center;
            gap: var(--spacing-md);
        }
        
        .logo-icon {
            width: 50px;
            height: 50px;
            background: var(--bg-elevated);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            box-shadow: 
                inset 4px 4px 8px var(--shadow-inset-dark),
                inset -2px -2px 6px var(--shadow-inset-light);
        }
        
        .logo-icon img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            padding: 5px;
            filter: drop-shadow(0 0 8px var(--neon-glow));
        }
        
        .logo-text h1 {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 2px;
            text-shadow: 0 0 20px var(--neon-glow);
        }
        
        .logo-text p {
            font-size: 13px;
            color: var(--text-secondary);
        }
        
        .print-btn {
            padding: 12px 24px;
            background: var(--bg-elevated);
            color: var(--neon-blue);
            border: none;
            border-radius: var(--radius-sm);
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 
                6px 6px 12px var(--shadow-dark),
                -3px -3px 8px var(--shadow-light);
        }
        
        .print-btn:hover {
            color: var(--neon-blue-light);
            box-shadow: 
                0 0 20px var(--neon-glow),
                inset 2px 2px 4px var(--shadow-inset-dark),
                inset -1px -1px 3px var(--shadow-inset-light);
        }
        
        .print-btn:active {
            box-shadow: 
                inset 4px 4px 8px var(--shadow-inset-dark),
                inset -2px -2px 6px var(--shadow-inset-light);
            transform: scale(0.98);
        }
        
        /* Layout Principal */
        .main-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            gap: var(--spacing-xl);
            padding: var(--spacing-xl);
        }
        
        /* Sidebar */
        .sidebar {
            width: 280px;
            flex-shrink: 0;
            position: sticky;
            top: 120px;
            height: fit-content;
            max-height: calc(100vh - 160px);
            overflow-y: auto;
        }
        
        .toc {
            background: var(--bg-elevated);
            border-radius: var(--radius-lg);
            padding: var(--spacing-lg);
            box-shadow: 
                8px 8px 16px var(--shadow-dark),
                -4px -4px 12px var(--shadow-light);
        }
        
        .toc-title {
            font-size: 16px;
            font-weight: 700;
            color: var(--neon-blue);
            margin-bottom: var(--spacing-md);
            padding-bottom: var(--spacing-sm);
            text-shadow: 0 0 10px var(--neon-glow);
        }
        
        .toc-list {
            list-style: none;
        }
        
        .toc-list li {
            margin-bottom: 8px;
        }
        
        .toc-list a {
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 14px;
            display: block;
            padding: 8px 12px;
            border-radius: var(--radius-sm);
            transition: all 0.3s;
        }
        
        .toc-list a:hover {
            color: var(--neon-blue);
            background: var(--bg-base);
            box-shadow: 
                inset 3px 3px 6px var(--shadow-inset-dark),
                inset -2px -2px 4px var(--shadow-inset-light);
        }
        
        .toc-level-1 {
            font-weight: 600;
        }
        
        .toc-level-2 {
            padding-left: 16px;
            font-weight: 500;
        }
        
        .toc-level-3 {
            padding-left: 32px;
            font-weight: 400;
            font-size: 13px;
        }
        
        /* Conteúdo Principal */
        .content {
            flex: 1;
            min-width: 0;
        }
        
        .page {
            background: var(--bg-elevated);
            border-radius: var(--radius-lg);
            padding: var(--spacing-xl);
            margin-bottom: var(--spacing-xl);
            box-shadow: 
                12px 12px 24px var(--shadow-dark),
                -6px -6px 16px var(--shadow-light);
        }
        
        /* Títulos */
        .section-header {
            margin-bottom: var(--spacing-lg);
        }
        
        .section-title {
            color: var(--text-primary);
            font-weight: 700;
            line-height: 1.3;
            scroll-margin-top: 100px;
        }
        
        h1.section-title {
            font-size: 32px;
            margin-bottom: var(--spacing-md);
            padding-bottom: var(--spacing-md);
            color: var(--neon-blue);
            text-shadow: 0 0 20px var(--neon-glow);
        }
        
        h2.section-title {
            font-size: 24px;
            margin-bottom: var(--spacing-sm);
            color: var(--neon-blue-light);
        }
        
        h3.section-title {
            font-size: 18px;
            margin-bottom: var(--spacing-sm);
            color: var(--text-secondary);
        }
        
        /* Blocos de Texto */
        .text-block {
            margin-bottom: var(--spacing-lg);
            background: var(--bg-sunken);
            padding: var(--spacing-md);
            border-radius: var(--radius-md);
            box-shadow: 
                inset 4px 4px 8px var(--shadow-inset-dark),
                inset -2px -2px 6px var(--shadow-inset-light);
        }
        
        .text-block p {
            margin-bottom: var(--spacing-md);
            color: var(--text-secondary);
            font-size: 15px;
            line-height: 1.7;
        }
        
        .text-block p:last-child {
            margin-bottom: 0;
        }
        
        /* Listas */
        .list-block {
            margin-bottom: var(--spacing-lg);
            background: var(--bg-sunken);
            padding: var(--spacing-md);
            border-radius: var(--radius-md);
            box-shadow: 
                inset 4px 4px 8px var(--shadow-inset-dark),
                inset -2px -2px 6px var(--shadow-inset-light);
        }
        
        .styled-list {
            list-style: none;
            padding-left: 0;
        }
        
        .styled-list li {
            position: relative;
            padding-left: 28px;
            margin-bottom: 12px;
            color: var(--text-secondary);
            font-size: 15px;
            line-height: 1.6;
        }
        
        .styled-list li::before {
            content: '●';
            position: absolute;
            left: 8px;
            color: var(--neon-blue);
            font-size: 12px;
            text-shadow: 0 0 8px var(--neon-glow);
        }
        
        /* Cards */
        .info-card {
            background: var(--bg-elevated);
            border-radius: var(--radius-md);
            padding: var(--spacing-lg);
            margin-bottom: var(--spacing-lg);
            border-left: 4px solid var(--neon-blue);
            box-shadow: 
                8px 8px 16px var(--shadow-dark),
                -4px -4px 12px var(--shadow-light),
                inset 1px 0 0 var(--neon-glow);
        }
        
        .card-title {
            font-size: 16px;
            font-weight: 700;
            color: var(--neon-blue);
            margin-bottom: var(--spacing-sm);
            text-shadow: 0 0 10px var(--neon-glow);
        }
        
        .card-content {
            color: var(--text-secondary);
            font-size: 14px;
            line-height: 1.6;
        }
        
        /* Grid de Informações */
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: var(--spacing-md);
            margin-bottom: var(--spacing-lg);
        }
        
        .grid-item {
            background: var(--bg-elevated);
            border-radius: var(--radius-sm);
            padding: var(--spacing-md);
            font-size: 14px;
            color: var(--text-secondary);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 
                6px 6px 12px var(--shadow-dark),
                -3px -3px 8px var(--shadow-light);
        }
        
        .grid-item:hover {
            transform: translateY(-2px);
            box-shadow: 
                0 0 20px var(--neon-glow),
                8px 8px 16px var(--shadow-dark),
                -4px -4px 12px var(--shadow-light);
            border: 1px solid var(--neon-blue);
        }
        
        .grid-item:active {
            transform: translateY(0);
            box-shadow: 
                inset 4px 4px 8px var(--shadow-inset-dark),
                inset -2px -2px 6px var(--shadow-inset-light);
        }
        
        /* Tabelas */
        .table-container {
            margin-bottom: var(--spacing-xl);
            border-radius: var(--radius-md);
            overflow: hidden;
            box-shadow: 
                12px 12px 24px var(--shadow-dark),
                -6px -6px 16px var(--shadow-light);
        }
        
        .table-wrapper {
            overflow-x: auto;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            background: var(--bg-elevated);
            font-size: 14px;
        }
        
        .data-table thead {
            background: var(--bg-sunken);
        }
        
        .data-table th {
            padding: 14px 16px;
            text-align: left;
            font-weight: 600;
            color: var(--neon-blue);
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            white-space: nowrap;
            text-shadow: 0 0 10px var(--neon-glow);
            box-shadow: 
                inset 0 -2px 0 var(--neon-blue);
        }
        
        .data-table td {
            padding: 12px 16px;
            color: var(--text-secondary);
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        }
        
        .data-table tbody tr {
            transition: all 0.2s;
        }
        
        .data-table tbody tr:hover {
            background: var(--bg-sunken);
        }
        
        .data-table tbody tr:last-child td {
            border-bottom: none;
        }
        
        /* Footer */
        .page-footer {
            background: var(--bg-elevated);
            padding: var(--spacing-lg);
            margin-top: var(--spacing-xl);
            text-align: center;
            box-shadow: 
                -8px -8px 16px var(--shadow-dark),
                4px 4px 12px var(--shadow-light);
        }
        
        .footer-content p {
            color: var(--text-secondary);
            font-size: 13px;
            margin: 4px 0;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-sunken);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--bg-elevated);
            border-radius: 5px;
            box-shadow: 
                inset 2px 2px 4px var(--shadow-inset-dark),
                inset -1px -1px 2px var(--shadow-inset-light);
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--neon-blue);
            box-shadow: 0 0 10px var(--neon-glow);
        }
        
        /* Smooth Scroll */
        html {
            scroll-behavior: smooth;
        }
        
        /* Seleção de texto */
        ::selection {
            background: var(--neon-blue);
            color: var(--bg-base);
        }
        
        /* Print Styles */
        @media print {
            body {
                background: white;
            }
            
            .page-header,
            .sidebar,
            .print-btn,
            .page-footer {
                display: none !important;
            }
            
            .main-container {
                padding: 0;
                max-width: 100%;
            }
            
            .content {
                width: 100%;
            }
            
            .page {
                page-break-inside: avoid;
                box-shadow: none;
                margin-bottom: 20px;
            }
        }
        
        /* Responsive */
        @media (max-width: 1024px) {
            .sidebar {
                display: none;
            }
            
            .main-container {
                padding: var(--spacing-md);
            }
        }
        
        @media (max-width: 768px) {
            .page-header {
                padding: var(--spacing-md);
            }
            
            .header-content {
                flex-direction: column;
                gap: var(--spacing-md);
            }
            
            .main-container {
                padding: var(--spacing-sm);
            }
            
            .page {
                padding: var(--spacing-md);
            }
            
            h1.section-title {
                font-size: 24px;
            }
            
            h2.section-title {
                font-size: 20px;
            }
            
            .info-grid {
                grid-template-columns: 1fr;
            }
            
            .data-table {
                font-size: 12px;
            }
            
            .data-table th,
            .data-table td {
                padding: 8px 10px;
            }
        }
        
        /* Animações */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes glow {
            0%, 100% {
                text-shadow: 0 0 10px var(--neon-glow);
            }
            50% {
                text-shadow: 0 0 20px var(--neon-glow), 0 0 30px var(--neon-glow);
            }
        }
        
        .page {
            animation: fadeIn 0.5s ease-out;
        }
        
        .logo-text h1 {
            animation: glow 3s ease-in-out infinite;
        }
    </style>
"""
    
    def _generate_scripts(self) -> str:
        """Gera scripts JavaScript"""
        return '''
    <script>
        // Highlight TOC item atual
        function updateTOC() {
            const sections = document.querySelectorAll('[id]');
            const tocLinks = document.querySelectorAll('.toc-list a');
            
            let currentSection = '';
            const scrollPosition = window.scrollY + 120;
            
            sections.forEach(section => {
                const sectionTop = section.offsetTop;
                const sectionHeight = section.offsetHeight;
                
                if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                    currentSection = section.getAttribute('id');
                }
            });
            
            tocLinks.forEach(link => {
                link.style.color = '';
                link.style.fontWeight = '';
                link.style.background = '';
                link.style.boxShadow = '';
                
                if (link.getAttribute('href') === '#' + currentSection) {
                    link.style.color = 'var(--neon-blue)';
                    link.style.fontWeight = '600';
                    link.style.background = 'var(--bg-base)';
                    link.style.boxShadow = 'inset 3px 3px 6px var(--shadow-inset-dark), inset -2px -2px 4px var(--shadow-inset-light)';
                }
            });
        }
        
        // Atualiza TOC on scroll
        window.addEventListener('scroll', updateTOC);
        window.addEventListener('load', updateTOC);
        
        // Smooth scroll para links internos
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
        
        // Efeito de pressed nos grid-items
        document.querySelectorAll('.grid-item').forEach(item => {
            item.addEventListener('mousedown', function() {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = 'inset 4px 4px 8px var(--shadow-inset-dark), inset -2px -2px 6px var(--shadow-inset-light)';
            });
            
            item.addEventListener('mouseup', function() {
                this.style.transform = '';
                this.style.boxShadow = '';
            });
            
            item.addEventListener('mouseleave', function() {
                this.style.transform = '';
                this.style.boxShadow = '';
            });
        });
    </script>
'''
