# ThreatLens
### AI-Powered Predictive Cyber Threat Intelligence & Hidden Network Analysis

<p align="center">
  <strong>Discover. Analyze. Predict.</strong>
</p>

<p align="center">
  An AI-driven threat intelligence platform designed to uncover hidden-network trends, identify emerging cyber threats, and predict potential industry-specific security risks.
</p>

---

## Overview

**ThreatLens** is an AI-powered cyber threat intelligence platform developed to analyze information gathered from hidden networks and identify patterns that may indicate emerging cybersecurity threats.

The platform combines automated data collection, web crawling, Natural Language Processing (NLP), and Machine Learning (ML) to transform unstructured threat-related information into meaningful intelligence.

Unlike conventional approaches that primarily focus on identifying existing threats, ThreatLens explores a predictive approach to cybersecurity by analyzing emerging patterns and estimating potential risks to different industries, organizations, and their internal departments.

The system aims to help security researchers and organizations gain better visibility into evolving cyber threats and make more informed security decisions.

## Key Features

- **Automated Intelligence Collection:** Collects threat-related information from hidden-network sources through automated crawling and scraping mechanisms.
- **Website Classification:** Applies machine learning techniques to classify websites based on their characteristics and collected information.
- **Threat Pattern Analysis:** Processes unstructured textual information to identify meaningful patterns and indicators.
- **Industry Risk Prediction:** Estimates which industries may be more susceptible to emerging cyber threats.
- **Department-Level Risk Assessment:** Analyzes potential exposure across organizational departments.
- **Data Exposure Insights:** Identifies categories of organizational information that may be at risk.
- **Automated Alerting:** Integrates Telegram-based notifications to deliver generated intelligence and relevant alerts.
- **Web-Based Interface:** Provides an interface for interacting with the platform's intelligence and prediction components.

## System Architecture

ThreatLens follows a modular architecture consisting of multiple interconnected components.

### 1. Intelligence Collection & Web Crawling

The collection layer is responsible for gathering information from publicly accessible and authorized hidden-network research sources.

It uses automated crawling and scraping techniques to collect relevant information for subsequent analysis.

### 2. Dataset Generation & Processing

Collected information is processed and transformed into structured datasets.

This stage involves:
- Data extraction and cleaning.
- Text preprocessing and normalization.
- Feature preparation.
- Dataset generation.
- Handling imbalanced datasets.

### 3. Website Classification

Machine learning models analyze extracted information to classify websites and identify relevant characteristics.

The classification pipeline explores different machine learning algorithms to evaluate their suitability for threat intelligence analysis.

### 4. Industry Risk Prediction

This component analyzes collected intelligence and classification results to estimate potential cyber risks across different industries.

The objective is to identify industry-level threat patterns and highlight sectors that may require increased security awareness.

### 5. Department Probability Analysis

ThreatLens extends its predictive capabilities to organizational departments.

Based on identified threat patterns, the system estimates which departments and categories of organizational information could potentially be affected.

### 6. Alert & Notification System

The alerting component integrates with the Telegram Bot API to communicate relevant intelligence and prediction results through automated notifications.

### 7. Web Interface

A dedicated web interface provides an interaction layer for the platform's underlying intelligence and prediction modules.

---

## Technology Stack

ThreatLens utilizes a combination of technologies across data collection, data science, machine learning, and application development.

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Web Scraping | BeautifulSoup, Requests |
| Data Processing | Pandas |
| Machine Learning | Scikit-learn |
| NLP | NLTK, TF-IDF |
| Classification Models | Random Forest, Naive Bayes, Gradient Boosting |
| Advanced ML Models | XGBoost, CatBoost |
| Data Balancing | SMOTE, Imbalanced-learn |
| Visualization | Matplotlib |
| Model Persistence | Joblib |
| Backend / Web Framework | Flask |
| Network Connectivity | PySocks |
| Notifications | Telegram Bot API |

### Machine Learning Techniques

The project explores multiple machine learning algorithms and preprocessing techniques, including:

