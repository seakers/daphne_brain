import json

from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from auth_API.helpers import get_user_information, get_or_create_user_information
from daphne_API.daphne_fields import daphne_fields
from daphne_API.models import UserInformation


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
            # Try to look for user session object. If it exists, then the session will be changed to that. If not,
            # the current session information will be transferred to the user
            userinfo_qs = UserInformation.objects.filter(user__exact=user)

            if len(userinfo_qs) == 0:
                # Try to get or create a session user_info from the session and transfer it to the user
                userinfo = get_or_create_user_information(request.session, user)
                userinfo.user = user
                userinfo.session = None
                userinfo.save()

            # Log the user in
            login(request, user)

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
    Logout a user -> Important!! When the frontend logs out it needs to start fresh
    """
    def post(self, request, format=None):
        # Log the user out
        logout(request)
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
                'status': 'Successful registration'
            })
        else:
            return Response({
                'status': 'Error registering'
            })


class CheckStatus(APIView):
    """
    Check if a user is logged in
    """
    def get(self, request, format=None):

        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

        problem = user_info.eosscontext.problem
        dataset = user_info.eosscontext.dataset_name

        response = {
            'username': request.user.username,
            'permissions': [],
            'problem': problem,
            'dataset': dataset
        }

        if request.user.is_authenticated:
            response['is_logged_in'] = True
            # Transform the database design data into a json for the frontend
            response['data'] = []
            if len(user_info.eosscontext.design_set.all()) > 0:
                for design in user_info.eosscontext.design_set.all():
                    response['data'].append(
                        {'id': design.id, 'inputs': json.loads(design.inputs), 'outputs': json.loads(design.outputs)})
                response['modified_dataset'] = True
            else:
                response['modified_dataset'] = False
        else:
            response['is_logged_in'] = False
        return Response(response)