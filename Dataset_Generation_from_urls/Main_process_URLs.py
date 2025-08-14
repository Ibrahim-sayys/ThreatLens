from _process_URLs import process_urls

if __name__ == "__main__":
    input_csv = "input_url_for_initial_testing.csv"
    output_csv = "output_keywords.csv"
    process_urls(input_csv, output_csv)