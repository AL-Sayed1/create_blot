# SVG to Blot Converter

This project is a web application that converts SVG files into Blot JavaScript code 😃.

## Features

- Upload SVG files
- Preview the uploaded SVG
- Convert SVG to Blot JavaScript code
- Download the converted JavaScript code
- Download polyline data extracted from the SVG

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/AL-Sayed1/create_blot
    cd create_blot
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Run the Streamlit application:
    ```sh
    streamlit run main.py
    ```

2. Open your web browser and go to the URL provided by Streamlit (usually `http://localhost:8501`).

3. Upload an SVG file using the file uploader.

4. Preview the SVG on the left side of the interface.

5. Download the converted Blot JavaScript code or the polyline data using the download buttons on the right side of the interface.