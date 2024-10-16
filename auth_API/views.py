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
from EOSS.aws.service.ServiceManager import ServiceManager


import requests
import threading
import json


class Register(APIView):
    """
    Register a user
    """
    username_blacklist = ['default']

    def post(self, request, format=None):


        # --> 1. Extract fields
        username = request.data["username"]
        email = request.data["email"]
        password1 = request.data["password1"]
        password2 = request.data["password2"]
        daphne_version = request.data['daphneVersion']


        # --> 2. Validate fields
        validation = self.validate(username, email, password1, password2)
        if validation is not None:
            return validation


        # --> 3. Create user / insert into default group
        try:
            user_id = self.create_user(username, email, password1)
            async_to_sync(AbstractGraphqlClient.add_user_to_group)(user_id, 1)
        except ValueError:
            return Response({'status': 'registration_error', 'registration_error': 'Error creating user!'})


        # --> 4. Authenticate registered user
        user = authenticate(request, username=username, password=password1)
        if user is None:
            return Response({'status': 'auth_error', 'login_error': 'Invalid Credentials'})


        # --> 5. Create user info / transfer session
        userinfo = self.get_user_info_wrapper(user, request, daphne_version)


        # --> 6. Log user in
        login(request, user)


        # --> 7. Initialize services
        def init_service(service_manager):
            async_to_sync(service_manager.initialize)(blocking=True)
        service_manager = ServiceManager(userinfo)
        thread = threading.Thread(target=init_service, args=(service_manager,))
        thread.start()



        # --> 8. Return
        return Response({
            'status': 'logged_in',
            'username': username,
            'pk': get_user_pk(username),
            'is_experiment_user': userinfo.is_experiment_user,
            'permissions': []
        })



    # --> TODO: Add logic so only pre-validated users can register. Saving resources
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

    def get_user_info_wrapper(self, user, request, daphne_version):
        userinfo = None

        # --> 1. Check if user_info object exists for user
        # - if user_info exists, set daphne_version and return
        # - if user_info dne, call get_or_create_user_information to create... then transfer current session
        query = UserInformation.objects.filter(user__exact=user)
        if len(query) > 0:
            # --> If UserInformation exists (return first)
            userinfo = query.first()
            userinfo.daphne_version = daphne_version
            userinfo.save()
        else:
            # --> If UserInformation DNE (create UserInformation)
            userinfo = get_or_create_user_information(request.session, user, daphne_version)

            # --> Transfer current session
            userinfo.user = user
            userinfo.session = None
            userinfo.save()

        return userinfo


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
            userinfo = self.handle_user_session(user, request, daphne_version)

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


    def handle_user_session(self, user, request, daphne_version):
        userinfo = None

        # --> 1. Check if UserInformation already exists
        query = UserInformation.objects.filter(user__exact=user)
        if len(query) > 0:
            # --> If UserInformation exists (return first)
            userinfo = query.first()
            userinfo.daphne_version = daphne_version
            userinfo.save()
        else:
            # --> If UserInformation DNE (create UserInformation)
            userinfo = get_or_create_user_information(request.session, user, daphne_version)

            # --> Transfer current session
            userinfo.user = user
            userinfo.session = None
            userinfo.save()

        return userinfo


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
        # Is this the first visit for this cookie?
        if request.session.session_key is None:
            print('--> GENERATING SESSION: GenerateSession')
            request.session['is_guest'] = False
        request.session.save()
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
