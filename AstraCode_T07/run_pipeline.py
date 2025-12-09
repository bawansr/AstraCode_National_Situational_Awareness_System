from src.pipeline import Pipeline
from src.database import NewsDatabase

if __name__ == "__main__":
    print("Initializing AstraCode Pipeline...")
    
    # Initialize DB (This will create data/news.db if missing)
    db = NewsDatabase()
    db.initialize()
    
    # Start the data collection loop
    worker = Pipeline()
    worker.run()