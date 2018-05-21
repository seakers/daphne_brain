from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from daphne_API.daphne_fields import daphne_fields


class Login(APIView):
    """
    Login a user
    """

    def post(self, request, format=None):
        # Try to authorize the user
        username = request.data['username']
        password = request.data['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Save interesting parts of session
            saved_session = {}
            for field in daphne_fields:
                if field in request.session:
                    saved_session[field] = request.session[field]
            # Log the user in
            login(request, user)
            # Restore the session
            for field in saved_session:
                request.session[field] = saved_session[field]
            # Return the login response
            return Response({
                'status': 'logged_in',
                'username': username,
                'permissions': []
            })
        else:
            # TODO: Get different messages based on auth error
            return Response({
                'status': 'auth_error',
                'login_error': 'This combination of username and password is not valid!'
            })


class Logout(APIView):
    """
    Logout a user
    """
    def post(self, request, format=None):
        # Save interesting parts of session
        saved_session = {}
        for field in daphne_fields:
            if field in request.session:
                saved_session[field] = request.session[field]
        # Log the user out
        logout(request)
        # Restore the session
        for field in saved_session:
            request.session[field] = saved_session[field]
        # Return the logout response
        return Response({
            'message': 'User logged out.'
        })


class Register(APIView):
    """
    Register a user
    """
    def post(self, request, format=None):
        if request.data["password1"] == request.data["password2"]:
            user = User.objects.create_user(request.data["username"], request.data["email"], request.data["password1"])
            user.save()
            return Response({
                'status': 'successful'
            })
        else:
            return Response({
                'status': 'error'
            })


class CheckStatus(APIView):
    """
    Check if a user is logged in
    """
    def get(self, request, format=None):
        if 'problem' in request.session:
            problem = request.session['problem']
        else:
            problem = ''
        if 'dataset' in request.session:
            dataset = request.session['dataset']
        else:
            dataset = ''

        response = {
            'username': request.user.username,
            'permissions': [],
            'problem': problem,
            'dataset': dataset
        }

        if request.user.is_authenticated:
            response['is_logged_in'] = True
            if 'data' in request.session:
                response['data'] = request.session['data']
                response['modified_dataset'] = True
            else:
                response['data'] = []
                response['modified_dataset'] = False
        else:
            response['is_logged_in'] = False
        return Response(response)