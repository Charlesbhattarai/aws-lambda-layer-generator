#!/bin/bash

# Author: Charles Bhattarai
# License: MIT License

echo "Python AWS Layer Generator"
echo
echo "Enter the Python version (e.g., 3.8, 3.9, 3.10, 3.11, 3.12):"

read PYTHON_VERSION

# Validate the Python version
if [[ "$PYTHON_VERSION" =~ ^3\.(8|9|10|11|12)$ ]]; then
  echo "Selected Python version: $PYTHON_VERSION"
else
  echo "Invalid Python version: $PYTHON_VERSION. Must be between 3.8 and 3.12."
  exit 1
fi

echo "Enter the name for the layer (this will be used for the zip file):"
read LAYER_NAME

# Verify the existence of requirements.txt
if [ -f requirements.txt ]; then
  echo "requirements.txt file found..."
else
  echo "ERROR: requirements.txt file not found"
  exit 1
fi

# Check if aws-layer directory exists, if not create it
if [ ! -d aws-layer ]; then
  echo "aws-layer directory not found. Creating aws-layer directory..."
  mkdir aws-layer
fi

# Create Dockerfile dynamically based on the user-selected Python version
cat <<EOF > Dockerfile
# Author: Charles Bhattarai
# License: MIT License

## 1. Load Python $PYTHON_VERSION-slim, a Debian image
FROM python:$PYTHON_VERSION-slim

## 2. Update packages and install zip
RUN apt-get update && apt-get upgrade -y
RUN apt-get install zip -y

## 3. Update pip
RUN pip install --no-cache-dir --upgrade pip

## 4. Create the package directory structure
RUN mkdir -p /python/lib/python$PYTHON_VERSION/site-packages/

## 5. Load and install the packages in requirements.txt
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --no-cache-dir --platform manylinux2014_x86_64 --only-binary=:all: --upgrade -t /python/lib/python$PYTHON_VERSION/site-packages/

## 6. Zip the installed Python libraries
RUN zip -r python-layer-$PYTHON_VERSION.zip /python/*
CMD ["/bin/bash"]
EOF

# Build Docker image
echo "Building Docker image for Python $PYTHON_VERSION..."
docker build -t python-docker-"$PYTHON_VERSION" .

# Run Docker container
echo "Running container in background..."
CONTAINER_ID=$(docker create python-docker-"$PYTHON_VERSION")

# Copy zipped package from Docker container
echo "Copying the zip file from the container into aws-layer/..."
docker cp "$CONTAINER_ID":/python-layer-"$PYTHON_VERSION".zip aws-layer/"$LAYER_NAME".zip

# Clean up
echo "Deleting container and image, and cleaning up..."
docker rm "$CONTAINER_ID"
docker rmi -f python-docker-"$PYTHON_VERSION"
rm Dockerfile
