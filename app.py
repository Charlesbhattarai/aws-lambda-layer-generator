import io
import os
import re
import subprocess
import zipfile

import requests
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import StreamingResponse

app = FastAPI()


def get_docker_content(python_version, requirements):
    # Convert requirements list to a pip install command in Dockerfile format
    requirements_install = " \\\n    ".join(requirements)

    return f'''
# Author: Charles Bhattarai
# License: MIT License

# 1. Load Python {python_version}-slim, a Debian image
FROM python:{python_version}-slim

# 2. Update packages and install zip
RUN apt-get update && apt-get upgrade -y \\
    && apt-get install -y zip

# 3. Update pip
RUN pip install --no-cache-dir --upgrade pip

# 4. Create the package directory structure
RUN mkdir -p /python/lib/python{python_version}/site-packages/

# 5. Install specified packages
RUN pip install --no-cache-dir {requirements_install} --platform manylinux2014_x86_64 --only-binary=:all: --upgrade -t /python/lib/python{python_version}/site-packages/

# 6. Zip the installed Python libraries
RUN zip -r python-layer-{python_version}.zip /python/*

CMD ["/bin/bash"]
'''


def generate_python_layer(python_version, layer_name, requirements):
    print("Python AWS Layer Generator")
    print()

    print(f"Selected Python version: {python_version}")

    temp_folder = 'aws-layer'

    # Check if temp folder directory exists, if not create it
    if not os.path.exists(temp_folder):
        print(f"{temp_folder} directory not found. Creating {temp_folder} directory...")
        os.mkdir(temp_folder)

    # Create Dockerfile content
    dockerfile_content = get_docker_content(python_version, requirements)

    # Write Dockerfile
    dockerfile_path = os.path.join(temp_folder, 'Dockerfile')
    if not os.path.exists(dockerfile_path):
        # If it doesn't exist, create an empty Dockerfile
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

    # Build Docker image
    print(f"Building Docker image for Python {python_version}...")
    docker_image_name = f"python-docker-{python_version}"
    subprocess.run(['docker', 'build', '-t', docker_image_name, temp_folder], check=True)

    # Run Docker container
    print("Running container in background...")
    container_id = subprocess.check_output(['docker', 'create', docker_image_name]).decode('utf-8').strip()

    # Create in-memory zip file
    zip_data = io.BytesIO()
    zip_file_path = f"{temp_folder}/{layer_name}.zip"
    try:
        # Copy zipped package from Docker container to in-memory zip
        print(f"Copying the zip file from the container into {temp_folder}/...")
        subprocess.run(
            ['docker', 'cp', f"{container_id}:/python-layer-{python_version}.zip", zip_file_path],
            check=True)

        # Add copied zip file into in-memory zip data
        with zipfile.ZipFile(zip_data, 'w') as zf:
            zf.write(zip_file_path, arcname=f"{layer_name}.zip")

    except subprocess.CalledProcessError as e:
        print(f"Error running Docker command: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate Python layer")

    finally:
        # Clean up Docker resources
        print("Deleting container and image, and cleaning up...")
        subprocess.run(['docker', 'rm', container_id])
        subprocess.run(['docker', 'rmi', '-f', docker_image_name])
        os.remove(dockerfile_path)

    zip_data.seek(0)
    return zip_data.getvalue()


def check_package_exists(package_name):
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"An error occurred while checking the package: {e}")
        return False


def validate_requests(python_version, layer_name, requirements):
    is_valid = True
    errors = list()
    pattern = re.compile(r'^[a-zA-Z0-9]{1,16}$')
    if not pattern.match(layer_name):
        errors.append(f"Invalid '{layer_name}' Layer name.")
    for package_name in requirements:
        if pattern.match(package_name):
            if not check_package_exists(package_name):
                is_valid = False
                errors.append(f"Package '{package_name}' does not exist.")
        else:
            is_valid = False
            errors.append(f"Invalid '{package_name}' package name.")

    valid_versions = ["3.8", "3.9", "3.10", "3.11", "3.12"]
    if python_version not in valid_versions:
        is_valid = False
        errors.append(f"Python version '{python_version}' is not supported.")
    return is_valid, errors


@app.post("/generate_layer/")
async def generate_layer(python_version: str = Form(...), layer_name: str = Form(...), requirements: list = Form(...)):
    is_valid, errors = validate_requests(python_version, layer_name, requirements)
    if not is_valid:
        raise HTTPException(status_code=400, detail=errors)

    zip_data = generate_python_layer(python_version, layer_name, requirements)

    return StreamingResponse(iter([zip_data]), media_type='application/zip',
                             headers={'Content-Disposition': f'attachment; filename={layer_name}.zip'})


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app,
                host="127.0.0.1",
                port=int(os.environ.get("PORT", 8000)),
                log_level="debug")
