














def base_feature_expression_to_string(feature_expression, orbit_list, instrument_list):
    try:
        e = remove_outer_parentheses(feature_expression)
        e = e[1:-1]
        out = {}

        feature_type = e.split("[")[0]
        arguments = e.split("[")[1][:-1]

        arg_split = arguments.split(";")

        orbit_indices = arg_split[0]
        instrument_indices = arg_split[1]


        orbit_names = []
        instrument_names = []
        for i in orbit_indices.split(","):
            if i == '':
                break
            orbit_names.append(orbit_list[int(i)])
        for i in instrument_indices.split(","):
            if i == '':
                break
            instrument_names.append(instrument_list[int(i)])


        numbers = None
        if len(arg_split) == 3:
            numbers = arg_split[2]

        if feature_type == "present":
            out['add'] = instrument_names[0]
        elif feature_type == "numOrbits":
            out['used orbits'] = numbers
        elif feature_type == "absent":
            out['instrumentAbsent'] = instrument_names[0]
        elif feature_type == "inOrbit":
            out['inOrbit'] = {orbit_names[0]: instrument_names}
        elif feature_type == "notInOrbit":
            out['notInOrbit'] = {orbit_names[0]: instrument_names}
        elif feature_type == "together":
            out['together'] = instrument_names
        elif feature_type == "separate":
            out['separate'] = instrument_names
        elif feature_type == "emptyOrbit":
            out['orbitAbsent'] = orbit_names[0]
        else:
            raise ValueError('Unrecognized feature name: {}'.format(feature_type))
        return out

    except Exception as e:
        msg = "Error in parsing feature expression: {}".format(feature_expression)
        print(msg)
        print(e)




def feature_expression_to_string(feature_expression, orbit_names, instrument_names):
    out = []
    if "&&" in feature_expression:
        individual_features = feature_expression.split("&&")
        for feat in individual_features:
            if feat == "":
                continue
            out.append(base_feature_expression_to_string(feat, orbit_names, instrument_names))
    elif "||" in feature_expression:
        pass
    else:
        if not feature_expression == "":
            out.append(base_feature_expression_to_string(feature_expression, orbit_names, instrument_names))

    return out


def remove_outer_parentheses(expression, **kwargs):
    if "outer_level" in kwargs:
        new_outer_level = kwargs["outer_level"]
    else:
        new_outer_level = 0

    clean_expression = expression

    has_outer = clean_expression[0] == '('
    while has_outer:
        level = 1
        for i in range(1, len(clean_expression) - 1):
            if clean_expression[i] == '(':
                level += 1
            elif clean_expression[i] == ')':
                level -= 1

            if level == 0:
                has_outer = False

        if has_outer:
            clean_expression = clean_expression[1:-1]
            has_outer = clean_expression[0] == '('
            new_outer_level += 1

    if "outer_level" in kwargs:
        return {
            "expression": clean_expression,
            "level": new_outer_level
        }
    else:
        return clean_expression



