import sqlite3
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# Path to SQLite database file
DATABASE = 'postal_data.db'

# Function to connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # To return rows as dictionaries
    return conn

# Route to get all postal codes
@app.route('/postal-codes', methods=['GET'])
def get_all_postal_codes():
    """Fetch all postal code data from the SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM postal_codes")
    rows = cursor.fetchall()
    conn.close()

    postal_codes = [
        {"postal_code": row["postal_code"], "concelho": row["concelho"], "distrito": row["distrito"]}
        for row in rows
    ]
    return jsonify(postal_codes)

# Route to get a specific postal code
@app.route('/postal-codes/<postal_code>', methods=['GET'])
def get_postal_code(postal_code):
    """Fetch a specific postal code from the SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM postal_codes WHERE postal_code = ?", (postal_code,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({"postal_code": row["postal_code"], "concelho": row["concelho"], "distrito": row["distrito"]})
    else:
        return jsonify({"error": f"Postal code {postal_code} not found."}), 404

# Route to update missing postal codes from an external API
@app.route('/postal-codes/update', methods=['POST'])
def update_postal_codes():
    """Update missing concelho and distrito data from external API."""
    api_key = request.json.get('api_key')
    if not api_key:
        return jsonify({"error": "API key is required."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT postal_code FROM postal_codes WHERE concelho IS NULL OR distrito IS NULL")
    missing_postal_codes = cursor.fetchall()

    if not missing_postal_codes:
        return jsonify({"message": "No missing data to update."}), 200

    for row in missing_postal_codes:
        postal_code = row["postal_code"]
        try:
            # Make the API call
            response = requests.get(f'https://www.cttcodigopostal.pt/api/v1/{api_key}/{postal_code}')
            api_data = response.json()

            if isinstance(api_data, list) and len(api_data) > 0:
                first_entry = api_data[0]
                concelho = first_entry.get("concelho")
                distrito = first_entry.get("distrito")

                # Update the database
                cursor.execute(
                    "UPDATE postal_codes SET concelho = ?, distrito = ? WHERE postal_code = ?",
                    (concelho, distrito, postal_code)
                )
                conn.commit()

        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch data for postal code {postal_code}: {e}")

    cursor.close()
    conn.close()
    return jsonify({"message": "Missing data updated successfully."}), 200

if __name__ == '__main__':
    app.run(debug=True)
