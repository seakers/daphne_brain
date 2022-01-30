import os

from pslpython.model import Model
from pslpython.partition import Partition
from pslpython.predicate import Predicate
from pslpython.rule import Rule

MODEL_NAME = 'data'
DATA_DIR = os.path.join('..', 'diagnosis', MODEL_NAME)

ADDITIONAL_PSL_OPTIONS = {
    'log4j.threshold': 'INFO'
}

ADDITIONAL_CLI_OPTIONS = [
    # '--postgres'
]


def main():
    model = Model(MODEL_NAME)

    # Add Predicates
    add_predicates(model)

    # Add Rules
    add_rules(model)

    # Inference
    results = infer(model)

    write_results(results, model)


def write_results(results, model):
    out_dir = 'inferred-predicates'
    os.makedirs(out_dir, exist_ok=True)

    for predicate in model.get_predicates().values():
        if predicate.closed():
            continue

        out_path = os.path.join(out_dir, "%s.txt" % (predicate.name()))
        results[predicate].to_csv(out_path, sep="\t", header=False, index=False)


def add_predicates(model):
    predicate = Predicate('Sensor_Measures', closed=True, size=4)
    model.add_predicate(predicate)

    predicate = Predicate('Filter_Measures', closed=True, size=4)
    model.add_predicate(predicate)

    predicate = Predicate('Same_Filter', closed=True, size=2)
    model.add_predicate(predicate)

    predicate = Predicate('Likes', closed=True, size=2)
    model.add_predicate(predicate)

    predicate = Predicate('Joins', closed=True, size=2)
    model.add_predicate(predicate)

    predicate = Predicate('Has_Sensor', closed=True, size=2)
    model.add_predicate(predicate)

    predicate = Predicate('Has_Filter', closed=True, size=2)
    model.add_predicate(predicate)

    predicate = Predicate('Is_Sensor', closed=False, size=4)
    model.add_predicate(predicate)

    predicate = Predicate('Is_Filter', closed=False, size=4)
    model.add_predicate(predicate)


def add_rules(model):
    # Priors from local classifiers
    # model.add_rule(Rule("100: symptoms(P1,L1) & measures(S1,P1) -> is_faulty_sensor(s1)"))
    # model.add_rule(Rule("50: symptoms(P1,L1) & affects(f1,P1) -> is_obstructed_filter(f1)"))
    # model.add_rule(Rule("50: symptoms(P1,L1) & affects(f1,P1) & measures(S1,P1) &visual_inspection(f1,"
    #                     "ok) -> faulty_sensor(s1)"))
    # model.add_rule(Rule("50: symptom(P1,L1) & affects(f1,P1) & measures(S1,P1) &visual_inspection(f1,"
    #                     "nok) -> obstructed_filter(f1)"))

    # Priors from local classifiers
    model.add_rule(Rule("1: Has_Sensor(U, S) & Sensor_Measures(S, U, A, L) -> Is_Sensor(U, S, A, L) ^2"))
    model.add_rule(Rule("1: Has_Sensor(U, S) & ~Sensor_Measures(S, U, A, L) -> ~Is_Sensor(U, S, A, L) ^2"))

    model.add_rule(Rule("1: Has_Filter(U, S) & Filter_Measures(S, U, A, L) -> Is_Filter(U, S, A, L) ^2"))
    model.add_rule(Rule("1: Has_Filter(U, S) & ~Filter_Measures(S, U, A, L) -> ~Is_Filter(U, S, A, L) ^2"))

    model.add_rule(Rule("1: Same_Filter(U, V) & Is_Filter(V, S, A, L)-> Is_Filter(U, S, A, L) ^2"))
    model.add_rule(Rule("1: Same_Filter(U, V) & ~Is_Filter(V, S, A, L)-> ~Is_Filter(U, S, A, L) ^2"))
    model.add_rule(Rule("1: Same_Filter(V, U) & Is_Filter(V, S, A, L)-> Is_Filter(U, S, A, L) ^2"))
    model.add_rule(Rule("1: Same_Filter(V, U) & ~Is_Filter(V, S, A, L)-> ~Is_Filter(U, S, A, L) ^2"))

    # Priors from local classifiers
    # model.add_rule(Rule("50: Has(U, S) & Predicts(S, U, A, L) -> Is(U, A, L) ^2"))
    # model.add_rule(Rule("50: Has(U, S) & ~Predicts(S, U, A, L) -> ~Is(U, A, L) ^2"))

    # # Collective Rules for relational signals
    # model.add_rule(Rule("100: Joins(U, G) & Joins(V, G) & Is(V, A, L) -> Is(U, A, L) ^2"))
    # model.add_rule(Rule("100: Joins(U, G) & Joins(V, G) & ~Is(V, A, L) -> ~Is(U, A, L) ^2"))
    # model.add_rule(Rule("10: Likes(U, T) & Likes(V, T) & Is(V, A, L) -> Is(U, A, L) ^2"))
    # model.add_rule(Rule("10: Likes(U, T) & Likes(V, T) & ~Is(V, A, L) -> ~Is(U, A, L) ^2"))
    #
    # model.add_rule(Rule("1: Friend(U, V) & Is(V, A, L)-> Is(U, A, L) ^2"))
    # model.add_rule(Rule("1: Friend(U, V) & ~Is(V, A, L)-> ~Is(U, A, L) ^2"))
    # model.add_rule(Rule("1: Friend(V, U) & Is(V, A, L)-> Is(U, A, L) ^2"))
    # model.add_rule(Rule("1: Friend(V, U) & ~Is(V, A, L)-> ~Is(U, A, L) ^2"))

    # Ensure that user has one attribute
    model.add_rule(Rule("1: Is_Sensor(U, S, A, +L) = 1"))
    model.add_rule(Rule("1: Is_Filter(U, F, A, +L) = 1"))


