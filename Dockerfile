# Dockerfile for Spotiplay Flask App
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set workdir
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements/base.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose the port Gunicorn will run on
EXPOSE 5000

# Start Gunicorn server
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:5000", "app:app"]

