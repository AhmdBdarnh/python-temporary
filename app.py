import psycopg2
import json

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",  # Use 'localhost' for local connections
            database="musicdb",
            user="postgres",
            password="password"
        )
        return conn
    except psycopg2.OperationalError as e:
        print("Cannot connect to the database")
        return None


def fetch_songs():
    conn = get_db_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM songs;')
        rows = cur.fetchall()

        # Fetching the column names from the cursor description
        column_names = [desc[0] for desc in cur.description]

        # Converting the result to a list of dictionaries
        songs_list = [dict(zip(column_names, row)) for row in rows]

        cur.close()
        conn.close()

        # Saving the result to a JSON file
        with open('songs.json', 'w', encoding='utf-8') as f:
            json.dump(songs_list, f, ensure_ascii=False, indent=4)

        print("Data saved to songs.json")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    fetch_songs()
