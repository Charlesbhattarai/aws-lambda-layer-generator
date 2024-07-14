import json
import os
import shutil
from http.client import HTTPException

import requests
import streamlit as st
from requests.exceptions import RequestException, HTTPError

# FastAPI server URL
FASTAPI_URL = "http://localhost:8000"


def save_and_download_file(filename, layer_name):
    # Save the zip file locally
    temp_dir = 'aws-layer'
    os.makedirs(temp_dir, exist_ok=True)

    zip_file_path = os.path.join(temp_dir, filename)

    st.success(f"Python layer '{layer_name}' generated successfully.")
    st.info(f"Downloading {filename}...")

    # Send the file to the user for download
    with open(zip_file_path, 'rb') as f:
        st.download_button(label="Click here to download", data=f.read(), file_name=filename)

    # Clean up temp directory
    shutil.rmtree(temp_dir)


def generate_layer(python_version, layer_name, requirements):
    endpoint = f"{FASTAPI_URL}/generate_layer/"
    data = {
        "python_version": python_version,
        "layer_name": layer_name,
        "requirements": requirements
    }

    try:
        response = requests.post(endpoint, data=data, stream=True)

        if response.status_code == 200:
            # Get content disposition header to extract filename
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            else:
                filename = f"{layer_name}.zip"

            save_and_download_file(filename, layer_name)
        else:
            errors = json.loads(response.text).get('detail')
            error_message = "\n".join([f"{i + 1}. {error}" for i, error in enumerate(errors)])
            st.error(f"Failed to generate Python layer. Server returned status code 400.\n\nCaused by:\n{error_message}")

    except HTTPError as http_err:
        raise HTTPException(f"Invalid HTTP error occurred: {http_err}")
    except RequestException as req_err:
        raise RequestException(f"Request Error: {req_err}")
    except Exception as e:
        raise Exception(f"Error: {e}")


def main():
    st.title("Python AWS Layer Generator")

    python_versions = ["Select", "3.8", "3.9", "3.10", "3.11", "3.12"]
    python_version = st.selectbox("Select Python Version:", python_versions)

    layer_name = st.text_input("Enter Layer Name:")
    requirements = st.text_area("Enter Requirements (one per line):")

    if st.button("Generate Python Layer"):
        if python_version and layer_name and requirements:
            requirements_list = requirements.splitlines()
            try:
                generate_layer(python_version, layer_name, requirements_list)
            except HTTPException as e:
                st.error(f"HTTP Error: {e}")
            except RequestException as e:
                st.error(f"Request Error: {e}")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Please enter Python version, layer name, and requirements.")


if __name__ == "__main__":
    main()
