import json
import logging
import sys
import traceback

from EOSS.data import problem_specific

logger = logging.getLogger('VASSAR')


def base_feature_expression_to_string(feature_expression, is_critique=False, context=None):
    try:
        e = remove_outer_parentheses(feature_expression)
        e = e[1:-1]
        out = None

        feature_type = e.split("[")[0]
        arguments = e.split("[")[1][:-1]

        arg_split = arguments.split(";")

        orbit_indices = arg_split[0]
        instrument_indices = arg_split[1]
        numbers = arg_split[2]

        orbit_dataset = problem_specific.get_orbit_dataset(context.problem)
        instrument_dataset = problem_specific.get_instrument_dataset(context.problem)

        orbit_names = []
        if orbit_indices:
            orbit_names = [orbit_dataset[int(i)]['name'] for i in orbit_indices.split(",")]
        instrument_names = []
        if instrument_indices:
            instrument_names = [instrument_dataset[int(i)]['name'] for i in instrument_indices.split(",")]
        if numbers:
            numbers = [int(n) for n in numbers.split(",")]

        if feature_type == "present":
            if is_critique:
                out = "add {}".format(instrument_names[0])
            else:
                out = "{} is used".format(instrument_names[0])
        elif feature_type == "absent":
            if is_critique:
                out = "remove {}".format(instrument_names[0])
            else:
                out = "{} is not used in any orbit".format(instrument_names[0])
        elif feature_type == "inOrbit":
            if is_critique:
                out = ["assign instruments", ", ".join(instrument_names), "to orbit", orbit_names[0]]
            else:
                out = ["instruments", ", ".join(instrument_names), "are assigned to orbit", orbit_names[0]]
            out = " ".join(out)

        elif feature_type == "notInOrbit":
            if is_critique:
                out = ["remove instruments", ", ".join(instrument_names), "in orbit", orbit_names[0]]
            else:
                out = ["instruments", ", ".join(instrument_names), "are not assigned to orbit", orbit_names[0]]
            out = " ".join(out)
        elif feature_type == "together":
            if is_critique:
                out = "assign instruments {} to the same orbit".format(", ".join(instrument_names))
            else:
                out = "instruments {} are assigned to the same orbit".format(", ".join(instrument_names))
        elif feature_type == "separate":
            if is_critique:
                out = "do not assign instruments {} to the same orbit".format(", ".join(instrument_names))
            else:
                out = "instruments {} are never assigned to the same orbit".format(", ".join(instrument_names))
        elif feature_type == "emptyOrbit":
            if is_critique:
                out = "no spacecraft should fly in orbit {}".format(orbit_names[0])
            else:
                out = "no spacecraft flies in orbit {}".format(orbit_names[0])
        else:
            raise ValueError('Unrecognized feature name: {}'.format(feature_type))
        return out

    except Exception as e:
        msg = "Error in parsing feature expression: {}".format(feature_expression)
        print(msg)
        traceback.print_exc(file=sys.stdout)
        logger.error(msg)


def feature_expression_to_string(feature_expression, is_critique=False, context=None):
    out = []
    # TODO: Generalize the feature expression parsing.
    # Currently assumes that the feature only contains conjunctions but no disjunction
    if "&&" in feature_expression:
        individual_features = feature_expression.split("&&")
        for feat in individual_features:
            if feat == "":
                continue
            out.append(base_feature_expression_to_string(feat, is_critique, context))
    elif "||" in feature_expression:
        pass
    else:
        if not feature_expression == "":
            out.append(base_feature_expression_to_string(feature_expression, is_critique, context))

    out = " AND ".join(out)
    out = out[0].upper() + out[1:]

    return out


def get_feature_satisfied(expression, design, context):
    out = []

    if type(expression) is list:
        # Multiple features passed
        for exp in expression:
            out.append(get_feature_unsatisfied(exp, design, context))
        return out

    else:
        # TODO: Generalize the feature expression parsing.
        # Currently assumes that the feature only contains conjunctions but no disjunction
        if '&&' in expression:
            individual_features = expression.split("&&")
        else:
            individual_features = [expression]

        for feat in individual_features:
            satisfied = apply_preset_filter(feat, design, context)
            if satisfied:
                out.append(feat)
        return "&&".join(out)


def get_feature_unsatisfied(expression, design, context):
    out = []

    if type(expression) is list:
        # Multiple features passed
        for exp in expression:
            out.append(get_feature_unsatisfied(exp, design, context))
        return out

    else:
        # TODO: Generalize the feature expression parsing.
        # Currently assumes that the feature only contains conjunctions but no disjunction
        if '&&' in expression:
            individual_features = expression.split("&&")
        else:
            individual_features = [expression]

        for feat in individual_features:
            satisfied = apply_preset_filter(feat, design, context)
            if not satisfied:
                out.append(feat)
        return "&&".join(out)


