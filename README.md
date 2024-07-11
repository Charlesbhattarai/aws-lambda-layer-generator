# Python AWS Layer Generator

This script helps you generate an AWS Lambda Layer for different versions of Python using Docker. It automates the process of creating a Docker image, installing the required Python packages, and packaging them into a zip file that can be used as an AWS Lambda Layer.

## Features

- Supports Python versions 3.8, 3.9, 3.10, 3.11, and 3.12.
- Automatically validates the Python version input.
- Ensures the presence of a `requirements.txt` file.
- Creates a Docker image to install Python packages.
- Packages the installed libraries into a zip file.

## Prerequisites

- Docker must be installed and running on your machine.
- A `requirements.txt` file must be present in the same directory as the script.

## Usage

1. **Clone the repository or download the script:**

   ```bash
   git clone <repository-url>
   cd <repository-directory>

2. **Run the script:**

   ```bash
   ./layer.sh
   
3. **Follow the prompts:**

- Enter the desired Python version (e.g., 3.8, 3.9, 3.10, 3.11, 3.12).
- Enter the name for the layer (this will be used as the name of the zip file).

4. **The script will:**

- Validate the Python version.
- Check for the presence of requirements.txt.
- Create a Dockerfile based on the selected Python version.
- Build a Docker image.
- Run a Docker container to install the packages.
- Copy the resulting zip file to the aws-layer directory.
- Clean up the Docker image and container.

**Example**

   ```bash
   $ ./layer.sh
      Python AWS Layer Generator
      
      Enter the Python version (e.g., 3.8, 3.9, 3.10, 3.11, 3.12):
      3.9
      
      Selected Python version: 3.9
      
      Enter the name for the layer (this will be used for the zip file):
      my-python-layer
      
      requirements.txt file found...
      Building Docker image for Python 3.9...
      Running container in background...
      Copying the zip file from the container into aws-layer/...
      Deleting container and image, and cleaning up...
   ```

**License**

This project is licensed under the MIT License. See the LICENSE file for details.

**Author**
Charles Bhattarai

```bash
This README file provides a comprehensive overview of the script, including its features, prerequisites, usage instructions, an example, and licensing information.
```



