# ===================== ML Utilities =====================
import pandas as pd
import numpy as np
import joblib
import os
import json
from typing import Dict, List, Any

# Global variables for model and data
model = None
df = None
columns = None
location_data = None

def load_model_and_data():
    """Load ML model and data files"""
    global model, df, columns, location_data
    
    try:
        # Load model
        model_path = 'model.pkl'
        if os.path.exists(model_path):
            model = joblib.load(model_path)
        else:
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Load data
        data_path = 'housing.csv'
        if os.path.exists(data_path):
            df = pd.read_csv(data_path)
        else:
            # Try alternative path
            data_path = 'Bengaluru_House_Data.csv'
            if os.path.exists(data_path):
                df = pd.read_csv(data_path)
            else:
                raise FileNotFoundError(f"Data file not found")
        
        # Load columns if exists
        columns_path = 'flask_app/columns.pkl'
        if os.path.exists(columns_path):
            columns = joblib.load(columns_path)
        
        # Load location data
        location_path = 'flask_app/location.json'
        if os.path.exists(location_path):
            with open(location_path, 'r') as f:
                location_data = json.load(f)
        
        print("✅ Model and data loaded successfully")
        
    except Exception as e:
        print(f"❌ Error loading model/data: {e}")
        raise

# Load on import
load_model_and_data()

def predict_price(data: Dict[str, Any]) -> float:
    """
    Predict property price using the ML model
    
    Args:
        data: Dictionary containing property features
        
    Returns:
        Predicted price in lakhs
    """
    try:
        # Create DataFrame from input
        input_df = pd.DataFrame([data])
        
        # Handle categorical encoding (one-hot encoding)
        input_df = pd.get_dummies(input_df)
        
        # If we have saved columns, align the input
        if columns is not None:
            input_df = input_df.reindex(columns=columns, fill_value=0)
        
        # Make prediction
        prediction = model.predict(input_df)[0]
        
        # If model was trained with log transformation, reverse it
        try:
            price = np.expm1(prediction)  # Reverse log1p transformation
        except:
            price = prediction
        
        return max(price, 0)  # Ensure non-negative price
        
    except Exception as e:
        print(f"Prediction error: {e}")
        # Return a reasonable default based on input
        return estimate_price_fallback(data)

def estimate_price_fallback(data: Dict[str, Any]) -> float:
    """Fallback price estimation when ML model fails"""
    base_price = 50  # Base price in lakhs
    
    # Adjust based on total_sqft
    sqft_factor = data.get('total_sqft', 1000) / 1000
    price = base_price * sqft_factor
    
    # Adjust based on BHK
    size = data.get('size', '2 BHK')
    if '3' in str(size):
        price *= 1.3
    elif '4' in str(size):
        price *= 1.6
    elif '1' in str(size):
        price *= 0.7
    
    # Adjust based on location (premium locations)
    location = data.get('location', '').lower()
    premium_locations = ['whitefield', 'koramangala', 'indiranagar', 'jayanagar']
    if any(loc in location for loc in premium_locations):
        price *= 1.4
    
    return price

def get_trend_data(location: str) -> Dict[str, List]:
    """
    Get price trend data for a location
    
    Args:
        location: Location name
        
    Returns:
        Dictionary with years and average prices
    """
    try:
        if df is None:
            return {'years': [], 'prices': []}
        
        # Filter data for the location
        location_data = df[df['location'].str.contains(location, case=False, na=False)]
        
        if location_data.empty:
            return {'years': [], 'prices': []}
        
        # Group by year and calculate average price
        if 'year' in df.columns:
            trend = location_data.groupby('year')['price'].mean().reset_index()
        else:
            # Create dummy years if year column doesn't exist
            years = list(range(2018, 2025))
            base_price = location_data['price'].mean()
            prices = [base_price * (1 + 0.05 * i) for i in range(len(years))]
            return {'years': years, 'prices': prices}
        
        return {
            'years': trend['year'].tolist(),
            'prices': trend['price'].tolist()
        }
        
    except Exception as e:
        print(f"Trend data error: {e}")
        return {'years': [], 'prices': []}

def recommend_properties(budget: float = None, location: str = None, 
                        size: str = None, area_type: str = None) -> List[Dict]:
    """
    Recommend properties based on criteria
    
    Args:
        budget: Maximum budget in lakhs
        location: Preferred location
        size: Property size (e.g., "2 BHK")
        area_type: Type of area
        
    Returns:
        List of recommended properties
    """
    try:
        if df is None:
            return []
        
        # Start with all properties
        filtered_df = df.copy()
        
        # Apply filters
        if budget:
            filtered_df = filtered_df[filtered_df['price'] <= budget]
        
        if location:
            filtered_df = filtered_df[filtered_df['location'].str.contains(location, case=False, na=False)]
        
        if size:
            filtered_df = filtered_df[filtered_df['size'].str.contains(size, case=False, na=False)]
        
        if area_type:
            filtered_df = filtered_df[filtered_df['area_type'].str.contains(area_type, case=False, na=False)]
        
        # Sort by price and get top 10
        recommendations = filtered_df.head(10)
        
        # Convert to list of dictionaries
        return recommendations.to_dict('records')
        
    except Exception as e:
        print(f"Recommendation error: {e}")
        return []
