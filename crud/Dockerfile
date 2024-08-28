# Base image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 8005

# Command to run the FastAPI app using uvicorn
CMD ["uvicorn", "handler:app", "--host", "0.0.0.0", "--port", "8005"]
