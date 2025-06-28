# Chess Engine Analysis Project

This project provides tools for analyzing chess games using Stockfish and Leela Chess Zero (lc0) engines.

## Features

- Download and setup Stockfish chess engine
- Download and setup Leela Chess Zero (lc0) chess engine
- Docker support with pre-built lc0 from source
- Cross-platform compatibility with separate scripts for different environments
- **Complete analysis pipeline** that automates the entire process from data fetching to analysis

## Quick Start (Docker)

The easiest way to run the complete analysis pipeline:

```bash
# Build the Docker image
docker build -t chess-analysis .

# Run complete analysis pipeline for a user
docker run --rm chess-analysis python src/run_analysis_pipeline.py magnuscarlsen stockfish

# Run with lc0 engine and custom parameters
docker run --rm chess-analysis python src/run_analysis_pipeline.py magnuscarlsen lc0 --depth 15 --workers 2
```

## Environment-Specific Scripts

### Windows Environment (`prepare_engine.py`)
- Downloads pre-built Windows binaries
- Optimized for Windows development
- Downloads Windows-specific engine versions

### Docker Environment (`prepare_engine_docker.py`)
- Uses pre-built lc0 from Docker build process
- Downloads Linux-compatible Stockfish
- Includes engine verification and neural network setup
- Optimized for containerized deployment

### Analysis Pipeline (`run_analysis_pipeline.py`)
- **Complete automation** of the entire analysis process
- Orchestrates all steps: engine setup → archive fetching → game scraping → analysis
- Supports both Stockfish and lc0 engines
- Configurable parameters for each engine type

## Analysis Pipeline

The `run_analysis_pipeline.py` script automates the entire chess analysis process:

### Pipeline Steps:
1. **Engine Setup**: Prepares Stockfish or lc0 engine
2. **Archive Fetching**: Downloads chess.com archives for the specified username
3. **Game Scraping**: Extracts PGN games from the archives
4. **Game Analysis**: Analyzes all games with the chosen engine
5. **Results**: Saves analysis results to CSV file

### Usage Examples:

```bash
# Basic usage with Stockfish
python src/run_analysis_pipeline.py magnuscarlsen stockfish

# Advanced usage with lc0
python src/run_analysis_pipeline.py magnuscarlsen lc0 --depth 15 --workers 2 --timeout 60

# Skip engine setup (if already prepared)
python src/run_analysis_pipeline.py magnuscarlsen stockfish --skip-engine-setup

# Skip archive fetching (if chess_archives.txt exists)
python src/run_analysis_pipeline.py magnuscarlsen stockfish --skip-archives

# Skip game scraping (if chess_games.json exists)
python src/run_analysis_pipeline.py magnuscarlsen stockfish --skip-scraping

# Custom Stockfish parameters
python src/run_analysis_pipeline.py magnuscarlsen stockfish --depth 20 --threads 4 --min-thinking-time 50

# Custom lc0 parameters
python src/run_analysis_pipeline.py magnuscarlsen lc0 --depth 12 --workers 1 --timeout 45
```

### Pipeline Parameters:

#### Stockfish Parameters:
- `--depth`: Analysis depth (default: 15)
- `--threads`: Number of threads (default: 2)
- `--min-thinking-time`: Minimum thinking time in ms (default: 30)

#### lc0 Parameters:
- `--depth`: Analysis depth (default: 10)
- `--workers`: Number of workers (default: 1)
- `--timeout`: Analysis timeout in seconds (default: 30)

#### General Parameters:
- `--no-verify`: Skip engine verification
- `--skip-engine-setup`: Skip engine preparation
- `--skip-archives`: Skip archive fetching
- `--skip-scraping`: Skip game scraping

## Docker Setup

### Building the Docker Image

