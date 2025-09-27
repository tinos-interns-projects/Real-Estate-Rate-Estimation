# ===================== Property Type Presets and Templates =====================
"""
Predefined templates and presets for common property configurations
to make the prediction process faster and more accurate.
"""

from typing import Dict, List, Any, Optional
from utils.property_types import property_type_manager

class PropertyPresets:
    """Manager for property presets and templates"""
    
    def __init__(self):
        self.presets = self._initialize_presets()
    
    def _initialize_presets(self) -> Dict[str, Dict[str, Any]]:
        """Initialize predefined property presets"""
        return {
            # Studio Apartment Presets
            'studio_basic': {
                'property_type': 'studio',
                'name': 'Basic Studio',
                'description': 'Affordable studio apartment for young professionals',
                'template': {
                    'total_sqft': 400,
                    'bathrooms': 1,
                    'furnishing': 'Unfurnished',
                    'availability': 'Ready To Move',
                    'area_type': 'Super built-up Area'
                },
                'typical_price_range': '25-45 Lakhs',
                'target_audience': 'Young professionals, students'
            },
            'studio_premium': {
                'property_type': 'studio',
                'name': 'Premium Studio',
                'description': 'Fully furnished premium studio in prime location',
                'template': {
                    'total_sqft': 550,
                    'bathrooms': 1,
                    'furnishing': 'Fully Furnished',
                    'availability': 'Ready To Move',
                    'area_type': 'Super built-up Area',
                    'floor': 5,
                    'parking': 1
                },
                'typical_price_range': '45-70 Lakhs',
                'target_audience': 'Working professionals, executives'
            },
            
            # 1RK Presets
            '1rk_basic': {
                'property_type': '1rk',
                'name': 'Basic 1RK',
                'description': 'Compact 1RK with separate kitchen',
                'template': {
                    'total_sqft': 500,
                    'bathrooms': 1,
                    'balconies': 1,
                    'furnishing': 'Unfurnished',
                    'availability': 'Ready To Move',
                    'area_type': 'Super built-up Area'
                },
                'typical_price_range': '30-50 Lakhs',
                'target_audience': 'Small families, couples'
            },
            
            # 1 BHK Presets
            '1bhk_standard': {
                'property_type': '1bhk',
                'name': 'Standard 1BHK',
                'description': 'Well-designed 1BHK for small families',
                'template': {
                    'total_sqft': 650,
                    'bathrooms': 1,
                    'balconies': 1,
                    'kitchen_type': 'Modular',
                    'furnishing': 'Semi-Furnished',
                    'availability': 'Ready To Move',
                    'area_type': 'Super built-up Area',
                    'parking': 1
                },
                'typical_price_range': '40-65 Lakhs',
                'target_audience': 'Small families, couples'
            },
            '1bhk_premium': {
                'property_type': '1bhk',
                'name': 'Premium 1BHK',
                'description': 'Spacious 1BHK with premium amenities',
                'template': {
                    'total_sqft': 800,
                    'bathrooms': 2,
                    'balconies': 2,
                    'kitchen_type': 'Modular',
                    'furnishing': 'Fully Furnished',
                    'availability': 'Ready To Move',
                    'area_type': 'Super built-up Area',
                    'floor': 8,
                    'parking': 1
                },
                'typical_price_range': '60-90 Lakhs',
                'target_audience': 'Working professionals, small families'
            },
            
            # 2 BHK Presets
            '2bhk_standard': {
                'property_type': '2bhk',
                'name': 'Standard 2BHK',
                'description': 'Family-friendly 2BHK apartment',
                'template': {
                    'total_sqft': 1100,
                    'bathrooms': 2,
                    'balconies': 2,
                    'kitchen_type': 'Modular',
                    'furnishing': 'Semi-Furnished',
                    'availability': 'Ready To Move',
                    'area_type': 'Super built-up Area',
                    'parking': 1
                },
                'typical_price_range': '65-95 Lakhs',
                'target_audience': 'Medium families, professionals'
            },
            '2bhk_premium': {
                'property_type': '2bhk',
                'name': 'Premium 2BHK',
                'description': 'Spacious 2BHK with luxury amenities',
                'template': {
                    'total_sqft': 1350,
                    'bathrooms': 3,
                    'balconies': 2,
                    'kitchen_type': 'Modular',
                    'furnishing': 'Fully Furnished',
                    'availability': 'Ready To Move',
                    'area_type': 'Super built-up Area',
                    'floor': 10,
                    'parking': 2
                },
                'typical_price_range': '90-140 Lakhs',
                'target_audience': 'Affluent families, executives'
            },
            
            # 3 BHK Presets
            '3bhk_family': {
                'property_type': '3bhk',
                'name': 'Family 3BHK',
                'description': 'Spacious 3BHK perfect for large families',
                'template': {
                    'total_sqft': 1500,
                    'bathrooms': 3,
                    'balconies': 2,
                    'kitchen_type': 'Modular',
                    'furnishing': 'Semi-Furnished',
                    'availability': 'Ready To Move',
                    'area_type': 'Super built-up Area',
                    'parking': 2
                },
                'typical_price_range': '95-150 Lakhs',
                'target_audience': 'Large families, multi-generational'
            },
            '3bhk_luxury': {
                'property_type': '3bhk',
                'name': 'Luxury 3BHK',
                'description': 'Premium 3BHK with high-end finishes',
                'template': {
                    'total_sqft': 1800,
                    'bathrooms': 4,
                    'balconies': 3,
                    'kitchen_type': 'Modular',
                    'furnishing': 'Fully Furnished',
                    'availability': 'Ready To Move',
                    'area_type': 'Super built-up Area',
                    'floor': 12,
                    'parking': 2
                },
                'typical_price_range': '140-220 Lakhs',
                'target_audience': 'High-income families, luxury seekers'
            },
            
            # Villa Presets
            'villa_standard': {
                'property_type': 'villa',
                'name': 'Standard Villa',
                'description': 'Independent villa with garden',
                'template': {
                    'total_sqft': 2200,
                    'bedrooms': 3,
                    'bathrooms': 3,
                    'balconies': 2,
                    'kitchen_type': 'Modular',
                    'furnishing': 'Semi-Furnished',
                    'availability': 'Ready To Move',
                    'area_type': 'Super built-up Area',
                    'total_floors': 2,
                    'parking': 2,
                    'garden_area': 800
                },
                'typical_price_range': '150-250 Lakhs',
                'target_audience': 'Families seeking independence'
            },
            'villa_luxury': {
                'property_type': 'villa',
                'name': 'Luxury Villa',
                'description': 'Premium villa with extensive amenities',
                'template': {
                    'total_sqft': 3500,
                    'bedrooms': 4,
                    'bathrooms': 5,
                    'balconies': 3,
                    'kitchen_type': 'Modular',
                    'furnishing': 'Fully Furnished',
                    'availability': 'Ready To Move',
                    'area_type': 'Super built-up Area',
                    'total_floors': 3,
                    'parking': 3,
                    'garden_area': 1500
                },
                'typical_price_range': '300-500 Lakhs',
                'target_audience': 'High-net-worth individuals'
            },
            
            # Commercial Presets
            'office_startup': {
                'property_type': 'office',
                'name': 'Startup Office',
                'description': 'Compact office space for startups',
                'template': {
                    'total_sqft': 800,
                    'commercial_type': 'Office Space',
                    'washrooms': 2,
                    'cabin_rooms': 1,
                    'conference_rooms': 1,
                    'workstations': 15,
                    'furnishing': 'Semi-Furnished',
                    'availability': 'Ready To Move',
                    'area_type': 'Super built-up Area',
                    'floor': 3,
                    'parking': 3
                },
                'typical_price_range': '60-90 Lakhs',
                'target_audience': 'Startups, small businesses'
            },
            'office_corporate': {
                'property_type': 'office',
                'name': 'Corporate Office',
                'description': 'Large office space for established companies',
                'template': {
                    'total_sqft': 2500,
                    'commercial_type': 'Office Space',
                    'washrooms': 6,
                    'cabin_rooms': 8,
                    'conference_rooms': 3,
                    'workstations': 80,
                    'furnishing': 'Fully Furnished',
                    'availability': 'Ready To Move',
                    'area_type': 'Super built-up Area',
                    'floor': 8,
                    'parking': 15
                },
                'typical_price_range': '200-350 Lakhs',
                'target_audience': 'Established companies, corporates'
            },
            
            'shop_retail': {
                'property_type': 'shop',
                'name': 'Retail Shop',
                'description': 'Ground floor retail space',
                'template': {
                    'total_sqft': 600,
                    'washrooms': 1,
                    'frontage': 15,
                    'main_road_facing': True,
                    'availability': 'Ready To Move',
                    'area_type': 'Super built-up Area',
                    'floor': 0,
                    'parking': 2
                },
                'typical_price_range': '80-150 Lakhs',
                'target_audience': 'Retailers, small business owners'
            },
            
            'hall_wedding': {
                'property_type': 'hall',
                'name': 'Wedding Hall',
                'description': 'Large hall for weddings and events',
                'template': {
                    'total_sqft': 4000,
                    'seating_capacity': 400,
                    'washrooms': 8,
                    'ac_available': True,
                    'kitchen_facility': True,
                    'availability': 'Ready To Move',
                    'area_type': 'Super built-up Area',
                    'floor': 0,
                    'parking': 50
                },
                'typical_price_range': '300-600 Lakhs',
                'target_audience': 'Event management, hospitality'
            }
        }
    
    def get_preset(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific preset by ID"""
        return self.presets.get(preset_id)
    
    def get_presets_by_property_type(self, property_type_id: str) -> List[Dict[str, Any]]:
        """Get all presets for a specific property type"""
        return [
            {**preset, 'preset_id': preset_id}
            for preset_id, preset in self.presets.items()
            if preset['property_type'] == property_type_id
        ]
    
    def get_all_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get all available presets"""
        return self.presets
    
    def apply_preset(self, preset_id: str, custom_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Apply a preset and optionally override with custom data"""
        preset = self.get_preset(preset_id)
        if not preset:
            raise ValueError(f"Preset not found: {preset_id}")
        
        # Start with preset template
        result = preset['template'].copy()
        
        # Override with custom data if provided
        if custom_data:
            result.update(custom_data)
        
        # Add property type
        result['property_type'] = preset['property_type']
        
        return result
    
    def get_preset_suggestions(self, property_type_id: str, budget_range: str = None) -> List[Dict[str, Any]]:
        """Get preset suggestions based on property type and budget"""
        presets = self.get_presets_by_property_type(property_type_id)
        
        if budget_range:
            # Filter by budget if provided
            # This is a simple implementation - could be enhanced with actual budget parsing
            budget_keywords = {
                'budget': ['basic', 'standard'],
                'premium': ['premium', 'luxury'],
                'luxury': ['luxury', 'premium']
            }
            
            relevant_keywords = budget_keywords.get(budget_range.lower(), [])
            if relevant_keywords:
                presets = [
                    preset for preset in presets
                    if any(keyword in preset['name'].lower() for keyword in relevant_keywords)
                ]
        
        return presets

# Global instance
property_presets = PropertyPresets()
