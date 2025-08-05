FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/docs

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///./aplicacion.db

# Expose port
EXPOSE 8000

# Create a startup script
RUN echo '#!/bin/bash\n\
echo "Initializing database..."\n\
python init_db.py\n\
echo "Starting FastAPI server..."\n\
uvicorn main:app --host 0.0.0.0 --port 8000 --reload' > /app/start.sh

RUN chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]