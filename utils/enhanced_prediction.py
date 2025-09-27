# ===================== Enhanced Property Price Prediction =====================
"""
Enhanced price prediction system that handles different property types
with type-specific features and prediction models.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from utils.property_types import property_type_manager, PropertyCategory, FieldType
import joblib
import os

class EnhancedPricePrediction:
    """Enhanced price prediction with property type awareness"""
    
    def __init__(self):
        self.base_model = None
        self.property_models = {}
        self.location_factors = {}
        self.load_models()
        self.initialize_location_factors()
    
    def load_models(self):
        """Load ML models"""
        try:
            # Load base model if available
            if os.path.exists('model.pkl'):
                self.base_model = joblib.load('model.pkl')
                print("✅ Base model loaded successfully")
            
            # Load property-specific models if available
            for prop_type_id in property_type_manager.get_all_property_types().keys():
                model_path = f'models/{prop_type_id}_model.pkl'
                if os.path.exists(model_path):
                    self.property_models[prop_type_id] = joblib.load(model_path)
                    print(f"✅ {prop_type_id} model loaded successfully")
        
        except Exception as e:
            print(f"❌ Error loading models: {e}")
    
    def initialize_location_factors(self):
        """Initialize location-based price factors"""
        # Premium locations with higher price factors
        self.location_factors = {
            # Tier 1 - Premium locations
            'koramangala': 1.5,
            'indiranagar': 1.45,
            'whitefield': 1.4,
            'jayanagar': 1.35,
            'hsr layout': 1.4,
            'btm layout': 1.3,
            'marathahalli': 1.35,
            'electronic city': 1.25,
            'sarjapur road': 1.3,
            'bellandur': 1.35,
            
            # Tier 2 - Good locations
            'rajajinagar': 1.2,
            'malleshwaram': 1.25,
            'basavanagudi': 1.2,
            'jp nagar': 1.15,
            'banashankari': 1.1,
            'vijayanagar': 1.1,
            'hebbal': 1.15,
            'rt nagar': 1.1,
            
            # Tier 3 - Developing areas
            'yelahanka': 1.0,
            'kengeri': 0.95,
            'bommanahalli': 1.05,
            'kr puram': 1.0,
            'ramamurthy nagar': 0.95,
            'hoodi': 1.1,
            'mahadevapura': 1.2,
            
            # Default factor for unlisted locations
            'default': 1.0
        }
    
    def get_location_factor(self, location: str) -> float:
        """Get price factor for a location"""
        if not location:
            return self.location_factors['default']
        
        location_lower = location.lower().strip()
        
        # Direct match
        if location_lower in self.location_factors:
            return self.location_factors[location_lower]
        
        # Partial match
        for loc_key, factor in self.location_factors.items():
            if loc_key != 'default' and loc_key in location_lower:
                return factor
        
        return self.location_factors['default']
    
    def predict_price(self, property_type_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict property price based on type and features
        
        Args:
            property_type_id: ID of the property type
            data: Property features data
            
        Returns:
            Dictionary with prediction results
        """
        try:
            # Get property type configuration
            prop_type = property_type_manager.get_property_type(property_type_id)
            if not prop_type:
                raise ValueError(f"Unknown property type: {property_type_id}")
            
            # Validate input data
            validation = property_type_manager.validate_property_data(property_type_id, data)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': 'Validation failed',
                    'validation_errors': validation['errors']
                }
            
            # Use property-specific model if available, otherwise use base calculation
            if property_type_id in self.property_models:
                predicted_price = self._predict_with_ml_model(property_type_id, data, prop_type)
            else:
                predicted_price = self._predict_with_rule_based(property_type_id, data, prop_type)
            
            # Calculate additional metrics
            total_sqft = float(data.get('total_sqft', 1000))
            price_per_sqft = (predicted_price * 100000) / total_sqft if total_sqft > 0 else 0
            
            # Generate confidence score
            confidence = self._calculate_confidence(property_type_id, data, prop_type)
            
            # Generate insights
            insights = self._generate_insights(property_type_id, data, predicted_price, prop_type)
            
            return {
                'success': True,
                'predicted_price': round(predicted_price, 2),
                'formatted_price': f"₹{predicted_price:,.2f} Lakhs",
                'price_per_sqft': round(price_per_sqft, 2),
                'confidence': confidence,
                'property_type': prop_type.name,
                'insights': insights,
                'breakdown': self._get_price_breakdown(property_type_id, data, predicted_price, prop_type)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _predict_with_ml_model(self, property_type_id: str, data: Dict[str, Any], prop_type) -> float:
        """Predict using ML model for specific property type"""
        try:
            model = self.property_models[property_type_id]
            
            # Prepare features for ML model
            features = self._prepare_ml_features(data, prop_type)
            
            # Make prediction
            prediction = model.predict([features])[0]
            
            # Apply property type base factor
            prediction *= prop_type.base_price_factor
            
            return max(prediction, 10)  # Minimum 10 lakhs
            
        except Exception as e:
            print(f"ML prediction error for {property_type_id}: {e}")
            # Fallback to rule-based prediction
            return self._predict_with_rule_based(property_type_id, data, prop_type)
    
    def _predict_with_rule_based(self, property_type_id: str, data: Dict[str, Any], prop_type) -> float:
        """Rule-based prediction for property types"""
        
        # Base price calculation
        total_sqft = float(data.get('total_sqft', 1000))
        base_price_per_sqft = 3500  # Base price per sqft in rupees
        
        # Calculate base price
        base_price = (total_sqft * base_price_per_sqft) / 100000  # Convert to lakhs
        
        # Apply property type factor
        price = base_price * prop_type.base_price_factor
        
        # Apply location factor
        location_factor = self.get_location_factor(data.get('location', ''))
        price *= location_factor
        
        # Apply feature-specific adjustments based on property type
        price = self._apply_feature_adjustments(price, data, prop_type)
        
        return max(price, 5)  # Minimum 5 lakhs
    
    def _apply_feature_adjustments(self, base_price: float, data: Dict[str, Any], prop_type) -> float:
        """Apply feature-specific price adjustments"""
        price = base_price
        
        # Age adjustment
        age = data.get('age', 'New Construction')
        age_factors = {
            'New Construction': 1.1,
            '1-5 years': 1.0,
            '5-10 years': 0.95,
            '10-15 years': 0.9,
            '15+ years': 0.85
        }
        price *= age_factors.get(age, 1.0)
        
        # Furnishing adjustment
        furnishing = data.get('furnishing', 'Unfurnished')
        furnishing_factors = {
            'Fully Furnished': 1.15,
            'Semi-Furnished': 1.08,
            'Unfurnished': 1.0
        }
        price *= furnishing_factors.get(furnishing, 1.0)
        
        # Floor adjustment (for apartments)
        if prop_type.category == PropertyCategory.RESIDENTIAL and 'floor' in data:
            floor = data.get('floor', 1)
            if isinstance(floor, (int, float)) and floor > 0:
                if floor == 1:  # Ground floor
                    price *= 0.95
                elif 2 <= floor <= 5:  # Mid floors
                    price *= 1.0
                elif floor > 5:  # High floors
                    price *= 1.05
        
        # Property-specific adjustments
        if prop_type.id in ['studio', '1rk']:
            # Studio and 1RK adjustments
            if data.get('furnishing') == 'Fully Furnished':
                price *= 1.2  # Higher premium for furnished small spaces
        
        elif prop_type.id in ['2bhk', '3bhk', '4bhk_plus']:
            # BHK apartment adjustments
            bathrooms = data.get('bathrooms', 2)
            if isinstance(bathrooms, (int, float)):
                if bathrooms >= 3:
                    price *= 1.05
                elif bathrooms <= 1:
                    price *= 0.95
            
            balconies = data.get('balconies', 1)
            if isinstance(balconies, (int, float)) and balconies >= 2:
                price *= 1.03
        
        elif prop_type.id == 'villa':
            # Villa-specific adjustments
            garden_area = data.get('garden_area', 0)
            if isinstance(garden_area, (int, float)) and garden_area > 0:
                price *= (1 + (garden_area / 10000) * 0.1)  # 10% increase per 1000 sqft garden

            parking = data.get('parking', 1)
            if isinstance(parking, (int, float)) and parking >= 2:
                price *= 1.05

        elif prop_type.id == 'hall':
            # Hall-specific adjustments
            seating_capacity = data.get('seating_capacity', 100)
            if isinstance(seating_capacity, (int, float)):
                if seating_capacity >= 500:
                    price *= 1.2
                elif seating_capacity >= 200:
                    price *= 1.1

            if data.get('ac_available'):
                price *= 1.15
            if data.get('kitchen_facility'):
                price *= 1.1

        elif prop_type.id == 'office':
            # Office-specific adjustments
            floor = data.get('floor', 1)
            if isinstance(floor, (int, float)) and floor >= 5:
                price *= 1.1  # Premium for higher floors in commercial

            cabin_rooms = data.get('cabin_rooms', 0)
            if isinstance(cabin_rooms, (int, float)) and cabin_rooms > 0:
                price *= (1 + cabin_rooms * 0.02)  # 2% per cabin room

        elif prop_type.id == 'shop':
            # Shop-specific adjustments
            if data.get('main_road_facing'):
                price *= 1.25  # Significant premium for main road facing

            frontage = data.get('frontage', 10)
            if isinstance(frontage, (int, float)) and frontage >= 20:
                price *= 1.1  # Premium for wider frontage

        # Amenities adjustment
        amenities = data.get('amenities', [])
        if amenities:
            amenities_factor = self._calculate_amenities_factor(amenities, prop_type)
            price *= amenities_factor

        return price

    def _calculate_amenities_factor(self, amenities: List[str], prop_type) -> float:
        """Calculate price factor based on nearby amenities"""
        if not amenities:
            return 1.0

        # Handle "No Amenities" option
        if isinstance(amenities, list) and 'No Amenities' in amenities:
            return 1.0  # No price adjustment for no amenities

        # Amenity weights based on importance and impact on property value
        amenity_weights = {
            # High impact amenities
            'Metro Station/Bus Stop': 0.08,
            'Hospital/Medical Center': 0.06,
            'School/Educational Institute': 0.06,
            'Shopping Mall/Market': 0.05,
            'IT Park/Tech Hub': 0.07,
            'Airport Nearby': 0.04,

            # Medium impact amenities
            'Park/Garden': 0.04,
            'Gym/Fitness Center': 0.03,
            'Bank/ATM': 0.03,
            'Restaurant/Food Court': 0.03,
            'Swimming Pool': 0.04,
            'Playground': 0.03,

            # Lower impact amenities
            'Pharmacy/Medical Store': 0.02,
            'Petrol Pump/Gas Station': 0.02,
            'Temple/Religious Place': 0.02,
            'Police Station': 0.02,
            'Fire Station': 0.02,
            'Library': 0.02,
            'Cinema/Entertainment': 0.02,
            'Government Office': 0.02
        }

        # Property type specific amenity preferences
        if prop_type.category == PropertyCategory.RESIDENTIAL:
            # Residential properties value schools, hospitals, parks more
            amenity_weights.update({
                'School/Educational Institute': 0.08,
                'Hospital/Medical Center': 0.07,
                'Park/Garden': 0.06,
                'Playground': 0.05,
                'Swimming Pool': 0.05
            })
        elif prop_type.category == PropertyCategory.COMMERCIAL:
            # Commercial properties value business amenities more
            amenity_weights.update({
                'Metro Station/Bus Stop': 0.10,
                'IT Park/Tech Hub': 0.09,
                'Bank/ATM': 0.05,
                'Restaurant/Food Court': 0.05,
                'Shopping Mall/Market': 0.07
            })

        # Calculate total amenities factor
        total_factor = 0.0
        unique_amenities = set(amenities) if isinstance(amenities, list) else {amenities}

        for amenity in unique_amenities:
            weight = amenity_weights.get(amenity, 0.01)  # Default small weight for unlisted amenities
            total_factor += weight

        # Cap the maximum amenities bonus at 25%
        total_factor = min(total_factor, 0.25)

        # Apply diminishing returns for too many amenities
        if len(unique_amenities) > 10:
            total_factor *= 0.9  # Reduce by 10% if more than 10 amenities

        return 1.0 + total_factor

    def _prepare_ml_features(self, data: Dict[str, Any], prop_type) -> List[float]:
        """Prepare features for ML model"""
        features = []

        # Add common numerical features
        features.append(float(data.get('total_sqft', 1000)))

        # Add property-specific features based on type
        for field in prop_type.fields:
            if field.field_type == FieldType.NUMBER:
                features.append(float(data.get(field.name, field.default_value or 0)))
            elif field.field_type == FieldType.BOOLEAN:
                features.append(1.0 if data.get(field.name, False) else 0.0)

        # Add location factor as a feature
        location_factor = self.get_location_factor(data.get('location', ''))
        features.append(location_factor)

        # Add amenities factor as a feature
        amenities = data.get('amenities', [])
        amenities_factor = self._calculate_amenities_factor(amenities, prop_type)
        features.append(amenities_factor)

        return features

    def _calculate_confidence(self, property_type_id: str, data: Dict[str, Any], prop_type) -> str:
        """Calculate prediction confidence"""
        confidence_score = 0.8  # Base confidence

        # Increase confidence if we have more data
        required_fields = prop_type.get_required_fields()
        provided_required = sum(1 for field in required_fields if data.get(field.name))
        confidence_score += (provided_required / len(required_fields)) * 0.1

        # Increase confidence for known locations
        location_factor = self.get_location_factor(data.get('location', ''))
        if location_factor != self.location_factors['default']:
            confidence_score += 0.05

        # Increase confidence if we have property-specific model
        if property_type_id in self.property_models:
            confidence_score += 0.1

        # Convert to categorical confidence
        if confidence_score >= 0.9:
            return 'Very High'
        elif confidence_score >= 0.8:
            return 'High'
        elif confidence_score >= 0.7:
            return 'Medium'
        else:
            return 'Low'

    def _generate_insights(self, property_type_id: str, data: Dict[str, Any],
                          predicted_price: float, prop_type) -> List[str]:
        """Generate insights about the prediction"""
        insights = []

        # Location insights
        location = data.get('location', '')
        location_factor = self.get_location_factor(location)
        if location_factor > 1.2:
            insights.append(f"Premium location with {((location_factor - 1) * 100):.0f}% price premium")
        elif location_factor < 0.95:
            insights.append(f"Developing area with potential for growth")

        # Size insights
        total_sqft = float(data.get('total_sqft', 1000))
        price_per_sqft = (predicted_price * 100000) / total_sqft
        if price_per_sqft > 5000:
            insights.append("High price per sqft indicates premium property")
        elif price_per_sqft < 3000:
            insights.append("Good value for money with competitive price per sqft")

        # Property-specific insights
        if prop_type.id in ['studio', '1rk']:
            insights.append("Ideal for young professionals and students")
            if data.get('furnishing') == 'Fully Furnished':
                insights.append("Ready to move in - perfect for immediate occupancy")

        elif prop_type.id in ['2bhk', '3bhk']:
            insights.append("Suitable for small to medium families")
            bathrooms = data.get('bathrooms', 2)
            if isinstance(bathrooms, (int, float)) and bathrooms >= 3:
                insights.append("Multiple bathrooms add convenience for families")

        elif prop_type.id == 'villa':
            insights.append("Independent living with privacy and space")
            garden_area = data.get('garden_area', 0)
            if isinstance(garden_area, (int, float)) and garden_area > 500:
                insights.append("Spacious garden area perfect for outdoor activities")

        elif prop_type.id == 'hall':
            seating_capacity = data.get('seating_capacity', 100)
            if isinstance(seating_capacity, (int, float)):
                if seating_capacity >= 300:
                    insights.append("Large capacity suitable for major events and weddings")
                else:
                    insights.append("Ideal for intimate gatherings and corporate events")

        elif prop_type.id == 'office':
            insights.append("Commercial space with business potential")
            floor = data.get('floor', 1)
            if isinstance(floor, (int, float)) and floor >= 5:
                insights.append("Higher floor provides better views and prestige")

        elif prop_type.id == 'shop':
            if data.get('main_road_facing'):
                insights.append("Main road facing ensures high visibility and footfall")
            insights.append("Retail space with commercial income potential")

        # Amenities insights
        amenities = data.get('amenities', [])
        if amenities:
            amenities_count = len(amenities) if isinstance(amenities, list) else 1
            if amenities_count >= 8:
                insights.append(f"Excellent connectivity with {amenities_count} nearby amenities")
            elif amenities_count >= 5:
                insights.append(f"Good amenities coverage with {amenities_count} facilities nearby")
            elif amenities_count >= 3:
                insights.append(f"Basic amenities available with {amenities_count} facilities")

            # Specific amenity insights
            if isinstance(amenities, list):
                if 'Metro Station/Bus Stop' in amenities:
                    insights.append("Excellent public transport connectivity")
                if 'Hospital/Medical Center' in amenities:
                    insights.append("Healthcare facilities readily accessible")
                if 'School/Educational Institute' in amenities:
                    insights.append("Good for families with educational institutions nearby")
                if 'IT Park/Tech Hub' in amenities:
                    insights.append("Ideal for IT professionals with tech hubs nearby")
                if 'Shopping Mall/Market' in amenities:
                    insights.append("Convenient shopping and retail options available")
        else:
            insights.append("Consider checking for nearby amenities to enhance property value")

        # Investment insights
        if predicted_price < 50:
            insights.append("Affordable property with good entry-level investment potential")
        elif predicted_price > 150:
            insights.append("Premium property suitable for high-end investment")

        return insights

    def _get_price_breakdown(self, property_type_id: str, data: Dict[str, Any],
                           predicted_price: float, prop_type) -> Dict[str, Any]:
        """Get detailed price breakdown"""
        total_sqft = float(data.get('total_sqft', 1000))
        base_price_per_sqft = 3500
        base_price = (total_sqft * base_price_per_sqft) / 100000

        breakdown = {
            'base_price': round(base_price, 2),
            'property_type_factor': prop_type.base_price_factor,
            'location_factor': self.get_location_factor(data.get('location', '')),
            'adjustments': {}
        }

        # Calculate individual adjustments
        age = data.get('age', 'New Construction')
        if age != 'New Construction':
            age_factors = {
                '1-5 years': 0.0,
                '5-10 years': -0.05,
                '10-15 years': -0.1,
                '15+ years': -0.15
            }
            breakdown['adjustments']['age'] = age_factors.get(age, 0)

        furnishing = data.get('furnishing', 'Unfurnished')
        if furnishing != 'Unfurnished':
            furnishing_factors = {
                'Semi-Furnished': 0.08,
                'Fully Furnished': 0.15
            }
            breakdown['adjustments']['furnishing'] = furnishing_factors.get(furnishing, 0)

        # Amenities adjustment
        amenities = data.get('amenities', [])
        if amenities:
            amenities_factor = self._calculate_amenities_factor(amenities, prop_type)
            breakdown['adjustments']['amenities'] = amenities_factor - 1.0  # Convert to percentage

        return breakdown

# Global instance
enhanced_predictor = EnhancedPricePrediction()
