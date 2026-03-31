# Use an official Python runtime as a parent image
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and their system dependencies
RUN playwright install chromium
RUN playwright install-deps chromium

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run main.py when the container launches
# Note: Since the code is now at the root of the repo, we use 'main:app'
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
