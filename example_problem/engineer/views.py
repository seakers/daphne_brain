import json
from rest_framework.views import APIView
from rest_framework.response import Response
from auth_API.helpers import get_or_create_user_information
from example_problem.data.design_helpers import add_design


class EvaluateArchitecture(APIView):
    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'example_problem')

        inputs = request.data['inputs']
        inputs = json.loads(inputs)

        # TODO: Call backend for evaluation
        architecture = {}

        # Check if the architecture already exists in DB before adding it again
        is_same = True
        for old_arch in user_info.examplecontext.design_set.all():
            is_same = True
            old_arch_outputs = json.loads(old_arch.outputs)
            for i in range(len(old_arch_outputs)):
                if old_arch_outputs[i] != architecture['outputs'][i]:
                    is_same = False
            if is_same:
                break

        if not is_same:
            architecture = add_design(architecture, request.session, request.user, False)

        user_info.save()

        return Response(architecture)
