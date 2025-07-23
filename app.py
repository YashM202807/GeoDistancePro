from flask import Flask, render_template, request, jsonify
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import logging
from functools import lru_cache

app = Flask(__name__)
geolocator = Nominatim(user_agent="distance_calculator_v2")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache geocoding results to improve performance
@lru_cache(maxsize=100)
def cached_geocode(query):
    return geolocator.geocode(query)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        if not data or 'place1' not in data or 'place2' not in data:
            return jsonify({'error': 'Please provide both locations'}), 400
            
        place1 = data['place1'].strip()
        place2 = data['place2'].strip()
        
        if not place1 or not place2:
            return jsonify({'error': 'Both locations are required'}), 400

        logger.info(f"Processing locations: {place1} and {place2}")
        location1 = cached_geocode(place1)
        location2 = cached_geocode(place2)

        if not location1:
            return jsonify({'error': f'Location not found: {place1}'}), 404
        if not location2:
            return jsonify({'error': f'Location not found: {place2}'}), 404

        coord1 = (location1.latitude, location1.longitude)
        coord2 = (location2.latitude, location2.longitude)

        distance_km = geodesic(coord1, coord2).kilometers
        distance_miles = distance_km * 0.621371

        logger.info(f"Distance calculated: {distance_km:.2f} km")

        return jsonify({
            'place1': location1.address,
            'place2': location2.address,
            'distance_km': round(distance_km, 2),
            'distance_miles': round(distance_miles, 2),
            'coord1': coord1,
            'coord2': coord2,
            'bbox1': get_location_bbox(location1),
            'bbox2': get_location_bbox(location2)
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'Service temporarily unavailable. Please try again later.'}), 500

def get_location_bbox(location):
    """Get bounding box for location if available"""
    if hasattr(location, 'raw') and 'boundingbox' in location.raw:
        return [float(x) for x in location.raw['boundingbox']]
    return None

if __name__ == '__main__':
    app.run(debug=True)