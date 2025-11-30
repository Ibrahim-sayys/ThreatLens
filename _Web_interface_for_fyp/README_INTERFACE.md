# ThreatLens - Website Classification System

A Flask-based web interface for classifying websites using machine learning to identify potential security threats and data leaks.

## Features

- 🔍 **Single URL Classification** - Analyze individual websites
- 📊 **Batch Processing** - Upload CSV/Excel files to analyze multiple URLs
- 🤖 **Multiple ML Models** - Choose from Naive Bayes, XGBoost, CatBoost, Random Forest, and Gradient Boosting
- 🔐 **Tor Support** - Built-in proxy support for .onion sites
- ⚡ **Real-time Results** - Instant classification with extracted keywords
- 🎨 **Minimalistic Cybersecurity Theme** - Clean, terminal-inspired interface

## Installation

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup

1. Navigate to the project directory:
```bash
cd /home/ibrahim-sayys/Projects/ThreatLens/_Web_interface_for_fyp
```

2. Install required dependencies:
```bash
pip install flask pandas openpyxl beautifulsoup4 requests joblib nltk scikit-learn xgboost catboost
```

3. Download NLTK stopwords (if not already downloaded):
```python
python -c "import nltk; nltk.download('stopwords')"
```

## Usage

### Starting the Server

Run the Flask application:
```bash
python app.py
```

The server will start on `http://0.0.0.0:5000`

### Accessing the Interface

Open your web browser and navigate to:
- **Home Page**: `http://localhost:5000`
- **Classification**: `http://localhost:5000/classify`
- **Developers**: `http://localhost:5000/developers`
- **About**: `http://localhost:5000/about`
- **Orion Intelligence**: `http://localhost:5000/orion` (redirects to external service)

## Features Guide

### Single URL Classification

1. Navigate to the **Classify** page
2. Select "Single URL" tab
3. Enter the URL to analyze
4. Choose an ML model from the dropdown
5. Optionally enable Tor proxy for .onion sites
6. Click "Classify URL"

### Batch Processing

1. Navigate to the **Classify** page
2. Select "Batch Upload" tab
3. Choose an ML model
4. Upload a CSV or Excel file with URLs
   - File must contain a column named: `url`, `urls`, `website`, or `link`
   - Maximum 50 URLs per batch
5. Click "Process Batch"

### Sample CSV Format

```csv
url
https://example.com
https://another-site.com
```

## ML Models

The system uses the following models (SMOTE-balanced versions):

- **Naive Bayes**: Probabilistic classifier
- **XGBoost**: Gradient boosting framework
- **CatBoost**: Gradient boosting with categorical support
- **Random Forest**: Ensemble learning method
- **Gradient Boosting**: Traditional gradient boosting

Models are located in: `/home/ibrahim-sayys/Projects/ThreatLens/_Website_classificatio_v1/`

## Classification Categories

- **Leaks**: Sites potentially related to data breaches or leaked information
- **Others**: General websites not classified as leaks

## Project Structure

```
_Web_interface_for_fyp/
├── app.py                    # Main Flask application
├── templates/
│   ├── base.html            # Base template
│   ├── index.html           # Home page
│   ├── classify.html        # Classification interface
│   ├── developers.html      # Developers page
│   └── about.html           # About page
├── static/
│   ├── css/
│   │   └── style.css        # Main stylesheet
│   └── js/                  # JavaScript files (optional)
├── uploads/                  # Temporary upload directory
└── sample_urls.csv          # Sample batch file
```

## Configuration

### Tor Proxy Settings

If using Tor for .onion sites, ensure Tor is running:
```bash
sudo service tor start
```

Default proxy settings in `app.py`:
```python
PROXIES = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050',
}
```

### File Upload Limits

Maximum file size: 16MB (configurable in `app.py`)

## API Endpoints

### GET `/`
Home page

### GET `/classify`
Classification interface

### POST `/classify`
Single URL classification
- Parameters: `url`, `model`, `use_tor` (optional)

### POST `/classify/batch`
Batch URL classification
- Parameters: `file` (CSV/Excel), `model`, `use_tor` (optional)

### GET `/orion`
Redirects to Orion Intelligence platform

### GET `/developers`
Developers information page

### GET `/about`
About page with system information

## Development

### Customizing Developer Information

Edit `templates/developers.html` to update:
- Developer names
- Roles/titles
- Descriptions
- LinkedIn profile links

### Customizing Styles

Edit `static/css/style.css` to modify:
- Color scheme (CSS variables in `:root`)
- Layout
- Typography
- Responsive breakpoints

## Troubleshooting

### Models Not Loading

- Verify model files exist in `_Website_classificatio_v1/`
- Check file permissions
- Ensure all required model files are present:
  - `{model}_smote.pkl`
  - `{model}_vectorizer.pkl`
  - `{model}_label_encoder.pkl`

### Connection Errors

- Check internet connectivity
- Verify Tor is running (if using Tor)
- Check firewall settings

### Template Not Found

- Ensure all HTML files are in `templates/` directory
- Check file permissions

## Security Considerations

- This tool is for educational and research purposes only
- Always obtain proper authorization before analyzing websites
- Respect privacy laws and website terms of service
- Use responsibly

## License

This project is part of the ThreatLens threat intelligence system.

## Support

For issues or questions, contact the developers listed in the Developers section of the application.

