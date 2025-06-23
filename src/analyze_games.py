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

    def classify_move(self, score_before, score_after, actual_move, best_move, board):
        """
        Classifies a move based on the change in evaluation score.
        This is a simplified classification inspired by chess.com's system.
        """
        # The logic is from the perspective of the player who made the move.
        # If it's Black's turn, it means White just moved.
        is_white_move = board.turn == chess.BLACK
        delta = score_after - score_before if is_white_move else score_before - score_after

        if board.fullmove_number <= 10 and actual_move == best_move:
            return "Book"
        if actual_move == best_move:
            if abs(delta) <= 10: # Very small change
                return "Best"
            elif abs(delta) <= 40:
                return "Excellent"
            else: # Best move, but score changed significantly (e.g., opponent's threat was high)
                return "Good"
        
        # Not the best move, so the delta will be negative for the player who moved.
        blunder_threshold = -90
        mistake_threshold = -40

        if delta < blunder_threshold:
            # Check for brilliant move criteria (a good sacrifice)
            # Simple check: was it a bad move that turns out to be winning?
            score_after_player_perspective = score_after if is_white_move else -score_after
            if score_after_player_perspective > 150:
                 return "Brilliant"
            return "Blunder"
        elif delta < mistake_threshold:
            return "Mistake"
        else:
            return "Inaccuracy"

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

            label = self.classify_move(score_before, score_after, actual_uci, best_uci, board)
            analysis_data.append(
                {
                    "MoveNumber": board.fullmove_number if board.turn == chess.BLACK else board.fullmove_number -1,
                    "Player": "White" if board.turn == chess.BLACK else "Black",
                    "SAN": san,
                    "UCI": actual_uci,
                    "ScoreBefore": score_before,
                    "ScoreAfter": score_after,
                    "BestMove": best_uci,
                    "Classification": label,
                }
            )
            move_pbar.set_postfix({"Last Move": san, "Classification": label})
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
        # group by GameID
        df = df.groupby('GameID').mean().reset_index()
        # print(df)
        return df

    def process_game_string(self, game_str):
        """
        Wrapper to analyze a game from a string, suitable for multiprocessing.
        """
        return self.analyze_game(io.StringIO(game_str))


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
        default="output/chess_analysis.csv",
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

    try:
        analyzer = GameAnalyzer(
            stockfish_path=args.stockfish_path,
            threads=args.threads,
            min_thinking_time=args.min_thinking_time,
            depth=args.depth,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

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
                executor.submit(analyzer.process_game_string, game): game
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