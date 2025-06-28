#!/usr/bin/env python3
"""
Chess Analysis Pipeline Orchestrator

This script orchestrates the entire chess analysis pipeline in Docker environment:
1. Setup chess engines (Stockfish or lc0)
2. Fetch chess archives for a username
3. Scrape games from archives
4. Analyze games with the chosen engine

Usage:
    python run_analysis_pipeline.py <username> <engine> [options]
    
Examples:
    python run_analysis_pipeline.py magnuscarlsen stockfish
    python run_analysis_pipeline.py magnuscarlsen lc0 --depth 15 --threads 4
"""

import os
import sys
import subprocess
import argparse
import time
import json
from pathlib import Path

def run_command(cmd, description, check=True):
    """Run a command and handle errors gracefully"""
    print(f"\n🔄 {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False

def setup_engine(engine_type, verify=True):
    """Setup the specified chess engine"""
    print(f"\n🎯 Setting up {engine_type.upper()} engine...")
    
    cmd = ["python", "src/prepare_engine_docker.py", engine_type]
    if verify:
        cmd.append("--verify")
    
    success = run_command(cmd, f"Setting up {engine_type} engine")
    
    if not success:
        print(f"❌ Failed to setup {engine_type} engine. Exiting.")
        sys.exit(1)
    
    return success

def fetch_archives(username):
    """Fetch chess archives for the given username"""
    print(f"\n📚 Fetching chess archives for user: {username}")
    
    cmd = ["python", "src/chess_archives.py", username]
    success = run_command(cmd, f"Fetching archives for {username}")
    
    if not success:
        print(f"❌ Failed to fetch archives for {username}. Exiting.")
        sys.exit(1)
    
    return success

def scrape_games():
    """Scrape games from the fetched archives"""
    print(f"\n🎮 Scraping games from archives...")
    
    cmd = ["python", "src/chess_games_scraper.py", "chess_archives.txt"]
    success = run_command(cmd, "Scraping games from archives")
    
    if not success:
        print(f"❌ Failed to scrape games. Exiting.")
        sys.exit(1)
    
    return success

def analyze_games(engine_type, **kwargs):
    """Analyze games with the specified engine"""
    print(f"\n🔍 Analyzing games with {engine_type.upper()}...")
    
    # Determine the correct analysis script and parameters
    if engine_type == "stockfish":
        cmd = ["python", "src/analyze_games.py", "output/chess_games.json"]
        
        # Add Stockfish-specific parameters
        stockfish_path = kwargs.get('stockfish_path', 'output/stockfish/stockfish')
        threads = kwargs.get('threads', 2)
        depth = kwargs.get('depth', 15)
        min_thinking_time = kwargs.get('min_thinking_time', 30)
        
        cmd.extend([
            "--stockfish_path", stockfish_path,
            "--threads", str(threads),
            "--depth", str(depth),
            "--min_thinking_time", str(min_thinking_time)
        ])
        
    elif engine_type == "lc0":
        cmd = ["python", "src/analyze_games_lc0.py", "output/chess_games.json"]
        
        # Add lc0-specific parameters
        lc0_path = kwargs.get('lc0_path', 'output/lc0/lc0')
        weights_path = kwargs.get('weights_path', 'output/lc0/network.pb.gz')
        depth = kwargs.get('depth', 10)
        workers = kwargs.get('workers', 1)
        timeout = kwargs.get('timeout', 30)
        
        cmd.extend([
            "--lc0_path", lc0_path,
            "--weights_path", weights_path,
            "--depth", str(depth),
            "--workers", str(workers),
            "--timeout", str(timeout)
        ])
    
    success = run_command(cmd, f"Analyzing games with {engine_type}")
    
    if not success:
        print(f"❌ Failed to analyze games with {engine_type}. Exiting.")
        sys.exit(1)
    
    return success

def verify_files():
    """Verify that required files exist"""
    output_dir = Path("output")
    
    required_files = {
        "chess_archives.txt": "Chess archives file",
        "chess_games.json": "Chess games data",
    }
    
    print(f"\n📋 Verifying required files...")
    
    for filename, description in required_files.items():
        file_path = output_dir / filename
        if file_path.exists():
            print(f"✅ {description}: {filename}")
        else:
            print(f"❌ {description}: {filename} - NOT FOUND")
            return False
    
    return True

def get_analysis_results(engine_type):
    """Get the path to the analysis results file"""
    if engine_type == "stockfish":
        return "output/chess_analysis_stockfish.csv"
    elif engine_type == "lc0":
        return "output/chess_analysis_lc0.csv"
    else:
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Run the complete chess analysis pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_analysis_pipeline.py magnuscarlsen stockfish
  python run_analysis_pipeline.py magnuscarlsen lc0 --depth 15 --threads 4
  python run_analysis_pipeline.py magnuscarlsen stockfish --no-verify --depth 20
        """
    )
    
    # Required arguments
    parser.add_argument("username", help="Chess.com username to analyze")
    parser.add_argument("engine", choices=["stockfish", "lc0"], 
                       help="Chess engine to use for analysis")
    
    # Optional arguments
    parser.add_argument("--no-verify", action="store_true", 
                       help="Skip engine verification")
    parser.add_argument("--depth", type=int, default=None,
                       help="Analysis depth (default: 15 for Stockfish, 10 for lc0)")
    parser.add_argument("--threads", type=int, default=None,
                       help="Number of threads (Stockfish only, default: 2)")
    parser.add_argument("--workers", type=int, default=None,
                       help="Number of workers (lc0 only, default: 1)")
    parser.add_argument("--timeout", type=int, default=None,
                       help="Analysis timeout in seconds (lc0 only, default: 30)")
    parser.add_argument("--min-thinking-time", type=int, default=None,
                       help="Minimum thinking time in ms (Stockfish only, default: 30)")
    parser.add_argument("--skip-engine-setup", action="store_true",
                       help="Skip engine setup (assumes engines are already prepared)")
    parser.add_argument("--skip-archives", action="store_true",
                       help="Skip fetching archives (assumes chess_archives.txt exists)")
    parser.add_argument("--skip-scraping", action="store_true",
                       help="Skip game scraping (assumes chess_games.json exists)")
    
    args = parser.parse_args()
    
    # Set default values based on engine type
    if args.depth is None:
        args.depth = 15 if args.engine == "stockfish" else 10
    
    if args.threads is None and args.engine == "stockfish":
        args.threads = 2
    
    if args.workers is None and args.engine == "lc0":
        args.workers = 1
    
    if args.timeout is None and args.engine == "lc0":
        args.timeout = 30
    
    if args.min_thinking_time is None and args.engine == "stockfish":
        args.min_thinking_time = 30
    
    print("🚀 Starting Chess Analysis Pipeline")
    print("=" * 50)
    print(f"Username: {args.username}")
    print(f"Engine: {args.engine}")
    print(f"Analysis Depth: {args.depth}")
    
    if args.engine == "stockfish":
        print(f"Threads: {args.threads}")
        print(f"Min Thinking Time: {args.min_thinking_time}ms")
    else:
        print(f"Workers: {args.workers}")
        print(f"Timeout: {args.timeout}s")
    
    print("=" * 50)
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Step 1: Setup engine (unless skipped)
    if not args.skip_engine_setup:
        setup_engine(args.engine, verify=not args.no_verify)
    else:
        print("\n⏭️  Skipping engine setup")
    
    # Step 2: Fetch archives (unless skipped)
    if not args.skip_archives:
        fetch_archives(args.username)
    else:
        print("\n⏭️  Skipping archive fetching")
    
    # Step 3: Verify files exist
    if not verify_files():
        print("❌ Required files not found. Please check the previous steps.")
        sys.exit(1)
    
    # Step 4: Scrape games (unless skipped)
    if not args.skip_scraping:
        scrape_games()
    else:
        print("\n⏭️  Skipping game scraping")
    
    # Step 5: Analyze games
    analysis_params = {
        "depth": args.depth,
        "threads": args.threads,
        "workers": args.workers,
        "timeout": args.timeout,
        "min_thinking_time": args.min_thinking_time
    }
    
    analyze_games(args.engine, **analysis_params)
    
    # Step 6: Report results
    results_file = get_analysis_results(args.engine)
    if results_file and os.path.exists(results_file):
        print(f"\n🎉 Analysis completed successfully!")
        print(f"Results saved to: {results_file}")
        
        # Try to get some basic stats
        try:
            import pandas as pd
            df = pd.read_csv(results_file)
            print(f"Total moves analyzed: {len(df)}")
            print(f"Games analyzed: {df['GameID'].nunique() if 'GameID' in df.columns else 'Unknown'}")
        except Exception as e:
            print(f"Could not read results file for stats: {e}")
    else:
        print(f"\n⚠️  Analysis completed, but results file not found: {results_file}")
    
    print("\n🏁 Pipeline completed!")

if __name__ == "__main__":
    main() 