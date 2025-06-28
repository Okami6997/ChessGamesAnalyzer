# Lichess Analysis Tool

A tool to import chess games from JSON files to Lichess for analysis using their powerful analysis features.

## Features

- **Batch Import**: Import multiple games from JSON files
- **Stdin Support**: Read games from standard input
- **Range Selection**: Import specific games by index
- **Dry Run Mode**: Preview what would be imported
- **Environment Configuration**: Secure API key management
- **Progress Tracking**: See import progress and results

## Setup

### 1. Install Dependencies

```bash
pip install -r ../requirements.txt
```

### 2. Get Lichess API Key

1. Go to [Lichess OAuth Tokens](https://lichess.org/account/oauth/token)
2. Create a new token with appropriate permissions
3. Copy the token

### 3. Configure Environment

Create a `.env` file in the chess directory:

```bash
# Create .env file
echo "LICHESS_API_KEY=your_actual_api_key_here" > .env
```

Replace `your_actual_api_key_here` with your actual Lichess API key.

## Usage

### Basic Usage

```bash
# Import all games from a JSON file
python src/lichess_analysis.py output/chess_games.json

# Import from stdin
cat output/chess_games.json | python src/lichess_analysis.py

# Import specific range of games (0-based indexing)
python src/lichess_analysis.py output/chess_games.json --start 5 --end 10

# Import single game
python src/lichess_analysis.py output/chess_games.json --start 0 --end 1

# Dry run (preview without importing)
python src/lichess_analysis.py output/chess_games.json --dry-run
```

### Command Line Options

- `file`: JSON file containing PGN games (optional, defaults to stdin)
- `--start`: Starting game index (0-based, default: 0)
- `--end`: Ending game index (exclusive, default: all games)
- `--dry-run`: Show what would be imported without actually importing

### Examples

```bash
# Import first 5 games
python src/lichess_analysis.py output/chess_games.json --start 0 --end 5

# Import games 10-20
python src/lichess_analysis.py output/chess_games.json --start 10 --end 20

# Preview what would be imported
python src/lichess_analysis.py output/chess_games.json --dry-run

# Import from pipeline
python src/run_analysis_pipeline.py magnuscarlsen stockfish | python src/lichess_analysis.py
```

## Input Format

The tool expects a JSON file containing a list of PGN strings:

```json
[
    "[Event \"Live Chess\"]\n[Site \"Chess.com\"]\n[Date \"2021.12.02\"]\n[White \"Player1\"]\n[Black \"Player2\"]\n[Result \"1-0\"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 1-0",
    "[Event \"Live Chess\"]\n[Site \"Chess.com\"]\n[Date \"2021.12.02\"]\n[White \"Player3\"]\n[Black \"Player4\"]\n[Result \"0-1\"]\n\n1. d4 d5 2. c4 e6 3. Nc3 Nf6 4. Bg5 Be7 0-1"
]
```

## Output

For each successfully imported game, you'll see:
- Game information (players, result)
- Lichess URL where you can view and analyze the game
- Summary of successful and failed imports

Example output:
```
Processing game 1/10...
Game: Player1 vs Player2 - 1-0
✅ Successfully imported! View at: https://lichess.org/analysis/abc123

Processing game 2/10...
Game: Player3 vs Player4 - 0-1
✅ Successfully imported! View at: https://lichess.org/analysis/def456

📊 Summary:
   Successful imports: 10
   Failed imports: 0
   Total processed: 10
```

## Integration with Analysis Pipeline

You can integrate this tool with your existing chess analysis pipeline:

```bash
# Complete workflow: analyze games and import to Lichess
python src/run_analysis_pipeline.py magnuscarlsen stockfish
python src/lichess_analysis.py output/chess_games.json

# Or pipe directly
python src/run_analysis_pipeline.py magnuscarlsen stockfish | python src/lichess_analysis.py
```

## Error Handling

The tool handles various error conditions:
- Missing or invalid API key
- Network connection issues
- Invalid JSON format
- File not found
- Lichess API errors

## Security

- API keys are stored in `.env` files (not committed to version control)
- `.env` files are automatically ignored by git
- No sensitive data is logged or displayed

## Troubleshooting

### API Key Issues
```
Error: Lichess API key not found!
Please set LICHESS_API_KEY in your .env file or environment variable.
```
**Solution**: Create a `.env` file with your API key

### Network Issues
```
Network error: Connection timeout
```
**Solution**: Check your internet connection and try again

### JSON Format Issues
```
Error: Invalid JSON format
```
**Solution**: Ensure your JSON file contains a valid list of PGN strings

### Rate Limiting
If you encounter rate limiting from Lichess, the tool will show appropriate error messages. Consider importing games in smaller batches. 