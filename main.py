"""
PDF to HTML Converter - Sistema Avançado com IA
Versão: 4.0 - Neumorphic Dark + AI Analysis
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
from datetime import datetime
import json
import webbrowser

# Importar módulos avançados - CORRIGIDO
from pdf_extractor import AdvancedPDFExtractor  # Mudado de PDFExtractor
from html_generator import HTMLGenerator

try:
    from config_manager import ConfigManager
except ImportError:
    # Fallback simples se não existir
    class ConfigManager:
        def __init__(self):
            self.config_file = Path("config.json")
            self.history_file = Path("history.json")
        
        def save_settings(self, settings):
            self.config_file.write_text(json.dumps(settings, indent=2))
        
        def load_settings(self):
            if self.config_file.exists():
                return json.loads(self.config_file.read_text())
            return {}
        
        def save_to_history(self, entry):
            history = self.get_history()
            history.append(entry)
            self.history_file.write_text(json.dumps(history, indent=2))
        
        def get_history(self):
            if self.history_file.exists():
                return json.loads(self.history_file.read_text())
            return []


class ModernPDFConverterApp:
    """Aplicação avançada com IA e design moderno"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 PDF to HTML AI Converter Pro 4.0")
        self.root.geometry("1100x850")
        self.root.resizable(True, True)
        
        # Configurações
        self.config = ConfigManager()
        self.pdf_file = None
        self.output_file = None
        self.is_processing = False
        self.current_analysis = None
        
        # Cores tema escuro
        self.colors = {
            'bg': '#1a1d29',
            'fg': '#e8edf4',
            'accent': '#00d4ff',
            'success': '#10b981',
            'warning': '#f59e0b',
            'error': '#ef4444',
            'surface': '#1f2233'
        }
        
        self.setup_modern_ui()
        self.load_saved_settings()
        
    def setup_modern_ui(self):
        """Configura interface moderna"""
        
        # Configurar tema
        style = ttk.Style()
        style.theme_use('clam')
        
        # Customizar cores
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('Title.TLabel', 
                       background=self.colors['bg'], 
                       foreground=self.colors['accent'],
                       font=('Segoe UI', 18, 'bold'))
        style.configure('Header.TLabel', 
                       background=self.colors['bg'],
                       foreground=self.colors['accent'],
                       font=('Segoe UI', 11, 'bold'))
        style.configure('Action.TButton', font=('Segoe UI', 10, 'bold'))
        
        self.root.configure(bg=self.colors['bg'])
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Título
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', pady=(0, 20))
        
        title = ttk.Label(
            title_frame, 
            text="🚀 PDF to HTML AI Converter", 
            style='Title.TLabel'
        )
        title.pack()
        
        subtitle = ttk.Label(
            title_frame,
            text="Powered by Advanced AI • Neumorphic Design • Smart Analysis",
            font=('Segoe UI', 9)
        )
        subtitle.pack()
        
        # Container de conteúdo (2 colunas)
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True)
        
        # Coluna esquerda - Configurações
        left_column = ttk.Frame(content_frame, padding="10")
        left_column.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Seleção de arquivo
        self.setup_file_section(left_column)
        
        # Método de Extração
        self.setup_extraction_section(left_column)
        
        # Design Theme
        self.setup_design_section(left_column)
        
        # Opções Avançadas
        self.setup_options_section(left_column)
        
        # Botões de ação
        self.setup_action_buttons(left_column)
        
        # Coluna direita - Status e Log
        right_column = ttk.Frame(content_frame, padding="10")
        right_column.pack(side='right', fill='both', expand=True)
        
        # Status Card
        self.setup_status_card(right_column)
        
        # Progress
        self.progress = ttk.Progressbar(right_column, mode='indeterminate')
        self.progress.pack(fill='x', pady=10)
        
        # Log
        self.setup_log_section(right_column)
    
    def setup_file_section(self, parent):
        """Seção de seleção de arquivo"""
        frame = ttk.LabelFrame(parent, text="📄 Arquivo PDF", padding="15")
        frame.pack(fill='x', pady=10)
        
        self.file_label = ttk.Label(
            frame, 
            text="Nenhum arquivo selecionado",
            font=('Segoe UI', 9)
        )
        self.file_label.pack(anchor='w', pady=(0, 10))
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x')
        
        ttk.Button(
            btn_frame,
            text="🔍 Selecionar PDF",
            command=self.select_pdf,
            style='Action.TButton'
        ).pack(side='left', padx=5)
        
        self.analyze_btn = ttk.Button(
            btn_frame,
            text="🔬 Análise",
            command=self.analyze_pdf,
            state='disabled'
        )
        self.analyze_btn.pack(side='left', padx=5)
        
        self.generate_html_btn = ttk.Button(
            btn_frame,
            text="🎨 Gerar HTML",
            command=self.generate_html_only,
            state='disabled'
        )
        self.generate_html_btn.pack(side='left', padx=5)
    
    def setup_extraction_section(self, parent):
        """Seção de método de extração"""
        frame = ttk.LabelFrame(parent, text="🔬 Método de Extração AI", padding="15")
        frame.pack(fill='x', pady=10)
        
        self.extraction_method = tk.StringVar(value="auto")
        
        methods = [
            ("🤖 Auto AI (Recomendado - Detecção Inteligente)", "auto"),
            ("📊 Advanced Tables (Multi-method + Validation)", "advanced"),
            ("⚡ Fast Processing (PyMuPDF only)", "fast")
        ]
        
        for text, value in methods:
            ttk.Radiobutton(
                frame,
                text=text,
                variable=self.extraction_method,
                value=value
            ).pack(anchor='w', pady=3)
    
    def setup_design_section(self, parent):
        """Seção de design"""
        frame = ttk.LabelFrame(parent, text="🎨 Design Theme", padding="15")
        frame.pack(fill='x', pady=10)
        
        self.design_theme = tk.StringVar(value="neumorphic_dark")
        
        themes = [
            ("🌙 Neumorphic Dark (Azul Neon - Recomendado)", "neumorphic_dark"),
            ("🏥 Medical Clean (Profissional)", "medical"),
            ("✨ Modern Pro (Minimalista)", "modern"),
            ("💼 Premium Dark (Elegante)", "premium")
        ]
        
        for text, value in themes:
            ttk.Radiobutton(
                frame,
                text=text,
                variable=self.design_theme,
                value=value
            ).pack(anchor='w', pady=3)
    
    def setup_options_section(self, parent):
        """Seção de opções avançadas"""
        frame = ttk.LabelFrame(parent, text="⚙️ Opções Avançadas", padding="15")
        frame.pack(fill='x', pady=10)
        
        self.include_toc = tk.BooleanVar(value=True)
        self.responsive_design = tk.BooleanVar(value=True)
        self.animations = tk.BooleanVar(value=True)
        self.enable_ocr = tk.BooleanVar(value=False)
        self.export_markdown = tk.BooleanVar(value=False)
        
        options = [
            ("📑 Índice navegável lateral", self.include_toc),
            ("📱 Design responsivo (mobile/tablet)", self.responsive_design),
            ("✨ Animações neumórficas", self.animations),
            ("🔍 OCR para PDFs escaneados (Beta)", self.enable_ocr),
            ("📝 Exportar também em Markdown", self.export_markdown)
        ]
        
        for text, var in options:
            ttk.Checkbutton(frame, text=text, variable=var).pack(anchor='w', pady=2)
    
    def setup_action_buttons(self, parent):
        """Botões de ação"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=20)
        
        self.convert_btn = ttk.Button(
            frame,
            text="🚀 CONVERTER AGORA",
            command=self.start_conversion,
            style='Action.TButton',
            state='disabled'
        )
        self.convert_btn.pack(fill='x', pady=5)
        
        btn_row = ttk.Frame(frame)
        btn_row.pack(fill='x', pady=5)
        
        ttk.Button(
            btn_row,
            text="💾 Salvar Config",
            command=self.save_settings
        ).pack(side='left', expand=True, padx=2)
        
        ttk.Button(
            btn_row,
            text="📂 Último",
            command=self.open_last_conversion
        ).pack(side='left', expand=True, padx=2)
        
        ttk.Button(
            btn_row,
            text="📊 Histórico",
            command=self.show_history
        ).pack(side='left', expand=True, padx=2)
    
    def setup_status_card(self, parent):
        """Card de status"""
        frame = ttk.LabelFrame(parent, text="📊 Status do Documento", padding="15")
        frame.pack(fill='x', pady=10)
        
        self.status_text = tk.Text(
            frame,
            height=8,
            width=50,
            font=('Consolas', 9),
            bg=self.colors['surface'],
            fg=self.colors['fg'],
            relief='flat',
            wrap=tk.WORD
        )
        self.status_text.pack(fill='x')
        self.status_text.insert('1.0', 'Aguardando arquivo PDF...\n\n'
                                      '💡 Dica: Use o botão "Análise Prévia" para\n'
                                      'visualizar a estrutura antes da conversão.')
        self.status_text.config(state='disabled')
    
    def setup_log_section(self, parent):
        """Seção de log"""
        frame = ttk.LabelFrame(parent, text="📋 Log de Processamento", padding="10")
        frame.pack(fill='both', expand=True, pady=10)
        
        # Frame com scroll
        log_container = ttk.Frame(frame)
        log_container.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(log_container)
        scrollbar.pack(side='right', fill='y')
        
        self.log_text = tk.Text(
            log_container,
            height=15,
            font=('Consolas', 9),
            bg=self.colors['surface'],
            fg=self.colors['fg'],
            yscrollcommand=scrollbar.set,
            relief='flat'
        )
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # Tags para cores
        self.log_text.tag_config('info', foreground=self.colors['fg'])
        self.log_text.tag_config('success', foreground=self.colors['success'])
        self.log_text.tag_config('warning', foreground=self.colors['warning'])
        self.log_text.tag_config('error', foreground=self.colors['error'])
        self.log_text.tag_config('accent', foreground=self.colors['accent'])
    
    def log(self, message, level="info"):
        """Adiciona mensagem ao log com cores"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"[{timestamp}] ", 'info')
        self.log_text.insert(tk.END, f"{message}\n", level)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update()
    
    def update_status(self, text):
        """Atualiza card de status"""
        self.status_text.config(state='normal')
        self.status_text.delete('1.0', tk.END)
        self.status_text.insert('1.0', text)
        self.status_text.config(state='disabled')
    
    def select_pdf(self):
        """Seleciona arquivo PDF"""
        filename = filedialog.askopenfilename(
            title="Selecionar PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            self.pdf_file = Path(filename)
            self.file_label.config(text=f"✅ {self.pdf_file.name}")
            self.convert_btn.config(state='normal')
            self.analyze_btn.config(state='normal')
            self.generate_html_btn.config(state='normal')
            
            size_mb = self.pdf_file.stat().st_size / (1024 * 1024)
            self.log(f"📄 Arquivo selecionado: {self.pdf_file.name}", "success")
            self.log(f"   Tamanho: {size_mb:.2f} MB", "info")
            
            self.update_status(
                f"Arquivo: {self.pdf_file.name}\n"
                f"Tamanho: {size_mb:.2f} MB\n\n"
                f"✅ Pronto para análise e conversão"
            )
    
    def analyze_pdf(self):
        """Analisa PDF sem converter"""
        if not self.pdf_file:
            return
        
        self.log("🔬 Iniciando análise prévia...", "accent")
        self.progress.start(10)
        
        thread = threading.Thread(target=self._analyze_thread)
        thread.daemon = True
        thread.start()
    
    def _analyze_thread(self):
        """Thread de análise"""
        try:
            extractor = AdvancedPDFExtractor(
                method='auto',
                log_callback=self.log
            )
            
            pages_data = extractor.extract(self.pdf_file)
            analysis = extractor.analyze_document_structure(pages_data)
            
            self.current_analysis = analysis
            
            # Formata resultado
            result = f"📊 ANÁLISE COMPLETA\n\n"
            result += f"Páginas: {analysis['total_pages']}\n"
            result += f"Zonas: {analysis['total_zones']}\n"
            result += f"Tabelas: {analysis['total_tables']}\n"
            result += f"Imagens: {analysis['total_images']}\n\n"
            result += f"Tipo: {analysis['document_type']}\n\n"
            result += f"📍 Distribuição de Conteúdo:\n"
            
            for zone_type, count in analysis['zone_type_distribution'].items():
                result += f"  • {zone_type}: {count}\n"
            
            result += f"\n🔤 Tipografia:\n"
            typo = analysis['typography']
            result += f"  • Fonte média: {typo['avg_font_size']:.1f}pt\n"
            result += f"  • Range: {typo['min_font_size']:.1f} - {typo['max_font_size']:.1f}pt"
            
            self.root.after(0, lambda: self.update_status(result))
            self.log("✅ Análise concluída!", "success")
            
        except Exception as e:
            self.log(f"❌ Erro na análise: {e}", "error")
        finally:
            self.root.after(0, self.progress.stop)
    
    def generate_html_only(self):
        """Gera HTML a partir da última análise ou extrai novamente"""
        if not self.pdf_file:
            messagebox.showerror("❌ Erro", "Selecione um arquivo PDF primeiro!")
            return
        
        if self.is_processing:
            messagebox.showwarning("⚠ Aviso", "Aguarde o processamento atual!")
            return
        
        self.log("\n" + "=" * 70, "accent")
        self.log("🎨 GERANDO HTML", "accent")
        self.log("=" * 70, "accent")
        
        self.is_processing = True
        self.generate_html_btn.config(state='disabled')
        self.analyze_btn.config(state='disabled')
        self.convert_btn.config(state='disabled')
        self.progress.start(10)
        
        thread = threading.Thread(target=self._generate_html_thread, daemon=True)
        thread.start()
    
    def _generate_html_thread(self):
        """Thread para gerar HTML"""
        try:
            # Se não tem análise prévia, extrai dados
            if not hasattr(self, 'pages_data') or not self.pages_data:
                self.log("\n📄 Extraindo dados do PDF...", "info")
                
                method = self.extraction_method.get()
                if method == 'advanced':
                    method = 'auto'
                elif method == 'fast':
                    method = 'pymupdf'
                
                extractor = AdvancedPDFExtractor(
                    method=method,
                    enable_ocr=self.enable_ocr.get(),
                    log_callback=self.log,
                    progress_callback=lambda p: self.root.after(0, 
                        lambda prog=p: self.update_status(f"Extraindo: {int(prog*100)}%"))
                )
                
                self.pages_data = extractor.extract(self.pdf_file)
                
                if not self.pages_data or len(self.pages_data) == 0:
                    raise Exception("Nenhum dado extraído do PDF")
                
                self.log(f"✅ Extraído: {len(self.pages_data)} páginas", "success")
            else:
                self.log(f"📋 Usando dados em cache: {len(self.pages_data)} páginas", "info")
            
            # Log detalhado dos dados extraídos
            self.log("\n🔍 Analisando estrutura extraída...", "info")
            for i, page in enumerate(self.pages_data[:3], 1):  # Primeiras 3 páginas
                self.log(f"   Página {i}:", "info")
                self.log(f"      • Zonas: {len(page.get('zones', []))}", "info")
                self.log(f"      • Tabelas: {len(page.get('tables', []))}", "info")
                self.log(f"      • Blocos de texto: {len(page.get('text_blocks', []))}", "info")
            
            # Gera HTML
            self.log("\n🎨 Criando gerador HTML...", "info")
            self.log(f"   • Tema: {self.design_theme.get()}", "info")
            self.log(f"   • TOC: {self.include_toc.get()}", "info")
            self.log(f"   • Responsivo: {self.responsive_design.get()}", "info")
            self.log(f"   • Animações: {self.animations.get()}", "info")
            
            generator = HTMLGenerator(
                theme=self.design_theme.get(),
                include_toc=self.include_toc.get(),
                responsive=self.responsive_design.get(),
                animations=self.animations.get()
            )
            
            self.log("✅ Gerador criado", "success")
            self.log("\n🔄 Gerando conteúdo HTML...", "info")
            
            html_content = generator.generate(self.pages_data)
            
            self.log(f"✅ HTML gerado: {len(html_content):,} caracteres", "success")
            
            if not html_content or len(html_content) < 100:
                raise Exception(f"HTML inválido: {len(html_content) if html_content else 0} chars")
            
            # Salvar arquivo
            theme_name = self.design_theme.get()
            output_path = self.pdf_file.parent / f"{self.pdf_file.stem}_{theme_name}.html"
            
            self.log(f"\n💾 Salvando arquivo...", "accent")
            self.log(f"   📂 Pasta: {output_path.parent}", "info")
            self.log(f"   📄 Nome: {output_path.name}", "info")
            
            # Garante diretório
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Salva arquivo
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Verifica
            if not output_path.exists():
                raise Exception(f"Arquivo não criado: {output_path}")
            
            file_size_kb = output_path.stat().st_size / 1024
            
            self.log(f"✅ ARQUIVO SALVO COM SUCESSO!", "success")
            self.log(f"   📊 Tamanho: {file_size_kb:.2f} KB", "info")
            self.log(f"   📍 Local: {output_path.absolute()}", "info")
            
            # Markdown opcional
            if self.export_markdown.get():
                self.log("\n📝 Exportando Markdown...", "info")
                try:
                    md_path = output_path.with_suffix('.md')
                    
                    if hasattr(self, 'pages_data'):
                        extractor = AdvancedPDFExtractor(method='auto', log_callback=self.log)
                        extractor.export_markdown(self.pages_data, md_path)
                        self.log(f"   ✅ Markdown: {md_path.name}", "success")
                except Exception as md_error:
                    self.log(f"   ⚠ Erro no Markdown: {md_error}", "warning")
            
            # Salvar histórico
            try:
                self.config.save_to_history({
                    'input': str(self.pdf_file),
                    'output': str(output_path),
                    'timestamp': datetime.now().isoformat(),
                    'method': self.extraction_method.get(),
                    'theme': theme_name
                })
            except:
                pass
            
            # Status final
            final_status = (
                f"✅ HTML GERADO!\n\n"
                f"📄 {output_path.name}\n"
                f"💾 {file_size_kb:.2f} KB\n\n"
                f"📂 {output_path.parent}\n\n"
                f"🎨 Tema: {theme_name}"
            )
            self.root.after(0, lambda: self.update_status(final_status))
            
            # Diálogo de sucesso
            self.root.after(0, lambda: self._show_html_success(output_path))
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"\n❌ ERRO: {error_msg}", "error")
            
            import traceback
            self.log(traceback.format_exc(), "error")
            
            self.root.after(0, lambda: messagebox.showerror(
                "❌ Erro ao Gerar HTML",
                f"Falha:\n\n{error_msg}\n\nVerifique o log."
            ))
        
        finally:
            self.is_processing = False
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.generate_html_btn.config(state='normal'))
            self.root.after(0, lambda: self.analyze_btn.config(state='normal'))
            self.root.after(0, lambda: self.convert_btn.config(state='normal'))
    
    def _show_html_success(self, output_path):
        """Mostra diálogo de sucesso do HTML"""
        result = messagebox.askquestion(
            "✅ HTML Gerado!",
            f"HTML criado com sucesso!\n\n"
            f"📄 {output_path.name}\n"
            f"📂 {output_path.parent}\n\n"
            f"Abrir no navegador?",
            icon='info'
        )
        
        if result == 'yes':
            webbrowser.open(str(output_path))
    
    def start_conversion(self):
        """Inicia conversão"""
        if self.is_processing:
            messagebox.showwarning("⚠ Aviso", "Uma conversão já está em andamento!")
            return
        
        if not self.pdf_file:
            messagebox.showerror("❌ Erro", "Selecione um arquivo PDF primeiro!")
            return
        
        if not self.pdf_file.exists():
            messagebox.showerror("❌ Erro", f"Arquivo não encontrado:\n{self.pdf_file}")
            return
        
        # Confirmação
        response = messagebox.askyesno(
            "🚀 Iniciar Conversão",
            f"Converter o arquivo:\n\n"
            f"📄 {self.pdf_file.name}\n"
            f"🎨 Tema: {self.design_theme.get()}\n"
            f"🔧 Método: {self.extraction_method.get()}\n\n"
            f"Deseja continuar?",
            icon='question'
        )
        
        if not response:
            return
        
        self.is_processing = True
        self.convert_btn.config(state='disabled')
        self.analyze_btn.config(state='disabled')
        self.generate_html_btn.config(state='disabled')
        self.progress.start(10)
        
        # Limpa log anterior
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')
        
        thread = threading.Thread(target=self.convert_pdf, daemon=True)
        thread.start()
    
    def convert_pdf(self):
        """Realiza conversão do PDF"""
        try:
            self.log("=" * 70, "accent")
            self.log("🚀 INICIANDO CONVERSÃO AVANÇADA COM IA", "accent")
            self.log("=" * 70, "accent")
            
            # Determina método de extração
            method = self.extraction_method.get()
            if method == 'advanced':
                method = 'auto'
            elif method == 'fast':
                method = 'pymupdf'
            
            # Extrator avançado
            self.log(f"\n🔧 Método selecionado: {method}", "info")
            self.log(f"📂 Arquivo: {self.pdf_file}", "info")
            self.log(f"📊 Tema: {self.design_theme.get()}", "info")
            
            extractor = AdvancedPDFExtractor(
                method=method,
                enable_ocr=self.enable_ocr.get(),
                log_callback=self.log,
                progress_callback=lambda p: self.root.after(0, 
                    lambda prog=p: self.update_status(f"Processando: {int(prog*100)}%"))
            )
            
            # Extração
            self.log("\n📄 Extraindo e analisando estrutura...", "info")
            pages_data = extractor.extract(self.pdf_file)
            
            self.log(f"🔍 DEBUG: pages_data tipo: {type(pages_data)}", "warning")
            self.log(f"🔍 DEBUG: pages_data length: {len(pages_data) if pages_data else 0}", "warning")
            
            if not pages_data:
                raise Exception("Nenhum dado extraído do PDF")
            
            if len(pages_data) == 0:
                raise Exception("Lista de páginas vazia")
            
            self.log(f"✅ Extração concluída: {len(pages_data)} páginas", "success")
            
            # Análise
            self.log("\n🔬 Analisando estrutura do documento...", "info")
            analysis = extractor.analyze_document_structure(pages_data)
            
            self.log(f"\n✅ {len(pages_data)} páginas processadas", "success")
            self.log(f"   • {analysis['total_zones']} zonas detectadas", "info")
            self.log(f"   • {analysis['total_tables']} tabelas encontradas", "info")
            self.log(f"   • {analysis['total_images']} imagens detectadas", "info")
            self.log(f"   • Tipo: {analysis['document_type']}", "info")
            
            # Gerador HTML
            self.log("\n🎨 Criando gerador HTML...", "info")
            self.log(f"   • Tema: {self.design_theme.get()}", "info")
            self.log(f"   • TOC: {self.include_toc.get()}", "info")
            self.log(f"   • Responsivo: {self.responsive_design.get()}", "info")
            self.log(f"   • Animações: {self.animations.get()}", "info")
            
            generator = HTMLGenerator(
                theme=self.design_theme.get(),
                include_toc=self.include_toc.get(),
                responsive=self.responsive_design.get(),
                animations=self.animations.get()
            )
            
            self.log("✅ Gerador criado com sucesso", "success")
            self.log("\n🔄 Gerando conteúdo HTML...", "info")
            
            html_content = generator.generate(pages_data)
            
            self.log(f"🔍 DEBUG: HTML gerado - tamanho: {len(html_content)} caracteres", "warning")
            
            if not html_content:
                raise Exception("HTML gerado está vazio")
            
            if len(html_content) < 100:
                raise Exception(f"HTML muito pequeno: {len(html_content)} caracteres")
            
            self.log("✅ HTML gerado com sucesso!", "success")
            
            # Salvar arquivo HTML
            theme_name = self.design_theme.get()
            output_path = self.pdf_file.parent / f"{self.pdf_file.stem}_{theme_name}.html"
            
            self.log(f"\n💾 Salvando arquivo HTML...", "accent")
            self.log(f"   • Diretório: {output_path.parent}", "info")
            self.log(f"   • Nome completo: {output_path.name}", "info")
            self.log(f"   • Caminho absoluto: {output_path.absolute()}", "info")
            
            try:
                # Garante que o diretório existe
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                self.log("   🔄 Escrevendo arquivo...", "info")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                self.log(f"   ✅ Arquivo escrito!", "success")
                
            except PermissionError as pe:
                raise Exception(f"Sem permissão para escrever em: {output_path}\n{pe}")
            except OSError as oe:
                raise Exception(f"Erro do sistema ao salvar arquivo: {oe}")
            except Exception as save_error:
                raise Exception(f"Erro ao salvar arquivo: {save_error}")
            
            # Verifica se arquivo foi criado
            self.log("   🔍 Verificando arquivo criado...", "info")
            if not output_path.exists():
                raise Exception(f"Arquivo não foi criado: {output_path}")
            
            file_size_kb = output_path.stat().st_size / 1024
            self.log(f"   ✅ Arquivo confirmado!", "success")
            self.log(f"   • Tamanho: {file_size_kb:.2f} KB", "info")
            
            # Markdown opcional
            if self.export_markdown.get():
                self.log("\n📝 Exportando Markdown...", "info")
                try:
                    md_path = output_path.with_suffix('.md')
                    extractor.export_markdown(pages_data, md_path)
                    self.log(f"   ✅ Markdown salvo: {md_path.name}", "success")
                except Exception as md_error:
                    self.log(f"   ⚠ Erro no Markdown: {md_error}", "warning")
            
            self.output_file = output_path
            
            # Salvar no histórico
            self.log("\n📊 Salvando no histórico...", "info")
            try:
                self.config.save_to_history({
                    'input': str(self.pdf_file),
                    'output': str(output_path),
                    'timestamp': datetime.now().isoformat(),
                    'method': method,
                    'theme': theme_name,
                    'analysis': {
                        'total_pages': len(pages_data),
                        'total_zones': analysis['total_zones'],
                        'total_tables': analysis['total_tables'],
                        'total_images': analysis['total_images'],
                        'document_type': analysis['document_type']
                    }
                })
                self.log("   ✅ Histórico atualizado", "success")
            except Exception as hist_error:
                self.log(f"   ⚠ Erro no histórico: {hist_error}", "warning")
            
            # Sucesso!
            self.log("\n" + "=" * 70, "success")
            self.log("🎉 CONVERSÃO CONCLUÍDA COM SUCESSO! 🎉", "success")
            self.log("=" * 70, "success")
            self.log(f"\n📄 Arquivo criado: {output_path.name}", "success")
            self.log(f"📂 Localização: {output_path.parent}", "info")
            
            # Atualiza status final
            final_status = (
                f"✅ CONVERSÃO CONCLUÍDA!\n\n"
                f"📄 {output_path.name}\n"
                f"💾 {file_size_kb:.2f} KB\n\n"
                f"📊 Estatísticas:\n"
                f"  • {len(pages_data)} páginas\n"
                f"  • {analysis['total_zones']} zonas\n"
                f"  • {analysis['total_tables']} tabelas\n"
                f"  • {analysis['total_images']} imagens\n\n"
                f"🎨 Tema: {theme_name}"
            )
            self.root.after(0, lambda: self.update_status(final_status))
            
            # Mostra diálogo
            self.root.after(0, lambda: self.show_completion_dialog(output_path))
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"\n{'=' * 70}", "error")
            self.log(f"❌ ERRO NA CONVERSÃO", "error")
            self.log(f"{'=' * 70}", "error")
            self.log(f"\n{error_msg}\n", "error")
            
            # Log detalhado do erro
            import traceback
            trace = traceback.format_exc()
            self.log("Detalhes técnicos:", "error")
            self.log(trace, "error")
            
            self.root.after(0, lambda: messagebox.showerror(
                "❌ Erro na Conversão", 
                f"Falha ao converter o PDF:\n\n{error_msg}\n\n"
                f"Verifique o log para mais detalhes."
            ))
        
        finally:
            self.is_processing = False
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.convert_btn.config(state='normal'))
            self.root.after(0, lambda: self.analyze_btn.config(state='normal'))
            self.root.after(0, lambda: self.generate_html_btn.config(state='normal'))
    
    def show_completion_dialog(self, output_path):
        """Diálogo de conclusão"""
        result = messagebox.askquestion(
            "✅ Sucesso!",
            f"Conversão concluída!\n\n"
            f"📄 {output_path.name}\n"
            f"📁 {output_path.parent}\n\n"
            f"Recursos:\n"
            f"✨ Design neumórfico dark\n"
            f"🎯 Análise com IA\n"
            f"📱 Responsivo\n"
            f"🖨️ Pronto para impressão\n\n"
            f"Abrir agora?",
            icon='info'
        )
        
        if result == 'yes':
            webbrowser.open(str(output_path))
    
    def save_settings(self):
        """Salva configurações"""
        settings = {
            'extraction_method': self.extraction_method.get(),
            'design_theme': self.design_theme.get(),
            'include_toc': self.include_toc.get(),
            'responsive_design': self.responsive_design.get(),
            'animations': self.animations.get(),
            'enable_ocr': self.enable_ocr.get(),
            'export_markdown': self.export_markdown.get()
        }
        
        self.config.save_settings(settings)
        self.log("💾 Configurações salvas!", "success")
        messagebox.showinfo("Sucesso", "Configurações salvas!")
    
    def load_saved_settings(self):
        """Carrega configurações"""
        settings = self.config.load_settings()
        
        if settings:
            self.extraction_method.set(settings.get('extraction_method', 'auto'))
            self.design_theme.set(settings.get('design_theme', 'neumorphic_dark'))
            self.include_toc.set(settings.get('include_toc', True))
            self.responsive_design.set(settings.get('responsive_design', True))
            self.animations.set(settings.get('animations', True))
            self.enable_ocr.set(settings.get('enable_ocr', False))
            self.export_markdown.set(settings.get('export_markdown', False))
            
            self.log("📂 Configurações carregadas", "info")
    
    def open_last_conversion(self):
        """Abre última conversão"""
        history = self.config.get_history()
        
        if not history:
            messagebox.showinfo("Info", "Nenhuma conversão anterior")
            return
        
        last = history[-1]
        output_path = Path(last['output'])
        
        if output_path.exists():
            webbrowser.open(str(output_path))
            self.log(f"📂 Abrindo: {output_path.name}", "success")
        else:
            messagebox.showerror("Erro", "Arquivo não encontrado")
    
    def show_history(self):
        """Mostra histórico"""
        history = self.config.get_history()
        
        if not history:
            messagebox.showinfo("Histórico", "Nenhuma conversão realizada ainda")
            return
        
        # Cria janela de histórico
        history_window = tk.Toplevel(self.root)
        history_window.title("📊 Histórico de Conversões")
        history_window.geometry("700x500")
        history_window.configure(bg=self.colors['bg'])
        
        frame = ttk.Frame(history_window, padding="20")
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="📊 Histórico", style='Title.TLabel').pack(pady=10)
        
        # Lista
        text = tk.Text(frame, font=('Consolas', 9), bg=self.colors['surface'], 
                      fg=self.colors['fg'], wrap=tk.WORD)
        text.pack(fill='both', expand=True)
        
        for i, entry in enumerate(reversed(history[-10:]), 1):
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%d/%m/%Y %H:%M")
            input_file = Path(entry['input']).name
            theme = entry.get('theme', 'unknown')
            
            text.insert(tk.END, f"\n{'='*60}\n")
            text.insert(tk.END, f"#{i} - {timestamp}\n")
            text.insert(tk.END, f"📄 {input_file}\n")
            text.insert(tk.END, f"🎨 {theme}\n")
            
            if 'analysis' in entry:
                analysis = entry['analysis']
                text.insert(tk.END, f"📊 {analysis.get('total_pages', 0)} páginas, ")
                text.insert(tk.END, f"{analysis.get('total_tables', 0)} tabelas\n")
        
        text.config(state='disabled')


def main():
    """Função principal"""
    root = tk.Tk()
    app = ModernPDFConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
