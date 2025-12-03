import os
import sys
import requests
import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect
from bs4 import BeautifulSoup
import re
from collections import Counter
import joblib
from nltk.corpus import stopwords
import nltk
from werkzeug.utils import secure_filename
import socket
import random
import asyncio

# Add parent directory to path for importing telegram integration
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _telegram_alert.telegram_integration import send_message_to_channel

# Ensure stopwords are downloaded
try:
    stop_words = set(stopwords.words('english'))
except LookupError:
    nltk.download('stopwords')
    stop_words = set(stopwords.words('english'))

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Base directory for models
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_Website_classificatio_v1')

# Model file mapping - using SMOTE versions
MODEL_FILES = {
    "naive_bayes": {
        "name": "Naive Bayes (SMOTE)",
        "model": os.path.join(MODEL_DIR, "naive_bayes_smote.pkl"),
        "vectorizer": os.path.join(MODEL_DIR, "naive_bayes_vectorizer.pkl"),
        "label_encoder": os.path.join(MODEL_DIR, "naive_bayes_label_encoder.pkl")
    },
    "xgboost": {
        "name": "XGBoost (SMOTE)",
        "model": os.path.join(MODEL_DIR, "xgboost_smote.pkl"),
        "vectorizer": os.path.join(MODEL_DIR, "xgboost_vectorizer.pkl"),
        "label_encoder": os.path.join(MODEL_DIR, "xgboost_label_encoder.pkl")
    },
    "catboost": {
        "name": "CatBoost (SMOTE)",
        "model": os.path.join(MODEL_DIR, "catboost_smote.pkl"),
        "vectorizer": os.path.join(MODEL_DIR, "catboost_vectorizer.pkl"),
        "label_encoder": os.path.join(MODEL_DIR, "catboost_label_encoder.pkl")
    },
    "random_forest": {
        "name": "Random Forest (SMOTE)",
        "model": os.path.join(MODEL_DIR, "random_forest_smote.pkl"),
        "vectorizer": os.path.join(MODEL_DIR, "random_forest_vectorizer.pkl"),
        "label_encoder": os.path.join(MODEL_DIR, "random_forest_label_encoder.pkl")
    },
    "gradient_boosting": {
        "name": "Gradient Boosting (SMOTE)",
        "model": os.path.join(MODEL_DIR, "gradient_boosting_smote.pkl"),
        "vectorizer": os.path.join(MODEL_DIR, "gradient_boosting_vectorizer.pkl"),
        "label_encoder": os.path.join(MODEL_DIR, "gradient_boosting_label_encoder.pkl")
    }
}

# Load models at startup
LOADED_MODELS = {}
for key, paths in MODEL_FILES.items():
    try:
        LOADED_MODELS[key] = {
            "name": paths["name"],
            "model": joblib.load(paths["model"]),
            "vectorizer": joblib.load(paths["vectorizer"]),
            "label_encoder": joblib.load(paths["label_encoder"])
        }
        print(f"✓ Loaded {paths['name']}")
    except Exception as e:
        print(f"✗ Failed to load {paths['name']}: {e}")

# Tor proxy settings (optional)
PROXIES = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050',
}

def is_tor_available(host='127.0.0.1', port=9050, timeout=1.0):
    """Quickly check if Tor SOCKS proxy is reachable"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False

def extract_text_from_html(html_content):
    """Extract clean text from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()
    full_text = soup.get_text(separator=' ')
    clean_text = ' '.join(full_text.split())
    return clean_text

def extract_keywords(text, num_keywords=10):
    """Extract top keywords from text"""
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    filtered_words = [word for word in words if word not in stop_words]
    word_counts = Counter(filtered_words)
    return [word for word, _ in word_counts.most_common(num_keywords)]

