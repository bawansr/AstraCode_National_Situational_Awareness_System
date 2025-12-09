import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer # Convert text data into numeric features
from sklearn.cluster import KMeans #Importing K-Means clustering 
from sklearn.linear_model import LinearRegression
from src.database import NewsDatabase

class RiskAnalytics:
    def __init__(self):
        # Create a connection to the database
        self.db = NewsDatabase()

        # DataFrame that will keep all the articles that came from the dataframe 
        self.df = pd.DataFrame()

        # Vectorizer used to convert article titles into numerical text features for clustering
        self.vectorizer = TfidfVectorizer(stop_words='english')

        print("RiskAnalytics Engine Initialized") #Print statement for debugging purpose 

    #Loads the latest news articles from the database
    def load_data(self):
        #This method pulls the latest 1000 records from the SQLite database
        #and stores them inside the DataFrame (self.df)
        #It returns True if data was successfully loaded.

        self.df = self.db.fetch_latest(1000)
        return not self.df.empty


    # --------------- INTERNAL HELPER -------------------
    def _get_data(self, sector):
        #Returns filtered data based on the requested sector
        #If 'All' is selected it returns the full dataset
        if not sector or sector == "All":
            return self.df
        return self.df[self.df['sector'] == sector]

    # ------------------ NATIONAL INDICATORS -----------------
    def get_national_indicators(self, sector=None):
        #Calculates national-level indicators such as stability, critical risks, and volume
        """
        Steps:
        1. Filter data by sector
        2. Calculate the average risk score from the newest 50 articles
        3. Convert this average into a "stability" score
        4. Count how many articles have a risk score greater than 80
        5. Calculate article volume within the last 24 hours
        """
        #Get the filtered data for the sectors 
        df = self._get_data(sector)
        #If  the dataframe is empty return zero 
        if df.empty: return 0, 0, 0
        
        #Calculate average risk of the first 50 articles 
        avg_risk = df['risk_score'].head(50).mean()
        #Calculate the stability 
        stability = int(100 - (avg_risk if not pd.isna(avg_risk) else 0))
        #Count the number of high risk articles with risk score > 80
        crit_count = len(df[df['risk_score'] > 80])
        
        # Count new articles from last 24 hours
        if 'published_dt' in df.columns and df['published_dt'].notna().any():
            #Current time UTC
            today = pd.Timestamp.now(tz='UTC')
            #Filtered articles published in the last 24hrs 
            last_24h = df[df['published_dt'] > (today - pd.Timedelta(hours=24))]
            #Count the number of recent articles 
            volume = len(last_24h)
        else:
            #If no data info use the total number of articles 
            volume = len(df)
        #Returns stability , critical_risk_count, volume_last_24h 
        return stability, crit_count, volume

    # ------------------ INSIGHTS -------------------
    def get_top_insights(self, sector=None):
        #Get the filtered data by the sector 
        df = self._get_data(sector)
        #If no data return empty dataframes 
        if df.empty: return pd.DataFrame(), pd.DataFrame()
        
        # Top high risks
        risks = df[df['risk_score'] > 70].head(5)

        # Top opportunities
        opp_mask = (df['risk_score'] < 20) | (df['category'] == 'Opportunity')
        opportunities = df[opp_mask].head(5)
        
        #Return both risks and opportunities
        return risks, opportunities

    # ------------------------ SECTOR STATUS ----------------------------
    def get_sector_status(self):
        #If  no data return empty dict 
        if self.df.empty: return {}

        #List of the sectors that we are tracking 
        sectors = ['INFRASTRUCTURE', 'LOGISTICS', 'FINANCE', 'LABOR', 'SOCIETY', 'EVENTS']
        status = {} # Dict to store sector avg scores 

        #Loop through each sector 
        for sec in sectors:
            #Filter articles for sector
            sec_data = self.df[self.df['sector'] == sec]
            #If no article found set risk to 0
            if sec_data.empty:
                status[sec] = 0
            else:
                #Calculate the avg risk of first 10 articles 
                avg_risk = int(sec_data['risk_score'].head(10).mean())
                status[sec] = avg_risk

        return status

    # ------------------------- UPCOMING EVENTS --------------------------
    def get_upcoming_events(self, sector=None):
        #Filter by sector 
        df = self._get_data(sector)
        #If no data return empty dataframe 
        if df.empty: return pd.DataFrame()
        #Check if 'is_upcoming' cols exists 
        if 'is_upcoming' in df.columns:
            #Return articles marked as upcoming
            #Limited to 5
            return df[df['is_upcoming'] == 1].head(5)
        return pd.DataFrame()

    # ------------------ K-Means ----------------------
    def get_emerging_themes(self, sector=None):
        #Filter data by sector 
        df = self._get_data(sector)
        #If less than 5 articles, clustering won't work 
        if len(df) < 5: return [] 
        
        try:
            #Convert article titles into numerical features 
            matrix = self.vectorizer.fit_transform(df['title'].fillna(''))
            
            # Decide number of clusters dynamically 
            n_clusters = min(3, len(df)//2)
            if n_clusters < 1: n_clusters = 1
            
            # Initialize K-Means model and fit it 
            model = KMeans(n_clusters=n_clusters, random_state=42)
            labels = model.fit_predict(matrix)
            
            #Get cluster centroids and sor features  
            centroids = model.cluster_centers_.argsort()[:, ::-1]
            terms = self.vectorizer.get_feature_names_out()
            
            results = [] #List to store cluster info 
            #Loop through each cluster 
            for i in range(n_clusters):
                # Select the top 2 most important keywords for the cluster
                keywords = [terms[ind] for ind in centroids[i, :2]]
                topic = " & ".join(keywords).upper()
                #Articles belonging to this cluster 
                cluster_docs = df.iloc[labels == i]
                count = len(cluster_docs)

                # Take top 3 articles for easy display 
                top_articles = cluster_docs.head(3).to_dict('records')
                #Add cluster info to results 
                results.append({
                    "topic": topic,
                    "count": count,
                    "articles": top_articles
                })

            return results

        except Exception as e:
            #Print error if clustering fails 
            print(f"Clustering error: {e}")
            return []

    #-------------------------- RISK FORECAST USING LINEAR MODEL --------------------
    def get_forecast(self, sector=None):
        """
        1. Filter data by sector.
        2. Group data by hourly intervals using resampling.
        3. Fit a linear regression model.
        4. Predict the next 4 hours.
        5. Build a DataFrame that combines history + predictions.
        """
        #Filter data by sector 
        df = self._get_data(sector)
        
        # If no data or timestamp return none 
        if df.empty or 'published_dt' not in df.columns: return None
        if not df['published_dt'].notna().any(): return None
        #Sort articles by published date  
        trend_df = df.set_index('published_dt').sort_index()

        # Resample by hour to get smoother trend data
        try:
            history = trend_df['risk_score'].resample('H').mean().fillna(0)
        except:
            return None
        #If not enough data skip forecasting 
        if len(history) < 3: return None
        
        #Prepare data for the linear reg
        y = history.values
        X = np.arange(len(y)).reshape(-1, 1)
        
        #Train linear reg model 
        model = LinearRegression()
        model.fit(X, y)
        #Predict next 4 hrs 
        next_X = np.arange(len(y), len(y)+4).reshape(-1, 1)
        predictions = model.predict(next_X)
        
        # Create timestamps for future predictions
        last_date = history.index[-1]
        future_dates = [last_date + pd.Timedelta(hours=i+1) for i in range(4)]
        
        # Combine historical and future timestamps
        full_index = history.index.union(future_dates)
        chart_df = pd.DataFrame(index=full_index)
        
        # Add actual trend
        chart_df['Actual Trend'] = history
        # Add forecast column
        chart_df['AI Forecast'] = np.nan
        
        # Fill Forecast for last actual pred 
        chart_df.loc[last_date, 'AI Forecast'] = history.iloc[-1]
        # Fill forecast for future pred 
        chart_df.loc[future_dates, 'AI Forecast'] = predictions
        
        return chart_df

    # ------------------------ MAP DATA WITH COORDINATES ------------------------
    def get_map_data(self, sector=None):
        #Filter by sector 
        df = self._get_data(sector)
        #If no data return empty 
        if df.empty: return pd.DataFrame()
        #Remove rows without coordinates 
        return df.dropna(subset=['lat', 'lon'])

  
    # ---------------------- FILTERED FEED --------------------------
    def get_filtered_feed(self, sector="All"):
        #Return filtered data or all articles 
        return self._get_data(sector)
