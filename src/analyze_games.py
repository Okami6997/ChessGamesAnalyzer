import os
import chess.pgn
import chess
from stockfish import Stockfish
import pandas as pd
import io
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time


class GameAnalyzer:
    """
    A class to analyze chess games using the Stockfish engine.
    """

    def __init__(self, stockfish_path, threads=2, min_thinking_time=30, depth=15):
        """
        Initializes the GameAnalyzer with a path to the Stockfish executable and parameters.
        """
        if not os.path.exists(stockfish_path):
            raise FileNotFoundError(f"Stockfish executable not found at: {stockfish_path}")
        
        self.stockfish = Stockfish(
            path=stockfish_path,
            parameters={"Threads": threads, "Minimum Thinking Time": min_thinking_time},
        )
        self.stockfish.set_depth(depth)

    def evaluate_board(self, board):
        """
        Evaluates the given board position using Stockfish.
        Returns the evaluation in centipawns.
        """
        self.stockfish.set_fen_position(board.fen())
        eval_info = self.stockfish.get_evaluation()
        if eval_info["type"] == "cp":
            return eval_info["value"]
        elif eval_info["type"] == "mate":
            # Assign a large score for mate positions
            return 100000 if eval_info["value"] > 0 else -100000
        return 0

    def analyze_game(self, pgn_io):
        """
        Analyzes a single game from a PGN string IO object.
        """
        game = chess.pgn.read_game(pgn_io)
        if not game:
            return None

        # Extract metadata
        white_name = game.headers.get("White", "Unknown")
        black_name = game.headers.get("Black", "Unknown")
        white_elo = game.headers.get("WhiteElo", "Unknown")
        black_elo = game.headers.get("BlackElo", "Unknown")
        site = game.headers.get("Link", "")
        game_id = None

        if "chess.com" in site:
            game_id = site.rstrip("/").split("/")[-1]
        elif "lichess.org" in site:
            game_id = site.rstrip("/").split("/")[-1]

        board = game.board()
        analysis_data = []

        # Prepare moves for progress bar
        moves = list(game.mainline_moves())
        total_moves = len(moves)
        move_pbar = tqdm(moves, total=total_moves, desc=f"Analyzing game {game_id if game_id else 'Unknown'}", leave=False, unit="moves")

        # Analyze Each Move
        for move in move_pbar:
            score_before = self.evaluate_board(board)
            actual_uci = move.uci()
            self.stockfish.set_fen_position(board.fen())
            best_uci = self.stockfish.get_best_move()
            san = board.san(move)

            board.push(move)
            score_after = self.evaluate_board(board)

            # Calculate win% for before and after using Lichess formula
            # Win% = 50 + 50 * (2 / (1 + exp(-0.00368208 * centipawns)) - 1)
            def win_percent(cp):
                return 50 + 50 * (2 / (1 + pow(2.718281828459045, -0.00368208 * cp)) - 1)

            win_before = win_percent(score_before)
            win_after = win_percent(score_after)
            delta = win_after - win_before
            win_loss = abs(delta)

            # Classification based on En Croissant doc
            # | Annotation           | Requirements                                        |
            # | -------------------- | --------------------------------------------------- |
            # | **Brilliant (!!)**   | sacrifice that is the only sound move               |
            # | **Good (!)**         | only sound move that punishes an opponent's mistake |
            # | **Interesting (!?)** | sacrifice that isn't the only sound move            |
            # | **Dubious (?!)**     | 5..10 win% loss                                     |
            # | **Mistake (?)**      | 10..20 win% loss                                    |
            # | **Blunder (??)**     | 20..100 win% loss                                   |
            annotation = "Neutral"
            if win_loss >= 20:
                annotation = "Blunder (??)"
            elif win_loss >= 10:
                annotation = "Mistake (?)"
            elif win_loss >= 5:
                annotation = "Dubious (?!)"
            else:
                annotation = "Neutral"
            # Placeholders for Brilliant, Good, Interesting (require multipv and sacrifice logic)
            # For now, only use win% loss for annotation
            analysis_data.append(
                {
                    "MoveNumber": board.fullmove_number if board.turn == chess.BLACK else board.fullmove_number -1,
                    "Player": "White" if board.turn == chess.BLACK else "Black",
                    "SAN": san,
                    "UCI": actual_uci,
                    "ScoreBefore": score_before,
                    "ScoreAfter": score_after,
                    "BestMove": best_uci,
                    "Classification": annotation,
                }
            )
            move_pbar.set_postfix({"Last Move": san, "Classification": annotation})
        move_pbar.close()
        print(f'Analysis complete for game {game_id} converting to df')
        # Create DataFrame
        df = pd.DataFrame(analysis_data)
        df["Player1"] = white_name
        df["Player2"] = black_name
        df["Player1Elo"] = white_elo
        df["Player2Elo"] = black_elo
        df["GameID"] = game_id
        df["Game_URL"] = site
        return df

    def process_game_string(self, game_str):
        """
        Wrapper to analyze a game from a string, suitable for multiprocessing.
        """
        return self.analyze_game(io.StringIO(game_str))

    def _wait_for(self, text, timeout=None):
        timeout = timeout or self.timeout
        start = time.time()
        while True:
            line = self.process.stdout.readline()
            print(f"[Lc0 OUT during wait_for]: {line.strip()}")
            if text in line:
                return True
            if time.time() - start > timeout:
                try:
                    err = self.process.stderr.read()
                    print(f"\n[Lc0 STDERR]:\n{err}\n")
                except Exception as e:
                    print(f"\n[Error reading Lc0 STDERR]: {e}\n")
                raise TimeoutError(f"Timeout waiting for '{text}' from Lc0. Last line: {line}")

    def evaluate_fen(self, fen):
        with self.lock:
            self._send('ucinewgame')
            print(f"[DEBUG] Sending FEN to Lc0: {fen}")
            self._send(f'position fen {fen}')
            self._send(f'go depth {self.depth}')
            # ... rest of the code ...


