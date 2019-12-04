from django.http import HttpResponse
from rest_framework.views import APIView


class PdfViewer(APIView):

    def get(self, request, format=None):
        filename = request.query_params["filename"]
        filepath = 'C:/Users/Michael/Documents/repos/daphne_brain/AT/Databases/procedures/' + filename
        with open(filepath, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'some_file.pdf'
            return response
