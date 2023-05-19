import os
import requests
import unittest
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Mapbox API credentials
MAPBOX_ACCESS_TOKEN = 'MAPBOX_ACCESS_TOKEN'

# DataSF Mobile Food Facility Permit dataset API URL
DATASF_API_URL = 'https://data.sfgov.org/resource/rqzj-sfat.json'


@app.route('/')
def index():
    return render_template('index.html',
                           mapbox_access_token=MAPBOX_ACCESS_TOKEN)


@app.route('/food-trucks', methods=['GET'])
def get_food_trucks():
    # Get latitude and longitude from the request parameters
    latitude = request.args.get('lat')
    longitude = request.args.get('lng')

    if not latitude or not longitude:
        return jsonify({'error': 'Latitude and longitude are required.'}), 400

    try:
        # Get food trucks near the specified location using DataSF API
        response = requests.get(DATASF_API_URL, params={
            '$$app_token': os.environ.get('DATASF_APP_TOKEN'),
            '$where': f"within_circle(location, {latitude}, {longitude}, 1000)"
        })

        if response.status_code == 200:
            data = response.json()
            food_trucks = [{'name': truck['applicant'], 'address':
                            truck['address'], 'lat': truck['latitude'],
                            'lng': truck['longitude']} for truck in data]
            return jsonify({'food_trucks': food_trucks})
        else:
            return jsonify({'error': 'Failed to fetch food trucks data.'}), 500

    except requests.exceptions.RequestException:
        return jsonify({'error': 'Failed to connect to the DataSF API.'}), 500


class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Food Truck Map', response.data)

    def test_food_trucks_route_missing_params(self):
        response = self.app.get('/food-trucks')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Latitude and longitude are required.')

    def test_food_trucks_route(self):
        response = self.app.get('/food-trucks?lat=37.7749&lng=-122.4194')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertIn('food_trucks', data)
        self.assertIsInstance(data['food_trucks'], list)


if __name__ == '__main__':
    unittest.main()
