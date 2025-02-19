# Use a lightweight Python base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the correct port (Fly.io expects 8080)
EXPOSE 8080

# Run the app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
