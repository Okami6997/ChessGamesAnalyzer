import zipfile
import os
import shutil
import subprocess
import time
import argparse
import requests
from bs4 import BeautifulSoup

# download the file in output directory
def download_stockfish():
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    try:
        result = subprocess.run([
            "curl", "-L", "-C", "-", 
            "-o", os.path.join(output_dir, 'stockfish.zip'),
            "https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-windows-x86-64-avx2.zip"
        ], check=True)
        print("Download successful (Stockfish)")
        return True
    except subprocess.CalledProcessError as e:
        print("Download failed (Stockfish):", e)
        return False
    
# unzip using python the zipped stockfish file and delete the zip
def unzip_stockfish():
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    stockfish_dir = os.path.join(output_dir, 'stockfish')
    if os.path.exists(stockfish_dir):
        shutil.rmtree(stockfish_dir)
    os.mkdir(stockfish_dir)
    with zipfile.ZipFile(os.path.join(output_dir,'stockfish.zip'), 'r') as zip_ref:
        zip_ref.extractall(output_dir)
        return True
    return False

def download_lc0():
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    lc0_dir = os.path.join(output_dir, 'lc0')
    if not os.path.exists(lc0_dir):
        os.mkdir(lc0_dir)
    # Download Lc0 Windows release (latest)
    try:
        result = subprocess.run([
            "curl", "-L", "-C", "-", 
            "-o", os.path.join(output_dir, 'lc0.zip'),
            "https://github.com/LeelaChessZero/lc0/releases/download/v0.31.2/lc0-v0.31.2-windows-gpu-nvidia-cuda.zip"
        ], check=True)
        print("Download successful (Lc0)")
        return True
    except subprocess.CalledProcessError as e:
        print("Download failed (Lc0):", e)
        return False

def unzip_lc0():
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    lc0_dir = os.path.join(output_dir, 'lc0')
    if os.path.exists(lc0_dir):
        shutil.rmtree(lc0_dir)
    os.mkdir(lc0_dir)
    with zipfile.ZipFile(os.path.join(output_dir,'lc0.zip'), 'r') as zip_ref:
        zip_ref.extractall(lc0_dir)
    # After extraction, rename any .pb.gz file to network.pb.gz
    for fname in os.listdir(lc0_dir):
        if fname.endswith('.pb.gz') and fname != 'network.pb.gz':
            src = os.path.join(lc0_dir, fname)
            dst = os.path.join(lc0_dir, 'network.pb.gz')
            if os.path.exists(dst):
                os.remove(dst)
            os.rename(src, dst)
            print(f"Renamed {fname} to network.pb.gz")
            break
    return True

def main():
    parser = argparse.ArgumentParser(description="Prepare chess engine for Windows environment")
    parser.add_argument('engine', choices=['stockfish', 'lc0'], help="Which engine to prepare: 'stockfish' or 'lc0'")
    args = parser.parse_args()

    if args.engine == 'stockfish':
        while True:
            success = download_stockfish()
            if success:
                print("✅ Download successful.")
                break
            else:
                print("❌ Download failed. Retrying in 5 seconds...")
                time.sleep(5)  # Optional wait before retrying
        while True:
            success = unzip_stockfish()
            if success:
                print("✅ Unzipping successful.")
                break
            else:
                print("❌ Unzipping failed. Retrying in 5 seconds...")
                time.sleep(5)
    elif args.engine == 'lc0':
        while True:
            success = download_lc0()
            if success:
                print("✅ Download successful (Lc0).")
                break
            else:
                print("❌ Download failed (Lc0). Retrying in 5 seconds...")
                time.sleep(5)
        while True:
            success = unzip_lc0()
            if success:
                print("✅ Unzipping successful (Lc0).")
                break
            else:
                print("❌ Unzipping failed (Lc0). Retrying in 5 seconds...")
                time.sleep(5)

if __name__ == "__main__":
    main()
    
