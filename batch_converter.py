"""
Batch Converter - Conversão em lote de múltiplos PDFs
Linha de comando para automação
"""

import argparse
import sys
from pathlib import Path
from typing import List
import time
from datetime import datetime

from pdf_extractor import PDFExtractor
from html_generator import HTMLGenerator


class BatchConverter:
    """Conversor em lote de PDFs"""
    
    def __init__(self, method="auto", theme="premium", verbose=True):
        self.method = method
        self.theme = theme
        self.verbose = verbose
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None
        }
    
    def log(self, message, level="info"):
        """Logger condicional"""
        if not self.verbose:
            return
        
        icons = {
            'info': 'ℹ️',
            'success': '✓',
            'warning': '⚠️',
            'error': '❌'
        }
        
        icon = icons.get(level, 'ℹ️')
        print(f"{icon} {message}")
    
    def find_pdfs(self, directory: Path, recursive=False) -> List[Path]:
        """Encontra todos os PDFs em um diretório"""
        pattern = "**/*.pdf" if recursive else "*.pdf"
        return list(directory.glob(pattern))
    
    def convert_file(self, pdf_path: Path, output_dir: Path = None) -> bool:
        """Converte um único arquivo"""
        try:
            self.log(f"Processando: {pdf_path.name}", "info")
            
            # Extrair dados
            extractor = PDFExtractor(method=self.method, log_callback=None)
            pages_data = extractor.extract(pdf_path)
            
            if not pages_data:
                self.log(f"  Nenhum dado extraído de {pdf_path.name}", "warning")
                return False
            
            # Gerar HTML
            generator = HTMLGenerator(
                theme=self.theme,
                include_toc=True,
                responsive=True,
                animations=True,
                dark_mode=True
            )
            html_content = generator.generate(pages_data)
            
            # Determinar caminho de saída
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"{pdf_path.stem}.html"
            else:
                output_path = pdf_path.parent / f"{pdf_path.stem}.html"
            
            # Salvar
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.log(f"  ✓ Salvo: {output_path.name}", "success")
            return True
        
        except Exception as e:
            self.log(f"  ❌ Erro: {str(e)}", "error")
            return False
    
    def convert_batch(self, pdf_files: List[Path], output_dir: Path = None, 
                     overwrite=False):
        """Converte múltiplos arquivos"""
        
        self.stats['total'] = len(pdf_files)
        self.stats['start_time'] = time.time()
        
        self.log(f"\n{'='*70}", "info")
        self.log(f"  CONVERSÃO EM LOTE - {self.stats['total']} arquivo(s)", "info")
        self.log(f"{'='*70}\n", "info")
        
        for i, pdf_path in enumerate(pdf_files, 1):
            self.log(f"[{i}/{self.stats['total']}] {pdf_path.name}", "info")
            
            # Verificar se já existe
            if output_dir:
                output_path = output_dir / f"{pdf_path.stem}.html"
            else:
                output_path = pdf_path.parent / f"{pdf_path.stem}.html"
            
            if output_path.exists() and not overwrite:
                self.log(f"  ⏭️ Já existe (use --overwrite para substituir)", "warning")
                self.stats['skipped'] += 1
                continue
            
            # Converter
            if self.convert_file(pdf_path, output_dir):
                self.stats['success'] += 1
            else:
                self.stats['failed'] += 1
            
            print()  # Linha em branco entre arquivos
        
        self.stats['end_time'] = time.time()
        self.print_summary()
    
    def print_summary(self):
        """Imprime resumo da conversão"""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        print("\n" + "="*70)
        print("  📊 RESUMO DA CONVERSÃO")
        print("="*70)
        print(f"\n  Total processado:  {self.stats['total']}")
        print(f"  ✓ Sucesso:         {self.stats['success']}")
        print(f"  ❌ Falhas:          {self.stats['failed']}")
        print(f"  ⏭️ Ignorados:       {self.stats['skipped']}")
        print(f"\n  ⏱️ Tempo total:     {duration:.2f}s")
        print(f"  📈 Média:          {duration/self.stats['total']:.2f}s por arquivo")
        print("\n" + "="*70 + "\n")


def main():
    """Função principal com argumentos de linha de comando"""
    
    parser = argparse.ArgumentParser(
        description="PDF to HTML Batch Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  
  # Converter todos PDFs no diretório atual
  python batch_converter.py
  
  # Converter PDFs de uma pasta específica
  python batch_converter.py --input /caminho/para/pdfs
  
  # Converter recursivamente (incluindo subpastas)
  python batch_converter.py --input /caminho --recursive
  
  # Especificar pasta de saída
  python batch_converter.py --input pdfs/ --output html/
  
  # Usar tema específico
  python batch_converter.py --theme medical
  
  # Usar método de extração específico
  python batch_converter.py --method camelot
  
  # Sobrescrever arquivos existentes
  python batch_converter.py --overwrite
  
  # Modo silencioso (sem verbose)
  python batch_converter.py --quiet
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        type=str,
        default='.',
        help='Diretório de entrada com PDFs (padrão: diretório atual)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Diretório de saída para HTMLs (padrão: mesmo do PDF)'
    )
    
    parser.add_argument(
        '-m', '--method',
        choices=['auto', 'camelot', 'pdfplumber', 'pymupdf'],
        default='auto',
        help='Método de extração (padrão: auto)'
    )
    
    parser.add_argument(
        '-t', '--theme',
        choices=['premium', 'medical', 'modern', 'classic'],
        default='premium',
        help='Tema do HTML (padrão: premium)'
    )
    
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Buscar PDFs recursivamente em subpastas'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Sobrescrever arquivos HTML existentes'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Modo silencioso (menos mensagens)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='PDF Converter Pro 2.0'
    )
    
    args = parser.parse_args()
    
    # Validar diretório de entrada
    input_dir = Path(args.input).resolve()
    if not input_dir.exists():
        print(f"❌ Erro: Diretório não encontrado: {input_dir}")
        sys.exit(1)
    
    if not input_dir.is_dir():
        print(f"❌ Erro: {input_dir} não é um diretório")
        sys.exit(1)
    
    # Preparar diretório de saída
    output_dir = Path(args.output).resolve() if args.output else None
    
    # Criar conversor
    converter = BatchConverter(
        method=args.method,
        theme=args.theme,
        verbose=not args.quiet
    )
    
    # Buscar PDFs
    pdf_files = converter.find_pdfs(input_dir, args.recursive)
    
    if not pdf_files:
        print(f"❌ Nenhum arquivo PDF encontrado em: {input_dir}")
        sys.exit(1)
    
    # Converter
    try:
        converter.convert_batch(pdf_files, output_dir, args.overwrite)
    except KeyboardInterrupt:
        print("\n\n❌ Conversão interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
