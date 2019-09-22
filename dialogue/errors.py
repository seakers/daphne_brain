class ParameterMissingError(Exception):
    def __init__(self, missing_param):
        self.missing_param = missing_param
