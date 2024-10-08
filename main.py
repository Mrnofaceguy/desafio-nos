import csv
import re
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Existing data dictionary to store postal code, concelho, and distrito
existing_data = {}

def is_valid_postal_code(code):
    """Validate postal code format."""
    return re.match(r'^\d{4}-\d{3}$', code) is not None

def load_existing_data(file_path):
    """Load data from CSV into the dictionary."""
    data = {}
    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                postal_code = row.get("cp7")
                concelho = row.get("concelho", "")
                distrito = row.get("distrito", "")
                if postal_code:
                    data[postal_code] = (concelho, distrito)
    except FileNotFoundError:
        print(f"{file_path} not found. Starting with an empty database.")
    return data

def update_csv(file_path, data):
    """Write the updated data back to the CSV."""
    fieldnames = ["cp7", "concelho", "distrito"]
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for postal_code, (concelho, distrito) in data.items():
            writer.writerow({"cp7": postal_code, "concelho": concelho, "distrito": distrito})

def request_api_data(api_url, postal_code):
    """Request data from the API for missing concelho and distrito."""
    try:
        api_response = requests.get(f'{api_url}/{postal_code}')
        api_response.raise_for_status()
        
        # Ensure the response is decoded properly
        api_response.encoding = 'utf-8'  # Force response to UTF-8
        api_data = api_response.json()

        if isinstance(api_data, list) and len(api_data) > 0:
            first_entry = api_data[0]
            concelho = first_entry.get("concelho", "")
            distrito = first_entry.get("distrito", "")
            return concelho, distrito
        else:
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"API request failed for {postal_code}: {e}")
        return None, None

# API endpoint to get all postal codes
@app.route('/postal-codes', methods=['GET'])
def get_all_postal_codes():
    """Return all postal code data."""
    return jsonify(existing_data)

# API endpoint to get a specific postal code's data
@app.route('/postal-codes/<postal_code>', methods=['GET'])
def get_postal_code(postal_code):
    """Return data for a specific postal code."""
    if postal_code in existing_data:
        concelho, distrito = existing_data[postal_code]
        return jsonify({"postal_code": postal_code, "concelho": concelho, "distrito": distrito})
    else:
        return jsonify({"error": "Postal code not found"}), 404

# API endpoint to update missing data using the external API
@app.route('/postal-codes/update', methods=['POST'])
def update_postal_codes():
    """Update postal codes without concelho or distrito using the external API."""
    global existing_data
    updated_count = 0

    api_key = request.json.get('api_key')  # Expecting API key in the request body
    api_url = f'https://www.cttcodigopostal.pt/api/v1/{api_key}'
    
    # Update only postal codes missing concelho and distrito
    for postal_code, (concelho, distrito) in existing_data.items():
        if not concelho or not distrito:
            print(f"Requesting data for postal code: {postal_code}")
            new_concelho, new_distrito = request_api_data(api_url, postal_code)
            if new_concelho and new_distrito:
                existing_data[postal_code] = (new_concelho, new_distrito)
                updated_count += 1

    update_csv(output_csv, existing_data)  # Save updated data back to CSV

    return jsonify({"message": f"{updated_count} postal codes updated successfully."})

# Start the Flask app
if __name__ == '__main__':
    api_file = 'secrets.txt'
    with open(api_file, 'r', encoding='utf-8') as file:
        api_key = file.readline().strip()

    output_csv = 'updated_data.csv'  # Define the output file

    # Load the existing data from the CSV into an internal dictionary
    existing_data = load_existing_data(output_csv)

    # Start the Flask server
    app.run(debug=True)
