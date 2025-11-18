#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Industry Extractor Helper Method
Classifies company descriptions into industry categories using AI/ML.
"""

import warnings
warnings.filterwarnings('ignore')

# Try to import required libraries
try:
    from transformers import pipeline
    import torch
    DEPENDENCIES_AVAILABLE = True
    print("AI/ML dependencies found - will use advanced classification.")
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("Warning: Required dependencies (transformers, torch) not found.")
    print("Industry classification will use fallback method.")


class IndustryClassifier:
    def __init__(self):
        """Initialize the classifier with predefined industry categories"""
        self.industries = [
            "Banking and Financial Services",
            "Healthcare and Medical",
            "Technology and Software",
            "Manufacturing and Industrial",
            "Retail and E-commerce",
            "Transportation and Logistics",
            "Security Services",
            "Real Estate and Construction",
            "Education and Training",
            "Hospitality and Tourism",
            "Energy and Utilities",
            "Telecommunications",
            "Consulting and Professional Services",
            "Media and Entertainment",
            "Agriculture and Food",
            "Automotive",
            "Pharmaceuticals",
            "Insurance",
            "Government and Public Sector",
            "Legal Services",
            "Marketing and Advertising",
            "Non-profit and Charity"
        ]

        if DEPENDENCIES_AVAILABLE:
            print("Loading AI model... (this may take a moment on first run)")
            try:
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli"
                )
                self.use_ai = True
                print("AI model loaded successfully!")
            except Exception as e:
                print(f"Failed to load AI model: {e}")
                print("Falling back to keyword-based classification.")
                self.use_ai = False
        else:
            print("Using keyword-based industry classification (AI model not available).")
            self.use_ai = False

        # Keyword mappings for fallback classification
        self.keyword_industries = {
            "bank": "Banking and Financial Services",
            "finance": "Banking and Financial Services",
            "financial": "Banking and Financial Services",
            "insurance": "Insurance",
            "healthcare": "Healthcare and Medical",
            "medical": "Healthcare and Medical",
            "hospital": "Healthcare and Medical",
            "clinic": "Healthcare and Medical",
            "pharma": "Pharmaceuticals",
            "pharmaceutical": "Pharmaceuticals",
            "drug": "Pharmaceuticals",
            "software": "Technology and Software",
            "technology": "Technology and Software",
            "tech": "Technology and Software",
            "it": "Technology and Software",
            "computer": "Technology and Software",
            "manufacturing": "Manufacturing and Industrial",
            "industrial": "Manufacturing and Industrial",
            "factory": "Manufacturing and Industrial",
            "production": "Manufacturing and Industrial",
            "retail": "Retail and E-commerce",
            "ecommerce": "Retail and E-commerce",
            "shop": "Retail and E-commerce",
            "store": "Retail and E-commerce",
            "transportation": "Transportation and Logistics",
            "logistics": "Transportation and Logistics",
            "shipping": "Transportation and Logistics",
            "delivery": "Transportation and Logistics",
            "security": "Security Services",
            "construction": "Real Estate and Construction",
            "real estate": "Real Estate and Construction",
            "property": "Real Estate and Construction",
            "building": "Real Estate and Construction",
            "education": "Education and Training",
            "school": "Education and Training",
            "university": "Education and Training",
            "training": "Education and Training",
            "hotel": "Hospitality and Tourism",
            "restaurant": "Hospitality and Tourism",
            "tourism": "Hospitality and Tourism",
            "hospitality": "Hospitality and Tourism",
            "energy": "Energy and Utilities",
            "utility": "Energy and Utilities",
            "electric": "Energy and Utilities",
            "power": "Energy and Utilities",
            "telecom": "Telecommunications",
            "telephone": "Telecommunications",
            "communication": "Telecommunications",
            "consulting": "Consulting and Professional Services",
            "consultant": "Consulting and Professional Services",
            "media": "Media and Entertainment",
            "entertainment": "Media and Entertainment",
            "film": "Media and Entertainment",
            "music": "Media and Entertainment",
            "agriculture": "Agriculture and Food",
            "food": "Agriculture and Food",
            "farming": "Agriculture and Food",
            "automotive": "Automotive",
            "car": "Automotive",
            "vehicle": "Automotive",
            "auto": "Automotive",
            "government": "Government and Public Sector",
            "public": "Government and Public Sector",
            "legal": "Legal Services",
            "law": "Legal Services",
            "attorney": "Legal Services",
            "marketing": "Marketing and Advertising",
            "advertising": "Marketing and Advertising",
            "nonprofit": "Non-profit and Charity",
            "charity": "Non-profit and Charity",
            "ngo": "Non-profit and Charity"
        }

    def _classify_by_keywords(self, text):
        """Fallback classification using keyword matching"""
        if not text or not isinstance(text, str):
            return "Unknown"

        text_lower = text.lower()
        scores = {}

        # Count keyword matches for each industry
        for keyword, industry in self.keyword_industries.items():
            if keyword in text_lower:
                if industry not in scores:
                    scores[industry] = 0
                scores[industry] += 1

        if scores:
            # Return industry with highest keyword matches
            return max(scores, key=scores.get)
        else:
            return "Unknown"

    def get_industry(self, text):
        """
        Classify the company description and return the industry name

        Args:
            text (str): Company description paragraph

        Returns:
            str: Single industry name
        """
        if not text or not isinstance(text, str):
            return "Unknown"

        if self.use_ai:
            try:
                result = self.classifier(text, self.industries)
                return result['labels'][0]
            except Exception as e:
                print(f"AI classification failed: {e}")
                return self._classify_by_keywords(text)
        else:
            return self._classify_by_keywords(text)

    def get_industry_with_confidence(self, text):
        """
        Classify and return both industry name and confidence score

        Args:
            text (str): Company description paragraph

        Returns:
            tuple: (industry_name, confidence_score)
        """
        if not text or not isinstance(text, str):
            return ("Unknown", 0.0)

        if self.use_ai:
            try:
                result = self.classifier(text, self.industries)
                return (result['labels'][0], result['scores'][0])
            except Exception as e:
                print(f"AI classification failed: {e}")
                industry = self._classify_by_keywords(text)
                return (industry, 0.5)  # Lower confidence for keyword-based
        else:
            industry = self._classify_by_keywords(text)
            return (industry, 0.5)  # Lower confidence for keyword-based


# Helper function for quick usage
def classify_industry(text):
    """
    Quick helper function to classify industry from text

    Args:
        text (str): Company description paragraph

    Returns:
        str: Industry name
    """
    classifier = IndustryClassifier()
    return classifier.get_industry(text)


# Example usage
if __name__ == "__main__":
    # Initialize classifier once
    classifier = IndustryClassifier()

    # Example 1: CODIVAL (Security Services)
    company_text = """
    Rotor Team, approved PART145 workshop, is specialized in helicopter maintenance, but also in overhaul, painting as well as avionics and optionals modifications on aircrafts : BELL 429, 212 et 505, Robinson R22 et R44, Cabri G2, Eurocopter H120, H130, H135, H155, AS350/H125, AS355.

Our technical office manages the airworthiness of your aircraft.

Established in 2011 by Sébastien Parmier, Rotor Team is composed with a dynamic team of 33 employees listening to his customers and their needs and has 65 helicopters on contract.

Our various bases at Annecy airport (crossroads between France, Switzerland and Italy), Grimaud (near Saint Tropez) and Cannes and our interventions in France or abroad, allow us availability and assistance to our customers 24/7.
    """

    industry = classifier.get_industry(company_text)
    print(f"Industry: {industry}")

    # If you want confidence score too
    industry, confidence = classifier.get_industry_with_confidence(company_text)
    print(f"\nIndustry: {industry}")
    print(f"Confidence: {confidence:.2%}")

    # Example 2: Healthcare company
    healthcare_text = """
    MedCare Hospital is a leading healthcare provider offering comprehensive medical
    services including emergency care, surgery, diagnostics, and patient rehabilitation.
    """

    industry2 = classifier.get_industry(healthcare_text)
    print(f"\nHealthcare Company Industry: {industry2}")

    # Example 3: Technology company
    tech_text = """
    apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company also offers software
    services, including 
    """

    industry3 = classifier.get_industry(tech_text)
    print(f"\nTech Company Industry: {industry3}")
