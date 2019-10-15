import json
import logging
import sys
import traceback

from EOSS.data import problem_specific

logger = logging.getLogger('VASSAR')


def base_feature_expression_to_string(feature_expression, is_critique=False, context=None):
    try:
        e = feature_expression[1:-1]
        out = None

        feature_type = e.split("[")[0]
        arguments = e.split("[")[1][:-1]

        arg_split = arguments.split(";")

        orbit_indices = arg_split[0]
        instrument_indices = arg_split[1]
        numbers = arg_split[2]

        orbit_dataset = problem_specific.get_orbit_dataset(context.eosscontext.problem)
        instrument_dataset = problem_specific.get_instrument_dataset(context.eosscontext.problem)

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
            satisfied = apply_base_filter(feat, design, context)
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
            satisfied = apply_base_filter(feat, design, context)
            if not satisfied:
                out.append(feat)
        return "&&".join(out)


def apply_base_filter(filter_expression, design, context):
    expression = filter_expression

    # Preset filter: {presetName[orbits;instruments;numbers]}
    if expression[0] == "{" and expression[-1] == "}":
        expression = expression[1:-1]

    orbit_dataset = problem_specific.get_orbit_dataset(context.eosscontext.problem)
    instrument_dataset = problem_specific.get_instrument_dataset(context.eosscontext.problem)
    norb = len(orbit_dataset)
    ninstr = len(instrument_dataset)
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
            for i in range(norb):
                if inputs[ninstr * i + instr]:
                    out = True
                    break

        elif feature_type == "absent":
            if len(instr) == 0:
                return False
            out = True
            instr = int(instr)
            for i in range(norb):
                if inputs[ninstr * i + instr]:
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
                    if inputs[orbit * ninstr + temp] is False:
                        out = False
                        break
            else:
                # Single instrument
                instrument = int(instr)
                out = False
                if inputs[orbit * ninstr + instrument]:
                    out = True

        elif feature_type == "notInOrbit":
            orbit = int(orbit)

            if "," in instr:
                # Multiple instruments
                out = True
                instruments = instr.split(",")
                for instrument in instruments:
                    temp = int(instrument)
                    if inputs[orbit * ninstr + temp] is True:
                        out = False
                        break
            else:
                # Single instrument
                instrument = int(instr)
                out = True
                if inputs[orbit * ninstr + instrument]:
                    out = False

        elif feature_type == "together":
            out = False
            instruments = instr.split(",")
            for i in range(norb):
                found = True
                for j in range(len(instruments)):
                    temp = int(instruments[j])
                    if inputs[i * ninstr + temp] is False:
                        found = False

                if found:
                    out = True
                    break

        elif feature_type == "separate":
            out = True
            instruments = instr.split(",")
            for i in range(norb):
                found = False
                for j in range(len(instruments)):
                    temp = int(instruments[j])
                    if inputs[i * ninstr + temp] is True:
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

            for i in range(ninstr):
                if inputs[orbit * ninstr + i]:
                    out = False
                    break

        elif feature_type == "numOrbits":
            count = 0
            out = False
            numb = int(numb)

            for i in range(norb):
                for j in range(ninstr):
                    if inputs[i * ninstr + j]:
                        count += 1
                        break

            if numb == count:
                out = True

        else:
            raise ValueError("Feature type not recognized: {}".format(feature_type))

    except Exception as e:
        raise ValueError("Exe in applying the base filter: " + str(e))

    return out