import os
import chess.pgn
import chess
import pandas as pd
import io
import json
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from tqdm import tqdm
import threading
import queue
import time

class PersistentLc0:
    """
    Persistent Lc0 process for a single game. Supports sending FENs and receiving evaluations.
    """
    def __init__(self, lc0_path, weights_path, depth=10, timeout=30):
        self.lc0_path = lc0_path
        self.weights_path = weights_path
        self.depth = depth
        self.timeout = timeout
        self.process = None
        self.lock = threading.Lock()
        self._start_engine()

    def _start_engine(self):
        self.process = subprocess.Popen(
            [self.lc0_path, f'--weights={self.weights_path}'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            bufsize=0
        )
        # UCI handshake
        self._send('uci')
        self._wait_for('uciok')
        self._send('isready')
        self._wait_for('readyok')

    def _send(self, cmd):
        self.process.stdin.write(cmd + '\r\n')
        self.process.stdin.flush()

    def _wait_for(self, text, timeout=None):
        timeout = timeout or self.timeout
        start = time.time()
        while True:
            line = self.process.stdout.readline()
            if text in line:
                return True
            if time.time() - start > timeout:
                err = ""
                try:
                    # Attempt to read from stderr for more context on timeout
                    err = self.process.stderr.read()
                except Exception:
                    pass
                raise TimeoutError(f"Timeout waiting for '{text}' from Lc0. Last line: {line}. Stderr: {err}")

    def evaluate_fen(self, fen):
        with self.lock:
            self._send('ucinewgame')
            if fen == chess.STARTING_FEN:
                self._send('position startpos')
            else:
                self._send(f'position fen {fen}')
            self._send(f'go depth {self.depth}')
            win_prob = draw_prob = loss_prob = nn_eval = None
            start = time.time()
            while True:
                line = self.process.stdout.readline()
                if line.startswith('info'):
                    nn_match = re.search(r'nn eval=([\-\d\.]+)', line)
                    if nn_match:
                        nn_eval = float(nn_match.group(1))
                    wp_match = re.search(r'win=([\d\.]+)', line)
                    dp_match = re.search(r'draw=([\d\.]+)', line)
                    lp_match = re.search(r'loss=([\d\.]+)', line)
                    if wp_match and dp_match and lp_match:
                        win_prob = float(wp_match.group(1))
                        draw_prob = float(dp_match.group(1))
                        loss_prob = float(lp_match.group(1))
                if line.startswith('bestmove'):
                    break
                if time.time() - start > self.timeout:
                    raise TimeoutError(f"Timeout waiting for evaluation from Lc0. Last line: {line}")
            return win_prob, draw_prob, loss_prob, nn_eval

    def quit(self):
        try:
            self._send('quit')
            self.process.terminate()
        except Exception:
            pass

class Lc0Analyzer:
    """
    A class to analyze chess games using a persistent Lc0 engine (GPU-accelerated).
    """
    def __init__(self, lc0_path, weights_path, depth=10, timeout=30):
        if not os.path.exists(lc0_path):
            raise FileNotFoundError(f"Lc0 executable not found at: {lc0_path}")
        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"Lc0 weights file not found at: {weights_path}")
        self.lc0_path = lc0_path
        self.weights_path = weights_path
        self.depth = depth
        self.timeout = timeout

    def analyze_game(self, pgn_io):
        game = chess.pgn.read_game(pgn_io)
        if not game:
            return None
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
        moves = list(game.mainline_moves())
        total_moves = len(moves)
        board = game.board()
        analysis_data = []
        move_pbar = tqdm(
            moves,
            total=total_moves,
            desc=f"Analyzing game {game_id if game_id else 'Unknown'}",
            leave=False,
            unit="moves"
        )
        engine = PersistentLc0(self.lc0_path, self.weights_path, self.depth, self.timeout)
        try:
            prev_win_prob = None
            for move in move_pbar:
                fen_before = board.fen()
                try:
                    win_prob_before, draw_prob_before, loss_prob_before, nn_eval_before = engine.evaluate_fen(fen_before)
                except Exception as e:
                    print(f"[Lc0 ERROR before move {move.uci()}]: {e}")
                    win_prob_before = draw_prob_before = loss_prob_before = nn_eval_before = None
                san = board.san(move)
                uci = move.uci()
                board.push(move)
                fen_after = board.fen()
                try:
                    win_prob_after, draw_prob_after, loss_prob_after, nn_eval_after = engine.evaluate_fen(fen_after)
                except Exception as e:
                    print(f"[Lc0 ERROR after move {move.uci()}]: {e}")
                    win_prob_after = draw_prob_after = loss_prob_after = nn_eval_after = None
                player = "White" if board.turn == chess.BLACK else "Black"
                # Calculate win% loss (delta)
                delta = None
                if win_prob_before is not None and win_prob_after is not None:
                    if player == "White":
                        delta = win_prob_after - win_prob_before
                    else:
                        delta = loss_prob_before - loss_prob_after
                # Classification based on En Croissant doc
                # https://encroissant.org/docs/guides/analyze-game
                # | Annotation           | Requirements                                        |
                # | -------------------- | --------------------------------------------------- |
                # | **Brilliant (!!)**   | sacrifice that is the only sound move               |
                # | **Good (!)**         | only sound move that punishes an opponent's mistake |
                # | **Interesting (!?)** | sacrifice that isn't the only sound move            |
                # | **Dubious (?!)**     | 5..10 win% loss                                     |
                # | **Mistake (?)**      | 10..20 win% loss                                    |
                # | **Blunder (??)**     | 20..100 win% loss                                   |
                # We'll use delta (win% loss) for Dubious, Mistake, Blunder, else Neutral
                annotation = "Neutral"
                win_loss = abs(delta) * 100 if delta is not None else None
                if win_loss is not None:
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
                analysis_data.append({
                    "MoveNumber": board.fullmove_number if board.turn == chess.BLACK else board.fullmove_number - 1,
                    "Player": player,
                    "SAN": san,
                    "UCI": uci,
                    "WinProbBefore": win_prob_before,
                    "DrawProbBefore": draw_prob_before,
                    "LossProbBefore": loss_prob_before,
                    "NNEvalBefore": nn_eval_before,
                    "WinProbAfter": win_prob_after,
                    "DrawProbAfter": draw_prob_after,
                    "LossProbAfter": loss_prob_after,
                    "NNEvalAfter": nn_eval_after,
                    "Classification": annotation,
                })
                move_pbar.set_postfix({"Last Move": san, "Classification": annotation})
            move_pbar.close()
        finally:
            engine.quit()
        df = pd.DataFrame(analysis_data)
        df["Player1"] = white_name
        df["Player2"] = black_name
        df["Player1Elo"] = white_elo
        df["Player2Elo"] = black_elo
        df["GameID"] = game_id
        df["Game_URL"] = site
        return df

    def process_game_string(self, game_str):
        return self.analyze_game(io.StringIO(game_str))

