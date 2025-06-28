#!/usr/bin/env python3
"""
Lichess Analysis Tool
Reads PGN from JSON files and imports them to Lichess for analysis.
"""

import requests
import json
import sys
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

LICHESS_API_URL = "https://lichess.org/api/import"

def load_api_key():
    """Load API key from environment variable or .env file."""
    # Try to load from .env file in multiple possible locations
    env_paths = [
        Path.cwd() / ".env",  # Current directory
        Path(__file__).parent.parent / ".env",  # Parent of src directory
        Path(__file__).parent / ".env",  # src directory
    ]
    
    print("Looking for .env file in:")
    for path in env_paths:
        print(f"  - {path}")
        if path.exists():
            print(f"    ✓ Found at {path}")
            load_dotenv(path)
            break
    else:
        print("  - No .env file found in common locations")
        # Try loading from current directory anyway
        load_dotenv()
    
    # Check for API key with multiple possible variable names
    api_key = os.getenv("LICHESS_API_KEY") or os.getenv("LICHESS_API_TOKEN")
    print(f"API key found: {'Yes' if api_key else 'No'}")
    
    if not api_key:
        print("Error: Lichess API key not found!")
        print("Please set LICHESS_API_KEY or LICHESS_API_TOKEN in your .env file or environment variable.")
        print("Example .env file content:")
        print("LICHESS_API_KEY=your_actual_api_key_here")
        print("or")
        print("LICHESS_API_TOKEN=your_actual_api_key_here")
        print("You can get an API key from: https://lichess.org/account/oauth/token")
        return None
    
    # Mask the API key for security
    masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else "****"
    print(f"Using API key: {masked_key}")
    return api_key

def read_json_games(file_path=None):
    """
    Read games from JSON file or stdin.
    
    Args:
        file_path: Path to JSON file (optional, defaults to stdin)
    
    Returns:
        list: List of PGN strings
    """
    try:
        if file_path:
            with open(file_path, 'r') as f:
                games = json.load(f)
        else:
            # Read from stdin
            games = json.load(sys.stdin)
        
        if not isinstance(games, list):
            print("Error: JSON should contain a list of PGN strings")
            return []
        
        return games
    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        return []
    except Exception as e:
        print(f"Error reading games: {e}")
        return []

