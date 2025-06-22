import os
import sys
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# check if chess_archives.txt is present in the output directory
def if_file_present(filename, output_dir):
    return filename in os.listdir(output_dir)

# read the file
def read_file(filename):
    with open(filename, 'r') as f:
        return f.readlines()

# fetches data from the url provided, extracts the pgn and returns the list of pgn values into a list
def fetch_data_from_url(url):
    '''
    Fetches data from the URL, extracts PGNs, and returns a list.
    '''
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        games = data.get("games", [])

        pgns = [game["pgn"] for game in games] if games else []
        return pgns

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON error: {e}")
        return None
    except KeyError as e:
        print(f"Missing key in JSON: {e}")
        return None
    
def fetch_all_pgns(urls):
    all_pgns = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_data_from_url, url): url for url in urls}

        for future in as_completed(futures):
            url = futures[future]
            try:
                result = future.result()
                if result:
                    all_pgns.extend(result)
            except Exception as e:
                print(f"Error processing {url}: {e}")
    return all_pgns
    
def main(args):
    print(args[1])
    filename = str(args[1])
    contents = []
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    if (if_file_present(filename, output_dir)):
        f = os.path.join(output_dir, filename)
        contents = read_file(f)
        # read_file adds '%0A' this character to the end of each line, so we need to ommit it for each item in the contents list
        contents = [line.strip() for line in contents]
    print(if_file_present(filename, output_dir))
    pgns = fetch_all_pgns(contents)
    if not pgns:
        print("No games found.")
        sys.exit(1)
    output_file = os.path.join(output_dir, 'chess_games.json')
    with open(output_file, 'w', encoding= 'UTF-8') as f:
        json_string = json.dumps(pgns, indent=4)
        f.write(json_string)
        print("Successfully wrote the data to chess_games.json")
if __name__ == '__main__':
    main(sys.argv)