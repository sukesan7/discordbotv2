import requests
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
from security import SPORTS_DATA_API_KEY

# --------------------------------------------------------------------------
# ------------------------------- API Setup -------------------------------
# --------------------------------------------------------------------------

API_KEY = SPORTS_DATA_API_KEY
BASE_URL = 'https://api.sportsdata.io/v3/nba'

# --------------------------------------------------------------------------
# ------------------------------- Data Fetching ----------------------------
# --------------------------------------------------------------------------

def fetch_data(endpoint):
    """Helper function to make API requests and return JSON data."""
    try:
        url = f"{BASE_URL}{endpoint}?key={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()  # Raise error for bad status codes
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
    return None

def get_games_by_date(date):
    """Fetch NBA games for a specific date."""
    return fetch_data(f'/scores/json/GamesByDate/{date}')

def get_game_scores(games):
    """Fetch scores for games and return DataFrame with outcomes."""
    if not games:
        return pd.DataFrame()

    # Create DataFrame and select relevant columns
    df = pd.DataFrame(games)
    
    # Ensure HomeTeamScore and AwayTeamScore exist in the games data
    if 'HomeTeamScore' not in df.columns or 'AwayTeamScore' not in df.columns:
        print("Score columns not found in the games data.")
        return pd.DataFrame()  # Return empty DataFrame if scores are not available

    # Safely handle missing scores
    df['HomeTeamScore'] = df['HomeTeamScore'].replace({np.nan: 0}).astype(float)
    df['AwayTeamScore'] = df['AwayTeamScore'].replace({np.nan: 0}).astype(float)

    # Create the 'Outcome' column
    df['Outcome'] = np.where(df['HomeTeamScore'] > df['AwayTeamScore'], 1, 0)

    # Keep relevant columns
    return df[['HomeTeam', 'AwayTeam', 'DateTime', 'HomeTeamScore', 'AwayTeamScore', 'Outcome']]

# --------------------------------------------------------------------------
# -------------------------- Data Processing -------------------------------
# --------------------------------------------------------------------------

def process_game_data(games):
    """Process game data into a DataFrame for analysis."""
    df = get_game_scores(games)
    # Convert DateTime to datetime object for sorting and filtering
    if not df.empty:
        df['DateTime'] = pd.to_datetime(df['DateTime'])
    else:
        print("No games data to process.")
    return df

def prepare_features(df):
    """Prepare features for machine learning model."""
    # Convert team names to numeric features using label encoding
    df['HomeTeam'] = df['HomeTeam'].astype('category').cat.codes
    df['AwayTeam'] = df['AwayTeam'].astype('category').cat.codes

    # Example features (you can add more)
    df['Feature1'] = np.random.rand(len(df))  # Placeholder for actual features
    df['Feature2'] = np.random.rand(len(df))

    return df

# --------------------------------------------------------------------------
# ------------------------ Model Training & Prediction ---------------------
# --------------------------------------------------------------------------

def train_model(df):
    """Train a machine learning model to predict game outcomes."""
    features = ['HomeTeam', 'AwayTeam', 'Feature1', 'Feature2']
    target = 'Outcome'  # This column now exists in the DataFrame

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(df[features], df[target], test_size=0.2, random_state=42)

    # Train a Random Forest model
    model_rf = RandomForestClassifier(random_state=42)
    model_rf.fit(X_train, y_train)

    # Train an XGBoost model
    model_xgb = XGBClassifier(random_state=42)
    model_xgb.fit(X_train, y_train)

    # Evaluate models
    rf_predictions = model_rf.predict(X_test)
    xgb_predictions = model_xgb.predict(X_test)

    rf_accuracy = accuracy_score(y_test, rf_predictions)
    xgb_accuracy = accuracy_score(y_test, xgb_predictions)

    print(f"Random Forest Accuracy: {rf_accuracy}")
    print(f"XGBoost Accuracy: {xgb_accuracy}")

    # Return the better-performing model
    return model_rf if rf_accuracy > xgb_accuracy else model_xgb

def predict_outcome(model, df):
    """Predict outcomes for upcoming games."""
    features = ['HomeTeam', 'AwayTeam', 'Feature1', 'Feature2']
    predictions = model.predict(df[features])
    df['PredictedOutcome'] = predictions
    return df[['HomeTeam', 'AwayTeam', 'PredictedOutcome']]

# --------------------------------------------------------------------------
# --------------------------- Prediction Logic -----------------------------
# --------------------------------------------------------------------------

def generate_predictions_for_today():
    """Generate predictions for today's games."""
    today = datetime.now().strftime('%Y-%m-%d')
    games = get_games_by_date(today)

    # Debugging output to check the fetched games
    print(f"Fetched games for {today}: {games}")

    game_df = process_game_data(games)
    
    if game_df.empty:
        print("No games available for today.")
        return "No games available for today."

    game_df = prepare_features(game_df)
    model = train_model(game_df)
    predictions = predict_outcome(model, game_df)
    
    return predictions

# --------------------------------------------------------------------------
# -------------------------- Example Usage ---------------------------------
# --------------------------------------------------------------------------

if __name__ == "__main__":
    # Example to run the prediction process
    predictions = generate_predictions_for_today()
    print(predictions)
