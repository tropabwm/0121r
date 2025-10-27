#!/usr/bin/env python3
"""
PDF Converter Pro - CLI Avançada
Interface de linha de comando com múltiplos comandos
"""

import click
import sys
from pathlib import Path
from typing import Optional
import json

from pdf_extractor import PDFExtractor
from html_generator import HTMLGenerator
from config_manager import ConfigManager
from batch_converter import BatchConverter


# Configuração global
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='2.0', prog_name='PDF Converter Pro')
def cli():
    """
    🧠 PDF Converter Pro 2.0 - Conversor Profissional de PDF para HTML
    
    Ferramenta completa para conversão de PDFs em páginas HTML responsivas
    e profissionais, com suporte a múltiplos temas e métodos de extração.
    
    Exemplos:
    
      # Converter um PDF
      pdf-converter convert documento.pdf
      
      # Converter com tema específico
      pdf-converter convert documento.pdf --theme medical
      
      # Conversão em lote
      pdf-converter batch -i pdfs/ -o html/
      
      # Ver configurações
      pdf-converter config show
    """
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Arquivo de saída')
@click.option('-m', '--method', 
              type=click.Choice(['auto', 'camelot', 'pdfplumber', 'pymupdf']),
              default='auto',
              help='Método de extração')
@click.option('-t', '--theme',
              type=click.Choice(['premium', 'medical', 'modern', 'classic']),
              default='premium',
              help='Tema do HTML')
@click.option('--no-toc', is_flag=True, help='Não incluir índice')
@click.option('--no-animations', is_flag=True, help='Desabilitar animações')
@click.option('--light-mode', is_flag=True, help='Usar modo claro')
@click.option('-v', '--verbose', is_flag=True, help='Modo verbose')
def convert(input_file, output, method, theme, no_toc, no_animations, light_mode, verbose):
    """
    Converte um único arquivo PDF para HTML.
    
    INPUT_FILE: Caminho para o arquivo PDF
    
    Exemplos:
    
      pdf-converter convert documento.pdf
      
      pdf-converter convert input.pdf -o output.html --theme medical
      
      pdf-converter convert data.pdf -m camelot --no-animations
    """
    input_path = Path(input_file)
    
    # Determinar saída
    if output:
        output_path = Path(output)
    else:
        output_path = input_path.parent / f"{input_path.stem}_converted.html"
    
    click.echo(f"🔄 Convertendo: {input_path.name}")
    
    if verbose:
        click.echo(f"   Método: {method}")
        click.echo(f"   Tema: {theme}")
        click.echo(f"   Saída: {output_path}")
    
    try:
        # Extrair
        if verbose:
            click.echo("\n📄 Extraindo dados do PDF...")
        
        extractor = PDFExtractor(
            method=method,
            log_callback=lambda msg, level: click.echo(f"   {msg}") if verbose else None
        )
        pages_data = extractor.extract(input_path)
        
        if not pages_data:
            click.echo("❌ Erro: Nenhum dado extraído", err=True)
            sys.exit(1)
        
        if verbose:
            click.echo(f"   ✓ {len(pages_data)} páginas extraídas")
        
        # Gerar HTML
        if verbose:
            click.echo("\n🎨 Gerando HTML...")
        
        generator = HTMLGenerator(
            theme=theme,
            include_toc=not no_toc,
            responsive=True,
            animations=not no_animations,
            dark_mode=not light_mode
        )
        html = generator.generate(pages_data)
        
        # Salvar
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        click.echo(f"\n✅ Sucesso! Arquivo salvo: {output_path}")
        
        # Perguntar se quer abrir
        if click.confirm('\nDeseja abrir o arquivo?', default=False):
            import webbrowser
            webbrowser.open(str(output_path))
    
    except Exception as e:
        click.echo(f"\n❌ Erro: {str(e)}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('-i', '--input-dir', type=click.Path(exists=True), 
              default='.', help='Diretório de entrada')
@click.option('-o', '--output-dir', type=click.Path(), 
              help='Diretório de saída')
@click.option('-m', '--method',
              type=click.Choice(['auto', 'camelot', 'pdfplumber', 'pymupdf']),
              default='auto',
              help='Método de extração')
@click.option('-t', '--theme',
              type=click.Choice(['premium', 'medical', 'modern', 'classic']),
              default='premium',
              help='Tema do HTML')
@click.option('-r', '--recursive', is_flag=True, 
              help='Buscar PDFs recursivamente')
