FROM python:3.10-slim

# Install system dependencies for building lc0
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    unzip \
    libopenblas-dev \
    liblapack-dev \
    libeigen3-dev \
    zlib1g-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone and build lc0 from source
RUN cd /tmp && \
    git clone https://github.com/LeelaChessZero/lc0.git && \
    cd lc0 && \
    git checkout v0.31.2 && \
    mkdir build && \
    cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    make -j$(nproc) && \
    make install && \
    cd / && \
    rm -rf /tmp/lc0

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p output/stockfish output/lc0

# Set the default command to run the analysis pipeline
# Usage: docker run --rm chess-analysis python src/run_analysis_pipeline.py <username> <engine>
# Examples:
#   docker run --rm chess-analysis python src/run_analysis_pipeline.py magnuscarlsen stockfish
#   docker run --rm chess-analysis python src/run_analysis_pipeline.py magnuscarlsen lc0 --depth 15
CMD ["python", "-u", "src/run_analysis_pipeline.py"] 

