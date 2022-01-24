import sys

from models.IIIPL import IIIPL
from estimators.MAP_Estimator import MAP_Estimator
from estimators.MLE_Estimator import MLE_Estimator


def run():

    answers = [
        (1, IIIPL(10, .5, .25)),
        (0, IIIPL(4, .4, .25)),
        (1, IIIPL(6, .8, .25))
    ]

    # --> Maximum Likelihood Estimation
    mle_estimate = MLE_Estimator(answers).estimate().x
    print('--> MLE ESTIMATE:', mle_estimate)

    # --> Maximum Aposteriori Estimation
    map_estimate = MAP_Estimator(answers).estimate().x
    print('--> MAP ESTIMATE:', map_estimate)



if __name__ == "__main__":
    run()

