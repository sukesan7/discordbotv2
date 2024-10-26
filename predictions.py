import requests
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
from security import SPORTS_DATA_API_KEY

API_KEY = SPORTS_DATA_API_KEY
BASE_URL = 'https://api.sportsdata.io/v3/nba'

def fetch_data(endpoint):
    """Helper function to make API requests and return JSON data."""
    try:
        url = f"{BASE_URL}{endpoint}?key={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
    return None

def get_games_by_date(date):
    """Fetch NBA games for a specific date."""
    data = fetch_data(f'/scores/json/GamesByDate/{date}')
    return data if data else []

def get_game_scores(games):
    """Fetch scores for games and return DataFrame with outcomes."""
    if not games:
        return pd.DataFrame()

    df = pd.DataFrame(games)
    
    if 'HomeTeamScore' not in df.columns or 'AwayTeamScore' not in df.columns:
        return pd.DataFrame()  # Return empty DataFrame if scores are not available

    df['HomeTeamScore'] = df['HomeTeamScore'].fillna(0).astype(float)
    df['AwayTeamScore'] = df['AwayTeamScore'].fillna(0).astype(float)
    df['Outcome'] = np.where(df['HomeTeamScore'] > df['AwayTeamScore'], 1, 0)

    return df[['HomeTeam', 'AwayTeam', 'DateTime', 'HomeTeamScore', 'AwayTeamScore', 'Outcome']]

def process_game_data(games):
    """Process game data into a DataFrame for analysis."""
    df = get_game_scores(games)
    if not df.empty:
        df['DateTime'] = pd.to_datetime(df['DateTime'])
    return df

def prepare_features(df):
    """Prepare features for machine learning model."""
    df['HomeTeam'] = df['HomeTeam'].astype('category')
    df['AwayTeam'] = df['AwayTeam'].astype('category')
    df['HomeTeamCode'] = df['HomeTeam'].cat.codes
    df['AwayTeamCode'] = df['AwayTeam'].cat.codes

    # Replace the placeholder features with actual stats for more meaningful analysis.
    df['Feature1'] = np.random.rand(len(df))
    df['Feature2'] = np.random.rand(len(df))
    return df

def train_model(df):
    """Train a machine learning model to predict game outcomes."""
    features = ['HomeTeamCode', 'AwayTeamCode', 'Feature1', 'Feature2']
    target = 'Outcome'

    X_train, X_test, y_train, y_test = train_test_split(df[features], df[target], test_size=0.2, random_state=42)

    model_rf = RandomForestClassifier(random_state=42)
    model_rf.fit(X_train, y_train)

    model_xgb = XGBClassifier(random_state=42)
    model_xgb.fit(X_train, y_train)

    rf_accuracy = accuracy_score(y_test, model_rf.predict(X_test))
    xgb_accuracy = accuracy_score(y_test, model_xgb.predict(X_test))

    return model_rf if rf_accuracy > xgb_accuracy else model_xgb

def predict_outcome(model, df):
    """Predict outcomes for upcoming games."""
    features = ['HomeTeamCode', 'AwayTeamCode', 'Feature1', 'Feature2']
    df['PredictedOutcome'] = model.predict(df[features])

    # Simulate Moneyline and Point Spread predictions
    df['MoneylinePrediction'] = np.where(df['PredictedOutcome'] == 1, df['HomeTeam'], df['AwayTeam'])
    df['PointSpread'] = np.random.uniform(2, 12, size=len(df))  # Placeholder for point spread values

    return df[['HomeTeam', 'AwayTeam', 'PredictedOutcome', 'MoneylinePrediction', 'PointSpread']]

def generate_predictions_for_today():
    """Generate predictions for today's games."""
    today = datetime.now().strftime('%Y-%m-%d')
    games = get_games_by_date(today)

    if not games:
        return {"nba": "No NBA games today."}

    game_df = process_game_data(games)
    game_df = prepare_features(game_df)
    model = train_model(game_df)
    predictions_df = predict_outcome(model, game_df)

    predictions = []
    for _, row in predictions_df.iterrows():
        predictions.append({
            'HomeTeam': row['HomeTeam'],
            'AwayTeam': row['AwayTeam'],
            'MoneylinePrediction': row['MoneylinePrediction'],
            'PointSpread': round(row['PointSpread'], 2)
        })

    return {"nba": predictions}
