# ===================== Chat Utilities =====================
import random
import re
from typing import Dict, List, Any
from utils.data_utils import get_locations, get_market_stats

def get_chat_response(message: str) -> str:
    """
    Generate AI chat response for real estate queries
    
    Args:
        message: User's message
        
    Returns:
        AI response string
    """
    message = message.lower().strip()
    
    # Price prediction queries
    if any(word in message for word in ['price', 'cost', 'predict', 'estimate', 'value']):
        return handle_price_query(message)
    
    # Location queries
    elif any(word in message for word in ['location', 'area', 'where', 'place', 'locality']):
        return handle_location_query(message)
    
    # Market trends
    elif any(word in message for word in ['trend', 'market', 'growth', 'appreciation', 'investment']):
        return handle_market_query(message)
    
    # Property features
    elif any(word in message for word in ['bhk', 'bedroom', 'bathroom', 'sqft', 'size', 'area']):
        return handle_features_query(message)
    
    # Loan and finance
    elif any(word in message for word in ['loan', 'emi', 'finance', 'mortgage', 'bank', 'interest']):
        return handle_finance_query(message)
    
    # Legal queries
    elif any(word in message for word in ['legal', 'document', 'registration', 'stamp duty', 'tax']):
        return handle_legal_query(message)
    
    # Buying process
    elif any(word in message for word in ['buy', 'purchase', 'process', 'steps', 'how to']):
        return handle_buying_query(message)
    
    # Greetings
    elif any(word in message for word in ['hello', 'hi', 'hey', 'good morning', 'good evening']):
        return handle_greeting()
    
    # Default response
    else:
        return handle_default_query(message)

def handle_price_query(message: str) -> str:
    """Handle price-related queries"""
    responses = [
        "🏠 To get an accurate price prediction, please use our Price Prediction tool. I can help you estimate property values based on location, size, and amenities.",
        "💰 Property prices vary significantly based on location, size, and amenities. Our ML model can predict prices with high accuracy. Would you like me to guide you through the prediction process?",
        "📊 For precise price estimates, I recommend using our prediction tool. It considers factors like location, BHK, total area, and current market trends.",
        "🎯 I can help you understand property pricing! Our AI model analyzes multiple factors including location premium, property size, and market conditions."
    ]
    
    # Add market context
    try:
        stats = get_market_stats()
        avg_price = stats.get('avg_price', 112.56)
        response = random.choice(responses)
        response += f"\n\n📈 Current market average: ₹{avg_price:.2f} lakhs"
        return response
    except:
        return random.choice(responses)

def handle_location_query(message: str) -> str:
    """Handle location-related queries"""
    locations = get_locations()
    popular_locations = locations[:10] if locations else [
        "Whitefield", "Koramangala", "Indiranagar", "Jayanagar", "BTM Layout"
    ]
    
    responses = [
        f"🗺️ We cover {len(locations)} locations in Bangalore! Popular areas include: {', '.join(popular_locations[:5])}.",
        f"📍 Some trending locations are: {', '.join(popular_locations[:6])}. Each area has unique advantages in terms of connectivity and amenities.",
        f"🏙️ Bangalore offers diverse localities. Premium areas include {', '.join(popular_locations[:4])}, while emerging areas offer great investment potential.",
        "🚇 Location is crucial for property value. Consider factors like metro connectivity, IT hubs proximity, schools, and hospitals when choosing."
    ]
    
    return random.choice(responses)

def handle_market_query(message: str) -> str:
    """Handle market trend queries"""
    responses = [
        "📈 Bangalore real estate has shown consistent growth over the years. IT sector expansion continues to drive demand in areas like Whitefield, Electronic City, and Sarjapur Road.",
        "💹 Market trends show steady appreciation in established areas. New infrastructure projects like metro extensions are creating opportunities in emerging localities.",
        "🏗️ The market is experiencing healthy growth with increased demand for 2-3 BHK apartments. Premium locations show 8-12% annual appreciation.",
        "📊 Current market indicators suggest stable growth. Areas with good connectivity and infrastructure development show the best investment potential."
    ]
    
    return random.choice(responses)

def handle_features_query(message: str) -> str:
    """Handle property features queries"""
    responses = [
        "🏠 Property features significantly impact pricing. Larger apartments (3-4 BHK) in premium locations command higher prices. Balconies and additional bathrooms add value.",
        "📐 Total square footage is a key factor. Generally, 1000-1500 sqft is ideal for 2 BHK, while 1500-2500 sqft suits 3 BHK apartments.",
        "🛁 Bathroom count and balcony availability affect both comfort and resale value. Modern amenities like parking and security also influence pricing.",
        "🏗️ Built-up area vs carpet area makes a difference. Super built-up area includes common areas, while carpet area is the actual usable space."
    ]
    
    return random.choice(responses)

