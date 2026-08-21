import re
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services import facade
from flask import request

api = Namespace('users', description='User operations')

# Define the user model for input validation (Creation)
user_model = api.model('User', {
    'first_name': fields.String(required=True, description='First name of the user'),
    'last_name': fields.String(required=True, description='Last name of the user'),
    'email': fields.String(required=True, description='Email of the user'),
    'password': fields.String(required=True, description='Password of the user')
})

# Define the user model for input validation (Update)
user_put_model = api.model('UserPut', {
    'first_name': fields.String(description='First name of the user'),
    'last_name': fields.String(description='Last name of the user'),
    'email': fields.String(description='Email of the user (admin only)'),
    'password': fields.String(description='Password of the user (admin only)'),
})

# Define the user model for output response (Required for Swagger documentation)
user_output_model = api.model('UserOutput', {
    'id': fields.String(description='The unique identifier of a user'),
    'first_name': fields.String(description='First name of the user'),
    'last_name': fields.String(description='Last name of the user'),
    'email': fields.String(description='Email of the user'),
})

# Regular expression for validating email formats
EMAIL_REGEX = r"^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$"

def _user_response(user):
    """Helper function to format user response without exposing the password."""
    return {
        'id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
    }


@api.route('/')
class UserList(Resource):
    @jwt_required()
    @api.expect(user_model, validate=True)
    @api.response(201, 'User successfully created', user_output_model)
    @api.response(400, 'Email already registered or Invalid input data')
    @api.response(401, 'Authentication required')
    @api.response(403, 'Admin privileges required')
    def post(self):
        """Register a new user (Requires Admin Privileges)"""
        
        # Verify if the current user has admin rights
        claims = get_jwt()
        if not claims.get('is_admin', False):
            return {'error': 'Admin privileges required'}, 403

        user_data = request.json

        # Ensure all required fields are provided
        if not user_data.get('first_name') or not user_data.get('last_name') or not user_data.get('email'):
            return {'error': 'Missing required fields'}, 400

        # Validate the email against the regular expression
        if not re.match(EMAIL_REGEX, user_data.get('email')):
            return {'error': 'Invalid email format'}, 400

        # Prevent duplicate emails in the database
        existing_user = facade.get_user_by_email(user_data['email'])
        if existing_user:
            return {'error': 'Email already registered'}, 400

        # Attempt to create the user and handle any domain errors
        try:
            new_user = facade.create_user(user_data)
        except ValueError as e:
            return {'error': str(e)}, 400
            
        # Return the created user data with a 201 Created status
        return _user_response(new_user), 201

    @api.response(200, 'List of users retrieved successfully', [user_output_model])
    def get(self):
        """Retrieve the list of all registered users"""
        users = facade.get_all_users()
        return [_user_response(u) for u in users], 200


@api.route('/<user_id>')
class UserResource(Resource):
    @api.response(200, 'User details retrieved successfully', user_output_model)
    @api.response(404, 'User not found')
    def get(self, user_id):
        """Get a specific user's details by their ID"""
        user = facade.get_user(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        return _user_response(user), 200

    @jwt_required()
    @api.expect(user_put_model, validate=True)
    @api.response(200, 'User updated successfully', user_output_model)
    @api.response(400, 'Invalid input data')
    @api.response(401, 'Authentication required')
    @api.response(403, 'Unauthorized action')
    @api.response(404, 'User not found')
    def put(self, user_id):
        """Update a user's information"""
        
        # Extract JWT claims to determine user role and identity
        claims = get_jwt()
        is_admin = claims.get('is_admin', False)
        current_user_id = get_jwt_identity()

        # Regular users can only update their own profiles
        if not is_admin and current_user_id != user_id:
            return {'error': 'Unauthorized action'}, 403

        # Verify that the target user exists
        user = facade.get_user(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        user_data = request.json

        # Restrict email modifications based on user privileges and validity
        if 'email' in user_data:
            if not is_admin:
                return {'error': 'You cannot modify email'}, 400
            if not re.match(EMAIL_REGEX, user_data.get('email')):
                return {'error': 'Invalid email format'}, 400
            
            # Ensure the new email doesn't conflict with an existing user
            existing = facade.get_user_by_email(user_data['email'])
            if existing and existing.id != user_id:
                return {'error': 'Email already in use'}, 400

        # Apply updates
        try:
            updated_user = facade.update_user(user_id, user_data)
        except ValueError as e:
            return {'error': str(e)}, 400
            
        return _user_response(updated_user), 200