# Parsing Documents

Welcome to the "Parsing Documents" repository. Here, you will find all the necessary files to execute the pipeline designed to extract associated information from text and tables within PDF files.

## Overview

This repository contains scripts and resources for processing PDF documents to retrieve and analyze both text and table data efficiently.

## Getting Started

To get started with the pipeline, follow these steps:

1. **Clone the Repository**
   - Run `git clone https://github.com/yourusername/parsing-documents.git`
   - Navigate to the directory with `cd parsing-documents`

2. **Set Up the Python Environment**
   - Create a Python 3.9 virtual environment: `python3.9 -m venv venv`
   - Activate the environment: `source venv/bin/activate` 

3. **Install Dependencies**
   - Install required packages: `pip install -r requirements.txt`

4. **Run the Pipeline**
   - Execute the pipeline: `python parsing.py --document_path "path/to/your/document.pdf" --save_path "path/to/save/output.json"`

These steps will guide you through setting up the environment, installing dependencies, and running the script to process your PDF files and save the extracted data in JSON format.