@click.option('--overwrite', is_flag=True,
              help='Sobrescrever arquivos existentes')
@click.option('-q', '--quiet', is_flag=True,
              help='Modo silencioso')
def batch(input_dir, output_dir, method, theme, recursive, overwrite, quiet):
    """
    Converte múltiplos PDFs em lote.
    
    Exemplos:
    
      pdf-converter batch -i pdfs/
      
      pdf-converter batch -i docs/ -o html/ --recursive
      
      pdf-converter batch -i . -t medical --overwrite
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else None
    
    converter = BatchConverter(
        method=method,
        theme=theme,
        verbose=not quiet
    )
    
    # Buscar PDFs
    pdf_files = converter.find_pdfs(input_path, recursive)
    
    if not pdf_files:
        click.echo(f"❌ Nenhum PDF encontrado em: {input_path}", err=True)
        sys.exit(1)
    
    if not quiet:
        click.echo(f"📁 Encontrados {len(pdf_files)} arquivo(s)")
        
        if not click.confirm('\nContinuar?', default=True):
            click.echo("Cancelado.")
            return
    
    # Converter
    converter.convert_batch(pdf_files, output_path, overwrite)


@cli.group()
def config():
    """Gerenciar configurações."""
    pass


@config.command('show')
@click.option('--json-format', is_flag=True, help='Exibir como JSON')
def config_show(json_format):
    """Mostra configurações atuais."""
    manager = ConfigManager()
    settings = manager.load_settings()
    
    if not settings:
        settings = manager.get_default_settings()
        click.echo("⚠️ Usando configurações padrão (nenhuma salva)")
    
    if json_format:
        click.echo(json.dumps(settings, indent=2, ensure_ascii=False))
    else:
        click.echo("\n📋 Configurações Atuais:\n")
        for key, value in settings.items():
            click.echo(f"  {key}: {value}")


@config.command('set')
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    """
    Define uma configuração.
    
    Exemplos:
    
      pdf-converter config set extraction_method camelot
      
      pdf-converter config set design_theme medical
    """
    manager = ConfigManager()
    settings = manager.load_settings() or {}
    
    # Converter string para tipo apropriado
    if value.lower() in ['true', 'false']:
        value = value.lower() == 'true'
    elif value.isdigit():
        value = int(value)
    
    settings[key] = value
    manager.save_settings(settings)
    
    click.echo(f"✅ Configuração salva: {key} = {value}")


@config.command('reset')
@click.confirmation_option(prompt='Tem certeza que deseja resetar todas as configurações?')
def config_reset():
    """Reseta configurações para padrão."""
    manager = ConfigManager()
    defaults = manager.get_default_settings()
    manager.save_settings(defaults)
    
    click.echo("✅ Configurações resetadas para padrão")


@cli.group()
def history():
    """Gerenciar histórico de conversões."""
    pass


@history.command('list')
@click.option('-n', '--number', type=int, default=10, 
              help='Número de itens a mostrar')
@click.option('--json-format', is_flag=True, help='Formato JSON')
def history_list(number, json_format):
    """Lista histórico de conversões."""
    manager = ConfigManager()
    items = manager.get_history()
    
    if not items:
        click.echo("📭 Histórico vazio")
        return
    
    # Mostrar últimos N itens
    items = items[-number:]
    
    if json_format:
        click.echo(json.dumps(items, indent=2, ensure_ascii=False))
    else:
        click.echo(f"\n📜 Últimas {len(items)} conversões:\n")
        for i, item in enumerate(reversed(items), 1):
            click.echo(f"{i}. {item.get('input', 'N/A')}")
            click.echo(f"   → {item.get('output', 'N/A')}")
            click.echo(f"   🕐 {item.get('timestamp', 'N/A')}")
            click.echo(f"   🎨 Tema: {item.get('theme', 'N/A')}")
            click.echo()


@history.command('clear')
@click.confirmation_option(prompt='Tem certeza que deseja limpar o histórico?')
def history_clear():
    """Limpa histórico de conversões."""
    manager = ConfigManager()
    manager.clear_history()
    click.echo("✅ Histórico limpo")


@history.command('open')
@click.option('-n', '--number', type=int, default=1,
              help='Número da conversão (1 = mais recente)')
def history_open(number):
    """Abre arquivo da conversão no histórico."""
    manager = ConfigManager()
    items = manager.get_history()
    
    if not items:
        click.echo("❌ Histórico vazio", err=True)
        return
    
    if number > len(items) or number < 1:
        click.echo(f"❌ Número inválido. Use 1-{len(items)}", err=True)
        return
    
    # Pegar item (reversed porque queremos o mais recente primeiro)
    item = list(reversed(items))[number - 1]
    output_path = Path(item['output'])
    
    if not output_path.exists():
        click.echo(f"❌ Arquivo não encontrado: {output_path}", err=True)
        return
    
    import webbrowser
    webbrowser.open(str(output_path))
    click.echo(f"✅ Abrindo: {output_path.name}")


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
def info(input_file):
    """
    Mostra informações sobre um PDF.
    
    Exibe metadados, número de páginas, tabelas detectadas, etc.
    """
    import fitz
    
    pdf_path = Path(input_file)
    
    try:
        doc = fitz.open(pdf_path)
        
        click.echo(f"\n📄 Informações do PDF: {pdf_path.name}\n")
        click.echo(f"  Páginas: {len(doc)}")
        click.echo(f"  Tamanho: {pdf_path.stat().st_size / 1024:.2f} KB")
        
        # Metadata
        metadata = doc.metadata
        if metadata:
            click.echo("\n  📋 Metadados:")
            for key, value in metadata.items():
                if value:
                    click.echo(f"    {key}: {value}")
        
        # Analisar páginas
        click.echo("\n  📊 Análise de Conteúdo:")
        
        total_text = sum(len(doc[i].get_text()) for i in range(len(doc)))
        total_images = sum(len(doc[i].get_images()) for i in range(len(doc)))
        
        click.echo(f"    Caracteres de texto: {total_text:,}")
        click.echo(f"    Imagens: {total_images}")
        
        # Detectar tabelas potenciais
        extractor = PDFExtractor()
        pages_data = extractor.extract(pdf_path)
        tables_count = sum(1 for p in pages_data if p.get('has_table'))
        
        click.echo(f"    Tabelas detectadas: {tables_count}")
        
        doc.close()
        
    except Exception as e:
        click.echo(f"\n❌ Erro ao ler PDF: {e}", err=True)
        sys.exit(1)


@cli.command()
def gui():
    """Abre interface gráfica."""
    click.echo("🖥️  Abrindo interface gráfica...")
    
    try:
        from main import main as gui_main
        gui_main()
    except ImportError:
        click.echo("❌ Erro ao importar GUI. Verifique a instalação.", err=True)
        sys.exit(1)


@cli.command()
def doctor():
    """
    Diagnóstico do sistema.
    
    Verifica dependências, configurações e identifica problemas.
    """
    click.echo("\n🔍 Executando diagnóstico...\n")
    
    issues = []
    warnings = []
    
    # Verificar Python
    import sys
    version = sys.version_info
    click.echo(f"✓ Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.minor < 8:
        issues.append("Python 3.8+ é necessário")
    
    # Verificar dependências
    deps = {
        'fitz': 'PyMuPDF',
        'camelot': 'Camelot',
        'pdfplumber': 'PDFPlumber',
        'PIL': 'Pillow',
        'pandas': 'Pandas',
        'tkinter': 'Tkinter'
    }
    
    for module, name in deps.items():
        try:
            __import__(module)
            click.echo(f"✓ {name}")
        except ImportError:
            if module in ['camelot', 'pdfplumber']:
                warnings.append(f"{name} não instalado (opcional)")
                click.echo(f"⚠️  {name} (opcional)")
            else:
                issues.append(f"{name} não instalado")
                click.echo(f"❌ {name}")
    
    # Verificar ghostscript (para Camelot)
    import subprocess
    try:
        subprocess.run(['gs', '--version'], 
                      capture_output=True, check=True)
        click.echo("✓ Ghostscript")
    except:
        warnings.append("Ghostscript não encontrado (necessário para Camelot)")
        click.echo("⚠️  Ghostscript (necessário para Camelot)")
    
    # Resumo
    click.echo("\n" + "="*50)
    
    if not issues and not warnings:
        click.echo("✅ Tudo certo! Sistema pronto para uso.")
    else:
        if issues:
            click.echo(f"\n❌ {len(issues)} problema(s) encontrado(s):")
            for issue in issues:
                click.echo(f"  • {issue}")
        
        if warnings:
            click.echo(f"\n⚠️  {len(warnings)} aviso(s):")
            for warning in warnings:
                click.echo(f"  • {warning}")
    
    click.echo()


if __name__ == '__main__':
    cli()
