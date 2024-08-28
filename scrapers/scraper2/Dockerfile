FROM selenium/standalone-chrome:latest

# Switch to root user to install packages
USER root

# Install Python and necessary packages
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get update --allow-releaseinfo-change && \
    apt-get install -y python3 python3-pip python3-venv build-essential && \
    python3 -m venv /opt/venv

# Set environment variables for Python
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the scraper script
COPY handler.py /app/handler.py

# Set the working directory
WORKDIR /app

# Run the scraper
CMD ["python3", "handler.py"]
