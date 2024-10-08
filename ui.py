import requests

# Replace this with the URL of the running Flask API
api_base_url = 'http://127.0.0.1:5000'

def print_menu():
    """Display the menu options."""
    print("\n1. View All Postal Code Data")
    print("2. Search for a Postal Code")
    print("3. Update Missing Data (Request from External API)")
    print("4. Exit")

def view_all_data():
    """Fetch and display all postal code data from the API."""
    try:
        response = requests.get(f'{api_base_url}/postal-codes')
        if response.status_code == 200:
            data = response.json()
            if data:
                for postal_code, details in data.items():
                    print(f"Postal Code: {postal_code}, Concelho: {details[0]}, Distrito: {details[1]}")
            else:
                print("No data found.")
        else:
            print(f"Error fetching data: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to the API: {e}")

def search_postal_code():
    """Search for a specific postal code."""
    postal_code = input("Enter the postal code to search (format: xxxx-xxx): ")
    try:
        response = requests.get(f'{api_base_url}/postal-codes/{postal_code}')
        if response.status_code == 200:
            data = response.json()
            if 'error' in data:
                print(data['error'])
            else:
                print(f"Postal Code: {data['postal_code']}, Concelho: {data['concelho']}, Distrito: {data['distrito']}")
        else:
            print(f"Postal code not found. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to the API: {e}")

def update_missing_data():
    """Update missing postal codes by requesting data from the external API."""
    api_key = input("Enter the API key to fetch data: ")
    try:
        response = requests.post(f'{api_base_url}/postal-codes/update', json={'api_key': api_key})
        if response.status_code == 200:
            result = response.json()
            print(result["message"])
        else:
            print(f"Error updating data. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to the API: {e}")

def main():
    """Main function to run the client-side application."""
    while True:
        print_menu()
        choice = input("Choose an option (1-4): ")

        if choice == '1':
            view_all_data()
        elif choice == '2':
            search_postal_code()
        elif choice == '3':
            update_missing_data()
        elif choice == '4':
            print("Exiting the program.")
            break
        else:
            print("Invalid option. Please choose a valid menu option.")

if __name__ == "__main__":
    main()
