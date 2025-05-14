FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Install Poetry
RUN pip install poetry


# Copy project files
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main
# Force Poetry to use CPU-only PyTorch and sentence-transformers
RUN poetry run pip install torch==2.2.2+cpu torchvision==0.17.2+cpu torchaudio==2.2.2+cpu --index-url https://download.pytorch.org/whl/cpu
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Start FastAPI server
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]