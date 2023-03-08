import json
from flask import jsonify, Blueprint, make_response

from flask_restful import (Resource, Api, reqparse,
                           fields, marshal, marshal_with, url_for)

import models


user_fields = {
    'username': fields.String,
}


class UserList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'username', required=True, help='No username provided', location=['form', 'json']
        )
        self.reqparse.add_argument(
            'email', required=True, help='No email provided', location=['form', 'json']
        )
        self.reqparse.add_argument(
            'password', required=True, help='No password provided', location=['form', 'json'])
        self.reqparse.add_argument(
            'verify_password', required=True, help='No password verification provided', location=['form', 'json'])
        super().__init__()

    def get(self):
        # provide marshal with record and defined fields
        users = [marshal(user, user_fields)
                 for user in models.User.select()]
        return jsonify({'users': users})

    @marshal_with(user_fields)
    def post(self):
        args = self.reqparse.parse_args()
        if args.get('password') == args.get('verify_password'):
            # feed everything in the args dictionary into User.create
            user = models.User.create(**args)
            return (user, 201)
        return make_response(json.dumps({'error': 'Password and password verification do not match'}), 400)


users_api = Blueprint('resources/users', __name__)
api = Api(users_api)
api.add_resource(UserList, '/users', endpoint='users')
