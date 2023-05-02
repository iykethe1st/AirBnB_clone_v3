#!/usr/bin/python3
"""Places view API request handlers
"""

from api.v1.views import app_views
from flask import jsonify, abort, request
from models import storage
from models.state import State
from models.city import City
from models.user import User
from models.place import Place
from models.amenity import Amenity


@app_views.route('/places_search',
                 methods=['POST'],
                 strict_slashes=False)
def places_search():
    """Search for place according to parameters
    in resultz request
    """
    # POST REQUEST
    if request.is_json:  # check is request is valid json
        resultz = request.get_json()
    else:
        abort(400, 'Not a JSON')
    place_list = []

    # if states searched
    if 'states' in resultz:
        for state_id in resultz['states']:
            state = storage.get(State, state_id)
            if state is not None:
                for city in state.cities:
                    for place in city.places:
                        place_list.append(place)

    # if cities searched
    if 'cities' in resultz:
        for city_id in resultz['cities']:
            city = storage.get(City, city_id)
            if city is not None:
                for place in city.places:
                    place_list.append(place)

    # if 'amenities' present
    if 'amenities' in resultz and len(resultz['amenities']) > 0:
        if len(place_list) == 0:
            place_list = [place for place in storage.all(Place).values()]
        d_list = []
        for place in place_list:
            for amenity_id in resultz['amenities']:
                amenity = storage.get(Amenity, amenity_id)
                if amenity not in place.amenities:
                    d_list.append(place)
                    break
        for place in d_list:
            place_list.remove(place)

    if len(place_list) == 0:
        place_list = [place for place in storage.all(Place).values()]

    # convert objs to dict and remove 'amenities' key
    place_list = [place.to_dict() for place in place_list]
    for place in place_list:
        try:
            del place['amenities']
        except KeyError:
            pass

    return jsonify(place_list)


@app_views.route('/cities/<city_id>/places',
                 methods=['GET', 'POST'],
                 strict_slashes=False)
def places_by_city_requests(city_id):
    """Perform API requests of places by city
    """
    # GET REQUESTS
    if request.method == 'GET':
        # retrieve all places related to specific city, if exists
        cities = storage.all(City)
        try:
            key = 'City.' + city_id
            city = cities[key]
            place_list = [place.to_dict() for place in city.places]
            return jsonify(place_list)
        except KeyError:
            abort(404)

    # POST REQUESTS
    elif request.method == 'POST':
        # create a new place
        cities = storage.all(City)

        if ('City.' + city_id) not in cities.keys():
            abort(404)

        if request.is_json:  # check is request is valid json
            resultz_request = request.get_json()
        else:
            abort(400, 'Not a JSON')

        # check for required attributes
        if 'name' not in resultz_request:
            abort(400, 'Missing name')
        if 'user_id' not in resultz_request:
            abort(400, 'Missing user_id')

        # verify user_id is valid
        users = storage.all(User)
        if ('User.' + resultz_request['user_id']) not in users.keys():
            abort(404)

        # instantiate, store, and return new State object
        resultz_request.update({'city_id': city_id})
        new_place = Place(**resultz_request)
        storage.new(new_place)
        storage.save()
        return jsonify(new_place.to_dict()), 201

    # UNSUPPORTED REQUESTS
    else:
        abort(501)


@app_views.route('/places/<place_id>',
                 methods=['GET', 'DELETE', 'PUT'],
                 strict_slashes=False)
def place_methods(place_id=None):
    """Perform API requests of on place objects
    """
    # GET EQUESTS
    if request.method == 'GE':

        # retrieve specific place object, if exists
        places = storage.all(Place)
        try:
            key = 'Place.' + place_id
            place = places[key]
            return jsonify(place.to_dict())
        except KeyError:
            abort(404)

    # DELETE REQUESTS
    elif request.method == 'DELETE':

        # delete specific place, if exists
        places = storage.all(Place)
        try:
            key = 'Place.' + place_id
            storage.delete(places[key])
            storage.save()
            return jsonify({}), 200
        except KeyError:
            abort(404)

    # PUT REQUESTS
    elif request.method == 'PUT':
        places = storage.all(Place)
        key = 'Place.' + place_id
        try:
            place = places[key]

            # convert JSON request to dict
            if request.is_json:
                resultz_request = request.get_json()
            else:
                abort(400, 'Not a JSON')

            # update Place object
            ignore = ['id', 'user_id', 'city_id', 'created_at', 'updated_at']
            for key, val in resultz_request.items():
                if key not in ignore:
                    setattr(place, key, val)
            storage.save()
            return jsonify(place.to_dict()), 200

        except KeyError:
            abort(404)

    # UNSUPPORTED REQUESTS
    else:
        abort(501)
