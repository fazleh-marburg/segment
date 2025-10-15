# Use an official PyTorch base image with CUDA
FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn8-runtime

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy and NLTK models
RUN python -m spacy download en_core_web_sm && \
    python -m nltk.downloader stopwords

# Copy your code into the container
COPY . .

# Default command to run your script
CMD ["python", "main.py"]

