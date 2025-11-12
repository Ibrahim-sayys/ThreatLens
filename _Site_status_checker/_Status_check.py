import csv
import requests

def check_site_status(url):
    proxies = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'} if '.onion' in url else None
    try:
        response = requests.get(url, timeout=30, proxies=proxies)
        if response.status_code == 200:
            return 'online'
        else:
            return 'offline'
    except requests.RequestException:
        return 'offline'

def main():
    input_csv = '../Dataset_Generation_from_urls/input_url_for_initial_testing.csv'
    output_csv = 'site_status_output.csv'

    with open(input_csv, 'r', newline='') as infile, open(output_csv, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = (reader.fieldnames or []) + ['status']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            url = row.get('urls')  # Assuming the column is named 'urls'
            if url:
                status = check_site_status(url)
                row['status'] = status
                writer.writerow(row)
            else:
                # If no url, still write the row with empty status
                row['status'] = 'no_url'
                writer.writerow(row)

if __name__ == '__main__':
    main()
