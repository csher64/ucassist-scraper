# UCAssist Scraper

This is a webdriver that extracts all service information from ucassist.org.

## How to run

### 1. Create a virtual environment

    python3 -m venv venv

### 2. Activate the virtual environment

On macOS/Linux:

    source venv/bin/activate

On Windows:

    .\venv\Scripts\Activate.ps1

### 3. Install the required packages

    pip install -r requirements.txt

### 4. Run the script

    python3 main.py

The script my take a while to run. Extracted data will be output to `ucassist_data.json`.
