from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User


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
            login(request, user)
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
        logout(request)
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
        if request.user.is_authenticated:
            return Response({
                'is_logged_in': True,
                'username': request.user.username,
                'permissions': []
            })
        else:
            return Response({
                'is_logged_in': False,
                'username': request.user.username,
                'permissions': []
            })