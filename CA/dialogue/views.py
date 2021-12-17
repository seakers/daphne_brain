from rest_framework.views import APIView
from rest_framework.response import Response

from dialogue.views import Command, Dialogue, ClearHistory

answer_sheet = {
    'launch-cost': ['$B$14', '$C$14', '$D$14', '$E$14']
}

phrases = [
    'The number of launches and launch vehicle cost are used to find mission launch cost.',
    'Bus cost is found by summing bus recurring and non-recurring costs',
    'Bus recurring cost is estimated using the following subsystem masses: thermal, structures, propulsion, ADCS, communications, EPS, and satellite BOL power',
    'Bus non-recurring cost is estimated using the following subsystem masses: thermal, structures, propulsion, ADCS, communications, and EPS',
    'Payload cost is estimated by summing the costs of its instruments',
    'Payload recurring cost is estimated from payload cost',
    'Payload non-recurring cost is estimated from payload cost',
    'Satellite cost is estimated by summing spacecraft recurring and non-recurring cost',
    'Spacecraft recurring cost is estimated with bus recurring cost and payload cost',
    'Spacecraft non-recurring cost is estimated with bus non-recurring cost and payload cost',
    'someting',
    'someting',
    'someting',
    'someting',
    'someting',
    'someting',
    'someting',
    'someting',
    'someting'
]


# --> Change this class to inherit from (dialogue.Command) class to reuse antoni's code
class CACommand(APIView):

    def get_answers(self):
        final_sheet = {}
        counter = 0
        for idx in range(14, 33):
            row = ['$B$'+str(idx), '$C$'+str(idx), '$D$'+str(idx), '$E$'+str(idx)]
            final_sheet[phrases[counter]] = row
            counter += 1
        return final_sheet

    def post(self, request, format=None):

        answers = self.get_answers()

        command = request.data['command']
        workbook = request.data['workbook']
        worksheet = request.data['worksheet']
        cell = request.data['cell']

        print('--> CA COMMAND:', command, workbook, worksheet, cell)

        for key, value in answers.items():
            if cell in value:
                return Response({'response': key})



        return Response({'response': 'some response'})



class CACommandHistory(APIView):

    def post(self, request, format=None):

        return Response({'response': 'some response'})



class CAEvent(APIView):

    def post(self, request, format=None):

        if 'value' not in request.data:
            return Response({'response': 'empty'})
        if 'row' not in request.data:
            return Response({'response': 'empty'})
        if 'col' not in request.data:
            return Response({'response': 'empty'})

        row = int(request.data['row'])
        col = int(request.data['col'])
        value = str(request.data['value'])

        # bus-cost | bus-recurring-cost | cus-non-recurring-cost --- Sat A
        if row in [15, 16, 17] and col == 3:
            if value not in ['none', 'None', 'dne']:
                return Response({'response': 'This cost element cant be estimated because Sat A\'s ADCS subsystem mass violates the CERs ADCS mass constraints: [20 - 192] (kg)'})

        return Response({'response': 'empty'})
