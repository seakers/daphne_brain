import json
import os

from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from auth_API.helpers import get_or_create_user_information
from daphne_context.models import UserInformation, MycroftUser
from EOSS.graphql.api import GraphqlClient

import requests
import json

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

            # Get user private key
            user_pk = get_user_pk(username)

            # Return the login response
            return Response({
                'status': 'logged_in',
                'username': username,
                'pk': user_pk,
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
        print("--> REGISTERING USER")
        username = request.data["username"]
        email = request.data["email"]
        password1 = request.data["password1"]
        password2 = request.data["password2"]

        # Validate all fields against our rules
        if not password1 or not password2 or password1 != password2:
            return Response({
                'status': 'registration_error',
                'registration_error': 'The passwords do not match.'
            })

        try:
            validate_email(email)
        except ValidationError:
            return Response({
                'status': 'registration_error',
                'registration_error': 'Email has an incorrect format.'
            })

        if username in ["default"]:
            return Response({
                'status': 'registration_error',
                'registration_error': 'This username is already in use.'
            })

        if User.objects.filter(username=username).exists():
            return Response({
                'status': 'registration_error',
                'registration_error': 'This username is already in use.'
            })

        print("---> PASSED TESTS")
        # Do the registration procedure which includes creating folders for all problems
        try:
            # Create user
            user_id = self.create_user(username, email, password1)


            # Create folders in the server structure
            # self.create_user_dirs(username)

            # We must give the user access to the default group: seakers (default) - all users will be admins
            self.insert_into_groups(user_id)
            print("--> USER INSERTED INTO GROUP")


        except ValueError:
            return Response({
                'status': 'registration_error',
                'registration_error': 'Please write a username.'
            })

        print("--> FINISHED REGISTRATION")
        return Response({
            'status': 'registered'
        })


    def create_user_dirs(self, username):
        folder_name = os.path.join(os.getcwd(), "EOSS", "data", "datasets", username)
        os.mkdir(folder_name)
        problem_list = ["ClimateCentric", "Decadal2017Aerosols", "SMAP", "SMAP_JPL1", "SMAP_JPL2"]
        for problem in problem_list:
            subfolder_name = os.path.join(folder_name, problem)
            os.mkdir(subfolder_name)

    def create_user(self, username, email, password):
        user = User.objects.create_user(username, email, password)
        user.save()

        # mycroft_user = MycroftUser(user=user)
        # mycroft_user.save()
        print("--> USER CREATED ", user.id)
        return user.id

    def insert_into_groups(self, user_id):
        client = GraphqlClient()
        result = client.insert_user_into_group(user_id)
        print("--> RESULT", result)



class ResetPassword(APIView):
    """
    Send a reset password email
    """
    def post(self, request, format=None):
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            password_reset_form.save(request=request)

            return Response({
                'status': 'email sent'
            })
        else:
            return Response({
                'status': 'bad email'
            })


class CheckStatus(APIView):
    """
    Check if a user is logged in
    """
    def get(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

        problem = user_info.eosscontext.problem
        problem_id = user_info.eosscontext.problem_id
        group_id = user_info.eosscontext.group_id
        dataset_filename = user_info.eosscontext.dataset_name
        dataset_user = user_info.eosscontext.dataset_user

        # problem: is now the problem_id (from the database)
        response = {
            'username': request.user.username,
            'permissions': [],
            'problem_id': problem_id,
            'group_id': group_id,
            'problem': problem,
            'dataset_filename': dataset_filename,
            'dataset_user': dataset_user
        }

        if request.user.is_authenticated:
            response['is_logged_in'] = True
            response['pk'] = get_user_pk(request.user.username)
            # Transform the database design data into a json for the frontend
            response['data'] = []
            if user_info.eosscontext.design_set.count() > 0:
                response['modified_dataset'] = True
            else:
                response['modified_dataset'] = False
        else:
            response['is_guest'] = request.session['is_guest']
            response['is_logged_in'] = False
        return Response(response)



class GenerateSession(APIView):
    """
    Simply generate a session for the user (solves a ton of bugs)
    """
    def post(self, request, format=None):
        # Is this the first visit for this cookie?
        if request.session.session_key is None:
            request.session['is_guest'] = False
        request.session.save()                        # If None, create new session key and save
        return Response("Session generated")


# Vassar Problem Editor
class GetUserPk(APIView):
    """
    Simply generate a session for the user (solves a ton of bugs)
    """
    def post(self, request, format=None):
        if request.user == None:
            return Response({'status': 'request.user is none'})
        users = User.objects.filter(username__exact=request.user)
        if len(users) == 1:
            print("USER", users[0].id)
            return Response({'user_id': users[0].id})
        else:
            return Response({'status': 'query returned more than one users'})


class CheckStatusHasura(APIView):
    """
    Request sent from the hasura container! Authenticates the user editing a problem
    """
    def get(self, request, format=None):
        print("Check hasura status", request.data)
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        print("--> GOT USER INFORMATION")
        problem = user_info.eosscontext.problem
        dataset_filename = user_info.eosscontext.dataset_name
        dataset_user = user_info.eosscontext.dataset_user

        response = {
            "X-Hasura-User-Id": "1",
            "X-Hasura-Role": "admin",
            "X-Hasura-Is-Owner": "true"
        }
        print("--> RESPONSE", response)
        return Response(response)

        # if request.user.is_authenticated:
        #     response['is_logged_in'] = True
        #     # Transform the database design data into a json for the frontend
        #     response['data'] = []
        #     if user_info.eosscontext.design_set.count() > 0:
        #         for design in user_info.eosscontext.design_set.order_by('id').all():
        #             response['data'].append(
        #                 {'id': design.id, 'inputs': json.loads(design.inputs), 'outputs': json.loads(design.outputs)})
        #         response['modified_dataset'] = True
        #     else:
        #         response['modified_dataset'] = False
        # else:
        #     response['is_logged_in'] = False
        # return Response(response)


def get_user_pk(username):
    users = User.objects.filter(username__exact=username)
    if len(users) == 1:
        print("---> USER FOUND", users[0].id)
        return users[0].id
    else:
        print("---> USER PK ERROR")
        return False


class ConfirmGuest(APIView):
    def post(self, request, format=None):
        request.session['is_guest'] = True
        request.session.save()
