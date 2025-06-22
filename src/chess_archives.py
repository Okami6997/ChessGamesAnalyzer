#!/usr/bin/env python3
"""
Chess.com Archives Fetcher

This script fetches all available archives for a given chess.com username
using the Chess.com API: https://api.chess.com/pub/player/{username}/games/archives

Usage:
    python chess_archives.py <username>
    
Example:
    python chess_archives.py magnuscarlsen
"""

import requests
import sys
import json
import os
from typing import List, Optional


def get_chess_archives(username: str) -> Optional[List[str]]:
    """
    Fetch all archives for a given chess.com username.
    
    Args:
        username (str): The chess.com username to fetch archives for
        
    Returns:
        Optional[List[str]]: List of archive URLs if successful, None if failed
    """
    # Construct the API URL
    api_url = f"https://api.chess.com/pub/player/{username}/games/archives"
    
    # Headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        # Make the API request with proper headers
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the JSON response
        data = response.json()
        
        # Extract the archives from the response
        # Response format: {"archives": ["url1", "url2", ...]}
        archives = data.get('archives', [])
        
        return archives
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status code: {e.response.status_code}")
            print(f"Response headers: {dict(e.response.headers)}")
            try:
                print(f"Response body: {e.response.text}")
            except:
                pass
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return None
    except KeyError as e:
        print(f"Unexpected response format: {e}")
        return None


def save_archives_to_local_file(archives: List[str]) -> str:
    """
    Save the archives to a local file in the script's directory.
    
    Args:
        archives (List[str]): List of archive URLs        
    Returns:
        str: Path to the local file
    """
    # Get the output directory
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    
    # Create filename with timestamp to avoid overwriting
    filename = f"chess_archives.txt"
    
    # Create the full file path
    file_path = os.path.join(output_dir, filename)
    print(file_path)
    
    # Write the data to the local file
    with open(file_path, 'w', encoding='utf-8') as f:
        for archive in archives:
            f.write(archive + "\n")
    
    return file_path


def display_archives(archives: List[str], username: str) -> None:
    """
    Display the archives in a formatted way.
    
    Args:
        archives (List[str]): List of archive URLs
        username (str): The username these archives belong to
    """
    if not archives:
        print(f"No archives found for user '{username}'")
        return
    
    print(f"\nFound {len(archives)} archives for user '{username}':")
    print("-" * 50)
    
    for i, archive_url in enumerate(archives, 1):
        # Extract the date from the URL (format: https://api.chess.com/pub/player/username/games/YYYY/MM)
        try:
            date_part = archive_url.split('/')[-2:]  # Get YYYY and MM
            year, month = date_part
            print(f"{i:3d}. {year}-{month}: {archive_url}")
        except (IndexError, ValueError):
            print(f"{i:3d}. {archive_url}")
    
    print("-" * 50)


def main():
    """Main function to handle command line arguments and execute the script."""
    # Check if username is provided as command line argument
    if len(sys.argv) != 2:
        print("Usage: python chess_archives.py <username>")
        print("Example: python chess_archives.py magnuscarlsen")
        sys.exit(1)
    
    username = sys.argv[1].strip()
    
    if not username:
        print("Error: Username cannot be empty")
        sys.exit(1)
    
    print(f"Fetching archives for chess.com user: {username}")
    
    # Get the archives
    archives = get_chess_archives(username)
    
    if archives is None:
        print(f"Failed to fetch archives for user '{username}'")
        sys.exit(1)
    
    # Display the results
    display_archives(archives, username)

    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    print(output_dir)
    if os.path.exists(output_dir):
        os.rmdir(output_dir)
    os.mkdir(output_dir)
    
    # Save to local file
    if archives:
        file_path = save_archives_to_local_file(archives)
        print(f"\nArchives saved to local file: {file_path}")
        print(f"File contains {len(archives)} archive URLs in JSON format")


if __name__ == "__main__":
    main() 