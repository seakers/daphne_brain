







class BitString:

    def __init__(self, representation):
        self.original = representation

        # --> Possible representations
        # 1. List of int values (default)
        # 2. List of boolean values
        # 3. String of bit chars
        self.value = []

        if isinstance(representation, list) and len(representation) > 0:
            element = representation[0]
            if isinstance(element, int):
                self.value = representation
            elif isinstance(element, bool):
                for item in representation:
                    if item is True:
                        self.value.append(1)
                    else:
                        self.value.append(0)
            else:
                print('--> INVALID BIT STRING LIST TYPE')
        elif isinstance(representation, str):
            for idx, ch in enumerate(representation):
                if ch == '0':
                    self.value.append(0)
                elif ch == '1':
                    self.value.append(1)

    def get_int_array(self):
        return self.value

    def get_bool_array(self):
        bool_array = []
        for item in self.value:
            if item == 0:
                bool_array.append(False)
            elif item == 1:
                bool_array.append(True)
        return bool_array

    def get_string(self):
        temp = ''
        for item in self.value:
            temp += str(item)
        return temp