The Docker image includes a complete build of Leela Chess Zero (lc0) from source, following the official build instructions from the [Leela Chess Zero repository](https://github.com/LeelaChessZero/lc0/blob/master/README.md#building-and-running-lc0).

```bash
# Build the Docker image
docker build -t chess-analysis .

# Run the complete pipeline
docker run --rm chess-analysis python src/run_analysis_pipeline.py magnuscarlsen stockfish

# Run individual steps
docker run --rm chess-analysis python src/prepare_engine_docker.py lc0 --verify
docker run --rm chess-analysis python src/chess_archives.py magnuscarlsen
docker run --rm chess-analysis python src/chess_games_scraper.py chess_archives.txt
docker run --rm chess-analysis python src/analyze_games.py output/chess_games.json --stockfish_path output/stockfish/stockfish
```

### What's Included in the Docker Image

- **Base Image**: `python:3.10-slim`
- **lc0**: Built from source (version v0.31.2) with all optimizations
- **Build Dependencies**: All necessary system libraries for compiling lc0
- **Python Dependencies**: Installed from `requirements.txt`

### Docker Build Process

1. **System Dependencies**: Installs build tools, CMake, Git, and required libraries
2. **lc0 Compilation**: 
   - Clones the lc0 repository
   - Checks out version v0.31.2
   - Builds with Release optimizations
   - Installs system-wide
3. **Python Setup**: Installs Python dependencies
4. **Application**: Copies application code and creates output directories

## Local Development

### Windows Environment

#### Prerequisites

- Python 3.10+
- curl (for downloading engines)
- unzip (for extracting archives)

#### Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the complete pipeline:
   ```bash
   python src/run_analysis_pipeline.py magnuscarlsen stockfish
   ```

3. Or run individual steps:
   ```bash
   # Setup Stockfish engine
   python src/prepare_engine.py stockfish
   
   # Setup lc0 (downloads pre-built binary)
   python src/prepare_engine.py lc0
   ```

### Linux Environment

For Linux development, you can use the Docker script directly:

```bash
# Setup lc0 (requires lc0 to be installed system-wide)
python src/prepare_engine_docker.py lc0

# Setup Stockfish
python src/prepare_engine_docker.py stockfish

# Run complete pipeline
python src/run_analysis_pipeline.py magnuscarlsen stockfish
```

## Usage

### Engine Setup

The project provides environment-specific scripts:

- **Windows**: `prepare_engine.py` - Downloads Windows pre-built binaries
- **Docker**: `prepare_engine_docker.py` - Uses pre-built lc0 and Linux binaries

### Available Commands

#### Windows Environment
```bash
# Setup Stockfish engine
python src/prepare_engine.py stockfish

# Setup Leela Chess Zero engine
python src/prepare_engine.py lc0
```

#### Docker Environment
```bash
# Setup Stockfish engine
python src/prepare_engine_docker.py stockfish

# Setup Leela Chess Zero engine
python src/prepare_engine_docker.py lc0

# Setup with verification
python src/prepare_engine_docker.py lc0 --verify
```

#### Complete Pipeline
```bash
# Run complete analysis pipeline
python src/run_analysis_pipeline.py <username> <engine> [options]
```

## Project Structure

```
chess/
├── Dockerfile                    # Docker configuration with lc0 build
├── .dockerignore                # Docker build optimization
├── requirements.txt             # Python dependencies
├── README.md                   # This file
└── src/
    ├── prepare_engine.py       # Windows environment engine setup
    ├── prepare_engine_docker.py # Docker environment engine setup
    ├── run_analysis_pipeline.py # Complete analysis pipeline orchestrator
    ├── chess_archives.py       # Fetch chess.com archives
    ├── chess_games_scraper.py  # Scrape games from archives
    ├── analyze_games.py        # Stockfish game analysis
    ├── analyze_games_lc0.py    # lc0 game analysis
    └── ...                     # Other analysis scripts
```

## Engine Information

### Leela Chess Zero (lc0)

- **Version**: v0.31.2
- **Build**: From source with Release optimizations (Docker) / Pre-built binary (Windows)
- **Installation**: System-wide in Docker, local binary in development
- **Source**: [GitHub Repository](https://github.com/LeelaChessZero/lc0)

### Stockfish

- **Version**: Latest release
- **Platform**: Windows x86-64 AVX2 (Windows), Linux x86-64 AVX2 (Docker)
- **Source**: [Official Stockfish Releases](https://github.com/official-stockfish/Stockfish/releases)

## Output Files

The pipeline generates several output files:

- `output/chess_archives.txt`: List of chess.com archive URLs
- `output/chess_games.json`: PGN game data extracted from archives
- `output/chess_analysis_stockfish.csv`: Analysis results using Stockfish
- `output/chess_analysis_lc0.csv`: Analysis results using lc0

## Notes

- The Docker build process may take several minutes due to the lc0 compilation
- The resulting image is optimized for production use with all engines pre-installed
- Windows development uses pre-built binaries for faster setup
- The Docker script includes additional features like engine verification and neural network setup
- The analysis pipeline can be run partially by using skip flags for faster iteration 