def main():
    parser = argparse.ArgumentParser(description="Analyze chess games from a JSON file using Lc0 (GPU).")
    parser.add_argument(
        "input_file",
        default="chess_games.json",
        help="Path to the input JSON file containing PGN game strings."
    )
    parser.add_argument(
        "-o",
        "--output_file",
        default="output/chess_analysis_lc0.csv",
        help="Path to save the output CSV file.",
    )
    parser.add_argument(
        "--lc0_path",
        default=r"output\lc0\lc0.exe",
        help="Path to the Lc0 executable.",
    )
    parser.add_argument(
        "--weights_path",
        default=r"output\lc0\network.pb.gz",
        help="Path to the Lc0 weights file.",
    )
    parser.add_argument(
        "--depth", type=int, default=10, help="Lc0 search depth."
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=os.cpu_count() or 1,
        help="Number of worker threads for processing games.",
    )
    parser.add_argument(
        "--timeout", type=int, default=30, help="Timeout in seconds for Lc0 engine responses."
    )
    args = parser.parse_args()
    try:
        analyzer = Lc0Analyzer(
            lc0_path=args.lc0_path,
            weights_path=args.weights_path,
            depth=args.depth,
            timeout=args.timeout,
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
            print(f"Analyzing {total_games} games with {args.workers} workers using Lc0...")
            for future in as_completed(future_to_game):
                try:
                    result_df = future.result()
                    if result_df is not None:
                        results.append(result_df)
                    game_pbar.update(1)
                except Exception as e:
                    game_id = future_to_game[future]
                    print(f"Error processing a game ({str(game_id)[:30]}...): {e}")
                    game_pbar.update(1)
        game_pbar.close()
        if results:
            df = pd.concat(results).reset_index(drop=True)
            df.to_csv(args.output_file, index=False)
            print(f"\nAnalysis complete. Results saved to {args.output_file}")
        else:
            print("\nNo games were successfully analyzed.")

if __name__ == "__main__":
    main()

# Instructions:
# - Download Lc0 for your OS and GPU: https://lczero.org/play/download/
# - Set --lc0_path and --weights_path accordingly.
# - This script will use your NVIDIA GPU for chess analysis via Lc0. 