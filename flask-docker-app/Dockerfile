# Use a lightweight Python image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files into the container
COPY . /app

# Expose the port Flask runs on
EXPOSE 5000

# Ensure the SQLite database is created
RUN mkdir -p /app/instance

# Command to start the Flask app using Gunicorn for production
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
