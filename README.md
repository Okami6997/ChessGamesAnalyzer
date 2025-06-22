# Chess.com Archives Fetcher

A Python script that fetches all available archives for a given chess.com username using the Chess.com API.

## Features

- Fetches all archives for a chess.com username
- Displays archives in a formatted list with dates
- Stores archives in a temporary JSON file
- Handles errors gracefully
- Command-line interface

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the script with a chess.com username as an argument:

```bash
python chess_archives.py <username>
```

### Examples

```bash
# Get archives for Magnus Carlsen
python chess_archives.py magnuscarlsen

# Get archives for Hikaru Nakamura
python chess_archives.py hikaru
```

## Output

The script will display:
- Number of archives found
- Each archive with its date (YYYY-MM format) and URL
- Formatted list for easy reading
- Path to the temporary file where archives are stored

Example output:
```
Fetching archives for chess.com user: magnuscarlsen

Found 45 archives for user 'magnuscarlsen':
--------------------------------------------------
  1. 2024-12: https://api.chess.com/pub/player/magnuscarlsen/games/2024/12
  2. 2024-11: https://api.chess.com/pub/player/magnuscarlsen/games/2024/11
  3. 2024-10: https://api.chess.com/pub/player/magnuscarlsen/games/2024/10
  ...
--------------------------------------------------

Archives saved to temporary file: /tmp/chess_archives_magnuscarlsen_abc123.json
File contains 45 archive URLs in JSON format
```

## Temporary File Storage

The script automatically saves the archives to a temporary JSON file with the following structure:

```json
{
  "username": "magnuscarlsen",
  "archives": [
    "https://api.chess.com/pub/player/magnuscarlsen/games/2024/12",
    "https://api.chess.com/pub/player/magnuscarlsen/games/2024/11",
    ...
  ],
  "total_count": 45
}
```

The temporary file:
- Has a meaningful name: `chess_archives_{username}_{random}.json`
- Is stored in the system's temporary directory
- Contains all archive URLs in JSON format
- Includes metadata (username and total count)

## API Endpoint

This script uses the Chess.com API endpoint:
```
https://api.chess.com/pub/player/{username}/games/archives
```

The API returns data in this format:
```json
{
  "archives": [
    "url1",
    "url2",
    ...
    "urlx"
  ]
}
```

## Error Handling

The script handles various error scenarios:
- Network connection issues
- Invalid JSON responses
- Missing username argument
- Empty username
- API errors

## Requirements

- Python 3.6+
- requests library

## License

This project is open source and available under the MIT License. 