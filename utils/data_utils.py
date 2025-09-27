# ===================== Data Utilities =====================
import pandas as pd
import numpy as np
import json
import os
from typing import List, Dict, Any

def get_locations() -> List[str]:
    """Get all available locations"""
    try:
        # Try to load from housing data
        if os.path.exists('housing.csv'):
            df = pd.read_csv('housing.csv')
            if 'location' in df.columns:
                return sorted(df['location'].unique().tolist())
        
        # Try alternative data file
        if os.path.exists('Bengaluru_House_Data.csv'):
            df = pd.read_csv('Bengaluru_House_Data.csv')
            if 'location' in df.columns:
                return sorted(df['location'].unique().tolist())
        
        # Fallback to predefined locations
        return [
            "Electronic City Phase II", "Chikka Tirupathi", "Uttarahalli",
            "Lingadheeranahalli", "Kothanur", "Whitefield", "Old Airport Road",
            "Rajaji Nagar", "Marathahalli", "Gandhi Bazar", "Koramangala",
            "Indiranagar", "Jayanagar", "BTM Layout", "HSR Layout",
            "Sarjapur Road", "Bannerghatta Road", "Hebbal", "Yeshwanthpur",
            "Malleshwaram", "Basavanagudi", "Yelahanka", "Kengeri",
            "Bommanahalli", "Bellandur"
        ]
        
    except Exception as e:
        print(f"Error getting locations: {e}")
        return []

def get_location_suggestions(query: str) -> List[str]:
    """Get location suggestions based on search query"""
    locations = get_locations()
    if not query:
        return locations[:10]  # Return first 10 if no query
    
    # Filter locations that contain the query
    suggestions = [loc for loc in locations if query.lower() in loc.lower()]
    return suggestions[:10]  # Return max 10 suggestions

def get_market_stats() -> Dict[str, Any]:
    """Get overall market statistics"""
    try:
        # Try to load data
        df = None
        if os.path.exists('housing.csv'):
            df = pd.read_csv('housing.csv')
        elif os.path.exists('Bengaluru_House_Data.csv'):
            df = pd.read_csv('Bengaluru_House_Data.csv')
        
        if df is None or df.empty:
            return get_default_market_stats()
        
        stats = {
            'total_properties': len(df),
            'avg_price': df['price'].mean() if 'price' in df.columns else 0,
            'median_price': df['price'].median() if 'price' in df.columns else 0,
            'min_price': df['price'].min() if 'price' in df.columns else 0,
            'max_price': df['price'].max() if 'price' in df.columns else 0,
            'total_locations': df['location'].nunique() if 'location' in df.columns else 0,
            'avg_sqft': df['total_sqft'].mean() if 'total_sqft' in df.columns else 0,
            'popular_sizes': df['size'].value_counts().head(5).to_dict() if 'size' in df.columns else {},
            'popular_locations': df['location'].value_counts().head(10).to_dict() if 'location' in df.columns else {}
        }
        
        return stats
        
    except Exception as e:
        print(f"Error getting market stats: {e}")
        return get_default_market_stats()

def get_default_market_stats() -> Dict[str, Any]:
    """Default market statistics when data is not available"""
    return {
        'total_properties': 13320,
        'avg_price': 112.56,
        'median_price': 95.00,
        'min_price': 8.52,
        'max_price': 3600.00,
        'total_locations': 242,
        'avg_sqft': 1374.5,
        'popular_sizes': {
            '2 BHK': 4512,
            '3 BHK': 3665,
            '4 BHK': 2141,
            '1 BHK': 1421,
            '5 BHK': 765
        },
        'popular_locations': {
            'Whitefield': 535,
            'Sarjapur Road': 392,
            'Electronic City': 304,
            'Kanakpura Road': 266,
            'Thanisandra': 236,
            'Yelahanka': 210,
            'Uttarahalli': 196,
            'Hebbal': 176,
            'Marathahalli': 169,
            'Raja Rajeshwari Nagar': 165
        }
    }

def get_location_analytics(location: str) -> Dict[str, Any]:
    """Get detailed analytics for a specific location"""
    try:
        # Try to load data
        df = None
        if os.path.exists('housing.csv'):
            df = pd.read_csv('housing.csv')
        elif os.path.exists('Bengaluru_House_Data.csv'):
            df = pd.read_csv('Bengaluru_House_Data.csv')
        
        if df is None:
            return get_default_location_analytics(location)
        
        # Filter for the specific location
        location_df = df[df['location'].str.contains(location, case=False, na=False)]
        
        if location_df.empty:
            return get_default_location_analytics(location)
        
        analytics = {
            'location': location,
            'total_properties': len(location_df),
            'avg_price': location_df['price'].mean() if 'price' in location_df.columns else 0,
            'median_price': location_df['price'].median() if 'price' in location_df.columns else 0,
            'price_range': {
                'min': location_df['price'].min() if 'price' in location_df.columns else 0,
                'max': location_df['price'].max() if 'price' in location_df.columns else 0
            },
            'avg_sqft': location_df['total_sqft'].mean() if 'total_sqft' in location_df.columns else 0,
            'size_distribution': location_df['size'].value_counts().to_dict() if 'size' in location_df.columns else {},
            'area_type_distribution': location_df['area_type'].value_counts().to_dict() if 'area_type' in location_df.columns else {},
            'price_per_sqft': (location_df['price'] / location_df['total_sqft']).mean() if all(col in location_df.columns for col in ['price', 'total_sqft']) else 0
        }
        
        return analytics
        
    except Exception as e:
        print(f"Error getting location analytics: {e}")
        return get_default_location_analytics(location)

def get_default_location_analytics(location: str) -> Dict[str, Any]:
    """Default location analytics when data is not available"""
    return {
        'location': location,
        'total_properties': 150,
        'avg_price': 95.5,
        'median_price': 85.0,
        'price_range': {'min': 45.0, 'max': 250.0},
        'avg_sqft': 1200,
        'size_distribution': {'2 BHK': 60, '3 BHK': 50, '1 BHK': 25, '4 BHK': 15},
        'area_type_distribution': {'Super built-up Area': 80, 'Built-up Area': 45, 'Plot Area': 15, 'Carpet Area': 10},
        'price_per_sqft': 7956
    }

def save_prediction_to_history(prediction_data: Dict[str, Any]) -> bool:
    """Save prediction to history file"""
    try:
        history_file = 'static/data/prediction_history.json'
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        
        # Load existing history
        history = []
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        
        # Add new prediction
        history.append(prediction_data)
        
        # Keep only last 1000 predictions
        history = history[-1000:]
        
        # Save back to file
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"Error saving prediction history: {e}")
        return False
