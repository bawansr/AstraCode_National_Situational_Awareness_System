import feedparser
import time
import os 
import json
from src.database import NewsDatabase
from src.engine import RiskEngine, load_config

class Pipeline:
    def __init__(self):
        self.db = NewsDatabase() # Object to save/read articles from SQLite
        self.engine = RiskEngine() # This initializes the AI model from engine.py
        self.config = load_config() #Loads the config (config.json)

    def run(self):
        print("--- Astra Code's Sri Lanka Situational Awareness System Online\ ---")
        print("--- AI Model is Ready ---")
        
        while True:
            # Reload configuration rules (Keywords/Locations)
            # In case user updated config.json
            self.config = load_config() 
            self.engine.reload_config()
            
            # Load sources
            sources_file = os.path.join("config", self.config['app_settings']['sources_file'])
            try:
                # Load the list of RSS sources (URLs)
                with open(sources_file, 'r') as f: 
                    feed_list = json.load(f)
            except FileNotFoundError:
                # If file not found, show error and continue with empty list
                print(f"Error: {sources_file} not found.")
                feed_list = []

            #Process each RSS source in the list 
            for source in feed_list:
                self.process_feed(source)
            # Get refresh interval
            # How many seconds to wait before next cycle
            interval = self.config['app_settings']['refresh_interval_seconds']
            print(f"--- Analyzing... (Refresh in {interval}s) ---")
            time.sleep(interval)

    #process the RSS Feed 
    def process_feed(self, source_config):
        try:
            # Download and parse the RSS feed using feedparser
            feed = feedparser.parse(source_config['url'])
            # If feed has no entries skip it 
            if not feed.entries: return

            #Only process the first five articles to avoid the heavy load 
            for entry in feed.entries[:5]:
                #Clean the article title (remove HTML, noise)
                clean_title = self.engine.preprocess(entry.title)
                
                # AI Analysis
                # Get risk category + risk score
                category, risk = self.engine.analyze_risk(clean_title)
                # Detect which sector the article belongs to
                sector = self.engine.detect_sector(clean_title)
                # Get latitude and longitude if a city name exists in the title
                lat, lon = self.engine.get_location(clean_title)
                # Check if news mentions about a future event
                is_upcoming = self.engine.detect_future_event(clean_title)
                
                #Prepare a dict containing all fields for database 
                article_data = {
                    "title": clean_title,
                    "link": entry.link,
                    "published": entry.get('published', 'Unknown'),
                    "source": source_config['name'],
                    "category": category,
                    "risk_score": risk,
                    "sector": sector,
                    "lat": lat,
                    "lon": lon,
                    "is_upcoming": is_upcoming
                }
                #Save the article into database 
                if self.db.save_article(article_data):
                    #Debugging purpose printing small summary in the console 
                    print(f"[{sector}] Risk:{risk}% -> {clean_title[:40]}...")
                    
        except Exception as e:
            #Catch any unexpected errors during the processing 
            print(f" Error processing {source_config['name']}: {e}")

if __name__ == "__main__":
    # Initialize DB table if it doesn't exist
    NewsDatabase().initialize()
    # Start the loop
    Pipeline().run()