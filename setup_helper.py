"""
Setup Helper for PDF to HTML AI Converter
Automated installation and environment check
"""

import subprocess
import sys
import platform
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def check_python_version():
    """Check if Python version is compatible"""
    print_header("🐍 Checking Python Version")
    
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ ERROR: Python 3.8+ is required")
        print("   Please upgrade Python from python.org")
        return False
    
    print("✅ Python version is compatible")
    return True


def check_pip():
    """Check if pip is available"""
    print_header("📦 Checking pip")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        print("✅ pip is available")
        return True
    except:
        print("❌ ERROR: pip is not available")
        print("   Install pip: python -m ensurepip --upgrade")
        return False


def install_requirements():
    """Install requirements from requirements.txt"""
    print_header("📥 Installing Dependencies")
    
    req_file = Path("requirements.txt")
    
    if not req_file.exists():
        print("❌ ERROR: requirements.txt not found")
        return False
    
    print("Installing packages... (this may take a few minutes)")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"],
            check=True
        )
        print("\n✅ All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR: Installation failed")
        print(f"   {e}")
        return False


def check_critical_imports():
    """Check if critical packages can be imported"""
    print_header("🔍 Verifying Installation")
    
    packages = {
        'fitz': 'PyMuPDF',
        'pdfplumber': 'pdfplumber',
        'camelot': 'camelot-py',
        'PIL': 'Pillow',
        'cv2': 'opencv-python',
        'pandas': 'pandas',
        'numpy': 'numpy'
    }
    
    failed = []
    
    for import_name, package_name in packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - FAILED")
            failed.append(package_name)
    
    if failed:
        print(f"\n⚠ WARNING: {len(failed)} package(s) failed to import")
        print("   Failed packages:", ", ".join(failed))
        return False
    
    print("\n✅ All critical packages verified")
    return True


def check_ghostscript():
    """Check if Ghostscript is installed (required for Camelot)"""
    print_header("👻 Checking Ghostscript")
    
    try:
        if platform.system() == "Windows":
            subprocess.run(["gswin64c", "--version"], 
                         check=True, capture_output=True)
        else:
            subprocess.run(["gs", "--version"], 
                         check=True, capture_output=True)
        
        print("✅ Ghostscript is installed")
        return True
    except:
        print("⚠ WARNING: Ghostscript not found")
        print("   Ghostscript is required for advanced table extraction")
        print("   Install from: https://www.ghostscript.com/")
        return False


def check_tesseract():
    """Check if Tesseract OCR is installed"""
    print_header("📖 Checking Tesseract OCR (Optional)")
    
    try:
        subprocess.run(["tesseract", "--version"], 
                      check=True, capture_output=True)
        print("✅ Tesseract OCR is installed")
        return True
    except:
        print("ℹ INFO: Tesseract OCR not found (optional)")
        print("   Required only for OCR on scanned PDFs")
        print("   Install: https://github.com/UB-Mannheim/tesseract/wiki")
        return False


def create_test_config():
    """Create initial config files"""
    print_header("⚙️ Creating Configuration")
    
    # Create config.json if not exists
    config_file = Path("config.json")
    if not config_file.exists():
        config_file.write_text('''{
    "extraction_method": "auto",
    "design_theme": "neumorphic_dark",
    "include_toc": true,
    "responsive_design": true,
    "animations": true,
    "enable_ocr": false,
    "export_markdown": false
}''')
        print("✅ Created config.json")
    
    # Create history.json if not exists
    history_file = Path("history.json")
    if not history_file.exists():
        history_file.write_text('[]')
        print("✅ Created history.json")
    
    return True


def print_system_info():
    """Print system information"""
    print_header("💻 System Information")
    
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python: {sys.version}")
    print(f"Installation Path: {sys.prefix}")


def run_setup():
    """Run complete setup process"""
    print("\n" + "🚀" * 35)
    print("  PDF to HTML AI Converter - Setup")
    print("🚀" * 35)
    
    # System info
    print_system_info()
    
    # Check Python
    if not check_python_version():
        return False
    
    # Check pip
    if not check_pip():
        return False
    
    # Install requirements
    if not install_requirements():
        print("\n⚠ Installation failed. Try manual installation:")
        print("   pip install -r requirements.txt")
        return False
    
    # Verify imports
    if not check_critical_imports():
        print("\n⚠ Some packages failed verification")
        print("   The application may not work correctly")
    
    # Check optional dependencies
    check_ghostscript()
    check_tesseract()
    
    # Create config
    create_test_config()
    
    # Success
    print_header("✅ Setup Complete!")
    print("You can now run the application:")
    print("   python main.py")
    print("\nFor help, check the documentation or README.md")
    
    return True


if __name__ == "__main__":
    try:
        success = run_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
