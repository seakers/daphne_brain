




class Excel:

    def __init__(self, client):
        self.client = client

        self.exercises = [
            'Tutorial'
        ]


    def index(self):

        for name in self.exercises:
            # --> 1. Index excel exercise
            exercise_id = self.client.index_excel_exercise(name)

            # --> 2. For each user, index ExcelExerciseCompletion for the exercise
            for user in self.client.get_users():
                self.client.index_excel_exercise_completion(user.id, exercise_id, False, 'Has not started')
        return 0