def classify_url(url, selected_model="xgboost", use_tor=False):
    """Classify a single URL using the selected model"""
    try:
        if not url.startswith("http"):
            url = "http://" + url

        # Detect .onion URLs and require Tor
        host = url.lower()
        if ".onion" in host and not use_tor:
            return {
                "url": url,
                "status": "error",
                "message": "Detected a .onion address. Please turn the Tor proxy on and try again.",
                "category": None,
                "keywords": None
            }

        proxies = PROXIES if use_tor else None
        timeout = 30 if use_tor else 10

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, proxies=proxies, timeout=timeout, headers=headers)

        if response.status_code == 200:
            html = response.text
            text = extract_text_from_html(html)

            if not text or len(text.strip()) < 10:
                return {
                    "url": url,
                    "status": "error",
                    "message": "Website contains little or no text to analyze",
                    "category": None,
                    "keywords": None
                }

            keywords = extract_keywords(text, num_keywords=10)
            keywords_joined = ' '.join(keywords)

            # Use the selected model
            if selected_model not in LOADED_MODELS:
                return {
                    "url": url,
                    "status": "error",
                    "message": f"Model {selected_model} not available",
                    "category": None,
                    "keywords": None
                }

            model_info = LOADED_MODELS[selected_model]
            vectorizer = model_info["vectorizer"]
            model = model_info["model"]
            label_encoder = model_info["label_encoder"]

            X = vectorizer.transform([keywords_joined])
            y_pred = model.predict(X)
            category = label_encoder.inverse_transform(y_pred)[0]

            return {
                "url": url,
                "status": "success",
                "category": category,
                "keywords": keywords,
                "message": "Classification successful"
            }
        else:
            return {
                "url": url,
                "status": "error",
                "message": f"HTTP {response.status_code}",
                "category": None,
                "keywords": None
            }

    except requests.exceptions.ConnectionError:
        # Special-case: .onion without Tor should already be handled above, but keep a helpful message
        if ".onion" in url.lower() and not use_tor:
            return {
                "url": url,
                "status": "error",
                "message": "Detected a .onion address. Please turn the Tor proxy on and try again.",
                "category": None,
                "keywords": None
            }
        return {
            "url": url,
            "status": "error",
            "message": "Connection failed",
            "category": None,
            "keywords": None
        }
    except requests.exceptions.Timeout:
        return {
            "url": url,
            "status": "error",
            "message": "Request timed out",
            "category": None,
            "keywords": None
        }
    except Exception as e:
        return {
            "url": url,
            "status": "error",
            "message": str(e),
            "category": None,
            "keywords": None
        }

