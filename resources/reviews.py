import json
from flask import jsonify, Blueprint, abort, g, make_response

from flask_restful import (Resource, Api, reqparse,
                           inputs, fields, marshal, marshal_with, url_for)

from auth import auth
import models


review_fields = {
    'id': fields.Integer,
    'for_course': fields.String,
    'rating': fields.Integer,
    'comment': fields.String(default=''),
    'created_at': fields.DateTime
}


def add_course(review):
    review.for_course = url_for(
        'resources.courses.course', id=review.course.id)
    return review


def review_or_404(review_id):
    try:
        review = models.Review.get(models.Review.id == review_id)
    except models.Review.DoesNotExist:
        abort(404)
    else:
        return review


class ReviewList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'course', required=True, help='No course id provided', location=['form', 'json'], type=inputs.positive
        )
        self.reqparse.add_argument(
            'rating', required=True, help='No course rating provided', location=['form', 'json'], type=inputs.int_range(1, 5)
        )
        self.reqparse.add_argument(
            'comment', required=False, nullables=True, location=['form', 'json'], default=''
        )
        super().__init__()

    def get(self):
        reviews = [marshal(add_course(review), review_fields)
                   for review in models.Review.select()]
        return {'reviews': reviews}

    @auth.login_required
    @marshal_with(review_fields)
    def post(self):
        args = self.reqparse.parse_args()
        review = models.Review.create(
            created_by=g.user,
            **args
        )
        return (add_course(review), 201, {'Location': url_for('resources.reviews.review', id=review.id)})


class Review(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'course', required=True, help='No course id provided', location=['form', 'json'], type=inputs.positive
        )
        self.reqparse.add_argument(
            'rating', required=True, help='No course rating provided', location=['form', 'json'], type=inputs.int_range(1, 5)
        )
        self.reqparse.add_argument(
            'comment', required=False, nullables=True, location=['form', 'json'], default=''
        )
        super().__init__()

    @marshal_with(review_fields)
    def get(self, id):
        return add_course(review_or_404(id))

    @marshal_with(review_fields)
    @auth.login_required
    def put(self, id):
        args = self.reqparse.parse_args()
        try:
            review = models.Review.select().where(models.Review.created_by ==
                                                  g.user, models.Review.id == id).get()
        except models.Review.DoesNotExist:
            return make_response(json.dumps({'error': 'That reviews does not exist or is not editable'}), 403)
        query = models.Review.update(**args)
        query.execute()
        # fetch the updated model
        review = add_course(review_or_404(id))
        return (review, 200, {'Location': url_for('resources/reviews.review', id=id)})

    @auth.login_required
    def delete(self, id):
        try:
            review = models.Review.select().where(models.Review.created_by ==
                                                  g.user, models.Review.id == id).get()
        except models.Review.DoesNotExist:
            return make_response(json.dumps({'error': 'That reviews does not exist or is not deletable'}), 403)
        query = review.delete()
        query.execute()
        return ('', 204, {'Location': url_for('resources/reviews.reviews')})


reviews_api = Blueprint('resources/reviews', __name__)
api = Api(reviews_api)
api.add_resource(
    ReviewList,
    '/reviews',
    endpoint='reviews'
)
api.add_resource(
    Review,
    '/reviews/<int:id>',
    endpoint='review'
)
