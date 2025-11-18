from transformers import pipeline
import warnings
import concurrent.futures
from helper_methods._stopword_filtering import (remove_stopwords,remove_stopwords_preserve_punctuation)


warnings.filterwarnings('ignore')

# Add a clear check for PyTorch so we fail fast with an actionable message
try:
    import torch  # noqa: F401
    _TORCH_AVAILABLE = True
except Exception:
    _TORCH_AVAILABLE = False


class BreachClassifier:
    def __init__(self):
        """Initialize the classifier for breach analysis"""
        if not _TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch is not installed or could not be imported. "
                "The transformers zero-shot pipeline requires a deep learning backend. "
                "Install PyTorch into your virtual environment, for example (CPU-only):\n"
                "    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu\n"
                "Or visit https://pytorch.org/get-started/locally/ for platform-specific instructions."
            )

        print("Loading breach analysis model... (this may take a moment)")
        # Using facebook/bart-large-mnli - commonly cached, good performance
        # Alternative tiny model: "typeform/distilbert-base-uncased-mnli" (only 250MB)
        self.classifier = pipeline(
            "zero-shot-classification",
            model="typeform/distilbert-base-uncased-mnli"  # Much smaller: ~250MB vs 1GB
        )

        self.departments = [
            "Human Resources and Employee Data",
            "Finance and Accounting",
            "Sales and Customer Relations",
            "Information Technology and Systems",
            "Legal and Compliance",
            "Marketing and Communications",
            "Operations and Logistics",
            "Research and Development",
            "Executive and Management",
            "Supply Chain and Procurement",
            "Customer Support and Service"
        ]

        self.data_types = [
            "Personal Identifiable Information (PII)",
            "Financial Records and Payment Data",
            "Health and Medical Records",
            "Login Credentials and Passwords",
            "Social Security Numbers",
            "Credit Card Information",
            "Email and Communication Data",
            "Employee Records and Payroll",
            "Customer Database",
            "Intellectual Property and Trade Secrets",
            "Legal Documents and Contracts",
            "Biometric Data",
            "Government IDs and Passports",
            "Banking and Account Information",
            "Corporate Financial Data"
        ]

        self.severity_levels = [
            "Critical - Highly Sensitive Data",
            "High - Sensitive Personal Information",
            "Medium - Business Data",
            "Low - Non-Sensitive Information"
        ]

        print("Breach analysis model loaded successfully!")

    def _classify(self, text, labels, top_n=3, key_name="label"):
        result = self.classifier(text, labels)
        return [
            {key_name: result['labels'][i], "confidence": result['scores'][i]}
            for i in range(min(top_n, len(result['labels'])))
        ]

    def get_affected_departments(self, text, top_n=3):
        return self._classify(text, self.departments, top_n, "department")

    def get_compromised_data_types(self, text, top_n=3):
        return self._classify(text, self.data_types, top_n, "data_type")

    def get_breach_severity(self, text):
        result = self.classifier(text, self.severity_levels)
        return {"severity": result['labels'][0], "confidence": result['scores'][0]}

    def analyze_breach(self, text, top_n=3):
        """Run departments, data types, severity in parallel"""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_dept = executor.submit(self.get_affected_departments, text, top_n)
            future_data = executor.submit(self.get_compromised_data_types, text, top_n)
            future_severity = executor.submit(self.get_breach_severity, text)

            departments = future_dept.result()
            data_types = future_data.result()
            severity = future_severity.result()

        return {
            "departments": departments,
            "data_types": data_types,
            "severity": severity
        }

    def get_simple_departments(self, text, top_n=1):
        return [item['department'] for item in self.get_affected_departments(text, top_n)]

    def get_simple_data_types(self, text, top_n=1):
        return [item['data_type'] for item in self.get_compromised_data_types(text, top_n)]


# Module-level runner
if __name__ == "__main__":
    classifier = BreachClassifier()
    breach_text = "A cyberattack exposed customer credit card details and login credentials."
    filtered_text= remove_stopwords(breach_text)
    analysis = classifier.analyze_breach(filtered_text)
    print(analysis)
