"""
Nearby Amenities and Location Intelligence
"""

import json
import random
from typing import Dict, List, Tuple

class AmenitiesManager:
    """Manage nearby amenities and location intelligence"""
    
    def __init__(self):
        # Sample amenities data for different locations
        self.amenities_data = {
            'Whitefield': {
                'schools': [
                    {'name': 'Ryan International School', 'distance': '0.8 km', 'rating': 4.2, 'type': 'CBSE'},
                    {'name': 'Inventure Academy', 'distance': '1.2 km', 'rating': 4.5, 'type': 'IB'},
                    {'name': 'Greenwood High School', 'distance': '2.1 km', 'rating': 4.3, 'type': 'ICSE'},
                    {'name': 'Oakridge International School', 'distance': '2.8 km', 'rating': 4.4, 'type': 'IB'}
                ],
                'hospitals': [
                    {'name': 'Columbia Asia Hospital', 'distance': '1.5 km', 'rating': 4.1, 'type': 'Multi-specialty'},
                    {'name': 'Manipal Hospital', 'distance': '3.2 km', 'rating': 4.3, 'type': 'Multi-specialty'},
                    {'name': 'Apollo Clinic', 'distance': '0.9 km', 'rating': 3.9, 'type': 'Clinic'},
                    {'name': 'Narayana Health', 'distance': '4.1 km', 'rating': 4.2, 'type': 'Multi-specialty'}
                ],
                'shopping': [
                    {'name': 'Phoenix MarketCity', 'distance': '2.3 km', 'rating': 4.4, 'type': 'Mall'},
                    {'name': 'Forum Shantiniketan', 'distance': '1.8 km', 'rating': 4.2, 'type': 'Mall'},
                    {'name': 'VR Bengaluru', 'distance': '3.5 km', 'rating': 4.3, 'type': 'Mall'},
                    {'name': 'Big Bazaar', 'distance': '1.1 km', 'rating': 3.8, 'type': 'Supermarket'}
                ],
                'transport': [
                    {'name': 'Whitefield Metro Station', 'distance': '2.1 km', 'rating': 4.0, 'type': 'Metro'},
                    {'name': 'ITPL Bus Stop', 'distance': '0.5 km', 'rating': 3.7, 'type': 'Bus'},
                    {'name': 'Kempegowda Airport', 'distance': '45 km', 'rating': 4.2, 'type': 'Airport'},
                    {'name': 'Whitefield Railway Station', 'distance': '3.8 km', 'rating': 3.5, 'type': 'Railway'}
                ],
                'restaurants': [
                    {'name': 'Toit Brewpub', 'distance': '2.5 km', 'rating': 4.3, 'type': 'Brewery'},
                    {'name': 'Barbeque Nation', 'distance': '1.9 km', 'rating': 4.1, 'type': 'Buffet'},
                    {'name': 'Cafe Coffee Day', 'distance': '0.7 km', 'rating': 3.9, 'type': 'Cafe'},
                    {'name': 'Dominos Pizza', 'distance': '1.2 km', 'rating': 4.0, 'type': 'Fast Food'}
                ],
                'entertainment': [
                    {'name': 'PVR Cinemas', 'distance': '2.3 km', 'rating': 4.2, 'type': 'Cinema'},
                    {'name': 'Smaaash', 'distance': '2.8 km', 'rating': 4.4, 'type': 'Gaming'},
                    {'name': 'Lumbini Gardens', 'distance': '8.5 km', 'rating': 3.8, 'type': 'Park'},
                    {'name': 'Innovative Film City', 'distance': '12 km', 'rating': 4.0, 'type': 'Theme Park'}
                ]
            },
            'Koramangala': {
                'schools': [
                    {'name': 'Indus International School', 'distance': '1.5 km', 'rating': 4.4, 'type': 'IB'},
                    {'name': 'National Public School', 'distance': '2.1 km', 'rating': 4.3, 'type': 'CBSE'},
                    {'name': 'Bethany High School', 'distance': '1.8 km', 'rating': 4.1, 'type': 'ICSE'},
                    {'name': 'Gear Innovative School', 'distance': '2.5 km', 'rating': 4.2, 'type': 'CBSE'}
                ],
                'hospitals': [
                    {'name': 'Fortis Hospital', 'distance': '2.8 km', 'rating': 4.3, 'type': 'Multi-specialty'},
                    {'name': 'St. Johns Medical College', 'distance': '1.2 km', 'rating': 4.5, 'type': 'Medical College'},
                    {'name': 'Manipal Hospital', 'distance': '3.5 km', 'rating': 4.2, 'type': 'Multi-specialty'},
                    {'name': 'Apollo Clinic', 'distance': '0.8 km', 'rating': 4.0, 'type': 'Clinic'}
                ],
                'shopping': [
                    {'name': 'Forum Mall', 'distance': '1.2 km', 'rating': 4.3, 'type': 'Mall'},
                    {'name': '1 MG Lido Mall', 'distance': '2.5 km', 'rating': 4.1, 'type': 'Mall'},
                    {'name': 'Central Mall', 'distance': '3.1 km', 'rating': 4.0, 'type': 'Mall'},
                    {'name': 'More Supermarket', 'distance': '0.5 km', 'rating': 3.8, 'type': 'Supermarket'}
                ],
                'transport': [
                    {'name': 'Koramangala Metro Station', 'distance': '1.8 km', 'rating': 4.1, 'type': 'Metro'},
                    {'name': 'Silk Board Bus Stop', 'distance': '2.2 km', 'rating': 3.6, 'type': 'Bus'},
                    {'name': 'Kempegowda Airport', 'distance': '38 km', 'rating': 4.2, 'type': 'Airport'},
                    {'name': 'Bangalore City Railway Station', 'distance': '8.5 km', 'rating': 3.8, 'type': 'Railway'}
                ],
                'restaurants': [
                    {'name': 'Truffles', 'distance': '0.8 km', 'rating': 4.4, 'type': 'Continental'},
                    {'name': 'Social', 'distance': '1.1 km', 'rating': 4.2, 'type': 'Pub'},
                    {'name': 'Starbucks', 'distance': '0.6 km', 'rating': 4.1, 'type': 'Cafe'},
                    {'name': 'Burger King', 'distance': '1.3 km', 'rating': 3.9, 'type': 'Fast Food'}
                ],
                'entertainment': [
                    {'name': 'Inox Cinemas', 'distance': '1.2 km', 'rating': 4.3, 'type': 'Cinema'},
                    {'name': 'Cubbon Park', 'distance': '6.5 km', 'rating': 4.1, 'type': 'Park'},
                    {'name': 'UB City Mall', 'distance': '7.2 km', 'rating': 4.4, 'type': 'Luxury Mall'},
                    {'name': 'Lal Bagh', 'distance': '4.8 km', 'rating': 4.2, 'type': 'Botanical Garden'}
                ]
            },
            'Indiranagar': {
                'schools': [
                    {'name': 'Bishop Cotton Boys School', 'distance': '2.1 km', 'rating': 4.5, 'type': 'ICSE'},
                    {'name': 'Clarence High School', 'distance': '1.8 km', 'rating': 4.2, 'type': 'CBSE'},
                    {'name': 'Sophia High School', 'distance': '2.5 km', 'rating': 4.1, 'type': 'ICSE'},
                    {'name': 'Delhi Public School', 'distance': '3.2 km', 'rating': 4.4, 'type': 'CBSE'}
                ],
                'hospitals': [
                    {'name': 'Sakra World Hospital', 'distance': '2.8 km', 'rating': 4.4, 'type': 'Multi-specialty'},
                    {'name': 'Mallya Hospital', 'distance': '1.5 km', 'rating': 4.1, 'type': 'Multi-specialty'},
                    {'name': 'Apollo Clinic', 'distance': '0.9 km', 'rating': 4.0, 'type': 'Clinic'},
                    {'name': 'Narayana Hrudayalaya', 'distance': '4.2 km', 'rating': 4.3, 'type': 'Cardiac'}
                ],
                'shopping': [
                    {'name': 'Garuda Mall', 'distance': '1.8 km', 'rating': 4.2, 'type': 'Mall'},
                    {'name': 'Commercial Street', 'distance': '3.5 km', 'rating': 4.0, 'type': 'Street Shopping'},
                    {'name': 'Brigade Road', 'distance': '4.1 km', 'rating': 4.1, 'type': 'Shopping Street'},
                    {'name': 'Reliance Fresh', 'distance': '0.7 km', 'rating': 3.9, 'type': 'Supermarket'}
                ],
                'transport': [
                    {'name': 'Indiranagar Metro Station', 'distance': '1.2 km', 'rating': 4.2, 'type': 'Metro'},
                    {'name': 'HAL Bus Stop', 'distance': '0.8 km', 'rating': 3.8, 'type': 'Bus'},
                    {'name': 'Kempegowda Airport', 'distance': '42 km', 'rating': 4.2, 'type': 'Airport'},
                    {'name': 'Bangalore Cantonment', 'distance': '5.5 km', 'rating': 3.9, 'type': 'Railway'}
                ],
                'restaurants': [
                    {'name': 'Toit', 'distance': '1.1 km', 'rating': 4.5, 'type': 'Brewery'},
                    {'name': 'The Fatty Bao', 'distance': '1.5 km', 'rating': 4.3, 'type': 'Asian'},
                    {'name': 'Third Wave Coffee', 'distance': '0.6 km', 'rating': 4.2, 'type': 'Cafe'},
                    {'name': 'McDonalds', 'distance': '1.0 km', 'rating': 3.8, 'type': 'Fast Food'}
                ],
                'entertainment': [
                    {'name': 'PVR Cinemas', 'distance': '1.8 km', 'rating': 4.3, 'type': 'Cinema'},
                    {'name': 'Ulsoor Lake', 'distance': '2.5 km', 'rating': 3.9, 'type': 'Lake'},
                    {'name': 'Cubbon Park', 'distance': '5.2 km', 'rating': 4.1, 'type': 'Park'},
                    {'name': 'Hard Rock Cafe', 'distance': '2.1 km', 'rating': 4.2, 'type': 'Music Venue'}
                ]
            }
        }
        
        # Default amenities for locations not in our database
        self.default_amenities = {
            'schools': [
                {'name': 'Local Public School', 'distance': '1.5 km', 'rating': 3.8, 'type': 'CBSE'},
                {'name': 'Private School', 'distance': '2.1 km', 'rating': 4.0, 'type': 'ICSE'}
            ],
            'hospitals': [
                {'name': 'Government Hospital', 'distance': '2.5 km', 'rating': 3.5, 'type': 'General'},
                {'name': 'Private Clinic', 'distance': '1.2 km', 'rating': 3.9, 'type': 'Clinic'}
            ],
            'shopping': [
                {'name': 'Local Market', 'distance': '1.0 km', 'rating': 3.7, 'type': 'Market'},
                {'name': 'Supermarket', 'distance': '1.8 km', 'rating': 3.8, 'type': 'Supermarket'}
            ],
            'transport': [
                {'name': 'Bus Stop', 'distance': '0.5 km', 'rating': 3.5, 'type': 'Bus'},
                {'name': 'Railway Station', 'distance': '5.2 km', 'rating': 3.6, 'type': 'Railway'}
            ],
            'restaurants': [
                {'name': 'Local Restaurant', 'distance': '0.8 km', 'rating': 3.8, 'type': 'Indian'},
                {'name': 'Fast Food', 'distance': '1.5 km', 'rating': 3.6, 'type': 'Fast Food'}
            ],
            'entertainment': [
                {'name': 'Local Cinema', 'distance': '2.8 km', 'rating': 3.7, 'type': 'Cinema'},
                {'name': 'Park', 'distance': '1.2 km', 'rating': 3.9, 'type': 'Park'}
            ]
        }
    
    def get_nearby_amenities(self, location: str) -> Dict:
        """Get nearby amenities for a location"""
        # Clean location name
        location = location.strip().title()
        
        # Check if we have specific data for this location
        if location in self.amenities_data:
            return self.amenities_data[location]
        
        # Check for partial matches
        for known_location in self.amenities_data.keys():
            if location.lower() in known_location.lower() or known_location.lower() in location.lower():
                return self.amenities_data[known_location]
        
        # Return default amenities with some randomization
        return self._generate_default_amenities(location)
    
    def _generate_default_amenities(self, location: str) -> Dict:
        """Generate default amenities with some variation"""
        amenities = {}
        
        for category, items in self.default_amenities.items():
            amenities[category] = []
            for item in items:
                # Add some randomization to distances and ratings
                distance_variation = random.uniform(0.8, 1.5)
                rating_variation = random.uniform(-0.3, 0.3)
                
                new_item = item.copy()
                # Modify distance
                base_distance = float(item['distance'].split()[0])
                new_distance = base_distance * distance_variation
                new_item['distance'] = f"{new_distance:.1f} km"
                
                # Modify rating
                new_rating = max(3.0, min(5.0, item['rating'] + rating_variation))
                new_item['rating'] = round(new_rating, 1)
                
                amenities[category].append(new_item)
        
        return amenities
    
    def get_location_score(self, location: str) -> Dict:
        """Calculate location score based on amenities"""
        amenities = self.get_nearby_amenities(location)
        
        scores = {}
        weights = {
            'schools': 0.2,
            'hospitals': 0.15,
            'shopping': 0.15,
            'transport': 0.25,
            'restaurants': 0.1,
            'entertainment': 0.15
        }
        
        total_score = 0
        for category, items in amenities.items():
            if category in weights:
                # Calculate category score based on average rating and proximity
                category_score = 0
                for item in items:
                    rating_score = (item['rating'] / 5.0) * 100
                    distance = float(item['distance'].split()[0])
                    proximity_score = max(0, 100 - (distance * 10))  # Closer is better
                    item_score = (rating_score + proximity_score) / 2
                    category_score += item_score
                
                category_score = category_score / len(items) if items else 0
                scores[category] = round(category_score, 1)
                total_score += category_score * weights[category]
        
        scores['overall'] = round(total_score, 1)
        return scores
    
    def get_amenity_summary(self, location: str) -> Dict:
        """Get a summary of amenities for display"""
        amenities = self.get_nearby_amenities(location)
        scores = self.get_location_score(location)
        
        summary = {
            'location': location,
            'overall_score': scores['overall'],
            'category_scores': scores,
            'highlights': [],
            'total_amenities': sum(len(items) for items in amenities.values()),
            'amenities': amenities
        }
        
        # Generate highlights
        if scores['transport'] > 70:
            summary['highlights'].append("Excellent connectivity")
        if scores['schools'] > 75:
            summary['highlights'].append("Great schools nearby")
        if scores['hospitals'] > 70:
            summary['highlights'].append("Good healthcare access")
        if scores['shopping'] > 70:
            summary['highlights'].append("Convenient shopping")
        if scores['entertainment'] > 70:
            summary['highlights'].append("Rich entertainment options")
        
        return summary

# Global amenities manager instance
amenities_manager = AmenitiesManager()

def get_location_amenities(location: str):
    """Helper function to get amenities for a location"""
    return amenities_manager.get_amenity_summary(location)

def search_nearby_amenities(location: str, category: str = None):
    """Search for specific category of amenities"""
    amenities = amenities_manager.get_nearby_amenities(location)
    
    if category and category in amenities:
        return {category: amenities[category]}
    
    return amenities