def handle_finance_query(message: str) -> str:
    """Handle finance and loan queries"""
    responses = [
        "🏦 Home loans typically cover 80-90% of property value. Current interest rates range from 8.5-11% depending on your profile and bank.",
        "💳 EMI calculation depends on loan amount, tenure, and interest rate. Use our Loan Calculator for precise EMI estimates.",
        "📋 Required documents include: Income proof, ID proof, property documents, and bank statements. Pre-approval can speed up the process.",
        "💰 Consider factors like processing fees, insurance, and registration costs. Total cost is typically 8-10% above the property price."
    ]
    
    return random.choice(responses)

def handle_legal_query(message: str) -> str:
    """Handle legal queries"""
    responses = [
        "⚖️ Essential documents: Sale deed, title documents, NOC from society, property tax receipts, and approved building plans.",
        "📜 Registration process involves stamp duty (varies by state), registration fees, and legal verification. Budget 6-8% of property value for these costs.",
        "🔍 Due diligence is crucial: Verify clear title, check for any legal disputes, ensure all approvals are in place, and confirm property tax payments.",
        "📋 Legal checklist: Title verification, encumbrance certificate, property tax clearance, building approval, and society NOC."
    ]
    
    return random.choice(responses)

def handle_buying_query(message: str) -> str:
    """Handle buying process queries"""
    responses = [
        "🛒 Buying process: 1) Budget planning 2) Location research 3) Property search 4) Site visits 5) Price negotiation 6) Legal verification 7) Loan processing 8) Registration",
        "📝 Key steps: Define budget → Shortlist properties → Physical inspection → Legal due diligence → Loan approval → Final negotiation → Registration",
        "🎯 Start with our Property Finder tool to identify suitable options based on your budget and preferences. Then use our prediction tool for price validation.",
        "💡 Pro tip: Always visit properties multiple times, check during different hours, verify amenities, and compare with similar properties in the area."
    ]
    
    return random.choice(responses)

def handle_greeting() -> str:
    """Handle greeting messages"""
    greetings = [
        "👋 Hello! I'm your Real Estate AI Assistant. I can help you with property prices, market trends, locations, and buying guidance. How can I assist you today?",
        "🏠 Hi there! Welcome to Real Estate AI. I'm here to help with property predictions, market insights, and buying advice. What would you like to know?",
        "✨ Greetings! I'm your property expert AI. Ask me about prices, locations, market trends, or any real estate questions you have!",
        "🎉 Hello! Ready to explore Bangalore real estate? I can help with price predictions, area analysis, and buying guidance. What interests you?"
    ]
    
    return random.choice(greetings)

def handle_default_query(message: str) -> str:
    """Handle unrecognized queries"""
    responses = [
        "🤔 I'd love to help! I specialize in real estate queries like property prices, market trends, locations, and buying guidance. Could you be more specific?",
        "💭 I'm here to assist with property-related questions. Try asking about prices, locations, market trends, or the buying process!",
        "🏠 I'm your real estate expert! I can help with price predictions, area analysis, market insights, and buying advice. What would you like to explore?",
        "✨ Let me help you with real estate matters! Ask me about property values, locations, market trends, or any buying-related questions."
    ]
    
    return random.choice(responses)

def extract_location_from_message(message: str) -> str:
    """Extract location name from user message"""
    locations = get_locations()
    message_lower = message.lower()
    
    for location in locations:
        if location.lower() in message_lower:
            return location
    
    return None

def extract_budget_from_message(message: str) -> float:
    """Extract budget amount from user message"""
    # Look for patterns like "50 lakh", "1 crore", "₹50", etc.
    patterns = [
        r'₹\s*(\d+(?:\.\d+)?)\s*(?:lakh|lakhs?)',
        r'(\d+(?:\.\d+)?)\s*(?:lakh|lakhs?)',
        r'₹\s*(\d+(?:\.\d+)?)\s*(?:crore|crores?)',
        r'(\d+(?:\.\d+)?)\s*(?:crore|crores?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message.lower())
        if match:
            amount = float(match.group(1))
            if 'crore' in pattern:
                amount *= 100  # Convert crore to lakh
            return amount
    
    return None
