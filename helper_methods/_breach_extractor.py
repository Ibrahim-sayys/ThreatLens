from transformers import pipeline
import warnings

warnings.filterwarnings('ignore')


class BreachClassifier:
    def __init__(self):
        """Initialize the classifier for breach analysis"""
        print("Loading breach analysis model... (this may take a moment)")
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )

        # Department categories
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

        # Data type categories
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

        # Breach severity
        self.severity_levels = [
            "Critical - Highly Sensitive Data",
            "High - Sensitive Personal Information",
            "Medium - Business Data",
            "Low - Non-Sensitive Information"
        ]

        print("Breach analysis model loaded successfully!")

    def get_affected_departments(self, text, top_n=3):
        """
        Identify which departments were affected

        Args:
            text (str): Breach description
            top_n (int): Number of top departments to return

        Returns:
            list: List of affected departments with confidence scores
        """
        if not text or not isinstance(text, str):
            return []

        result = self.classifier(text, self.departments)

        departments_with_confidence = [
            {
                "department": result['labels'][i],
                "confidence": result['scores'][i]
            }
            for i in range(min(top_n, len(result['labels'])))
        ]

        return departments_with_confidence

    def get_compromised_data_types(self, text, top_n=3):
        """
        Identify what types of data were compromised

        Args:
            text (str): Breach description
            top_n (int): Number of top data types to return

        Returns:
            list: List of compromised data types with confidence scores
        """
        if not text or not isinstance(text, str):
            return []

        result = self.classifier(text, self.data_types)

        data_types_with_confidence = [
            {
                "data_type": result['labels'][i],
                "confidence": result['scores'][i]
            }
            for i in range(min(top_n, len(result['labels'])))
        ]

        return data_types_with_confidence

    def get_breach_severity(self, text):
        """
        Determine breach severity

        Args:
            text (str): Breach description

        Returns:
            dict: Severity level with confidence
        """
        if not text or not isinstance(text, str):
            return {"severity": "Unknown", "confidence": 0.0}

        result = self.classifier(text, self.severity_levels)

        return {
            "severity": result['labels'][0],
            "confidence": result['scores'][0]
        }

    def analyze_breach(self, text, top_n=3):
        """
        Complete breach analysis - departments, data types, and severity

        Args:
            text (str): Breach description
            top_n (int): Number of top results for departments and data types

        Returns:
            dict: Complete breach analysis
        """
        return {
            "departments": self.get_affected_departments(text, top_n),
            "data_types": self.get_compromised_data_types(text, top_n),
            "severity": self.get_breach_severity(text)
        }

    def get_simple_departments(self, text, top_n=1):
        """
        Simple helper - just return department names as list

        Args:
            text (str): Breach description
            top_n (int): Number of departments to return

        Returns:
            list: List of department names only
        """
        results = self.get_affected_departments(text, top_n)
        return [item['department'] for item in results]

    def get_simple_data_types(self, text, top_n=1):
        """
        Simple helper - just return data type names as list

        Args:
            text (str): Breach description
            top_n (int): Number of data types to return

        Returns:
            list: List of data type names only
        """
        results = self.get_compromised_data_types(text, top_n)
        return [item['data_type'] for item in results]


# Quick helper functions
def analyze_breach(text):
    """Quick function to analyze a breach"""
    classifier = BreachClassifier()
    return classifier.analyze_breach(text)


if __name__ == "__main__":
    # Initialize classifier
    classifier = BreachClassifier()

    # Example 1: Healthcare breach
    breach1 = """
    A major data breach at HealthCare Inc. exposed patient medical records, 
    including diagnoses, treatment history, prescription information, and 
    social security numbers of over 500,000 patients. The breach occurred 
    when hackers gained unauthorized access to the hospital's patient database 
    through a compromised employee login credential.
    """

    print("=" * 70)
    print("BREACH ANALYSIS - Healthcare Example")
    print("=" * 70)

    # Full analysis
    analysis = classifier.analyze_breach(breach1)

    print("\n📊 AFFECTED DEPARTMENTS:")
    for dept in analysis['departments']:
        print(f"  • {dept['department']}: {dept['confidence']:.1%}")

    print("\n🔓 COMPROMISED DATA TYPES:")
    for data in analysis['data_types']:
        print(f"  • {data['data_type']}: {data['confidence']:.1%}")

    print(f"\n⚠️  SEVERITY: {analysis['severity']['severity']}")
    print(f"   Confidence: {analysis['severity']['confidence']:.1%}")

    # Example 2: Financial breach
    breach2 = """
    A cyberattack on GlobalBank resulted in the theft of customer credit card 
    numbers, bank account details, and transaction histories. The breach affected 
    the finance department's payment processing system and compromised data from 
    the sales and customer service teams who had access to customer financial information.
    """

    print("\n" + "=" * 70)
    print("BREACH ANALYSIS - Financial Example")
    print("=" * 70)

    # Simple usage - just get department names
    departments = classifier.get_simple_departments(breach2, top_n=2)
    print(f"\n📁 Affected Departments: {', '.join(departments)}")

    # Simple usage - just get data types
    data_types = classifier.get_simple_data_types(breach2, top_n=2)
    print(f"🔐 Compromised Data: {', '.join(data_types)}")

    # Example 3: HR breach
    breach3 = """
    Employee payroll data was leaked including salary information, direct deposit 
    details, tax forms, and performance reviews. The HR department's internal 
    database was accessed by unauthorized personnel.
    """

    print("\n" + "=" * 70)
    print("BREACH ANALYSIS - HR Example")
    print("=" * 70)

    analysis3 = classifier.analyze_breach(breach3, top_n=2)
    print("\n📊 AFFECTED DEPARTMENTS:")
    for dept in analysis3['departments']:
        print(f"  • {dept['department']}: {dept['confidence']:.1%}")

    print("\n🔓 COMPROMISED DATA TYPES:")
    for data in analysis3['data_types']:
        print(f"  • {data['data_type']}: {data['confidence']:.1%}")