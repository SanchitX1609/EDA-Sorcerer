
# Automated EDA Agent

## Overview

This project involves the creation of an Automated Exploratory Data Analysis (EDA) Agent, which uses a combination of advanced tools and techniques to generate detailed insights and recommendations from a dataset.

## Components

### 1. Automated EDA Agent

- **Input**: The input dataset is provided as a CSV file.
- **Process**:
  1. **Profile Report Generation**: Uses the `ydata-profiling` library to generate a detailed profile report of the dataset, saved as an HTML file.
  2. **SVG Extraction and Conversion**: Parses the HTML file to find SVG elements, converts them to PNG images using `cairosvg`, and saves the images.
  3. **Image Analysis**: A ChatGPT-based component analyzes the images and returns a JSON dictionary detailing the chart type, axis ranges, and descriptions.
  4. **Summary and Recommendations**: Combines the image descriptions with statistics from the profile report to summarize the information and recommend actions based on the insights.

### 2. Critique Agent

- **Function**: Critiques the insights generated by the Data Insight Agent, ensuring the insights are accurate and providing additional perspectives.

## Installation

To install the necessary dependencies, use the `requirements.txt` file provided:

```bash
pip install -r requirements.txt
```

## Dependencies

- `ydata-profiling`
- `cairosvg`
- `openai`
- `pyautogen`

## Credits

This project was developed as part of an internship at LLMind by me, a 2nd-year computer science student at Delhi University.