def apply_preset_filter(filter_expression, design, context):
    expression = remove_outer_parentheses(filter_expression)

    # Preset filter: {presetName[orbits;instruments;numbers]}
    if expression[0] == "{" and expression[-1] == "}":
        expression = expression[1:-1]

    flip = False
    if expression[0] == '~':
        flip = True
        expression = expression[1:]

    orbit_dataset = problem_specific.get_orbit_dataset(context.problem)
    instrument_dataset = problem_specific.get_instrument_dataset(context.problem)
    num_orbits = len(orbit_dataset)
    num_instruments = len(instrument_dataset)
    feature_type = expression.split("[")[0]
    arguments = expression.split("[")[1]
    arguments = arguments[:-1]

    inputs = json.loads(design.inputs)

    arg_split = arguments.split(";")
    orbit = arg_split[0]
    instr = arg_split[1]
    numb = arg_split[2]

    try:
        out = None
        if feature_type == "present":
            if len(instr) == 0:
                return False
            out = False
            instr = int(instr)
            for i in range(num_orbits):
                if inputs[num_instruments * i + instr]:
                    out = True
                    break

        elif feature_type == "absent":
            if len(instr) == 0:
                return False
            out = True
            instr = int(instr)
            for i in range(num_orbits):
                if inputs[num_instruments * i + instr]:
                    out = False
                    break

        elif feature_type == "inOrbit":
            orbit = int(orbit)

            if "," in instr:
                # Multiple instruments
                out = True
                instruments = instr.split(",")
                for instrument in instruments:
                    temp = int(instrument)
                    if inputs[orbit * num_instruments + temp] is False:
                        out = False
                        break
            else:
                # Single instrument
                instrument = int(instr)
                out = False
                if inputs[orbit * num_instruments + instrument]:
                    out = True

        elif feature_type == "notInOrbit":
            orbit = int(orbit)

            if "," in instr:
                # Multiple instruments
                out = True
                instruments = instr.split(",")
                for instrument in instruments:
                    temp = int(instrument)
                    if inputs[orbit * num_instruments + temp] is True:
                        out = False
                        break
            else:
                # Single instrument
                instrument = int(instr)
                out = True
                if inputs[orbit * num_instruments + instrument]:
                    out = False

        elif feature_type == "together":
            out = False
            instruments = instr.split(",")
            for i in range(num_orbits):
                found = True
                for j in range(len(instruments)):
                    temp = int(instruments[j])
                    if inputs[i * num_instruments + temp] is False:
                        found = False

                if found:
                    out = True
                    break

        elif feature_type == "separate":
            out = True
            instruments = instr.split(",")
            for i in range(num_orbits):
                found = False
                for j in range(len(instruments)):
                    temp = int(instruments[j])
                    if inputs[i * num_instruments + temp] is True:
                        if found:
                            out = False
                            break
                        else:
                            found = True
                if out is False:
                    break

        elif feature_type == "emptyOrbit":
            out = True
            orbit = int(orbit)

            for i in range(num_instruments):
                if inputs[orbit * num_instruments + i]:
                    out = False
                    break

        elif feature_type == "numOrbits":
            count = 0
            out = False
            numb = int(numb)

            for i in range(num_orbits):
                for j in range(num_instruments):
                    if inputs[i * num_instruments + j]:
                        count += 1
                        break

            if numb == count:
                out = True

        elif feature_type == 'subsetOfInstruments':
            count = 0
            instruments = instr.split(",")
            numbers = numb.split(',')
            orbit = int(orbit)
            out = False

            for instrument in instruments:
                temp = int(instrument)
                if inputs[orbit * num_instruments + temp]:
                    count += 1

            if len(numbers) == 1:
                if count > int(numbers[0]):
                    out = True
            else:
                if count >= int(numbers[0]) and count <= int(numbers[1]):
                    out = True

        elif feature_type == 'numOfInstruments':
            count = 0
            out = False
            numb = int(numb)

            if orbit == "":
                # num of instruments across all orbits
                if instr == "":
                    # num of specified instrument
                    for i in range(num_orbits):
                        for j in range(num_instruments):
                            if inputs[i * num_instruments+j]:
                                count += 1
                else:
                    instr = int(instr)
                    # num of all instruments
                    for i in range(num_orbits):
                        if inputs[i * num_instruments+instr]:
                            count += 1

            else:
                orbit = int(orbit)
                # number of instruments in a specified orbit
                for i in range(num_instruments):
                    if inputs[orbit * num_instruments+i]:
                        count += 1

            if count == numb:
                out = True

        else:
            raise ValueError("Feature type not recognized: {}".format(feature_type))

    except Exception as e:
        raise ValueError("Exe in applying the base filter: " + str(e))

    if flip:
        return not out
    else:
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
        for i in range(1, len(clean_expression)-1):
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
