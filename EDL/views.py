import json
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from EDL import sensitivity_analysis
from auth_API.helpers import get_user_information


class MetricsOfInterest(APIView):
    def get(self, request, format=None):
        user_info = get_user_information(request.session, request.user)
        return Response({ "metrics_list": json.loads(user_info.edlcontext.current_metrics_of_interest)})


class SensitivityAnalysis(APIView):
    def post(self, request, format=None):
        user_info = get_user_information(request.session, request.user)
        metric_name = request.data['metric_name']
        sub_df = sensitivity_analysis.run_SA(metric_name, user_info)
        p_vals = (sub_df['p_vals']).tolist()
        input_name = (sub_df['metric_name']).tolist()
        input_descr = (sub_df['description']).tolist()
        input_label = (sub_df['label']).tolist()
        input_model = (sub_df['model']).tolist()
        distance = (sub_df['distance']).tolist()
        return Response({"pvals": p_vals, "input_name": input_name, "input_description": input_descr,
                         "input_label": input_label, "input_model": input_model, "distance": distance})


class ImportDataAvail(APIView):
    def post(self, request, format = None):
        user_info = get_user_information(request.session, request.user)

        file_to_load = request.data['filename']
        file_to_load = file_to_load
        user_info.edlcontext.current_mat_file = os.path.join('/Users/ssantini/Code/Code_Daphne/daphne_brain/edl_API/EDLData/', file_to_load)
        user_info.edlcontext.current_mat_file_for_print = file_to_load
        user_info.edlcontext.save()
        return Response({'file_status': 'file loaded !'})
