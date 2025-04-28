FROM python:3.12-slim

# Set environment variables
ENV PORT=21 
ENV UV_LINK_MODE=copy

# Set the working directory in the container
WORKDIR /app

# Upgrade pip to the latest version
RUN pip install --upgrade pip


# Copy the requirements.txt file to the container
COPY requirements.txt /app/

# Install the dependencies from requirements.txt using `uv pip`
RUN uv pip install --system -r requirements.txt

# Copy the rest of your application files into the container
COPY . /app/

# Expose the FTP port (or the port you want to use for your app)
EXPOSE $PORT

# Run the FTP server (replace 'ftp_server.py' with your actual script if needed)
CMD ["python", "main.py"]
