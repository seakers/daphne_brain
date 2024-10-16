import os

from django.http import HttpResponse
from rest_framework.views import APIView


class PdfViewer(APIView):

    def get(self, request, format=None):
        filename = request.query_params["filename"]
        folder_path = os.path.join(os.getcwd(), "daphne_brain", "AT", "databases", "procedures")
        filepath = os.path.join(folder_path, filename)
        with open(filepath, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = filename + '.pdf'
            return response


class PngViewer(APIView):

    def get(self, request, format=None):
        filename = request.query_params["filename"]
        folder_path = os.path.join(os.getcwd(), "daphne-at-interface", "src", "images")
        filepath = os.path.join(folder_path, filename)
        image_data = open(filepath, "rb").read()
        return HttpResponse(image_data, content_type="image/png")