@app.route("/")
def index():
    """Home page with breach carousel"""
    # Load CSV and prepare random 20 items from first 500 having image_url
    csv_path = "/home/ibrahim-sayys/Projects/ThreatLens/Scraping_Sites_for_Threat_Intelligence_Model_taining_DS/threat_intelligence_data.csv"
    breaches = []
    documents = []  # Second carousel for sarcomawmawlhov7o5mdhz4eszxxlkyaoiyiy2b5iwxnds2dmb4jakad

    try:
        # Read only necessary columns to reduce memory
        usecols = ["company_name", "content", "download_link", "image_url", "views_count"]
        df = pd.read_csv(csv_path, usecols=usecols)
        # First 500 rows
        df = df.head(500)
        df["image_url"] = df["image_url"].astype(str)
        df = df[df["image_url"].str.strip().ne("")]

        # First carousel: 5butbkrljkaorg5maepuca25oma7eiwo6a2rlhvkblb4v6mf3ki2ovid
        onion_host = "5butbkrljkaorg5maepuca25oma7eiwo6a2rlhvkblb4v6mf3ki2ovid"
        df_breaches = df[df["image_url"].str.contains(onion_host, case=False, na=False)]
        # Filter out records with company_name "Victim" (case insensitive)
        df_breaches = df_breaches[~df_breaches["company_name"].astype(str).str.strip().str.lower().eq("victim")]
        sample_count = min(20, len(df_breaches))
        if sample_count > 0:
            df_sample = df_breaches.sample(n=sample_count, random_state=random.randint(0, 10_000))
            for _, row in df_sample.iterrows():
                company_name = str(row.get("company_name", "")).strip()
                content = str(row.get("content", "")).strip()
                # Truncate content to ~180 chars
                max_len = 180
                truncated = (content[:max_len] + "…") if len(content) > max_len else content
                breaches.append({
                    "company_name": company_name or "Unknown",
                    "content": truncated,
                    "download_link": str(row.get("download_link", "")).strip(),
                    "image_url": str(row.get("image_url", "")).strip(),
                    "views_count": int(row.get("views_count", 0)) if pd.notna(row.get("views_count", None)) else 0
                })
            # Shuffle the breaches list
            random.shuffle(breaches)

        # Second carousel: sarcomawmawlhov7o5mdhz4eszxxlkyaoiyiy2b5iwxnds2dmb4jakad (portrait documents/PDFs)
        doc_host = "sarcomawmawlhov7o5mdhz4eszxxlkyaoiyiy2b5iwxnds2dmb4jakad"
        df_docs = df[df["image_url"].str.contains(doc_host, case=False, na=False)]
        # Filter out records with company_name "Victim" (case insensitive)
        df_docs = df_docs[~df_docs["company_name"].astype(str).str.strip().str.lower().eq("victim")]
        sample_count_docs = min(15, len(df_docs))
        if sample_count_docs > 0:
            df_sample_docs = df_docs.sample(n=sample_count_docs, random_state=random.randint(0, 10_000))
            for _, row in df_sample_docs.iterrows():
                company_name = str(row.get("company_name", "")).strip()
                content = str(row.get("content", "")).strip()
                max_len = 180
                truncated = (content[:max_len] + "…") if len(content) > max_len else content
                image_url_raw = str(row.get("image_url", "")).strip()

                # Parse comma-separated URLs
                image_urls = [url.strip() for url in image_url_raw.split(',') if url.strip()]

                # Create a document entry for each URL (or take first few if too many)
                for img_url in image_urls[:5]:  # Limit to first 5 images per company
                    documents.append({
                        "company_name": company_name or "Unknown",
                        "content": truncated,
                        "download_link": str(row.get("download_link", "")).strip(),
                        "image_url": img_url
                    })
            # Shuffle the documents list
            random.shuffle(documents)
    except Exception as e:
        print(f"Failed to load breaches CSV: {e}")

    tor_available = is_tor_available()
    return render_template("index.html", breaches=breaches, documents=documents, tor_available=tor_available)

@app.route('/image_proxy')
def image_proxy():
    """Proxy image fetch via Tor for .onion and other URLs; returns image bytes.
    If fetch fails, respond 502 and let frontend show a placeholder.
    """
    url = request.args.get('url', '').strip()
    if not url:
        return ("Missing url", 400)
    try:
        # Force Tor for .onion; otherwise still use Tor to avoid DNS leaks
        proxies = PROXIES
        timeout = 30
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        resp = requests.get(url, proxies=proxies, timeout=timeout, headers=headers, stream=True)
        if resp.status_code != 200:
            return (f"Upstream status {resp.status_code}", 502)
        content_type = resp.headers.get('Content-Type', 'image/jpeg')
        return (resp.content, 200, {'Content-Type': content_type, 'Cache-Control': 'no-store'})
    except Exception as e:
        return (f"Proxy error: {str(e)}", 502)

@app.route("/classify", methods=["GET", "POST"])
def classify():
    """URL Classification page"""
    if request.method == "GET":
        model_choices = [(key, info["name"]) for key, info in LOADED_MODELS.items()]
        return render_template("classify.html", model_choices=model_choices)

    # POST request - handle classification
    data = request.get_json() if request.is_json else request.form
    url = data.get("url", "").strip()
    selected_model = data.get("model", "xgboost")
    use_tor = data.get("use_tor", False)

    if not url:
        return jsonify({"error": "URL is required"}), 400

    result = classify_url(url, selected_model, use_tor)

    if request.is_json:
        return jsonify(result)
    else:
        model_choices = [(key, info["name"]) for key, info in LOADED_MODELS.items()]
        return render_template("classify.html",
                             result=result,
                             model_choices=model_choices,
                             selected_model=selected_model)

