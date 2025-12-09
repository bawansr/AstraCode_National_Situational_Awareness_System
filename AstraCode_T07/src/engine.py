import json
import re
from bs4 import BeautifulSoup

# Try importing transformers from Hugging face 
try:
    from transformers import pipeline
# If transformers not imported show error and exit the program
except ImportError:
    print("Error: 'transformers' library not found")
    exit(1)

def load_config():
    # Try to open and load config file from /config folder
    try:
        with open('config/config.json', 'r') as f: return json.load(f)
    except FileNotFoundError:
        # If file is not found print a warning msg 
        print("Warning: config.json not found")
        return {'sector_logic': {}, 'app_settings': {'refresh_interval_seconds': 300, 'sources_file': 'config/locations.json'}}

class RiskEngine:
    def __init__(self):
        # Load the AI model 
        print("Loading AI Model (DistilBART)...")
        #Initialize zero-shot classifier
        #Model that we used is "valhalla/distilbart-mnli-12-1" 
        self.classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1")
        
        # Load runtime configuration 
        # Reloading without restarting the process 
        self.reload_config()
        
        # Labels for the AI to detect
        # The model will compute scores for each label 
        self.risk_labels = [
            "Critical Unrest", 
            "Natural Disaster", 
            "Economic Crisis", 
            "Political Instability", 
            "Supply Chain Disruption", 
            "Normal Business Operation",
            "Positive Growth"
        ]

    def reload_config(self):
        #Load the configuration
        self.config = load_config()
        #Load sector keywords rules
        self.sector_rules = self.config.get('sector_logic', {})
        #Load the locations file, which stores city names and their coordinates
        #If anything goes wrong, we use an empty dictionary
        #so the program won't crash — only the location accuracy will be lower
        try:
            with open('locations.json', 'r') as f:
                self.locations = json.load(f)
        except:
            #Keep an empty mapping to make get_location() safe
            self.locations = {}

    def preprocess(self, text):
        #Clean and normalize raw HTML/text for NLP
        if not text: return ""
        #parse HTML and extract visible text
        #concatenation when tags are removed 
        soup = BeautifulSoup(text, "html.parser")
        text = soup.get_text(separator=' ')
        #Remove characters that are not word characters, whitespace, or chosen punctuation
        #This removes weird unicode characters 
        text = re.sub(r'[^\w\s.,!?\'"-]', '', text)
        #Replace any extra spaces with a single space and remove spaces at the start and end
        return re.sub(r'\s+', ' ', text).strip()

    #Classify news into sectors 
    def detect_sector(self, text):
        text_lower = text.lower()
        #Loop through configured sector rules
        #sector_rules should be a dict
        for sector, keywords in self.sector_rules.items():
            #Keywords is expected to be an iterable of Strings 
            for word in keywords:
                if word in text_lower: return sector
        #If no rules matched return safe default 
        return "GENERAL"

    #Detect if text refers to an upcoming or scheduled event
    def detect_future_event(self, text):
        #The method checks for common future related phrases and returns 1 if any are present and 0 otherwise
        future_keywords = ["scheduled", "tomorrow", "next week", "planned", "to be", "upcoming", "postponed", "will be", "expected"]
        text_lower = text.lower()
        for word in future_keywords:
            if word in text_lower:
                return 1
        return 0

    #Classify the text into a risk category and compute a numeric score
    def analyze_risk(self, text):
        """Uses AI to classify risk and assign a score (0-100)."""
        # Run zero-shot classification against the configured labels
        result = self.classifier(text, self.risk_labels)
        # The pipeline returns labels sorted by score and grab the top one 
        top_label = result['labels'][0]
        # confidence in the top label
        confidence = result['scores'][0]
        
        #Business rules mapping label 
        if top_label in ["Critical Unrest", "Natural Disaster", "Supply Chain Disruption"]:
            # High-impact labels map to 'Critical'
            score = int(80 + (confidence * 20)) # scale into 80–100
            return "Critical", score
        elif top_label in ["Economic Crisis", "Political Instability"]:
            # Medium-impact labels map to 'Warning'
            score = int(50 + (confidence * 29)) # scale into 50–79
            return "Warning", score
        elif top_label == "Positive Growth":
            # Positive label(not a risk)
            return "Opportunity", 0
        else:
            # Default lower importance label 
            return "Info", 10

    #Extract geographic coordinates for a known Sri Lankan city mentioned in text
    def get_location(self, text):
        #Loop through the known city
        #coords mapping and test for presence
        for city, coords in self.locations.items():
            if city in text:
                return coords['lat'], coords['lon']
        # No city matched
        #return None 
        return None, None