# Chess Game Analysis Pipeline

This project provides tools to analyze chess games using either Stockfish or Lc0 engines, with modern move annotation based on win% loss (En Croissant/lichess style).

## Table of Contents
- [Setup](#setup)
- [Stockfish Analysis](#stockfish-analysis)
- [Lc0 Analysis](#lc0-analysis)
- [Troubleshooting](#troubleshooting)
- [Move Annotation System](#move-annotation-system)

---

## Setup

1. **Clone the repository**
   ```sh
   git clone <repo-url>
   cd chess
   ```

2. **Create a virtual environment and install dependencies**
   ```sh
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   pip install -r requirements.txt
   # If using Lc0 weights downloader, also:
   pip install requests beautifulsoup4
   ```

3. **Prepare the engines**
   - To download and unzip Stockfish or Lc0 binaries:
     ```sh
     python src/prepare_engine.py stockfish
     python src/prepare_engine.py lc0
     ```
   - This will place the engine binaries in `output/stockfish/` and `output/lc0/`.

4. **Lc0 Weights**
   - **Manual download required!**
   - Go to [http://training.lczero.org/networks](http://training.lczero.org/networks) or [https://lczero.org/networks/](https://lczero.org/networks/)
   - Download the latest `.pb.gz` weights file (e.g., `network-xxxx.pb.gz`).
   - Place it in `output/lc0/` and rename it to `network.pb.gz`.
   - After unzipping `lc0.zip`, the script will also rename any `.pb.gz` file in that folder to `network.pb.gz` automatically.

---

## Stockfish Analysis

1. **Prepare your input games**
   - Use the provided scraper or your own method to create a JSON file of PGN strings (e.g., `output/chess_games.json`).

2. **Run the analysis**
   ```sh
   python src/analyze_games.py output/chess_games.json --stockfish_path output/stockfish/stockfish-windows-x86-64-avx2.exe
   # Optional: set output file, threads, depth, etc.
   ```
   - Results will be saved to `output/chess_analysis_stockfish.csv` by default.

---

## Lc0 Analysis

1. **Ensure you have a valid Lc0 weights file**
   - See the setup section above.
   - The weights file must be valid and at least 40MB+ in size. If Lc0 reports "error The file seems to be unparseable.", your weights file is invalid or incomplete.

2. **Run the analysis**
   ```sh
   python src/analyze_games_lc0.py output/chess_games.json --lc0_path output/lc0/lc0.exe --weights_path output/lc0/network.pb.gz
   # Optional: set output file, depth, workers, etc.
   ```
   - Results will be saved to `output/chess_analysis_lc0.csv` by default.

---

## Troubleshooting

- **Lc0 "error The file seems to be unparseable."**
  - Your weights file is invalid. Download a new one from [http://training.lczero.org/networks](http://training.lczero.org/networks) or [https://lczero.org/networks/](https://lczero.org/networks/).
  - The file should be at least 40MB+.
  - Place it in `output/lc0/` as `network.pb.gz`.

- **Lc0 hangs or is slow**
  - Try reducing the number of workers (e.g., `--workers 1`).
  - Ensure your GPU drivers and CUDA are up to date if using the GPU version.

- **Stockfish not found**
  - Ensure the path to the Stockfish binary is correct and the file exists.

---

## Move Annotation System

Both Stockfish and Lc0 analysis scripts use a modern annotation system based on win% loss, inspired by [En Croissant](https://encroissant.org/docs/guides/analyze-game) and Lichess:

| Annotation           | Win% Loss Range         |
|---------------------|------------------------|
| **Blunder (??)**    | 20..100 win% loss      |
| **Mistake (?)**     | 10..20 win% loss       |
| **Dubious (?!)**    | 5..10 win% loss        |
| **Neutral**         | <5 win% loss           |

- Win% is calculated from centipawn evaluation using the Lichess formula:
  ```
  Win% = 50 + 50 * (2 / (1 + exp(-0.00368208 * centipawns)) - 1)
  ```
- The annotation is based on the absolute change in win% before and after each move.
- (Brilliant, Good, Interesting, etc. are placeholders for future multipv/sacrifice logic.)

---

## Example Output

The output CSV will contain, for each move:
- Move number, player, SAN, UCI, evaluation before/after, best move, and classification (annotation).

---

## License

MIT 