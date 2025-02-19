# Use a lightweight Python image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only the requirements file first (for Docker caching)
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Flask app folder into the container
COPY flask-docker-app /app/flask-docker-app

# Set the working directory to the Flask app folder
WORKDIR /app/flask-docker-app

# Expose the correct port (Fly.io expects 8080)
EXPOSE 8080

# Run the app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
