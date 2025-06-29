# create a chess board with the engine eval-bar and the moves with annotations coloring it in the same fashion as chess.com

import chess
import chess.pgn
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
import matplotlib.widgets as widgets
import numpy as np
import seaborn as sns
import argparse
import json
import os
from typing import List, Dict, Tuple, Optional
import io

# Set style for better looking plots
plt.style.use('default')
sns.set_palette("husl")

class ChessBoardVisualizer:
    """
    A class to create chess board visualizations with engine evaluation bars and move annotations
    similar to chess.com style.
    """
    
    def __init__(self, board_size=8, square_size=60):
        """
        Initialize the chess board visualizer.
        
        Args:
            board_size: Size of the chess board (default 8)
            square_size: Size of each square in pixels (default 60)
        """
        self.board_size = board_size
        self.square_size = square_size
        self.total_size = board_size * square_size
        
        # Chess piece Unicode symbols
        self.pieces = {
            'white': {
                'king': '♔', 'queen': '♕', 'rook': '♖', 'bishop': '♗', 'knight': '♘', 'pawn': '♙'
            },
            'black': {
                'king': '♚', 'queen': '♛', 'rook': '♜', 'bishop': '♝', 'knight': '♞', 'pawn': '♟'
            }
        }
        
        # Color scheme similar to chess.com
        self.colors = {
            'light_square': '#F0D9B5',
            'dark_square': '#B58863',
            'highlight': '#7B61FF',
            'last_move': '#F7EC58',
            'check': '#FF6B6B',
            'eval_positive': '#4CAF50',
            'eval_negative': '#F44336',
            'eval_neutral': '#9E9E9E',
            'background': '#1a1a2e',  # Dark blue-black background
            'annotation_colors': {
                'Brilliant (!!)': '#FFD700',
                'Good (!)': '#32CD32',
                'Interesting (!?)': '#FFA500',
                'Dubious (?!)': '#FF8C00',
                'Mistake (?)': '#FF6347',
                'Blunder (??)': '#DC143C',
                'Neutral': '#808080'
            }
        }
    
    def create_board_figure(self, figsize=(16, 12)):
        """
        Create the main figure with chess board and evaluation bar.
        
        Args:
            figsize: Figure size (width, height)
        
        Returns:
            tuple: (figure, axes) for the chess board and evaluation bar
        """
        fig = plt.figure(figsize=figsize)
        fig.patch.set_facecolor(self.colors['background'])
        
        # Create grid layout: chess board on left, evaluation bar on right (very slim)
        gs = fig.add_gridspec(1, 2, width_ratios=[8, 1], wspace=0.1)
        
        # Chess board axis
        board_ax = fig.add_subplot(gs[0, 0])
        board_ax.set_xlim(0, self.total_size)
        board_ax.set_ylim(0, self.total_size)
        board_ax.set_aspect('equal')
        board_ax.axis('off')
        board_ax.set_facecolor(self.colors['background'])
        
        # Evaluation bar axis (very slim)
        eval_ax = fig.add_subplot(gs[0, 1])
        eval_ax.set_xlim(0, 1)
        eval_ax.set_ylim(0, 1)
        eval_ax.axis('off')
        eval_ax.set_facecolor(self.colors['background'])
        
        return fig, board_ax, eval_ax
    
    def draw_chess_board(self, board_ax, board_state=None, last_move=None, check_square=None, move_classification=None, white_player=None, black_player=None):
        """
        Draw the chess board with pieces.
        
        Args:
            board_ax: Matplotlib axis for the chess board
            board_state: chess.Board object or FEN string
            last_move: Tuple of (from_square, to_square) for highlighting
            check_square: Square number if king is in check
            move_classification: Classification of the last move for coloring
            white_player: Name of the white player
            black_player: Name of the black player
        """
        # Create chess board object if needed
        if isinstance(board_state, str):
            board = chess.Board(board_state)
        elif board_state is None:
            board = chess.Board()
        else:
            board = board_state
        
        # Draw squares
        for rank in range(8):
            for file in range(8):
                square = rank * 8 + file
                x = file * self.square_size
                y = (7 - rank) * self.square_size  # Flip for visual representation
                
                # Determine square color
                is_light = (rank + file) % 2 == 0
                color = self.colors['light_square'] if is_light else self.colors['dark_square']
                
                # Highlight last move with classification-based color
                if last_move and square in last_move:
                    if move_classification and move_classification in self.colors['annotation_colors']:
                        # Use classification color for move highlighting
                        color = self.colors['annotation_colors'][move_classification]
                    else:
                        # Use default last move color
                        color = self.colors['last_move']
                
                # Highlight check
                if check_square and square == check_square:
                    color = self.colors['check']
                
                # Draw square
                rect = Rectangle((x, y), self.square_size, self.square_size, 
                               facecolor=color, edgecolor='black', linewidth=1)
                board_ax.add_patch(rect)
                
                # Add piece if present
                piece = board.piece_at(square)
                if piece:
                    piece_symbol = self._get_piece_symbol(piece)
                    piece_color = 'white' if piece.color else 'black'
                    
                    # Position text in center of square
                    text_x = x + self.square_size / 2
                    text_y = y + self.square_size / 2
                    
                    # Add solid piece (no shadow effect)
                    board_ax.text(text_x, text_y, piece_symbol, 
                                fontsize=self.square_size // 2, 
                                color='white' if piece_color == 'white' else 'black', 
                                ha='center', va='center', weight='bold')
        
        # Add coordinates
        for i in range(8):
            # File labels (a-h)
            board_ax.text(i * self.square_size + self.square_size / 2, -10, 
                         chr(97 + i), ha='center', va='center', fontsize=12, weight='bold', color='white')
            # Rank labels (1-8)
            board_ax.text(-10, i * self.square_size + self.square_size / 2, 
                         str(8 - i), ha='center', va='center', fontsize=12, weight='bold', color='white')
        
        # Add player names
        if white_player:
            # White player name at top left
            board_ax.text(-30, self.total_size + 10, f"White: {white_player}", 
                         ha='right', va='bottom', fontsize=14, weight='bold', color='white')
        
        if black_player:
            # Black player name at bottom left
            board_ax.text(-30, -10, f"Black: {black_player}", 
                         ha='right', va='top', fontsize=14, weight='bold', color='white')
    
    def _get_piece_symbol(self, piece):
        """Get Unicode symbol for a chess piece."""
        piece_type = piece.piece_type
        color = 'white' if piece.color else 'black'
        
        piece_names = {
            chess.PAWN: 'pawn',
            chess.KNIGHT: 'knight',
            chess.BISHOP: 'bishop',
            chess.ROOK: 'rook',
            chess.QUEEN: 'queen',
            chess.KING: 'king'
        }
        
        return self.pieces[color][piece_names[piece_type]]
    
    def draw_evaluation_bar(self, eval_ax, evaluation, max_eval=1000):
        """
        Draw the evaluation bar similar to chess.com.
        
        Args:
            eval_ax: Matplotlib axis for the evaluation bar
            evaluation: Evaluation in centipawns (positive = white advantage)
            max_eval: Maximum evaluation to display (default 1000 centipawns)
        """
        # Convert centipawns to win percentage using Lichess formula
        def centipawns_to_win_percent(cp):
            return 50 + 50 * (2 / (1 + np.exp(-0.00368208 * cp)) - 1)
        
        win_percent = centipawns_to_win_percent(evaluation)
        
        # Draw background
        eval_ax.add_patch(Rectangle((0, 0), 1, 1, facecolor='white', edgecolor='black'))
        
        # Determine evaluation color
        if evaluation > 50:
            color = self.colors['eval_positive']
        elif evaluation < -50:
            color = self.colors['eval_negative']
        else:
            color = self.colors['eval_neutral']
        
        # Draw evaluation indicator
        if evaluation > 0:
            # White advantage - fill from bottom
            height = win_percent / 100
            eval_ax.add_patch(Rectangle((0, 0), 1, height, facecolor=color, alpha=0.7))
        else:
            # Black advantage - fill from top
            height = (100 - win_percent) / 100
            eval_ax.add_patch(Rectangle((0, 1 - height), 1, height, facecolor=color, alpha=0.7))
        
        # Add center line
        eval_ax.axhline(y=0.5, color='black', linewidth=2, alpha=0.5)
        
        # Add evaluation text
        if abs(evaluation) >= 10000:  # Mate
            if evaluation > 0:
                mate_moves = (evaluation - 10000) // 1000
                text = f"M{mate_moves}" if mate_moves > 0 else "M1"
            else:
                mate_moves = (abs(evaluation) - 10000) // 1000
                text = f"M-{mate_moves}" if mate_moves > 0 else "M-1"
        else:
            text = f"{evaluation/100:+.1f}"
        
        eval_ax.text(0.5, 0.5, text, ha='center', va='center', 
                    fontsize=14, weight='bold', color='black')
        
        # Add win percentage
        eval_ax.text(0.5, 0.1, f"{win_percent:.1f}%", ha='center', va='center', 
                    fontsize=10, color='black')
        eval_ax.text(0.5, 0.9, f"{100-win_percent:.1f}%", ha='center', va='center', 
                    fontsize=10, color='black')
    
    def create_move_list(self, moves_data, current_move=None, figsize=(8, 10)):
        """
        Create a move list with annotations similar to chess.com.
        
        Args:
            moves_data: List of move dictionaries with analysis data
            current_move: Current move number to highlight
            figsize: Figure size for move list
        
        Returns:
            matplotlib.figure.Figure: Figure with move list
        """
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Title
        ax.text(0.5, 0.95, "Move Analysis", ha='center', va='center', 
               fontsize=16, weight='bold')
        
        # Header
        ax.text(0.1, 0.9, "Move", ha='left', va='center', fontsize=12, weight='bold')
        ax.text(0.3, 0.9, "Evaluation", ha='left', va='center', fontsize=12, weight='bold')
        ax.text(0.6, 0.9, "Classification", ha='left', va='center', fontsize=12, weight='bold')
        
        # Draw moves
        y_pos = 0.85
        for i, move_data in enumerate(moves_data):
            # Highlight current move
            bg_color = 'lightblue' if i == current_move else 'white'
            ax.add_patch(Rectangle((0.05, y_pos - 0.02), 0.9, 0.04, 
                                 facecolor=bg_color, alpha=0.3))
            
            # Move number and SAN
            move_text = f"{move_data['MoveNumber']}. {move_data['SAN']}"
            ax.text(0.1, y_pos, move_text, ha='left', va='center', fontsize=11)
            
            # Evaluation
            eval_text = f"{move_data['ScoreAfter']/100:+.1f}"
            ax.text(0.3, y_pos, eval_text, ha='left', va='center', fontsize=11)
            
            # Classification with color
            classification = move_data['Classification']
            color = self.colors['annotation_colors'].get(classification, '#808080')
            ax.text(0.6, y_pos, classification, ha='left', va='center', 
                   fontsize=11, color=color, weight='bold')
            
            y_pos -= 0.05
            
            # Add separator line
            if i < len(moves_data) - 1:
                ax.axhline(y=y_pos + 0.025, color='gray', alpha=0.3, linewidth=0.5)
        
        return fig
    
    def visualize_game(self, analysis_data, game_pgn=None, output_file=None):
        """
        Create a complete game visualization with board, evaluation bar, and move list.
        
        Args:
            analysis_data: DataFrame with move analysis data
            game_pgn: PGN string of the game (optional)
            output_file: Path to save the visualization (optional)
        """
        if game_pgn:
            game = chess.pgn.read_game(io.StringIO(game_pgn))
            board = game.board()
        else:
            board = chess.Board()
        
        # Create main figure
        fig, board_ax, eval_ax = self.create_board_figure(figsize=(16, 10))
        
        # Get current position evaluation
        current_eval = analysis_data.iloc[-1]['ScoreAfter'] if not analysis_data.empty else 0
        
        # Draw board and evaluation bar
        self.draw_chess_board(board_ax, board)
        self.draw_evaluation_bar(eval_ax, current_eval)
        
        # Add title
        if not analysis_data.empty:
            white_player = analysis_data.iloc[0]['Player1']
            black_player = analysis_data.iloc[0]['Player2']
            title = f"{white_player} vs {black_player}"
            fig.suptitle(title, fontsize=16, weight='bold')
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Game visualization saved to {output_file}")
        
        plt.show()
        
        # Create move list
        if not analysis_data.empty:
            move_list_fig = self.create_move_list(analysis_data.to_dict('records'))
            if output_file:
                move_list_path = output_file.replace('.png', '_moves.png')
                move_list_fig.savefig(move_list_path, dpi=300, bbox_inches='tight')
                print(f"Move list saved to {move_list_path}")
            move_list_fig.show()
    
    def create_evaluation_graph(self, analysis_data, output_file=None):
        """
        Create an evaluation graph showing how the evaluation changed throughout the game.
        
        Args:
            analysis_data: DataFrame with move analysis data
            output_file: Path to save the graph (optional)
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Prepare data
        move_numbers = analysis_data['MoveNumber'].tolist()
        evaluations = analysis_data['ScoreAfter'].tolist()
        classifications = analysis_data['Classification'].tolist()
        
        # Convert to centipawns
        evaluations_cp = [eval_val / 100 for eval_val in evaluations]
        
        # Create the evaluation line
        ax.plot(move_numbers, evaluations_cp, 'b-', linewidth=2, alpha=0.7)
        
        # Add scatter points with colors based on classification
        for i, (move_num, eval_val, classification) in enumerate(zip(move_numbers, evaluations_cp, classifications)):
            color = self.colors['annotation_colors'].get(classification, '#808080')
            ax.scatter(move_num, eval_val, c=color, s=50, alpha=0.8, edgecolors='black', linewidth=1)
        
        # Add horizontal line at 0
        ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Labels and title
        ax.set_xlabel('Move Number')
        ax.set_ylabel('Evaluation (centipawns)')
        ax.set_title('Game Evaluation Over Time')
        
        # Add legend for classifications
        legend_elements = []
        for classification, color in self.colors['annotation_colors'].items():
            if classification in classifications:
                legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                                markerfacecolor=color, markersize=8, 
                                                label=classification))
        
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper right')
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Evaluation graph saved to {output_file}")
        
        plt.show()
    
    def interactive_game_viewer(self, analysis_data, game_pgn=None):
        """
        Create an interactive game viewer with GUI buttons.
        
        Args:
            analysis_data: DataFrame with move analysis data
            game_pgn: PGN string of the game (optional)
        """
        if game_pgn:
            game = chess.pgn.read_game(io.StringIO(game_pgn))
            board = game.board()
            moves = list(game.mainline_moves())
        else:
            board = chess.Board()
            moves = []
        
        # If no moves from PGN, try to extract moves from analysis data
        if not moves and not analysis_data.empty and 'SAN' in analysis_data.columns:
            print("No PGN data provided, but analysis data found. Creating moves from analysis...")
            # We'll create a simple board progression based on analysis data
            moves = []
            current_board = chess.Board()
            
            for _, row in analysis_data.iterrows():
                try:
                    # Try to parse the SAN move
                    san_move = row['SAN']
                    move = current_board.parse_san(san_move)
                    moves.append(move)
                    current_board.push(move)
                except Exception as e:
                    print(f"Warning: Could not parse move {san_move}: {e}")
                    break
        
        print(f"Interactive Game Viewer - Total moves: {len(moves)}")
        
        # Create the main figure with extra space for buttons
        fig = plt.figure(figsize=(18, 14))
        fig.patch.set_facecolor(self.colors['background'])
        
        # Create grid layout with space for buttons at bottom
        gs = fig.add_gridspec(2, 2, height_ratios=[8, 1], width_ratios=[8, 1], hspace=0.1, wspace=0.1)
        
        # Chess board axis
        board_ax = fig.add_subplot(gs[0, 0])
        board_ax.set_xlim(0, self.total_size)
        board_ax.set_ylim(0, self.total_size)
        board_ax.set_aspect('equal')
        board_ax.axis('off')
        board_ax.set_facecolor(self.colors['background'])
        
        # Evaluation bar axis
        eval_ax = fig.add_subplot(gs[0, 1])
        eval_ax.set_xlim(0, 1)
        eval_ax.set_ylim(0, 1)
        eval_ax.axis('off')
        eval_ax.set_facecolor(self.colors['background'])
        
        # Button area axis (bottom left section)
        button_ax = fig.add_subplot(gs[1, 0])
        button_ax.axis('off')
        button_ax.set_facecolor(self.colors['background'])
        
        # Initialize state
        current_move = 0
        current_board = chess.Board()
        
        # Get player names from analysis data
        white_player = None
        black_player = None
        if not analysis_data.empty:
            if 'Player1' in analysis_data.columns:
                white_player = analysis_data.iloc[0]['Player1']
            if 'Player2' in analysis_data.columns:
                black_player = analysis_data.iloc[0]['Player2']
        
        def update_display():
            """Update the chess board and evaluation display."""
            # Clear previous content
            board_ax.clear()
            eval_ax.clear()
            
            # Reset axes
            board_ax.set_xlim(0, self.total_size)
            board_ax.set_ylim(0, self.total_size)
            board_ax.set_aspect('equal')
            board_ax.axis('off')
            board_ax.set_facecolor(self.colors['background'])
            
            eval_ax.set_xlim(0, 1)
            eval_ax.set_ylim(0, 1)
            eval_ax.axis('off')
            eval_ax.set_facecolor(self.colors['background'])
            
            # Get current evaluation and move info
            analysis_index = current_move - 1
            current_eval = 0
            last_move_squares = None
            move_classification = None
            
            if 0 <= analysis_index < len(analysis_data):
                current_eval = analysis_data.iloc[analysis_index]['ScoreAfter']
                move_classification = analysis_data.iloc[analysis_index]['Classification']
                
                # Get the last move squares for highlighting
                if current_move > 0 and current_move <= len(moves):
                    last_move = moves[current_move - 1]
                    last_move_squares = (last_move.from_square, last_move.to_square)
            
            # Draw board and evaluation
            self.draw_chess_board(board_ax, current_board, last_move=last_move_squares, 
                                move_classification=move_classification, 
                                white_player=white_player, black_player=black_player)
            self.draw_evaluation_bar(eval_ax, current_eval)
            
            # Update title
            if 0 <= analysis_index < len(analysis_data):
                move_info = analysis_data.iloc[analysis_index]
                title = f"Move {current_move}: {move_info['SAN']} - {move_info['Classification']}"
            elif current_move == 0:
                title = "Initial Position"
            else:
                title = f"Move {current_move}"
            
            fig.suptitle(title, fontsize=14, weight='bold', color='white')
            
            # Update button states
            prev_button.active = current_move > 0
            next_button.active = current_move < len(moves)
            
            plt.draw()
        
        def next_move(event):
            """Go to next move."""
            nonlocal current_move
            if current_move < len(moves):
                current_board.push(moves[current_move])
                current_move += 1
                update_display()
        
        def prev_move(event):
            """Go to previous move."""
            nonlocal current_move
            if current_move > 0:
                current_board.pop()
                current_move -= 1
                update_display()
        
        def first_move(event):
            """Go to first move."""
            nonlocal current_move, current_board
            current_board = chess.Board()
            current_move = 0
            update_display()
        
        def last_move(event):
            """Go to last move."""
            nonlocal current_move, current_board
            current_board = chess.Board()
            for i in range(len(moves)):
                current_board.push(moves[i])
            current_move = len(moves)
            update_display()
        
        # Create buttons in the bottom left section using the button_ax
        button_width = 0.18
        button_height = 0.6
        button_y = 0.2
        
        # First move button
        first_button = widgets.Button(
            button_ax.inset_axes([0.05, button_y, button_width, button_height]),
            'First',
            color='lightgray',
            hovercolor='white'
        )
        first_button.on_clicked(first_move)
        
        # Previous button
        prev_button = widgets.Button(
            button_ax.inset_axes([0.25, button_y, button_width, button_height]),
            'Previous',
            color='lightgray',
            hovercolor='white'
        )
        prev_button.on_clicked(prev_move)
        
        # Next button
        next_button = widgets.Button(
            button_ax.inset_axes([0.45, button_y, button_width, button_height]),
            'Next',
            color='lightgray',
            hovercolor='white'
        )
        next_button.on_clicked(next_move)
        
        # Last move button
        last_button = widgets.Button(
            button_ax.inset_axes([0.65, button_y, button_width, button_height]),
            'Last',
            color='lightgray',
            hovercolor='white'
        )
        last_button.on_clicked(last_move)
        
        # Close button
        close_button = widgets.Button(
            button_ax.inset_axes([0.85, button_y, button_width, button_height]),
            'Close',
            color='#ff6b6b',
            hovercolor='#ff5252'
        )
        close_button.on_clicked(lambda event: plt.close())
        
        # Initial display
        update_display()
        
        # Show the interactive window
        plt.show()


def load_analysis_data(file_path):
    """
    Load analysis data from CSV file.
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        pandas.DataFrame: Analysis data
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Analysis file not found: {file_path}")
    
    return pd.read_csv(file_path)


