from flask_restx import Namespace, Resource, fields  # pyright: ignore[reportMissingImports]
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt  # pyright: ignore[reportMissingImports]
from app.services import facade

api = Namespace('reviews', description='Review operations')

# user_id is now derived from the JWT token on POST; it is not required in the body.
review_model = api.model('Review', {
    'text': fields.String(required=True, description='Text of the review'),
    'rating': fields.Integer(required=True, description='Rating of the place (1-5)'),
    'place_id': fields.String(required=True, description='ID of the place')
})

# Separate model for PUT: only text/rating may be updated.
review_update_model = api.model('ReviewUpdate', {
    'text': fields.String(description='Text of the review'),
    'rating': fields.Integer(description='Rating of the place (1-5)')
})


@api.route('/')
class ReviewList(Resource):
    @jwt_required()
    @api.expect(review_model, validate=True)
    @api.response(201, 'Review successfully created')
    @api.response(400, 'Invalid input data')
    @api.response(401, 'Authentication required')
    @api.response(404, 'Place not found')
    def post(self):
        """Create a new review (authentication required)"""
        current_user = get_jwt_identity()
        review_data = api.payload
        
        # Reviewer is always the authenticated user.
        review_data['user_id'] = current_user

        # Validate place before delegating to the facade.
        place = facade.get_place(review_data.get('place_id'))
        if not place:
            return {'error': 'Place not found'}, 404

        # Defensively get the owner ID to prevent AttributeError during tests
        place_owner_id = getattr(place, 'owner_id', place.owner.id if getattr(place, 'owner', None) else None)

        if place_owner_id == current_user:
            return {'error': 'You cannot review your own place'}, 400

        # Prevent duplicate reviews using the facade to avoid lazy-loading issues
        existing_reviews = facade.get_reviews_by_place(review_data.get('place_id'))
        if existing_reviews:
            for r in existing_reviews:
                reviewer_id = getattr(r, 'user_id', r.user.id if getattr(r, 'user', None) else None)
                if reviewer_id == current_user:
                    return {'error': 'You have already reviewed this place'}, 400

        try:
            new_review = facade.create_review(review_data)
        except ValueError as e:
            return {'error': str(e)}, 400
            
        return {
            'id': new_review.id,
            'text': new_review.text,
            'rating': new_review.rating,
            'user_id': getattr(new_review, 'user_id', new_review.user.id if getattr(new_review, 'user', None) else None),
            'place_id': getattr(new_review, 'place_id', new_review.place.id if getattr(new_review, 'place', None) else None)
        }, 201

    @api.response(200, 'List of reviews retrieved successfully')
    def get(self):
        """Retrieve a list of all reviews"""
        reviews = facade.get_all_reviews()
        return [{'id': r.id, 'text': r.text, 'rating': r.rating} for r in reviews], 200


@api.route('/<review_id>')
class ReviewResource(Resource):
    @api.response(200, 'Review details retrieved successfully')
    @api.response(404, 'Review not found')
    def get(self, review_id):
        """Get review details by ID"""
        review = facade.get_review(review_id)
        if not review:
            return {'error': 'Review not found'}, 404
            
        return {
            'id': review.id,
            'text': review.text,
            'rating': review.rating,
            'user_id': getattr(review, 'user_id', review.user.id if getattr(review, 'user', None) else None),
            'place_id': getattr(review, 'place_id', review.place.id if getattr(review, 'place', None) else None)
        }, 200

    @jwt_required()
    @api.expect(review_update_model, validate=True)
    @api.response(200, 'Review updated successfully')
    @api.response(400, 'Invalid input data')
    @api.response(401, 'Authentication required')
    @api.response(403, 'Unauthorized action')
    @api.response(404, 'Review not found')
    def put(self, review_id):
        """Update a review (original reviewer only; admins bypass ownership check)"""
        claims = get_jwt()
        is_admin = claims.get('is_admin', False)
        current_user_id = get_jwt_identity()

        review = facade.get_review(review_id)
        if not review:
            return {'error': 'Review not found'}, 404

        # Defensively get the user ID
        reviewer_id = getattr(review, 'user_id', review.user.id if getattr(review, 'user', None) else None)

        if not is_admin and reviewer_id != current_user_id:
            return {'error': 'Unauthorized action'}, 403

        review_data = api.payload
        try:
            facade.update_review(review_id, review_data)
        except ValueError as e:
            return {'error': str(e)}, 400
        return {'message': 'Review updated successfully'}, 200

    @jwt_required()
    @api.response(200, 'Review deleted successfully')
    @api.response(401, 'Authentication required')
    @api.response(403, 'Unauthorized action')
    @api.response(404, 'Review not found')
    def delete(self, review_id):
        """Delete a review (original reviewer only; admins bypass ownership check)"""
        claims = get_jwt()
        is_admin = claims.get('is_admin', False)
        current_user_id = get_jwt_identity()

        review = facade.get_review(review_id)
        if not review:
            return {'error': 'Review not found'}, 404

        # Defensively get the user ID
        reviewer_id = getattr(review, 'user_id', review.user.id if getattr(review, 'user', None) else None)

        if not is_admin and reviewer_id != current_user_id:
            return {'error': 'Unauthorized action'}, 403

        facade.delete_review(review_id)
        return {'message': 'Review deleted successfully'}, 200