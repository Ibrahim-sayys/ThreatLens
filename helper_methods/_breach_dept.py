# _breach_dept_extractor_spacy.py
import spacy
from spacy.matcher import PhraseMatcher
import re


class SpacyDepartmentExtractor:
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spaCy model...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")

        # Comprehensive department patterns with variations
        self.department_patterns = {
            # Technology & IT
            "IT": [
                "it", "information technology", "tech", "technology", "cyber",
                "cybersecurity", "security team", "infosec", "information security",
                "it department", "technical team", "tech team", "systems", "infrastructure",
                "network", "networking", "database", "server", "cloud", "devops",
                "software", "hardware", "helpdesk", "service desk", "sysadmin",
                "system administrator", "network administrator", "it support"
            ],

            # Finance & Accounting
            "Finance": [
                "finance", "financial", "accounting", "accounts", "treasury",
                "billing", "accounts payable", "accounts receivable", "ap", "ar",
                "payroll", "accounting department", "finance team", "financial services",
                "audit", "internal audit", "external audit", "tax", "taxation",
                "bookkeeping", "controller", "comptroller", "revenue", "budgeting",
                "expense", "invoice", "payment processing", "financial planning"
            ],

            # Human Resources
            "HR": [
                "hr", "human resources", "personnel", "recruitment", "hiring",
                "talent acquisition", "employee relations", "benefits", "compensation",
                "onboarding", "training", "learning and development", "l&d",
                "workforce", "staffing", "people operations", "people ops",
                "employee services", "hr department", "human capital", "talent management",
                "performance management", "employee engagement"
            ],

            # Sales & Business Development
            "Sales": [
                "sales", "business development", "revenue", "sales team",
                "account management", "account manager", "sales department",
                "inside sales", "outside sales", "field sales", "telesales",
                "sales operations", "sales ops", "crm", "customer relationship",
                "lead generation", "pipeline", "deals", "contracts", "proposals",
                "quotas", "territory", "channel sales", "partner sales"
            ],

            # Marketing & Communications
            "Marketing": [
                "marketing", "advertising", "promotion", "brand", "branding",
                "digital marketing", "content marketing", "social media",
                "communications", "public relations", "pr", "media relations",
                "creative", "creative services", "design", "graphics",
                "marketing operations", "demand generation", "campaign",
                "seo", "sem", "email marketing", "product marketing",
                "market research", "analytics", "growth marketing"
            ],

            # Customer Service & Support
            "Customer Service": [
                "customer service", "customer support", "support", "helpdesk",
                "call center", "contact center", "service desk", "customer care",
                "client services", "customer success", "customer experience",
                "cx", "cs", "support team", "technical support", "tech support",
                "customer operations", "customer relations", "client support",
                "ticket", "case management", "escalation", "service level"
            ],

            # Legal & Compliance
            "Legal": [
                "legal", "compliance", "regulatory", "audit", "legal department",
                "corporate counsel", "general counsel", "in-house counsel",
                "legal affairs", "legal team", "contracts", "intellectual property",
                "ip", "patent", "trademark", "litigation", "dispute resolution",
                "governance", "risk management", "grc", "policy", "regulatory affairs",
                "data protection", "privacy", "gdpr", "hipaa", "sox", "pci"
            ],

            # Operations & Logistics
            "Operations": [
                "operations", "ops", "logistics", "supply chain", "warehouse",
                "distribution", "fulfillment", "inventory", "operations team",
                "business operations", "operational", "facilities", "facility management",
                "procurement operations", "order management", "shipping", "receiving",
                "transportation", "fleet", "supply chain management", "scm"
            ],

            # Research & Development
            "R&D": [
                "r&d", "research", "development", "innovation", "research and development",
                "product development", "engineering", "r&d team", "lab", "laboratory",
                "innovation team", "product engineering", "design engineering",
                "prototype", "testing", "quality assurance", "qa", "qc", "quality control"
            ],

            # Administration
            "Admin": [
                "admin", "administration", "administrative", "office management",
                "office admin", "administrative services", "general admin",
                "back office", "administrative support", "receptionist", "front desk",
                "office operations", "admin team", "clerical", "secretarial"
            ],

            # Procurement & Purchasing
            "Procurement": [
                "procurement", "purchasing", "sourcing", "strategic sourcing",
                "procurement team", "buyer", "purchasing department", "vendor management",
                "supplier management", "contract management", "spend management",
                "category management", "procurement operations"
            ],

            # Executive & Management
            "Executive": [
                "executive", "management", "c-suite", "ceo", "cfo", "cto", "cio",
                "coo", "cmo", "chro", "chief", "president", "vice president",
                "vp", "director", "senior management", "leadership", "board",
                "executive team", "senior leadership", "top management", "csuite"
            ],

            # Manufacturing & Production
            "Manufacturing": [
                "manufacturing", "production", "plant", "factory", "assembly",
                "production line", "manufacturing operations", "shop floor",
                "process engineering", "industrial", "fabrication", "machining",
                "quality", "production control", "manufacturing engineering"
            ],

            # Healthcare Specific
            "Medical": [
                "medical", "clinical", "healthcare", "health services", "patient care",
                "nursing", "physician", "doctor", "nurse", "medical records",
                "patient services", "radiology", "pharmacy", "laboratory services",
                "emergency", "surgery", "outpatient", "inpatient"
            ],

            # Retail & Store Operations
            "Retail": [
                "retail", "store", "store operations", "merchant", "merchandising",
                "point of sale", "pos", "cashier", "checkout", "store management",
                "retail operations", "ecommerce", "e-commerce", "online store"
            ],

            # Education & Training
            "Education": [
                "education", "training", "learning", "academic", "instruction",
                "teaching", "faculty", "educational services", "student services",
                "curriculum", "course", "enrollment", "registrar"
            ],

            # Real Estate & Facilities
            "Facilities": [
                "facilities", "facility", "real estate", "property management",
                "building management", "maintenance", "janitorial", "hvac",
                "facilities management", "fm", "workplace services", "estate management"
            ],

            # Risk & Security
            "Security": [
                "security", "physical security", "security operations", "guard",
                "surveillance", "access control", "security team", "protection",
                "safety", "corporate security", "loss prevention"
            ],

            # Data & Analytics
            "Data Analytics": [
                "data", "analytics", "data science", "data analytics", "business intelligence",
                "bi", "reporting", "insights", "data engineering", "data warehouse",
                "big data", "data management", "master data", "data governance"
            ],

            # Product Management
            "Product": [
                "product", "product management", "product team", "product manager",
                "product development", "product strategy", "roadmap", "product owner",
                "agile", "scrum", "product operations"
            ],

            # Government & Public Sector
            "Government": [
                "government", "public sector", "municipal", "federal", "state",
                "county", "city", "public services", "civil service", "administration"
            ],

            # Insurance
            "Insurance": [
                "insurance", "underwriting", "claims", "policy", "actuarial",
                "risk assessment", "insurance operations", "benefits administration"
            ],

            # Banking
            "Banking": [
                "banking", "bank", "branch", "teller", "loan", "mortgage",
                "credit", "deposits", "wealth management", "private banking",
                "retail banking", "commercial banking", "investment banking"
            ]
        }

        # Create phrase matcher
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")

        # Add patterns
        for dept, patterns in self.department_patterns.items():
            patterns_docs = [self.nlp.make_doc(pattern) for pattern in patterns]
            self.matcher.add(dept, patterns_docs)

        print("SpaCy Department Extractor initialized with comprehensive patterns")

    def extract_departments(self, text):
        """Extract departments based on context and keywords"""
        if not text or not text.strip():
            return ["General Breach"]

        doc = self.nlp(text.lower())
        matches = self.matcher(doc)

        # Get unique departments
        departments = list(set([self.nlp.vocab.strings[match_id] for match_id, _, _ in matches]))

        # Infer additional departments based on context
        inferred = self._infer_from_context(text.lower())
        departments.extend(inferred)

        # Remove duplicates
        departments = list(set(departments))

        # If no departments found, return "General Breach"
        if not departments:
            return ["General Breach"]

        return sorted(departments)  # Return sorted for consistency

    def _infer_from_context(self, text):
        """Infer departments based on breach context and data types"""
        inferred = []

        # Financial data indicators
        financial_keywords = [
            "credit card", "debit card", "payment", "financial", "bank", "transaction",
            "account number", "routing number", "swift", "iban", "card number",
            "cvv", "pin", "balance", "statement", "wire transfer"
        ]
        if any(word in text for word in financial_keywords):
            inferred.extend(["Finance", "Customer Service"])

        # Authentication & Access
        auth_keywords = [
            "login", "credential", "password", "authentication", "username",
            "access", "authorization", "token", "session", "api key",
            "private key", "certificate", "oauth", "sso", "2fa", "mfa"
        ]
        if any(word in text for word in auth_keywords):
            inferred.append("IT")

        # Employee/HR data
        hr_keywords = [
            "employee", "staff", "personnel", "salary", "ssn", "social security",
            "tax id", "w2", "w-2", "ein", "paycheck", "benefit", "401k",
            "employment", "hire date", "termination", "performance review"
        ]
        if any(word in text for word in hr_keywords):
            inferred.append("HR")

        # Customer data
        customer_keywords = [
            "customer", "client", "user", "subscriber", "member", "account holder",
            "consumer", "buyer", "purchaser", "shopper"
        ]
        if any(word in text for word in customer_keywords):
            inferred.extend(["Customer Service", "Sales"])

        # Email/Communication
        if any(word in text for word in ["email", "inbox", "message", "communication"]):
            inferred.append("IT")

        # Healthcare/Medical
        medical_keywords = [
            "patient", "medical", "health", "hipaa", "phi", "diagnosis",
            "prescription", "treatment", "clinical", "medical record"
        ]
        if any(word in text for word in medical_keywords):
            inferred.extend(["Medical", "IT", "Legal"])

        # Personal Identifiable Information (PII)
        pii_keywords = [
            "pii", "personal data", "personally identifiable", "name", "address",
            "phone number", "date of birth", "dob", "driver license", "passport"
        ]
        if any(word in text for word in pii_keywords):
            inferred.extend(["IT", "Legal"])

        # Intellectual Property
        ip_keywords = [
            "intellectual property", "trade secret", "proprietary", "confidential",
            "patent", "trademark", "copyright", "source code", "design"
        ]
        if any(word in text for word in ip_keywords):
            inferred.extend(["Legal", "R&D"])

        # Contract/Agreement data
        if any(word in text for word in ["contract", "agreement", "terms", "nda"]):
            inferred.extend(["Legal", "Sales"])

        # Database/System breach
        system_keywords = [
            "database", "server", "system", "network", "cloud", "backup",
            "data breach", "cyber attack", "ransomware", "malware", "phishing"
        ]
        if any(word in text for word in system_keywords):
            inferred.append("IT")

        # Retail/E-commerce
        retail_keywords = [
            "order", "purchase", "shopping", "cart", "checkout", "product",
            "inventory", "sku", "catalog", "store"
        ]
        if any(word in text for word in retail_keywords):
            inferred.extend(["Retail", "Operations"])

        # Insurance specific
        if any(word in text for word in ["policy", "claim", "premium", "coverage", "insured"]):
            inferred.append("Insurance")

        # Banking specific
        if any(word in text for word in ["loan", "mortgage", "deposit", "withdrawal", "atm"]):
            inferred.append("Banking")

        return inferred

    def analyze_breach(self, text, return_details=False):
        """
        Analyze breach and optionally return detailed information

        Args:
            text: Breach description
            return_details: If True, returns dict with departments and confidence

        Returns:
            List of departments or dict with details
        """
        departments = self.extract_departments(text)

        if not return_details:
            return departments

        return {
            "departments": departments,
            "is_general": departments == ["General Breach"],
            "department_count": len(departments),
            "original_text": text[:100] + "..." if len(text) > 100 else text
        }


