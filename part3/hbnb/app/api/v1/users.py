from flask_restx import Namespace, Resource, fields  # pyright: ignore[reportMissingImports]
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt  # pyright: ignore[reportMissingImports]
from app.services import facade

api = Namespace('users', description='User operations')

# Model for user creation (POST) – all fields required.
user_model = api.model('User', {
    'first_name': fields.String(required=True, description='First name of the user'),
    'last_name': fields.String(required=True, description='Last name of the user'),
    'email': fields.String(required=True, description='Email of the user'),
    'password': fields.String(required=True, description='Password of the user'),
})

# Model for user update (PUT).
# Admins may supply email and password; non-admins are blocked in endpoint logic.
user_put_model = api.model('UserPut', {
    'first_name': fields.String(description='First name of the user'),
    'last_name': fields.String(description='Last name of the user'),
    'email': fields.String(description='Email of the user (admin only)'),
    'password': fields.String(description='Password of the user (admin only)'),
})


def _user_response(user):
    """Return a user dict without the password field."""
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
    @api.response(201, 'User successfully created')
    @api.response(400, 'Email already registered')
    @api.response(400, 'Invalid input data')
    @api.response(401, 'Authentication required')
    @api.response(403, 'Admin privileges required')
    def post(self):
        """Register a new user (admin only)"""
        claims = get_jwt()
        if not claims.get('is_admin', False):
            return {'error': 'Admin privileges required'}, 403

        user_data = api.payload

        existing_user = facade.get_user_by_email(user_data['email'])
        if existing_user:
            return {'error': 'Email already registered'}, 400

        try:
            new_user = facade.create_user(user_data)
        except ValueError as e:
            return {'error': str(e)}, 400
        return {'id': new_user.id, 'message': 'User successfully created'}, 201

    @api.response(200, 'List of users retrieved successfully')
    def get(self):
        """Retrieve the list of users"""
        users = facade.get_all_users()
        return [_user_response(u) for u in users], 200


@api.route('/<user_id>')
class UserResource(Resource):
    @api.response(200, 'User details retrieved successfully')
    @api.response(404, 'User not found')
    def get(self, user_id):
        """Get user details by ID"""
        user = facade.get_user(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        return _user_response(user), 200

    @jwt_required()
    @api.expect(user_put_model, validate=True)
    @api.response(200, 'User updated successfully')
    @api.response(400, 'Invalid input data')
    @api.response(401, 'Authentication required')
    @api.response(403, 'Unauthorized action')
    @api.response(404, 'User not found')
    def put(self, user_id):
        """Update a user's information (own record for regular users; any record for admins)"""
        claims = get_jwt()
        is_admin = claims.get('is_admin', False)
        current_user_id = get_jwt_identity()

        # Non-admins may only modify their own record.
        if not is_admin and current_user_id != user_id:
            return {'error': 'Unauthorized action'}, 403

        user = facade.get_user(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        user_data = api.payload

        if not is_admin:
            # Non-admins cannot change email or password through this endpoint.
            if 'email' in user_data or 'password' in user_data:
                return {'error': 'You cannot modify email or password'}, 400
        else:
            # Admins may change email, but must keep it unique.
            if 'email' in user_data:
                existing = facade.get_user_by_email(user_data['email'])
                if existing and existing.id != user_id:
                    return {'error': 'Email already in use'}, 400

        try:
            updated_user = facade.update_user(user_id, user_data)
        except ValueError as e:
            return {'error': str(e)}, 400
        return _user_response(updated_user), 200
