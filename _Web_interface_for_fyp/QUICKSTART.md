# 🔒 ThreatLens Quick Start Guide

## Instant Setup

### 1. Start the Application

Simply run:
```bash
cd /home/ibrahim-sayys/Projects/ThreatLens/_Web_interface_for_fyp
./run.sh
```

Or manually:
```bash
python app.py
```

### 2. Access the Interface

Open your browser and go to: **http://localhost:5000**

---

## Quick Feature Overview

### 🏠 Home Page
- Overview of the system
- Quick navigation to all features

### 🔍 Classify URLs
**Single URL Analysis:**
1. Click "Classify" in navigation
2. Enter a URL (e.g., `https://example.com`)
3. Select an ML model (XGBoost recommended)
4. Click "Classify URL"

**Batch Analysis:**
1. Click "Classify" in navigation
2. Click "Batch Upload" tab
3. Upload CSV/Excel file with URLs
4. Select an ML model
5. Click "Process Batch"

### 🌐 Orion Intelligence
- Click "Try Orion Intelligence" to access external threat intelligence platform
- Opens in new tab

### 👥 Developers
- View developer information
- Connect via LinkedIn

### ℹ️ About
- Learn about the system
- View available ML models
- Understand classification process

---

## Sample Test

### Test Single URL:
```
URL: https://github.com
Model: XGBoost (SMOTE)
Expected: Classification result with keywords
```

### Test Batch Upload:
Use the provided `sample_urls.csv` file:
```bash
# File contains:
# url
# https://example.com
# https://google.com
# https://github.com
```

---

## Available ML Models

1. **Naive Bayes (SMOTE)** - Fast, probabilistic
2. **XGBoost (SMOTE)** - Recommended, high accuracy
3. **CatBoost (SMOTE)** - Good for categorical data
4. **Random Forest (SMOTE)** - Ensemble method
5. **Gradient Boosting (SMOTE)** - Traditional boosting

---

## Classification Categories

- **Leaks** 🔴 - Potentially contains leaked/sensitive data
- **Others** 🟡 - General website content

---

## Tips

- Use **XGBoost** for best accuracy
- Enable **Tor proxy** only for .onion sites
- Batch processing limited to **50 URLs**
- CSV must have column named: `url`, `urls`, `website`, or `link`

---

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9
# Then restart
./run.sh
```

### Models Not Loading
- Check that model files exist in `../_Website_classificatio_v1/`
- Verify files: `{model}_smote.pkl`, `{model}_vectorizer.pkl`, `{model}_label_encoder.pkl`

### Connection Errors
- Check internet connection
- For .onion sites: `sudo service tor start`

---

## Developer Customization

### Update Developer Info
Edit: `templates/developers.html`
- Lines 12-32: Developer 1
- Lines 35-55: Developer 2

### Change Colors
Edit: `static/css/style.css`
- Lines 5-15: Color variables in `:root`

### Modify Port
Edit: `app.py`
- Line 303: Change `port=5000` to your preferred port

---

## Project Structure
```
_Web_interface_for_fyp/
├── app.py                 # Main Flask application
├── run.sh                 # Startup script
├── templates/             # HTML templates
│   ├── base.html         # Base layout
│   ├── index.html        # Home page
│   ├── classify.html     # Classification UI
│   ├── developers.html   # Dev info
│   └── about.html        # About page
├── static/
│   └── css/
│       └── style.css     # Cybersecurity theme
├── uploads/              # Temporary files
└── sample_urls.csv       # Example batch file
```

---

## Next Steps

1. ✅ Start the server: `./run.sh`
2. ✅ Open browser: `http://localhost:5000`
3. ✅ Test single URL classification
4. ✅ Test batch processing
5. ✅ Customize developer information
6. ✅ Enjoy your threat intelligence system!

---

**Need Help?** Check README_INTERFACE.md for detailed documentation.

