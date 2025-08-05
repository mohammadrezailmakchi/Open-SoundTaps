import sqlite3
import os
from pathlib import Path
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError

DB_FILE = "music_library.db"

def connect():
    """Connects to the SQLite database and returns the connection and cursor."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn, conn.cursor()

def create_tables():
    """Creates the necessary database tables if they don't exist."""
    conn, c = connect()
    c.execute('''
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS albums (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            artist_id INTEGER,
            FOREIGN KEY (artist_id) REFERENCES artists (id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            path TEXT UNIQUE NOT NULL,
            duration REAL,
            album_id INTEGER,
            artist_id INTEGER,
            FOREIGN KEY (album_id) REFERENCES albums (id),
            FOREIGN KEY (artist_id) REFERENCES artists (id)
        )
    ''')
    conn.commit()
    conn.close()
    print("Database tables created or already exist.")

def get_or_create_artist(c, artist_name):
    """Gets the ID of an artist, creating them if they don't exist."""
    c.execute("SELECT id FROM artists WHERE name = ?", (artist_name,))
    result = c.fetchone()
    if result:
        return result['id']
    c.execute("INSERT INTO artists (name) VALUES (?)", (artist_name,))
    return c.lastrowid

def get_or_create_album(c, album_name, artist_id):
    """Gets the ID of an album, creating it if it doesn't exist."""
    c.execute("SELECT id FROM albums WHERE name = ? AND artist_id = ?", (album_name, artist_id))
    result = c.fetchone()
    if result:
        return result['id']
    c.execute("INSERT INTO albums (name, artist_id) VALUES (?, ?)", (album_name, artist_id))
    return c.lastrowid

def sync_library(music_folder, progress_callback):
    """Scans a folder and syncs it with the database."""
    conn, c = connect()
    
    # 1. Get all song paths from the database
    c.execute("SELECT id, path FROM songs")
    db_songs = {row['path']: row['id'] for row in c.fetchall()}
    
    # 2. Get all MP3 files from the filesystem
    disk_songs = set(str(p) for p in Path(music_folder).rglob("*.mp3"))
    db_paths = set(db_songs.keys())

    # 3. Find new songs to add
    new_songs = disk_songs - db_paths
    for i, file_path in enumerate(new_songs):
        try:
            audio = MP3(file_path, ID3=EasyID3)
            duration = audio.info.length
            
            # Use .get() to avoid errors with missing tags
            artist_name = audio.get('artist', ['Unknown Artist'])[0]
            album_name = audio.get('album', ['Unknown Album'])[0]
            title = audio.get('title', [Path(file_path).stem])[0]

            artist_id = get_or_create_artist(c, artist_name)
            album_id = get_or_create_album(c, album_name, artist_id)

            c.execute(
                "INSERT INTO songs (title, path, duration, album_id, artist_id) VALUES (?, ?, ?, ?, ?)",
                (title, file_path, duration, album_id, artist_id)
            )
            progress_callback(f"Added: {title}")
        except (ID3NoHeaderError, Exception) as e:
            progress_callback(f"Could not read: {Path(file_path).name} - {e}")

    # 4. Find deleted songs to remove
    deleted_songs = db_paths - disk_songs
    for file_path in deleted_songs:
        c.execute("DELETE FROM songs WHERE path = ?", (file_path,))
        progress_callback(f"Removed: {Path(file_path).name}")

    conn.commit()
    conn.close()
    progress_callback("Sync complete!")