@app.route("/classify/batch", methods=["POST"])
def classify_batch():
    """Handle batch classification from CSV/Excel file"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    selected_model = request.form.get("model", "xgboost")
    use_tor = request.form.get("use_tor") == "true"

    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Read file based on extension
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        else:
            return jsonify({"error": "Invalid file format. Use CSV or Excel"}), 400

        # Find URL column (case insensitive)
        url_column = None
        for col in df.columns:
            if col.lower() in ['url', 'urls', 'website', 'link']:
                url_column = col
                break

        if url_column is None:
            return jsonify({"error": "No URL column found. Column should be named 'url', 'urls', 'website', or 'link'"}), 400

        urls = df[url_column].dropna().tolist()

        if len(urls) == 0:
            return jsonify({"error": "No URLs found in file"}), 400

        # Classify each URL
        results = []
        for url in urls[:50]:  # Limit to 50 URLs to prevent timeout
            result = classify_url(url, selected_model, use_tor)
            results.append(result)

        # Clean up uploaded file
        os.remove(filepath)

        return jsonify({"results": results})

    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

@app.route("/telegram_alert", methods=["GET", "POST"])
def telegram_alert():
    """Telegram Alerts page - Send breach predictions to Telegram channel"""
    if request.method == "GET":
        return render_template("telegram_alert.html")

    # POST request - send message to Telegram
    try:
        industry = request.form.get("industry", "").strip()
        departments = request.form.get("departments", "").strip()

        if not industry or not departments:
            return jsonify({
                "status": "error",
                "message": "Both industry and department(s) are required"
            }), 400

        # Format professional breach prediction message
        message = f"""🚨 **BREACH PREDICTION ALERT** 🚨

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 **Orion Intelligence Analysis**

**Industry at Risk:** {industry}

**Affected Department(s):** {departments}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **Threat Assessment:**
Our advanced threat intelligence systems have identified potential vulnerabilities in the {industry} sector, specifically targeting the {departments} department(s). Immediate attention and enhanced security measures are recommended.

📋 **Recommended Actions:**
• Conduct immediate security audit
• Review access controls and permissions
• Update security protocols
• Monitor for suspicious activities
• Brief security team on potential threats

🛡️ **ThreatLens Advisory:**
This alert has been generated by Orion Intelligence based on current threat landscape analysis. Organizations in this sector should implement enhanced monitoring and preventive measures immediately.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 **ThreatLens Security Operations**
Stay vigilant. Stay secure.

⏰ Alert Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""

        # Telegram bot configuration (hardcoded as per requirements)
        TOKEN = "8534807443:AAF529s1Q0OcDfBDVb37WTvXEH1SodaTPNI"
        CHANNEL_NAME = "@ThreatLens"

        # Send message using asyncio
        success = asyncio.run(send_message_to_channel(TOKEN, CHANNEL_NAME, message))

        if success:
            return jsonify({
                "status": "success",
                "message": "Breach prediction alert has been successfully sent to the ThreatLens Telegram channel!",
                "industry": industry,
                "departments": departments
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to send message to Telegram. Please check bot configuration and network connectivity."
            }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500

@app.route("/orion")
def orion():
    """Redirect to Orion Intelligence"""
    return redirect("https://try.orionintelligence.org/login?redirect=%2Fdashboard%2Fhome")

@app.route("/developers")
def developers():
    """Developers page"""
    return render_template("developers.html")

@app.route("/about")
def about():
    """About page"""
    return render_template("about.html")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔒 ThreatLens - Website Classification System")
    print("="*60)
    print(f"\nLoaded {len(LOADED_MODELS)} models:")
    for key, model in LOADED_MODELS.items():
        print(f"  • {model['name']}")
    print("\n" + "="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
