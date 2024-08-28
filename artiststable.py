import psycopg2
import json

def fetch_artists_data():
    connection = None
    cursor = None
    try:
        # Connect to your postgres DB
        connection = psycopg2.connect(
            host="localhost",  # Use 'localhost' for local connections
            database="musicdb",
            user="postgres",
            password="password"
        )

        # Create a cursor object
        cursor = connection.cursor()

        # Query to fetch all data from the artists table
        fetch_query = "SELECT * FROM artists;"

        # Execute the query
        cursor.execute(fetch_query)

        # Fetch all rows from the result
        artists_data = cursor.fetchall()

        # Get column names
        column_names = [desc[0] for desc in cursor.description]

        # Convert to a list of dictionaries
        artists_list = [dict(zip(column_names, row)) for row in artists_data]

        # Save the data as a JSON file in the root directory
        with open('artists_data.json', 'w', encoding='utf-8') as json_file:
            json.dump(artists_list, json_file, ensure_ascii=False, indent=4)

        print("Data saved to 'artists_data.json' successfully.")

    except Exception as error:
        print(f"Error fetching data: {error}")
    
    finally:
        # Close the cursor and connection
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

if __name__ == "__main__":
    fetch_artists_data()
