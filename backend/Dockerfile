FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Set environment variable for Python path
ENV PYTHONPATH=/app

# Expose port and start
EXPOSE 8000
CMD ["python", "backend/main.py"]
