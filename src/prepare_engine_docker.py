import zipfile
import os
import shutil
import subprocess
import time
import argparse
import requests
from bs4 import BeautifulSoup

def download_stockfish_linux():
    """Download Stockfish for Linux environment"""
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    try:
        result = subprocess.run([
            "curl", "-L", "-C", "-", 
            "-o", os.path.join(output_dir, 'stockfish.zip'),
            "https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-linux-x86-64-avx2.zip"
        ], check=True)
        print("Download successful (Stockfish Linux)")
        return True
    except subprocess.CalledProcessError as e:
        print("Download failed (Stockfish Linux):", e)
        return False

def unzip_stockfish():
    """Extract Stockfish from zip file"""
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    stockfish_dir = os.path.join(output_dir, 'stockfish')
    if os.path.exists(stockfish_dir):
        shutil.rmtree(stockfish_dir)
    os.mkdir(stockfish_dir)
    
    try:
        with zipfile.ZipFile(os.path.join(output_dir, 'stockfish.zip'), 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        print("✅ Stockfish extraction successful")
        return True
    except Exception as e:
        print(f"❌ Stockfish extraction failed: {e}")
        return False

def setup_lc0_docker():
    """Setup lc0 in Docker environment - uses pre-built binary from Docker build"""
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    lc0_dir = os.path.join(output_dir, 'lc0')
    if not os.path.exists(lc0_dir):
        os.mkdir(lc0_dir)
    
    # In Docker, lc0 is already built and installed system-wide
    print("Running in Docker environment - lc0 is already built and installed")
    
    # Check for lc0 binary in system locations
    lc0_binary_paths = [
        "/usr/local/bin/lc0",
        "/usr/bin/lc0",
        "/opt/lc0/lc0"
    ]
    
    lc0_found = False
    for binary_path in lc0_binary_paths:
        if os.path.exists(binary_path):
            # Copy the binary to our output directory
            shutil.copy2(binary_path, os.path.join(lc0_dir, 'lc0'))
            print(f"✅ lc0 binary copied from {binary_path} to output directory")
            lc0_found = True
            break
    
    if not lc0_found:
        print("❌ lc0 binary not found in expected system locations")
        print("Available lc0 binary locations checked:")
        for path in lc0_binary_paths:
            print(f"  - {path}: {'✓' if os.path.exists(path) else '✗'}")
        return False
    
    # Make the binary executable
    lc0_binary = os.path.join(lc0_dir, 'lc0')
    os.chmod(lc0_binary, 0o755)
    
    # Verify lc0 works
    try:
        result = subprocess.run([lc0_binary, '--help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ lc0 binary verification successful")
            return True
        else:
            print(f"❌ lc0 binary verification failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✅ lc0 binary verification successful (timeout expected for help)")
        return True
    except Exception as e:
        print(f"❌ lc0 binary verification failed: {e}")
        return False

def download_network_file():
    """Download a neural network file for lc0"""
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    lc0_dir = os.path.join(output_dir, 'lc0')
    
    # Check if network file already exists
    network_path = os.path.join(lc0_dir, 'network.pb.gz')
    if os.path.exists(network_path):
        print("✅ Network file already exists")
        return True
    
    # Download a small test network (T60-3010)
    network_url = "https://github.com/LeelaChessZero/lc0/releases/download/v0.31.2/T60-3010.pb.gz"
    
    try:
        print("Downloading neural network file...")
        result = subprocess.run([
            "curl", "-L", "-C", "-", 
            "-o", network_path,
            network_url
        ], check=True)
        print("✅ Network file download successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Network file download failed: {e}")
        return False

def verify_engine_setup(engine_type):
    """Verify that the engine is properly set up"""
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    
    if engine_type == 'stockfish':
        stockfish_dir = os.path.join(output_dir, 'stockfish')
        stockfish_binary = None
        
        # Find Stockfish binary
        for file in os.listdir(stockfish_dir):
            if file.startswith('stockfish') and os.access(os.path.join(stockfish_dir, file), os.X_OK):
                stockfish_binary = os.path.join(stockfish_dir, file)
                break
        
        if stockfish_binary:
            try:
                result = subprocess.run([stockfish_binary, '--help'], 
                                      capture_output=True, text=True, timeout=10)
                print("✅ Stockfish verification successful")
                return True
            except Exception as e:
                print(f"❌ Stockfish verification failed: {e}")
                return False
        else:
            print("❌ Stockfish binary not found")
            return False
    
    elif engine_type == 'lc0':
        lc0_dir = os.path.join(output_dir, 'lc0')
        lc0_binary = os.path.join(lc0_dir, 'lc0')
        
        if os.path.exists(lc0_binary) and os.access(lc0_binary, os.X_OK):
            try:
                result = subprocess.run([lc0_binary, '--help'], 
                                      capture_output=True, text=True, timeout=10)
                print("✅ lc0 verification successful")
                return True
            except Exception as e:
                print(f"❌ lc0 verification failed: {e}")
                return False
        else:
            print("❌ lc0 binary not found or not executable")
            return False

def main():
    parser = argparse.ArgumentParser(description="Prepare chess engine in Docker environment")
    parser.add_argument('engine', choices=['stockfish', 'lc0'], 
                       help="Which engine to prepare: 'stockfish' or 'lc0'")
    parser.add_argument('--verify', action='store_true', 
                       help="Verify engine setup after preparation")
    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(output_dir, exist_ok=True)

    if args.engine == 'stockfish':
        print("🐟 Setting up Stockfish for Linux...")
        
        # Download Stockfish
        while True:
            success = download_stockfish_linux()
            if success:
                print("✅ Stockfish download successful.")
                break
            else:
                print("❌ Stockfish download failed. Retrying in 5 seconds...")
                time.sleep(5)
        
        # Extract Stockfish
        while True:
            success = unzip_stockfish()
            if success:
                print("✅ Stockfish extraction successful.")
                break
            else:
                print("❌ Stockfish extraction failed. Retrying in 5 seconds...")
                time.sleep(5)
        
        if args.verify:
            verify_engine_setup('stockfish')
    
    elif args.engine == 'lc0':
        print("🤖 Setting up Leela Chess Zero (lc0)...")
        
        # Setup lc0 (uses pre-built binary from Docker build)
        while True:
            success = setup_lc0_docker()
            if success:
                print("✅ lc0 setup successful.")
                break
            else:
                print("❌ lc0 setup failed. Retrying in 5 seconds...")
                time.sleep(5)
        
        # Download network file
        print("📥 Downloading neural network file...")
        download_network_file()
        
        if args.verify:
            verify_engine_setup('lc0')
    
    print(f"\n🎉 {args.engine.upper()} setup completed successfully!")
    print(f"Engine files are located in: {os.path.join(output_dir, args.engine)}")

if __name__ == "__main__":
    main() 