# Usage Examples
if __name__ == "__main__":
    extractor = SpacyDepartmentExtractor()

    test_cases = [
        "A cyberattack exposed customer credit card details and login credentials.",
        "Employee payroll information and SSN numbers were leaked in a data breach.",
        "The IT department discovered unauthorized access to the company's financial systems.",
        "Patient medical records were compromised affecting the healthcare provider.",
        "Unknown breach occurred in the organization.",  # Should return "General Breach"
        "Data was stolen.",  # Should return "General Breach"
        "Ransomware attack encrypted all company files including contracts and proposals.",
        "Email system compromised exposing internal communications.",
        "Point of sale systems at retail stores were infected with malware.",
        "Cloud backup containing customer data was publicly accessible.",
        "",  # Empty text - should return "General Breach"
    ]

    print("=" * 80)
    print("DEPARTMENT EXTRACTION TEST RESULTS")
    print("=" * 80 + "\n")

    for i, text in enumerate(test_cases, 1):
        print(f"Test Case #{i}:")
        print(f"Text: {text if text else '(Empty text)'}")
        print("-" * 60)

        # Simple extraction
        departments = extractor.extract_departments(text)
        print(f"Departments: {', '.join(departments)}")

        # Detailed analysis
        details = extractor.analyze_breach(text, return_details=True)
        print(f"Is General Breach: {details['is_general']}")
        print(f"Total Departments: {details['department_count']}")
        print("\n" + "=" * 80 + "\n")