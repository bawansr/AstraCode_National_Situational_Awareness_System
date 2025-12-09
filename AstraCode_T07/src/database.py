import sqlite3
import os
import pandas as pd

#Save the database file name 
class NewsDatabase:
    def __init__(self, db_name="data/news.db"):
        self.db_name = db_name

    
    def initialize(self):
        #Resets the DB. Call this first!
        if os.path.exists(self.db_name):
            try:
                #Delete the Old database if exists 
                os.remove(self.db_name)
                print("Old database deleted")
            except:
                pass

        #Creates a connection and a cursor
        conn = self._get_connection()
        c = conn.cursor()
        
        # Create the article table 
        c.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, 
                link TEXT UNIQUE, -- Ensures each article link is stored only once
                published TEXT,
                source TEXT,
                category TEXT,     -- Risk Level
                risk_score INTEGER,
                sector TEXT,       -- Business/Social Sector
                lat REAL,
                lon REAL,
                is_upcoming INTEGER  -- 1 if future event, 0 otherwise
            )
        ''')
        conn.commit()
        conn.close()
        print(f"Database '{self.db_name}' initialized.")

    def _get_connection(self):
        # Opens and returns a connection to the SQLite database
        return sqlite3.connect(self.db_name)

    def save_article(self, data):
        
        # Open a connection to the database
        conn = self._get_connection()
        # Create a cursor to run SQL commands
        c = conn.cursor()
        try:
            # Try to insert the article into the database
            # If another article already has the same link
            # SQLite will ignore the insert
            c.execute('''
                INSERT OR IGNORE INTO articles 
                (title, link, published, source, category, risk_score, sector, lat, lon, is_upcoming) 
                VALUES (:title, :link, :published, :source, :category, :risk_score, :sector, :lat, :lon, :is_upcoming)
            ''', data)
            # If rowcount > 0 - insert was successful
            # If rowcount = 0 - insert was ignored 
            return c.rowcount > 0
        except Exception as e:
            # Print any database errors
            print(f"DB Error: {e}")
            return False
        finally:
            #Save the changes to the database 
            conn.commit()
            #Close the database connection
            conn.close()

    def fetch_latest(self, limit=1000):
        # Open a connection to the database 
        conn = self._get_connection()
        try:
            #Read the latest article from the database 
            #Newest first using DESC
            df = pd.read_sql_query(f"SELECT * FROM articles ORDER BY id DESC LIMIT {limit}", conn)
            
            #Convert the 'published' columns into an actual dataframe 
            #if a date is invalid, set it to Not a time 
            df['published_dt'] = pd.to_datetime(df['published'], utc=True, errors='coerce')
            #return the final dataframe 
            return df
        finally:
            #Always close the database 
            conn.close()

if __name__ == "__main__":
    NewsDatabase().initialize()