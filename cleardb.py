import psycopg2

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
        print("Cannot connect to database")
        return None

def delete_data_from_table(table_name):
    conn = get_db_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()
        
        # Execute the DELETE statement to remove all rows from the table
        cur.execute(f"DELETE FROM {table_name};")
        
        # Commit the transaction
        conn.commit()
        
        print(f"All data from table '{table_name}' deleted successfully.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"An error occurred while deleting data from table {table_name}: {e}")

if __name__ == "__main__":
    # List of tables to delete data from
    tables_to_delete = ["songs", "artists"]  # Add more tables if needed

    for table in tables_to_delete:
        delete_data_from_table(table)