def add_data(model):
    for predicate in model.get_predicates().values():
        predicate.clear_data()

    # path = os.path.join(DATA_DIR, 'symptoms_obs.txt')
    # model.get_predicate('symptoms').add_data_file(Partition.OBSERVATIONS, path)
    #
    # path = os.path.join(DATA_DIR, 'sensor_measures_obs.txt')
    # model.get_predicate('measures').add_data_file(Partition.OBSERVATIONS, path)
    #
    # path = os.path.join(DATA_DIR, 'filter_affects_obs.txt')
    # model.get_predicate('affects').add_data_file(Partition.OBSERVATIONS, path)
    #
    # path = os.path.join(DATA_DIR, 'visual_inspection_obs.txt')
    # model.get_predicate('affects').add_data_file(Partition.OBSERVATIONS, path)
    #
    # path = os.path.join(DATA_DIR, 'user_target_sensor.txt')
    # model.get_predicate('Is_Sensor').add_data_file(Partition.TARGETS, path)
    #
    # path = os.path.join(DATA_DIR, 'user_target_filter.txt')
    # model.get_predicate('Is_Filter').add_data_file(Partition.TARGETS, path)
    #
    # path = os.path.join(DATA_DIR, 'user_truth.txt')
    # model.get_predicate('Is').add_data_file(Partition.TRUTH, path)

    path = os.path.join(DATA_DIR, 'has_sensor_obs.txt')
    model.get_predicate('has_sensor').add_data_file(Partition.OBSERVATIONS, path)

    path = os.path.join(DATA_DIR, 'has_filter_obs.txt')
    model.get_predicate('has_filter').add_data_file(Partition.OBSERVATIONS, path)

    path = os.path.join(DATA_DIR, 'sensor_measures_obs.txt')
    model.get_predicate('sensor_measures').add_data_file(Partition.OBSERVATIONS, path)

    path = os.path.join(DATA_DIR, 'filter_measures_obs.txt')
    model.get_predicate('filter_measures').add_data_file(Partition.OBSERVATIONS, path)

    path = os.path.join(DATA_DIR, 'same_filter_obs.txt')
    model.get_predicate('same_filter').add_data_file(Partition.OBSERVATIONS, path)

    path = os.path.join(DATA_DIR, 'user_target_sensor.txt')
    model.get_predicate('Is_Sensor').add_data_file(Partition.TARGETS, path)

    path = os.path.join(DATA_DIR, 'user_target_filter.txt')
    model.get_predicate('Is_Filter').add_data_file(Partition.TARGETS, path)

    path = os.path.join(DATA_DIR, 'user_truth.txt')
    model.get_predicate('Is_Filter').add_data_file(Partition.TRUTH, path)


def infer(model):
    add_data(model)
    return model.infer(additional_cli_optons=ADDITIONAL_CLI_OPTIONS, psl_config=ADDITIONAL_PSL_OPTIONS)


if __name__ == '__main__':
    main()