def analyze_game_worker(game_str, stockfish_path, threads, min_thinking_time, depth):
    analyzer = GameAnalyzer(
        stockfish_path=stockfish_path,
        threads=threads,
        min_thinking_time=min_thinking_time,
        depth=depth,
    )
    return analyzer.process_game_string(game_str)


def main():
    """
    Main function to run the chess game analysis.
    """
    parser = argparse.ArgumentParser(description="Analyze chess games from a JSON file.")
    parser.add_argument(
        "input_file",
        default="chess_games.json",
        help="Path to the input JSON file containing PGN game strings."
    )
    parser.add_argument(
        "-o",
        "--output_file",
        default="output/chess_analysis_stockfish.csv",
        help="Path to save the output CSV file.",
    )
    parser.add_argument(
        "--stockfish_path",
        default=r"output\stockfish\stockfish-windows-x86-64-avx2.exe",
        help="Path to the Stockfish executable.",
    )
    parser.add_argument(
        "--threads", type=int, default=2, help="Number of threads for Stockfish engine."
    )
    parser.add_argument(
        "--depth", type=int, default=15, help="Stockfish search depth."
    )
    parser.add_argument(
        "--min_thinking_time",
        type=int,
        default=30,
        help="Minimum thinking time for Stockfish in ms.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=os.cpu_count() or 1,
        help="Number of worker threads for processing games.",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: Input file not found at {args.input_file}")
        return

    with open(args.input_file, "r") as f:
        data = json.load(f)

    if data:
        results = []
        total_games = len(data)
        game_pbar = tqdm(total=total_games, desc="Total Games", unit="games")
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_game = {
                executor.submit(
                    analyze_game_worker,
                    game,
                    args.stockfish_path,
                    args.threads,
                    args.min_thinking_time,
                    args.depth,
                ): game
                for game in data
            }
            print(f"Analyzing {len(data)} games with {args.workers} workers...")
            for future in as_completed(future_to_game):
                try:
                    result_df = future.result()
                    if result_df is not None:
                        results.append(result_df)
                    game_pbar.update(1)
                except Exception as e:
                    game_id = future_to_game[future]
                    print(f"Error processing a game ({game_id[:30]}...): {e}")
                    game_pbar.update(1)
        game_pbar.close()
        if results:
            df = pd.concat(results).reset_index(drop=True)
            df.to_csv(args.output_file, index=False)
            print(f"Analysis complete. Results saved to {args.output_file}")
        else:
            print("No games were successfully analyzed.")

if __name__ == "__main__":
    main()