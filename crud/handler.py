from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import psycopg2
import logging
import os

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to connect to the database
def connect_to_db():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DATABASE_HOST", "db"),
            database=os.getenv("DATABASE_NAME", "musicdb"),
            user=os.getenv("DATABASE_USER", "postgres"),
            password=os.getenv("DATABASE_PASSWORD", "password")
        )
        cursor = conn.cursor()
        logging.info("Connected to the Postgres database.")
        return conn, cursor
    except Exception as e:
        logging.error(f"Error connecting to the database: {e}")
        raise

# Function to insert song and artist data into the database
def insert_song_data(conn, cursor, song_data, artist_data, genre, duration_ms, spotify_link, source):
    try:
        # Insert or get artist ID
        cursor.execute("""
            INSERT INTO artists (name, country, gender, disambiguation, aliases, tags)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
        """, (
            artist_data['artist_name'],
            artist_data['country'],
            artist_data['gender'],
            artist_data['disambiguation'],
            artist_data['aliases'],
            artist_data['tags']
        ))
        artist_id = cursor.fetchone()[0]

        # Insert the song data into the songs table with artist_id
        cursor.execute(
            """
            INSERT INTO songs (rank, title, artist_id, distribution_date, genre, duration_ms, spotify_link, source, album, language, artist_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                song_data['rank'],
                song_data['title'],
                artist_id,
                song_data['distribution_date'],
                genre,
                duration_ms,
                spotify_link,
                source,
                song_data.get('album', 'Unknown'),
                song_data.get('language', 'Unknown'),
                song_data.get('artist_type', 'Unknown')
            )
        )
        conn.commit()

        logging.info(f"Data for song '{song_data['title']}' inserted into the database.")

    except Exception as e:
        logging.error(f"Error inserting data into the database: {e}")
        conn.rollback()

# Close the database connection when done
def close_connection(conn, cursor):
    cursor.close()
    conn.close()

@app.get("/charts")
def get_charts_by_date(date: str):
    conn, cursor = connect_to_db()
    try:
        # Fetch charts data for all countries on the specified date
        cursor.execute("""
            SELECT s.rank, s.title, a.name AS artist, s.album, s.duration_ms, s.spotify_link, s.genre, s.language, s.artist_type, s.source, s.distribution_date
            FROM songs s
            JOIN artists a ON s.artist_id = a.id
            WHERE s.distribution_date = %s;
        """, (date,))
        results = cursor.fetchall()
        if not results:
            raise HTTPException(status_code=404, detail="No charts found for the specified date")

        charts = {}
        # Use the distribution date from the first result (they should all be the same)
        distribution_date = results[0][10] if results else date

        for result in results:
            country = result[9]  # Replace with actual country source if stored differently

            # Check if duration_ms is None and handle it
            duration_ms = result[4]
            if duration_ms is not None:
                duration = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02}"  # Convert ms to min:sec
            else:
                duration = "Unknown"  # Or any default value you prefer

            song_data = {
                "position": result[0],
                "song": result[1],
                "artist": result[2],
                "album": result[3],
                "duration": duration,
                "spotify_url": result[5],
                "songFeatures": {
                    "key": "F# Major",  # Example value; replace with actual data if available
                    "genre": result[6],
                    "language": result[7]
                },
                "artistFeatures": {
                    "type": result[8]
                }
            }
            if country not in charts:
                charts[country] = []
            charts[country].append(song_data)

        return {"date": distribution_date.strftime("%Y-%m-%d"), "charts": charts}

    except Exception as e:
        logging.error(f"Error fetching charts: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        close_connection(conn, cursor)

@app.get("/charts/available-dates")
def get_available_chart_dates():
    conn, cursor = connect_to_db()
    try:
        cursor.execute("""
            SELECT DISTINCT EXTRACT(YEAR FROM distribution_date) AS year,
                            EXTRACT(MONTH FROM distribution_date) AS month,
                            EXTRACT(DAY FROM distribution_date) AS day
            FROM songs;
        """)
        results = cursor.fetchall()
        dates = {}
        for year, month, day in results:
            year = int(year)
            month = int(month)
            day = int(day)
            if year not in dates:
                dates[year] = {}
            if month not in dates[year]:
                dates[year][month] = []
            dates[year][month].append(day)

        return JSONResponse(content=dates)

    except Exception as e:
        logging.error(f"Error fetching available dates: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        close_connection(conn, cursor)
