# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 8000

# Set the health check with an extremely large number of retries
HEALTHCHECK --interval=30s --timeout=5s --retries=300000000 \
    CMD curl --silent --fail http://localhost:8000/health || exit 1

# Run app.py when the container launches
CMD ["python", "app.py"]
