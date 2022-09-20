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
from daphne_context.models import UserInformation
from asgiref.sync import async_to_sync, sync_to_async
from EOSS.graphql.client.Abstract import AbstractGraphqlClient

import requests
import json


class InitializeServices(APIView):
    """
    Initialize user AWS resources
    """

class Register(APIView):
    """
    Register a user
    """
    username_blacklist = ['default']

    def post(self, request, format=None):

        # --> Extract fields
        username = request.data["username"]
        email = request.data["email"]
        password1 = request.data["password1"]
        password2 = request.data["password2"]

        # --> Validate fields
        validation = self.validate(username, email, password1, password2)
        if validation is not None:
            return validation

        # --> Create user and insert into default group: (all users are admins)
        try:
            user_id = self.create_user(username, email, password1)
            async_to_sync(AbstractGraphqlClient.add_user_to_group)(user_id, 1)
        except ValueError:
            return Response({'status': 'registration_error',
                             'registration_error': 'Error creating user!'})
        return Response({'status': 'registered'})

    def validate(self, username, email, password1, password2):

        # --> Validate email
        try:
            validate_email(email)
        except ValidationError:
            return Response({
                'status': 'registration_error',
                'registration_error': 'Email has an incorrect format.'
            })

        # --> Validate password
        if not password1 or not password2 or password1 != password2:
            return Response({
                'status': 'registration_error',
                'registration_error': 'The passwords do not match.'
            })

        # --> Validate username isn't blacklisted
        if username in self.username_blacklist:
            return Response({
                'status': 'registration_error',
                'registration_error': 'This username is already in use.'
            })

        # --> Validate username uniqueness
        if User.objects.filter(username=username).exists():
            return Response({
                'status': 'registration_error',
                'registration_error': 'This username is already in use.'
            })

    def create_user(self, username, email, password):
        user = User.objects.create_user(username, email, password)
        user.save()
        return user.id



class Login(APIView):
    """
    Login a user
    """
    def post(self, request, format=None):

        # --> Authenticate user from request
        username = request.data['username']
        password = request.data['password']
        daphne_version = request.data['daphneVersion']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Try to look for user session object. If it exists, then the session will be changed to that. If not,
            # the current session information will be transferred to the user
            userinfo_qs = UserInformation.objects.filter(user__exact=user)

            if len(userinfo_qs) == 0:
                # Try to get or create a session user_info from the session and transfer it to the user
                userinfo = get_or_create_user_information(request.session, user, daphne_version)
                userinfo.user = user
                userinfo.session = None
                userinfo.save()
            else:
                userinfo = userinfo_qs.first()

            if len(userinfo_qs) != 0:
                # Force the user information daphne version to be the one from the login
                userinfo = userinfo_qs[0]
                userinfo.daphne_version = daphne_version
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
                'is_experiment_user': userinfo.is_experiment_user,
                'permissions': []
            })
        else:
            return Response({
                'status': 'auth_error',
                'login_error': 'Invalid Login!'
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

        problem_id = user_info.eosscontext.problem_id
        group_id = user_info.eosscontext.group_id
        dataset_id = user_info.eosscontext.dataset_id

        # problem: is now the problem_id (from the database)
        response = {
            'username': request.user.username,
            'permissions': [],
            'problem_id': problem_id,
            'group_id': group_id,
            'dataset_id': dataset_id,
            'is_experiment_user': user_info.is_experiment_user
        }

        if request.user.is_authenticated:
            response['is_logged_in'] = True
            response['pk'] = get_user_pk(request.user.username)
        else:
            if 'is_guest' in request.session:
                response['is_guest'] = request.session['is_guest']
            else:
                response['is_guest'] = False  # --> Assume user hasn't selected guest if is_guest key not in session
            response['is_logged_in'] = False
        return Response(response)


class GenerateSession(APIView):
    """
    Simply generate a session for the user (solves a ton of bugs)
    """
    def post(self, request, format=None):
        print('--> ENV CHECK:', os.environ['POSTGRES_HOST'])

        # Is this the first visit for this cookie?
        if request.session.session_key is None:
            request.session['is_guest'] = False
        request.session.save()                        # If None, create new session key and save
        return Response("Session generated")


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
        #user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        #print("--> GOT USER INFORMATION")
        #problem = user_info.eosscontext.problem
        #dataset_filename = user_info.eosscontext.dataset_name
        #dataset_user = user_info.eosscontext.dataset_user

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


class ConfirmGuest(APIView):
    def post(self, request, format=None):
        request.session['is_guest'] = True
        request.session.save()


def get_user_pk(username):
    users = User.objects.filter(username__exact=username)
    if len(users) == 1:
        return users[0].id
    else:
        print("---> USER PK ERROR")
        return False
