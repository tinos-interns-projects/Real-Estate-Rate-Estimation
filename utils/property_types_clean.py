# ===================== Property Types Configuration =====================
"""
Property type configuration system for dynamic price prediction.
Defines different property types and their specific features/requirements.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class PropertyCategory(Enum):
    """Main property categories"""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    MIXED_USE = "mixed_use"

class FieldType(Enum):
    """Field types for form generation"""
    TEXT = "text"
    NUMBER = "number"
    SELECT = "select"
    MULTISELECT = "multiselect"
    BOOLEAN = "boolean"
    RANGE = "range"

@dataclass
class PropertyField:
    """Configuration for a property field"""
    name: str
    label: str
    field_type: FieldType
    required: bool = False
    options: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    default_value: Optional[Any] = None
    help_text: Optional[str] = None
    icon: Optional[str] = None
    unit: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'label': self.label,
            'field_type': self.field_type.value,
            'required': self.required,
            'options': self.options,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'default_value': self.default_value,
            'help_text': self.help_text,
            'icon': self.icon,
            'unit': self.unit
        }

@dataclass
class PropertyType:
    """Configuration for a property type"""
    id: str
    name: str
    category: PropertyCategory
    description: str
    fields: List[PropertyField]
    prediction_weights: Dict[str, float]
    base_price_factor: float = 1.0
    icon: Optional[str] = None
    
    def get_required_fields(self) -> List[PropertyField]:
        """Get only required fields"""
        return [field for field in self.fields if field.required]
    
    def get_optional_fields(self) -> List[PropertyField]:
        """Get only optional fields"""
        return [field for field in self.fields if not field.required]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.value,
            'description': self.description,
            'fields': [field.to_dict() for field in self.fields],
            'prediction_weights': self.prediction_weights,
            'base_price_factor': self.base_price_factor,
            'icon': self.icon
        }

# ===================== Common Field Definitions =====================

# Common fields used across property types
COMMON_FIELDS = {
    'location': PropertyField(
        name='location',
        label='Location',
        field_type=FieldType.TEXT,
        required=True,
        icon='fas fa-map-marker-alt',
        help_text='Enter the location or area'
    ),
    'total_sqft': PropertyField(
        name='total_sqft',
        label='Total Area',
        field_type=FieldType.NUMBER,
        required=True,
        min_value=100,
        max_value=50000,
        unit='sqft',
        icon='fas fa-expand-arrows-alt',
        help_text='Total area in square feet'
    ),
    'area_type': PropertyField(
        name='area_type',
        label='Area Type',
        field_type=FieldType.SELECT,
        required=True,
        options=['Super built-up Area', 'Built-up Area', 'Plot Area', 'Carpet Area'],
        default_value='Super built-up Area',
        icon='fas fa-ruler-combined'
    ),
    'availability': PropertyField(
        name='availability',
        label='Availability',
        field_type=FieldType.SELECT,
        required=True,
        options=['Ready To Move', 'Under Construction', 'New Launch'],
        default_value='Ready To Move',
        icon='fas fa-calendar-check'
    ),
    'age': PropertyField(
        name='age',
        label='Property Age',
        field_type=FieldType.SELECT,
        required=False,
        options=['New Construction', '1-5 years', '5-10 years', '10-15 years', '15+ years'],
        icon='fas fa-clock'
    ),
    'furnishing': PropertyField(
        name='furnishing',
        label='Furnishing Status',
        field_type=FieldType.SELECT,
        required=False,
        options=['Unfurnished', 'Semi-Furnished', 'Fully Furnished'],
        default_value='Unfurnished',
        icon='fas fa-couch'
    ),
    'parking': PropertyField(
        name='parking',
        label='Parking Spaces',
        field_type=FieldType.NUMBER,
        required=False,
        min_value=0,
        max_value=10,
        default_value=1,
        icon='fas fa-car'
    ),
    'floor': PropertyField(
        name='floor',
        label='Floor Number',
        field_type=FieldType.NUMBER,
        required=False,
        min_value=0,
        max_value=50,
        icon='fas fa-building'
    ),
    'total_floors': PropertyField(
        name='total_floors',
        label='Total Floors in Building',
        field_type=FieldType.NUMBER,
        required=False,
        min_value=1,
        max_value=50,
        icon='fas fa-building'
    )
}

# Residential specific fields
RESIDENTIAL_FIELDS = {
    'bedrooms': PropertyField(
        name='bedrooms',
        label='Bedrooms',
        field_type=FieldType.NUMBER,
        required=True,
        min_value=0,
        max_value=10,
        icon='fas fa-bed'
    ),
    'bathrooms': PropertyField(
        name='bathrooms',
        label='Bathrooms',
        field_type=FieldType.NUMBER,
        required=True,
        min_value=1,
        max_value=10,
        icon='fas fa-bath'
    ),
    'balconies': PropertyField(
        name='balconies',
        label='Balconies',
        field_type=FieldType.NUMBER,
        required=False,
        min_value=0,
        max_value=5,
        default_value=1,
        icon='fas fa-building'
    ),
    'kitchen_type': PropertyField(
        name='kitchen_type',
        label='Kitchen Type',
        field_type=FieldType.SELECT,
        required=False,
        options=['Modular', 'Semi-Modular', 'Traditional'],
        icon='fas fa-utensils'
    )
}

# Commercial specific fields
COMMERCIAL_FIELDS = {
    'commercial_type': PropertyField(
        name='commercial_type',
        label='Commercial Type',
        field_type=FieldType.SELECT,
        required=True,
        options=['Office Space', 'Retail Shop', 'Warehouse', 'Showroom', 'Restaurant Space'],
        icon='fas fa-briefcase'
    ),
    'washrooms': PropertyField(
        name='washrooms',
        label='Washrooms',
        field_type=FieldType.NUMBER,
        required=False,
        min_value=1,
        max_value=20,
        icon='fas fa-restroom'
    ),
    'cabin_rooms': PropertyField(
        name='cabin_rooms',
        label='Cabin Rooms',
        field_type=FieldType.NUMBER,
        required=False,
        min_value=0,
        max_value=20,
        icon='fas fa-door-closed'
    ),
    'conference_rooms': PropertyField(
        name='conference_rooms',
        label='Conference Rooms',
        field_type=FieldType.NUMBER,
        required=False,
        min_value=0,
        max_value=10,
        icon='fas fa-users'
    )
}

# Amenities field - common to all property types
AMENITIES_FIELD = PropertyField(
    name='amenities',
    label='Nearby Amenities',
    field_type=FieldType.MULTISELECT,
    required=False,
    options=[
        'Hospital/Medical Center',
        'School/Educational Institute', 
        'Shopping Mall/Market',
        'Metro Station/Bus Stop',
        'Park/Garden',
        'Gym/Fitness Center',
        'Restaurant/Food Court',
        'Bank/ATM',
        'Pharmacy/Medical Store',
        'Petrol Pump/Gas Station',
        'Temple/Religious Place',
        'Police Station',
        'Fire Station',
        'Swimming Pool',
        'Playground',
        'Library',
        'Cinema/Entertainment',
        'Airport Nearby',
        'IT Park/Tech Hub',
        'Government Office'
    ],
    icon='fas fa-map-marked-alt',
    help_text='Select nearby amenities (within 2-3 km radius)'
)

# ===================== Property Type Creation =====================

def create_property_types() -> Dict[str, PropertyType]:
    """Create all predefined property types with amenities"""

    property_types = {}

    # 1. Studio Apartment
    property_types['studio'] = PropertyType(
        id='studio',
        name='Studio Apartment',
        category=PropertyCategory.RESIDENTIAL,
        description='Single room living space with attached bathroom and kitchenette',
        icon='fas fa-home',
        base_price_factor=0.6,
        fields=[
            COMMON_FIELDS['location'],
            COMMON_FIELDS['total_sqft'],
            COMMON_FIELDS['area_type'],
            COMMON_FIELDS['availability'],
            RESIDENTIAL_FIELDS['bathrooms'],
            COMMON_FIELDS['floor'],
            COMMON_FIELDS['total_floors'],
            COMMON_FIELDS['age'],
            COMMON_FIELDS['furnishing'],
            COMMON_FIELDS['parking'],
            AMENITIES_FIELD
        ],
        prediction_weights={
            'total_sqft': 0.35,
            'location': 0.25,
            'floor': 0.1,
            'age': 0.1,
            'furnishing': 0.1,
            'amenities': 0.1
        }
    )

    # 2. 1RK (1 Room Kitchen)
    property_types['1rk'] = PropertyType(
        id='1rk',
        name='1 RK',
        category=PropertyCategory.RESIDENTIAL,
        description='One room with separate kitchen and bathroom',
        icon='fas fa-door-open',
        base_price_factor=0.7,
        fields=[
            COMMON_FIELDS['location'],
            COMMON_FIELDS['total_sqft'],
            COMMON_FIELDS['area_type'],
            COMMON_FIELDS['availability'],
            RESIDENTIAL_FIELDS['bathrooms'],
            RESIDENTIAL_FIELDS['balconies'],
            COMMON_FIELDS['floor'],
            COMMON_FIELDS['total_floors'],
            COMMON_FIELDS['age'],
            COMMON_FIELDS['furnishing'],
            COMMON_FIELDS['parking'],
            AMENITIES_FIELD
        ],
        prediction_weights={
            'total_sqft': 0.3,
            'location': 0.25,
            'floor': 0.1,
            'age': 0.1,
            'furnishing': 0.1,
            'balconies': 0.05,
            'amenities': 0.1
        }
    )

    # 3. 1 BHK Apartment
    property_types['1bhk'] = PropertyType(
        id='1bhk',
        name='1 BHK Apartment',
        category=PropertyCategory.RESIDENTIAL,
        description='One bedroom with hall, kitchen and bathroom',
        icon='fas fa-bed',
        base_price_factor=0.8,
        fields=[
            COMMON_FIELDS['location'],
            COMMON_FIELDS['total_sqft'],
            COMMON_FIELDS['area_type'],
            COMMON_FIELDS['availability'],
            RESIDENTIAL_FIELDS['bathrooms'],
            RESIDENTIAL_FIELDS['balconies'],
            RESIDENTIAL_FIELDS['kitchen_type'],
            COMMON_FIELDS['floor'],
            COMMON_FIELDS['total_floors'],
            COMMON_FIELDS['age'],
            COMMON_FIELDS['furnishing'],
            COMMON_FIELDS['parking'],
            AMENITIES_FIELD
        ],
        prediction_weights={
            'total_sqft': 0.25,
            'location': 0.25,
            'floor': 0.1,
            'age': 0.1,
            'furnishing': 0.1,
            'balconies': 0.05,
            'kitchen_type': 0.05,
            'amenities': 0.1
        }
    )

    # 4. 2 BHK Apartment
    property_types['2bhk'] = PropertyType(
        id='2bhk',
        name='2 BHK Apartment',
        category=PropertyCategory.RESIDENTIAL,
        description='Two bedrooms with hall, kitchen and bathrooms',
        icon='fas fa-bed',
        base_price_factor=1.0,
        fields=[
            COMMON_FIELDS['location'],
            COMMON_FIELDS['total_sqft'],
            COMMON_FIELDS['area_type'],
            COMMON_FIELDS['availability'],
            RESIDENTIAL_FIELDS['bathrooms'],
            RESIDENTIAL_FIELDS['balconies'],
            RESIDENTIAL_FIELDS['kitchen_type'],
            COMMON_FIELDS['floor'],
            COMMON_FIELDS['total_floors'],
            COMMON_FIELDS['age'],
            COMMON_FIELDS['furnishing'],
            COMMON_FIELDS['parking'],
            AMENITIES_FIELD
        ],
        prediction_weights={
            'total_sqft': 0.25,
            'location': 0.2,
            'bathrooms': 0.1,
            'floor': 0.1,
            'age': 0.1,
            'furnishing': 0.1,
            'balconies': 0.05,
            'amenities': 0.1
        }
    )

    return property_types

# ===================== Property Type Manager =====================

class PropertyTypeManager:
    """Manager class for property types"""

    def __init__(self):
        self.property_types = create_property_types()

    def get_property_type(self, type_id: str) -> Optional[PropertyType]:
        """Get a specific property type by ID"""
        return self.property_types.get(type_id)

    def get_all_property_types(self) -> Dict[str, PropertyType]:
        """Get all property types"""
        return self.property_types

    def get_property_types_by_category(self, category: PropertyCategory) -> Dict[str, PropertyType]:
        """Get property types filtered by category"""
        return {
            type_id: prop_type
            for type_id, prop_type in self.property_types.items()
            if prop_type.category == category
        }

    def get_property_type_list(self) -> List[Dict[str, Any]]:
        """Get property types as a list for frontend"""
        return [
            {
                'id': prop_type.id,
                'name': prop_type.name,
                'category': prop_type.category.value,
                'description': prop_type.description,
                'icon': prop_type.icon
            }
            for prop_type in self.property_types.values()
        ]

    def get_fields_for_type(self, type_id: str) -> List[Dict[str, Any]]:
        """Get form fields for a specific property type"""
        prop_type = self.get_property_type(type_id)
        if not prop_type:
            return []

        return [field.to_dict() for field in prop_type.fields]

    def validate_property_data(self, type_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate property data against type requirements"""
        prop_type = self.get_property_type(type_id)
        if not prop_type:
            return {'valid': False, 'errors': ['Invalid property type']}

        errors = []
        required_fields = prop_type.get_required_fields()

        # Check required fields
        for field in required_fields:
            if field.name not in data or data[field.name] is None or data[field.name] == '':
                errors.append(f'{field.label} is required')

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

# Global instance
property_type_manager = PropertyTypeManager()
