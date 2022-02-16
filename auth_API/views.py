import json
import os

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_API.helpers import get_or_create_user_information, get_user_information, str_to_bool
from daphne_context.models import UserInformation


class Login(APIView):
    """
    Login a user
    """

    def post(self, request, format=None):
        # Try to authorize the user
        username = request.data['username']
        password = request.data['password']
        daphne_version = request.data['daphneVersion']
        isSecondUser = str_to_bool(request.data['isSecondUser'])
        user = authenticate(request, username=username, password=password)

        if user is not None:

            try:
                user_info = get_user_information(None, user)
            except Exception:
                user_info = None
            if (not isSecondUser) and (user_info is None or not hasattr(user_info, "atexperimentcontext") or (not
            user_info.atexperimentcontext.is_running)):
                # Try to look for user session object. If it exists, then the session will be changed to that. If not,
                # the current session information will be transferred to the user
                userinfo_qs = UserInformation.objects.filter(user__exact=user)

                if len(userinfo_qs) == 0:
                    # Try to get or create a session user_info from the session and transfer it to the user
                    userinfo = get_or_create_user_information(request.session, user, daphne_version)
                    userinfo.user = user
                    userinfo.session = None
                    userinfo.save()

                if len(userinfo_qs) != 0:
                    # Force the user information daphne version to be the one from the login
                    userinfo = userinfo_qs[0]
                    userinfo.daphne_version = daphne_version
                    userinfo.save()

                # Log the user in
                login(request, user)

                # Return the login response
                return Response({
                    'status': 'logged_in',
                    'username': username,
                    'password': password,
                    'permissions': []
                })
            elif isSecondUser:
                # If the User has clicked on Yes to continue with the session
                # Try to look for user session object. If it exists, then the session will be changed to that. If not,
                # the current session information will be transferred to the user
                userinfo_qs = UserInformation.objects.filter(user__exact=user)

                if len(userinfo_qs) == 0:
                    # Try to get or create a session user_info from the session and transfer it to the user
                    userinfo = get_or_create_user_information(request.session, user, daphne_version)
                    userinfo.user = user
                    userinfo.session = None
                    userinfo.save()

                if len(userinfo_qs) != 0:
                    # Force the user information daphne version to be the one from the login
                    userinfo = userinfo_qs[0]
                    userinfo.daphne_version = daphne_version
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
                return Response({
                    'status': 'login_alert',
                    'login_error': 'This username is already in use! Are you sure you want to continue?'
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

        # Do the registration procedure which includes creating folders for all problems
        try:
            user = User.objects.create_user(username, email, password1)
            user.save()
            # Create folders in the server structure
            folder_name = os.path.join(os.getcwd(), "EOSS", "data", "datasets", username)
            os.mkdir(folder_name)
            problem_list = ["ClimateCentric", "Decadal2017Aerosols", "SMAP", "SMAP_JPL1", "SMAP_JPL2"]
            for problem in problem_list:
                subfolder_name = os.path.join(folder_name, problem)
                os.mkdir(subfolder_name)
        except ValueError:
            return Response({
                'status': 'registration_error',
                'registration_error': 'Please write a username.'
            })

        return Response({
            'status': 'registered'
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

        problem = user_info.eosscontext.problem
        dataset_filename = user_info.eosscontext.dataset_name
        dataset_user = user_info.eosscontext.dataset_user

        response = {
            'username': request.user.username,
            'permissions': [],
            'problem': problem,
            'dataset_filename': dataset_filename,
            'dataset_user': dataset_user
        }

        if request.user.is_authenticated:
            response['is_logged_in'] = True
            # Transform the database design data into a json for the frontend
            response['data'] = []
            if user_info.eosscontext.design_set.count() > 0:
                for design in user_info.eosscontext.design_set.order_by('id').all():
                    response['data'].append(
                        {'id': design.id, 'inputs': json.loads(design.inputs), 'outputs': json.loads(design.outputs)})
                response['modified_dataset'] = True
            else:
                response['modified_dataset'] = False
        else:
            response['is_logged_in'] = False
        return Response(response)


class GenerateSession(APIView):
    """
    Simply generate a session for the user (solves a ton of bugs)
    """

    def post(self, request, format=None):
        request.session.set_expiry(0)
        request.session.save()
        return Response("Session generated")
