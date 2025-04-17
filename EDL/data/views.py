import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response


class ImportDataEDLSTATS(APIView):
    """ Imports data from a csv file. To be deprecated in the future.

    Request Args:
        filename: Name of the sample data file

    Returns:
        data: Json string with the read data
        columns: array with the columns of the data

    """

    def post(self, request, format=None):

        # Set the path of the file containing data
        file_path = '/Users/ssantini/Desktop/Code_Daphne/daphne_brain/daphne/' + request.data['filename']

        data = pd.read_csv(file_path, parse_dates=True, index_col='timestamp')

        return Response(data)
