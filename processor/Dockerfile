# Base image
FROM python:3.11-slim

# Install curl
RUN apt-get update && apt-get install -y curl

# Set work directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Command to run the processor
CMD ["python", "handler.py"]