def load_game_pgn(file_path, game_index=0):
    """
    Load a specific game from JSON file.
    
    Args:
        file_path: Path to the JSON file with PGN games
        game_index: Index of the game to load (default 0)
    
    Returns:
        str: PGN string of the game
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Games file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        games = json.load(f)
    
    if game_index >= len(games):
        raise IndexError(f"Game index {game_index} out of range. Total games: {len(games)}")
    
    return games[game_index]


def main():
    """
    Main function to run the chess game visualizer.
    """
    parser = argparse.ArgumentParser(description="Visualize chess games with engine evaluation and annotations.")
    parser.add_argument(
        "analysis_file",
        help="Path to the analysis CSV file"
    )
    parser.add_argument(
        "--games_file",
        help="Path to the games JSON file (optional)"
    )
    parser.add_argument(
        "--game_index",
        type=int,
        default=0,
        help="Index of the game to visualize (default 0)"
    )
    parser.add_argument(
        "--output",
        help="Output file path for visualization (optional)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive game viewer"
    )
    parser.add_argument(
        "--evaluation_graph",
        action="store_true",
        help="Create evaluation graph"
    )
    
    args = parser.parse_args()
    
    try:
        # Load analysis data
        analysis_data = load_analysis_data(args.analysis_file)
        
        # Filter data for specific game if games file is provided
        if args.games_file:
            game_pgn = load_game_pgn(args.games_file, args.game_index)
            # Filter analysis data for this specific game
            if 'GameID' in analysis_data.columns:
                game_id = analysis_data.iloc[args.game_index]['GameID']
                analysis_data = analysis_data[analysis_data['GameID'] == game_id]
        else:
            game_pgn = None
        
        # Create visualizer
        visualizer = ChessBoardVisualizer()
        
        if args.interactive:
            visualizer.interactive_game_viewer(analysis_data, game_pgn)
        else:
            # Create visualization
            visualizer.visualize_game(analysis_data, game_pgn, args.output)
            
            if args.evaluation_graph:
                eval_output = args.output.replace('.png', '_eval.png') if args.output else None
                visualizer.create_evaluation_graph(analysis_data, eval_output)
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