def check_analysis_status(game_id, api_key):
    """
    Check the status of computer analysis for a game.
    
    Args:
        game_id: Lichess game ID
        api_key: Lichess API key
    
    Returns:
        dict: Analysis status information
    """
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        # Get game analysis status
        status_url = f"https://lichess.org/api/game/{game_id}/analysis"
        response = requests.get(status_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Status check failed: {response.status_code}"}
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {e}"}

def import_game_to_lichess(pgn_text, api_key):
    """
    Import a single game to Lichess and request computer analysis.
    
    Args:
        pgn_text: PGN string of the game
        api_key: Lichess API key
    
    Returns:
        str: Game URL if successful, None otherwise
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {api_key}"
    }
    body = {"pgn": pgn_text}
    
    try:
        # Step 1: Import the game
        print("  Importing game to Lichess...")
        response = requests.post(LICHESS_API_URL, headers=headers, data=body, timeout=30)
        
        if response.status_code == 200:
            game_url = response.text.strip()
            game_id = game_url.split('/')[-1]  # Extract game ID from URL
            
            # Step 2: Request computer analysis
            print("  Requesting computer analysis...")
            analysis_url = f"https://lichess.org/api/game/{game_id}/request-analysis"
            analysis_response = requests.post(analysis_url, headers=headers, timeout=30)
            
            if analysis_response.status_code == 200:
                print("  ✅ Computer analysis requested successfully!")
                print(f"  📊 Analysis will be available at: {game_url}")
                print("  ⏳ Analysis typically takes 1-5 minutes to complete...")
                return game_url
            else:
                print(f"  ⚠️  Game imported but analysis request failed: {analysis_response.status_code}")
                print(f"     You can manually request analysis at: {game_url}")
                return game_url
        else:
            print(f"Error importing game: {response.status_code} - {response.text}")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None

def extract_game_info(pgn_text):
    """
    Extract basic game information from PGN text.
    
    Args:
        pgn_text: PGN string of the game
    
    Returns:
        str: Formatted game info string
    """
    pgn_lines = pgn_text.split('\n')
    game_info = {}
    
    for line in pgn_lines:
        if line.startswith('[') and ']' in line:
            try:
                key, value = line[1:-1].split(' "', 1)
                game_info[key] = value[:-1]  # Remove closing quote
            except:
                continue
    
    white_player = game_info.get('White', 'Unknown')
    black_player = game_info.get('Black', 'Unknown')
    result = game_info.get('Result', 'Unknown')
    
    return f"{white_player} vs {black_player} - {result}"

def analyze_games(games, api_key, start_index=0, end_index=None):
    """
    Import multiple games to Lichess.
    
    Args:
        games: List of PGN strings
        api_key: Lichess API key
        start_index: Starting index (0-based)
        end_index: Ending index (exclusive, None for all)
    """
    if not games:
        print("No games to analyze")
        return
    
    if end_index is None:
        end_index = len(games)
    
    total_games = end_index - start_index
    print(f"Importing {total_games} games to Lichess (index {start_index} to {end_index-1})")
    
    successful_imports = 0
    failed_imports = 0
    
    for i in range(start_index, end_index):
        if i >= len(games):
            break
        
        print(f"\nProcessing game {i+1}/{len(games)}...")
        
        # Extract basic game info from PGN
        pgn_lines = games[i].split('\n')
        game_info = {}
        for line in pgn_lines:
            if line.startswith('[') and ']' in line:
                try:
                    key, value = line[1:-1].split(' "', 1)
                    game_info[key] = value[:-1]  # Remove closing quote
                except:
                    continue
        
        white_player = game_info.get('White', 'Unknown')
        black_player = game_info.get('Black', 'Unknown')
        result = game_info.get('Result', 'Unknown')
        
        print(f"Game: {white_player} vs {black_player} - {result}")
        
        # Import to Lichess
        game_url = import_game_to_lichess(games[i], api_key)
        
        if game_url:
            print(f"✅ Successfully imported! View at: {game_url}")
            successful_imports += 1
        else:
            print("❌ Failed to import")
            failed_imports += 1
    
    print(f"\n📊 Summary:")
    print(f"   Successful imports: {successful_imports}")
    print(f"   Failed imports: {failed_imports}")
    print(f"   Total processed: {successful_imports + failed_imports}")

def main():
    parser = argparse.ArgumentParser(description="Import chess games to Lichess with computer analysis")
    parser.add_argument("--file", "-f", help="JSON file containing PGN data (reads from stdin if not specified)")
    parser.add_argument("--start", "-s", type=int, default=0, help="Starting game index (default: 0)")
    parser.add_argument("--end", "-e", type=int, help="Ending game index (exclusive, default: all games)")
    parser.add_argument("--check-status", "-c", help="Check analysis status for a specific game ID")
    parser.add_argument("--api-key", help="Lichess API key (overrides .env file)")
    
    args = parser.parse_args()
    
    # Load API key
    api_key = args.api_key
    if not api_key:
        load_dotenv()
        api_key = os.getenv('LICHESS_API_KEY') or os.getenv('LICHESS_API_TOKEN')
    
    if not api_key:
        print("❌ Error: No API key found!")
        print("Please set LICHESS_API_KEY or LICHESS_API_TOKEN in your .env file")
        print("Or provide it with --api-key argument")
        return
    
    # Check analysis status for a specific game
    if args.check_status:
        print(f"Checking analysis status for game: {args.check_status}")
        status = check_analysis_status(args.check_status, api_key)
        if "error" in status:
            print(f"❌ Error: {status['error']}")
        else:
            print("✅ Analysis status:")
            print(json.dumps(status, indent=2))
        return
    
    # Read PGN data
    pgn_data = read_json_games(args.file)
    if not pgn_data:
        print("❌ No PGN data found!")
        return
    
    # Filter games by range
    start_idx = args.start
    end_idx = args.end if args.end is not None else len(pgn_data)
    games_to_process = pgn_data[start_idx:end_idx]
    
    print(f"📊 Processing {len(games_to_process)} games (index {start_idx} to {end_idx-1})")
    print(f"🔑 Using API key: {api_key[:8]}...")
    print()
    
    successful_imports = []
    failed_imports = []
    
    for i, game_data in enumerate(games_to_process, start=start_idx):
        pgn_text = game_data.get('pgn', '')
        if not pgn_text:
            print(f"⚠️  Game {i}: No PGN data found, skipping...")
            continue
        
        print(f"🎮 Game {i+1}/{len(games_to_process)} (index {i}):")
        
        # Extract basic game info for display
        game_info = extract_game_info(pgn_text)
        if game_info:
            print(f"  📝 {game_info}")
        
        game_url = import_game_to_lichess(pgn_text, api_key)
        
        if game_url:
            successful_imports.append((i, game_url))
            print(f"  ✅ Success: {game_url}")
        else:
            failed_imports.append(i)
            print(f"  ❌ Failed to import game {i}")
        
        print()  # Empty line between games
        
        # Small delay to avoid overwhelming the API
        time.sleep(1)
    
    # Summary
    print("=" * 50)
    print("📋 IMPORT SUMMARY")
    print("=" * 50)
    print(f"✅ Successfully imported: {len(successful_imports)} games")
    print(f"❌ Failed imports: {len(failed_imports)} games")
    
    if successful_imports:
        print("\n🎯 Successfully imported games:")
        for idx, url in successful_imports:
            print(f"  Game {idx}: {url}")
    
    if failed_imports:
        print(f"\n⚠️  Failed games (indices): {failed_imports}")
    
    print(f"\n💡 Tip: Analysis typically takes 1-5 minutes to complete.")
    print(f"   You can check analysis status with: python lichess_analysis.py --check-status <game_id>")

if __name__ == "__main__":
    main()