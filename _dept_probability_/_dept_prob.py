import pandas as pd
from collections import defaultdict, Counter


class IndustryDepartmentAnalyzer:
    def __init__(self, csv_path):
        """
        Initialize the analyzer with a CSV file.

        Args:
            csv_path: Path to the CSV file with 'industry' and 'department' columns
        """
        self.csv_path = csv_path
        self.df = None
        self.industry_dept_map = defaultdict(list)
        self.load_and_process_data()

    def load_and_process_data(self):
        """Load CSV and process industry-department associations."""
        try:
            self.df = pd.read_csv(self.csv_path)

            # Validate columns
            if 'industry' not in self.df.columns or 'departments' not in self.df.columns:
                raise ValueError("CSV must contain 'industry' and 'departments' columns")

            # Process each row
            for _, row in self.df.iterrows():
                industry = str(row['industry']).strip()
                departments = str(row['departments']).strip()

                # Split comma-separated departments
                dept_list = [dept.strip() for dept in departments.split(',') if dept.strip()]

                # Add to mapping
                self.industry_dept_map[industry].extend(dept_list)

            print(f"✓ Loaded {len(self.df)} rows from CSV")
            print(f"✓ Found {len(self.industry_dept_map)} unique industries")

        except FileNotFoundError:
            print(f"Error: File '{self.csv_path}' not found.")
            raise
        except Exception as e:
            print(f"Error loading CSV: {e}")
            raise

    def get_affected_departments(self, industry_name, top_n=3):
        """
        Get the top N most frequently associated departments for an industry.

        Args:
            industry_name: Name of the industry to query
            top_n: Number of top departments to return (default: 3)

        Returns:
            List of tuples: [(department, probability), ...]
        """
        industry_name = industry_name.strip()

        # Check if industry exists
        if industry_name not in self.industry_dept_map:
            available = list(self.industry_dept_map.keys())
            print(f"\n❌ Industry '{industry_name}' not found in data.")
            print(f"\nAvailable industries: {', '.join(available)}")
            return []

        # Count department frequencies
        dept_list = self.industry_dept_map[industry_name]
        dept_counter = Counter(dept_list)
        total_occurrences = len(dept_list)

        # Calculate probabilities and get top N
        dept_probabilities = [
            (dept, count / total_occurrences)
            for dept, count in dept_counter.most_common(top_n)
        ]

        return dept_probabilities

    def print_results(self, industry_name, top_n=3):
        """Print the results in a formatted way."""
        print(f"\n{'=' * 60}")
        print(f"Industry: {industry_name}")
        print(f"{'=' * 60}")

        results = self.get_affected_departments(industry_name, top_n)

        if results:
            print(f"\nTop {len(results)} most frequently associated departments:\n")
            for i, (dept, prob) in enumerate(results, 1):
                print(f"{i}. {dept:20s} - {prob * 100:.1f}% probability")

        print(f"{'=' * 60}\n")

        return results

    def list_all_industries(self):
        """Display all available industries."""
        print("\nAvailable Industries:")
        print("-" * 40)
        for industry in sorted(self.industry_dept_map.keys()):
            print(f"  • {industry}")
        print("-" * 40)


# Main execution
if __name__ == "__main__":
    # Configuration
    CSV_FILE = "/home/ibrahim-sayys/Projects/ThreatLens/_dept_probability_/Data/department_threat_DS_v1.csv"  # Change this to your CSV file path

    try:
        # Initialize analyzer
        analyzer = IndustryDepartmentAnalyzer(CSV_FILE)

        # Show available industries
        analyzer.list_all_industries()



        # Interactive mode
        print("\n" + "=" * 60)
        print("INTERACTIVE MODE")
        print("=" * 60)
        print("Enter an industry name to see affected departments (or 'quit' to exit)")

        while True:
            user_input = input("\nEnter industry name: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if user_input:
                analyzer.print_results(user_input, top_n=3)

    except Exception as e:
        print(f"\nFailed to run analyzer: {e}")