- Random Forest
- Naive Bayes
- Gradient Boosting
- XGBoost
- CatBoost
- TF-IDF Vectorization
- Label Encoding
- SMOTE and Random Oversampling

These techniques are used across different classification and prediction components of the platform.

---

## Repository Structure

The repository is organized into independent modules, each responsible for a particular stage of the ThreatLens pipeline.

```text
ThreatLens/
│
├── Dataset_Generation_from_urls/
│   └── Dataset generation and preparation
│
├── Industry_Prediction_model/
│   └── Industry-level risk prediction
│
├── Scraping_Sites_for_Threat_Intelligence_Model_taining_DS/
│   └── Intelligence collection and dataset preparation
│
├── _Site_status_checker/
│   └── Website availability and status checking
│
├── _Web_interface_for_fyp/
│   └── Web-based application interface
│
├── _Website_Classification_Models/
│   └── Website classification models
│
├── _Website_classificatio_v1/
│   └── Earlier website classification implementation
│
├── _dept_probability_/
│   └── Department-level probability analysis
│
├── _telegram_alert/
│   └── Telegram notification integration
│
├── helper_methods/
│   └── Shared utility methods
│
├── onionOwl_DS/
│   └── Supporting dataset and research components
│
├── requirements.txt
└── README.md
```

*Note: The repository contains multiple development iterations and experimental modules. Individual implementations may have their own dependencies and execution requirements.*

---

## Installation & Setup

### Prerequisites

- Python 3.x
- pip
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Ibrahim-sayys/ThreatLens.git

cd ThreatLens
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment:

**Linux / macOS**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Explore the Modules

Navigate to the respective module directories to explore individual implementations.

Each component may have its own execution requirements, configuration, and dataset dependencies.

---

## Project Objectives

ThreatLens was developed with the following objectives:

1. Explore the application of Artificial Intelligence in cybersecurity and threat intelligence.
2. Automate the collection and processing of threat-related information.
3. Develop machine learning models capable of identifying meaningful patterns in hidden-network data.
4. Investigate predictive approaches to industry-specific cyber risk assessment.
5. Extend threat analysis to organizational departments and potentially exposed data categories.
6. Deliver relevant intelligence through automated notification mechanisms.

## Research & Development

ThreatLens explores the intersection of several research areas:

- Artificial Intelligence in Cybersecurity
- Open-Source Intelligence (OSINT)
- Dark Web and Hidden Network Intelligence
- Natural Language Processing
- Machine Learning and Predictive Analytics
- Cyber Threat Intelligence (CTI)
- Automated Data Collection and Analysis

The project demonstrates how machine learning and automated intelligence pipelines can contribute to a more proactive approach to cybersecurity research.

## Project Recognition

**3rd Place — Bahria University Open House 2025**

ThreatLens was recognized at Bahria University's Open House 2025 for its implementation and application of AI-driven cybersecurity research.

## Future Scope

Potential areas for further development include:

- Integration of additional threat intelligence sources.
- Improved prediction models and model evaluation.
- Advanced NLP and transformer-based architectures.
- Real-time intelligence processing.
- Enhanced visualization and analytical dashboards.
- Improved alert prioritization and threat correlation.
- Expanded industry and organizational risk assessment capabilities.

## Disclaimer

ThreatLens is an academic research and development project intended for cybersecurity research, threat intelligence analysis, and educational purposes.

All research and data collection activities should comply with applicable laws, regulations, and the terms of service of the respective platforms.

The predictions and risk assessments generated by machine learning models are estimates and should not be treated as confirmed security incidents or definitive evidence of compromise.

## Acknowledgements

Developed as a Final Year Project at **Bahria University, Lahore Campus**, with a focus on applying Artificial Intelligence and Machine Learning to cybersecurity and threat intelligence.

---

<p align="center">
  <strong>ThreatLens</strong><br>
  <em>Turning Hidden Intelligence into Actionable Insights.</em>
</p>
