# Chess Board Visualizer

A comprehensive chess board visualization tool that creates chess board displays with engine evaluation bars and move annotations similar to chess.com style.

## Features

- **Chess Board Visualization**: Beautiful chess board with Unicode piece symbols
- **Engine Evaluation Bar**: Real-time evaluation display with win percentages
- **Move Annotations**: Color-coded move classifications (Brilliant, Good, Mistake, Blunder, etc.)
- **Evaluation Graphs**: Visual representation of evaluation changes throughout the game
- **Interactive Viewer**: Step through moves interactively
- **Move Lists**: Detailed move analysis with annotations
- **Multiple Output Formats**: Save visualizations as high-quality PNG files

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. The visualizer requires these additional packages:
   - `matplotlib` - For creating visualizations
   - `seaborn` - For enhanced plotting styles
   - `chess` - For chess game handling
   - `pandas` - For data manipulation

## Quick Start

### Basic Usage

```python
from chess_games import ChessBoardVisualizer

# Create a visualizer
visualizer = ChessBoardVisualizer()

# Create a basic chess board
fig, board_ax, eval_ax = visualizer.create_board_figure()
visualizer.draw_chess_board(board_ax)
visualizer.draw_evaluation_bar(eval_ax, 0)
plt.show()
```

### Using with Analysis Data

```python
import pandas as pd
from chess_games import ChessBoardVisualizer

# Load your analysis data
analysis_data = pd.read_csv('output/chess_analysis_stockfish.csv')

# Create visualizer
visualizer = ChessBoardVisualizer()

# Create complete game visualization
visualizer.visualize_game(analysis_data)
```

## Command Line Usage

### Basic Visualization

```bash
# Visualize a game from analysis data
python src/chess_games.py output/chess_analysis_stockfish.csv

# Visualize with games file
python src/chess_games.py output/chess_analysis_stockfish.csv --games_file output/chess_games.json

# Visualize specific game
python src/chess_games.py output/chess_analysis_stockfish.csv --games_file output/chess_games.json --game_index 0

# Save visualization to file
python src/chess_games.py output/chess_analysis_stockfish.csv --output my_game.png
```

### Advanced Features

```bash
# Create evaluation graph
python src/chess_games.py output/chess_analysis_stockfish.csv --evaluation_graph

# Interactive game viewer
python src/chess_games.py output/chess_analysis_stockfish.csv --interactive

# Combine multiple features
python src/chess_games.py output/chess_analysis_stockfish.csv --games_file output/chess_games.json --evaluation_graph --output game_analysis.png
```

## Example Script

Run the example script to see the visualizer in action:

```bash
python src/example_visualization.py
```

This will create:
- A basic chess board
- A game visualization with sample data
- An evaluation graph

## Data Format

The visualizer expects analysis data in the following format:

```csv
MoveNumber,Player,SAN,ScoreAfter,Classification,Player1,Player2
1,White,e4,15,Neutral,Player1,Player2
1,Black,e5,0,Neutral,Player1,Player2
2,White,Nf3,25,Neutral,Player1,Player2
2,Black,Nc6,0,Neutral,Player1,Player2
3,White,Bb5,35,Good (!),Player1,Player2
```

### Required Columns:
- `MoveNumber`: Move number in the game
- `Player`: "White" or "Black"
- `SAN`: Standard Algebraic Notation for the move
- `ScoreAfter`: Evaluation after the move (in centipawns)
- `Classification`: Move classification (Neutral, Good (!), Mistake (?), etc.)
- `Player1`: Name of white player
- `Player2`: Name of black player

### Optional Columns:
- `UCI`: UCI notation for the move
- `ScoreBefore`: Evaluation before the move
- `BestMove`: Engine's best move
- `GameID`: Unique game identifier
- `Game_URL`: URL to the game

## Move Classifications

The visualizer supports the following move classifications with color coding:

| Classification | Color | Description |
|----------------|-------|-------------|
| Brilliant (!!) | Gold | Sacrifice that is the only sound move |
| Good (!) | Green | Only sound move that punishes opponent's mistake |
| Interesting (!?) | Orange | Sacrifice that isn't the only sound move |
| Dubious (?!) | Dark Orange | 5-10% win probability loss |
| Mistake (?) | Red | 10-20% win probability loss |
| Blunder (??) | Dark Red | 20-100% win probability loss |
| Neutral | Gray | Standard move |

## Evaluation Bar

The evaluation bar shows:
- **Current evaluation** in centipawns or mate notation
- **Win percentages** for both players
- **Color coding**: Green for white advantage, red for black advantage
- **Mate detection**: Shows "M1", "M2", etc. for mate sequences

## Interactive Viewer

The interactive viewer allows you to:
- Navigate through moves with 'n' (next) and 'p' (previous)
- Jump to specific moves with 'm <move_number>'
- Quit with 'q'
- See real-time board updates and evaluations

## Customization

### Colors and Styling

You can customize the visualizer by modifying the color scheme:

```python
visualizer = ChessBoardVisualizer()

# Custom colors
visualizer.colors['light_square'] = '#F0D9B5'
visualizer.colors['dark_square'] = '#B58863'
visualizer.colors['eval_positive'] = '#4CAF50'
visualizer.colors['eval_negative'] = '#F44336'
```

### Board Size

Adjust the board size and square size:

```python
# Larger board
visualizer = ChessBoardVisualizer(square_size=80)

# Smaller board
visualizer = ChessBoardVisualizer(square_size=40)
```

## Integration with Analysis Pipeline

The visualizer integrates seamlessly with the existing chess analysis pipeline:

1. **Run analysis**: Use the existing analysis scripts to generate CSV files
2. **Visualize results**: Use the visualizer to create beautiful visualizations
3. **Share insights**: Save high-quality images for reports or sharing

### Complete Workflow Example

```bash
# 1. Run complete analysis pipeline
python src/run_analysis_pipeline.py magnuscarlsen stockfish

# 2. Create visualizations
python src/chess_games.py output/chess_analysis_stockfish.csv --games_file output/chess_games.json --evaluation_graph --output magnus_game.png

# 3. View results
# The script will display the visualization and save it to magnus_game.png
```

## Output Files

The visualizer can generate several types of output:

- **Main visualization**: Chess board with evaluation bar
- **Move list**: Detailed move analysis with annotations
- **Evaluation graph**: Line graph showing evaluation changes
- **Interactive session**: Real-time game navigation

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Ensure all required packages are installed
2. **Data format**: Check that your CSV file has the required columns
3. **Display issues**: Some environments may need backend configuration for matplotlib

### Matplotlib Backend Issues

If you encounter display issues, try setting the matplotlib backend:

```python
import matplotlib
matplotlib.use('TkAgg')  # or 'Qt5Agg', 'Agg' for non-interactive
import matplotlib.pyplot as plt
```

## Contributing

To extend the visualizer:

1. **Add new features**: Extend the `ChessBoardVisualizer` class
2. **Custom themes**: Create new color schemes and styles
3. **Additional annotations**: Support for new move classifications
4. **Export formats**: Add support for other image formats

## License

This project is part of the chess analysis toolkit and follows the same licensing terms. 