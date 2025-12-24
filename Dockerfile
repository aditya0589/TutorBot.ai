# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (needed for mysqlclient/pymysql if compiling)
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY src/requirements.txt ./requirements.txt

# Install any needed packages specified in requirements.txt
# Adding gunicorn for production server
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

# Copy the current directory contents into the container at /app
COPY src/ ./src/
# COPY .env . (Not needed in production, use Environment Variables)
COPY isrgrootx1.pem .

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=src/app.py

# Run gunicorn when the container launches
# Workers = 2 * cores + 1 is a good rule of thumb
CMD ["gunicorn", "--chdir", "src", "--bind", "0.0.0.0:5000", "app:app", "--workers", "3"]
