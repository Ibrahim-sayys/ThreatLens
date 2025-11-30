#!/bin/bash

# ThreatLens Flask Application Startup Script

echo "============================================================"
echo "🔒 Starting ThreatLens - Website Classification System"
echo "============================================================"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider activating a virtual environment first"
    echo ""
fi

# Navigate to script directory
cd "$(dirname "$0")"

# Check for required dependencies
echo "📦 Checking dependencies..."
python -c "import flask" 2>/dev/null || { echo "❌ Flask not installed. Run: pip install flask"; exit 1; }
python -c "import pandas" 2>/dev/null || { echo "❌ Pandas not installed. Run: pip install pandas"; exit 1; }
python -c "import bs4" 2>/dev/null || { echo "❌ BeautifulSoup not installed. Run: pip install beautifulsoup4"; exit 1; }
python -c "import joblib" 2>/dev/null || { echo "❌ Joblib not installed. Run: pip install joblib"; exit 1; }
python -c "import nltk" 2>/dev/null || { echo "❌ NLTK not installed. Run: pip install nltk"; exit 1; }
echo "✓ All dependencies installed"
echo ""

# Download NLTK stopwords if needed
echo "📚 Checking NLTK data..."
python -c "import nltk; nltk.download('stopwords', quiet=True)"
echo "✓ NLTK stopwords ready"
echo ""

# Create uploads directory
mkdir -p uploads
echo "✓ Created uploads directory"
echo ""

# Kill any existing Flask processes on port 5000
if lsof -ti:5000 >/dev/null 2>&1; then
    echo "🔄 Port 5000 is in use. Stopping existing process..."
    lsof -ti:5000 | xargs kill -9 2>/dev/null
    sleep 2
fi

echo "============================================================"
echo "🚀 Starting Flask application..."
echo "============================================================"
echo ""
echo "   Access the application at:"
echo "   → http://localhost:5000"
echo "   → http://127.0.0.1:5000"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""
echo "============================================================"
echo ""

# Start Flask application
python app.py

