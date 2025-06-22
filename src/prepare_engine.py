import zipfile
import os
import shutil
import subprocess
import time
# download the file in output directory
def download_stockfish():
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    try:
        result = subprocess.run([
            "curl", "-L", "-C", "-", 
            "-o", os.path.join(output_dir, 'stockfish.zip'),
            "https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-windows-x86-64-avx2.zip"
        ], check=True)
        print("Download successful")
        return True
    except subprocess.CalledProcessError as e:
        print("Download failed:", e)
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


# Loop until success
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
    
