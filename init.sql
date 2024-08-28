CREATE TABLE artists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE,
    country VARCHAR(255),
    gender VARCHAR(50),
    disambiguation VARCHAR(255),
    aliases TEXT,
    tags TEXT
);

CREATE TABLE songs (
    id SERIAL PRIMARY KEY,
    rank INT,  -- Changed to INTEGER for numerical operations
    title VARCHAR(255),
    artist_id INT,  -- Foreign key referencing artists table
    distribution_date DATE,  -- Changed to DATE for proper date handling
    genre VARCHAR(255),
    duration_ms BIGINT,
    spotify_link TEXT,
    source VARCHAR(64),
    album VARCHAR(255),
    language VARCHAR(50),
    artist_type VARCHAR(50),
    CONSTRAINT fk_artist
        FOREIGN KEY(artist_id) 
        REFERENCES artists(id)
);
