FROM python:3.12-slim

# Set environment variables
ENV PORT=8022

# Set working directory
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
 && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --upgrade pip

# Install dependencies
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . /app/

# Expose SFTP port
EXPOSE 8022

# Run your main script
CMD ["python", "main.py"]
