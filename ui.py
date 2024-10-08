import sqlite3
import requests
import re
import csv

# Path to the SQLite database file
DATABASE = 'postal_data.db'

# Path to the original CSV file
CSV_FILE = 'original_data.csv'

# Function to connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Returns rows as dictionaries
    return conn

# Function to create the postal_codes table if it doesn't exist
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS postal_codes (
            postal_code TEXT PRIMARY KEY,
            concelho TEXT,
            distrito TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Function to check if postal code format is valid
def is_valid_postal_code(code):
    return re.match(r'^\d{4}-\d{3}$', code) is not None

# Function to load all postal codes from the database
def load_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM postal_codes")
    data = cursor.fetchall()
    conn.close()
    return data

# Function to search for a specific postal code in the database
def search_postal_code(postal_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM postal_codes WHERE postal_code = ?", (postal_code,))
    result = cursor.fetchone()
    conn.close()
    return result

# Function to update or insert data from an API
def update_postal_code(api_key, postal_code):
    try:
        # API call
        api_response = requests.get(f'https://www.cttcodigopostal.pt/api/v1/{api_key}/{postal_code}')
        api_data = api_response.json()

        # If we get valid data
        if isinstance(api_data, list) and len(api_data) > 0:
            first_entry = api_data[0]
            concelho = first_entry.get("concelho")
            distrito = first_entry.get("distrito")

            # Insert or update the database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO postal_codes (postal_code, concelho, distrito)
                VALUES (?, ?, ?)
                ON CONFLICT(postal_code) DO UPDATE SET concelho = ?, distrito = ?
            ''', (postal_code, concelho, distrito, concelho, distrito))
            conn.commit()
            conn.close()

            print(f"Data updated: {postal_code} - {concelho}, {distrito}")
        else:
            print(f"No data found for postal code {postal_code}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to update postal code {postal_code}: {e}")

# Function to update missing data from the API
def update_missing_data(api_key):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT postal_code FROM postal_codes WHERE concelho IS NULL OR distrito IS NULL")
    missing_postal_codes = cursor.fetchall()
    
    if not missing_postal_codes:
        print("No missing data to update.")
        return

    for row in missing_postal_codes:
        postal_code = row['postal_code']
        update_postal_code(api_key, postal_code)

    conn.close()

# Function to read data from CSV and update database using the API
def load_data_from_csv(api_key):
    with open(CSV_FILE, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            postal_code = row.get("cp7")  # Assuming the column name for postal code is "cp7"
            
            if postal_code and is_valid_postal_code(postal_code):
                result = search_postal_code(postal_code)
                
                if result:
                    # If data exists, skip API request
                    print(f"Postal code {postal_code} already exists in the database.")
                else:
                    # If data is missing, request data from the API
                    print(f"Requesting data for postal code: {postal_code}")
                    update_postal_code(api_key, postal_code)

# Menu to allow the user to choose actions
def menu(api_key):
    while True:
        print("\nMenu:")
        print("1. View all postal codes")
        print("2. Search for a postal code")
        print("3. Update missing data from API")
        print("4. Load data from CSV and update the database")
        print("5. Exit")

        choice = input("Select an option: ")

        if choice == '1':
            data = load_data()
            if data:
                print("\nPostal Codes Data:")
                for row in data:
                    print(f"{row['postal_code']}: {row['concelho']}, {row['distrito']}")
            else:
                print("No data available.")

        elif choice == '2':
            postal_code = input("Enter postal code (format: xxxx-xxx): ")
            if is_valid_postal_code(postal_code):
                result = search_postal_code(postal_code)
                if result:
                    print(f"Postal Code {postal_code}: Concelho: {result['concelho']}, Distrito: {result['distrito']}")
                else:
                    print(f"Postal code {postal_code} not found in database.")
                    update_postal_code(api_key, postal_code)  # Prompt to update the code from API if missing
            else:
                print("Invalid postal code format. Try again.")

        elif choice == '3':
            update_missing_data(api_key)

        elif choice == '4':
            load_data_from_csv(api_key)

        elif choice == '5':
            print("Exiting...")
            break

        else:
            print("Invalid option. Please try again.")

# Main execution block
if __name__ == "__main__":
    # Set up the SQLite database table if it doesn't exist
    create_table()

    # Read API key from secrets.txt file
    api_file = 'secrets.txt'
    with open(api_file, 'r') as file:
        api_key = file.readline().strip()

    # Start the menu-driven application
    menu(api_key)
