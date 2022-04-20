import numpy as np
import matplotlib.pyplot as plt

"""
    Definition:
        - The IIIPL class models a Daphne Academy Question. The main function is 'prob_correct', 
            which takes a user's ability parameter (theta) and finds the probability they get it correct.

    Functions:
        1. prob_correct - takes a user ability parameter (theta in [0, 1]) and finds probability user answers correctly
        2. prob_correct_arr - same as prob_correct only takes a list of ability parameter values

    Daphne Academy Question Types:
        - Adaptive Test Question (factored into ability parameter)
        - Learning Module Practice Question
        - Learning Module Exam Question (factored into ability parameter)
"""

class IIIPL:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def plot_model(self, theta=None):
        if not theta:
            theta = np.arange(0, 1, 0.01)
        prob_correct = self.prob_correct_arr(theta)
        plt.plot(theta, prob_correct)
        plt.xlabel("user ability")
        plt.ylabel("probability of correctly answering")
        _ = plt.title(f"Item Characteristic Curve a={self.a}, b={self.b}, c={self.c}")
        # plt.show()

    def prob_correct_arr(self, theta_arr):
        probs = []
        for theta in theta_arr:
            probs.append(self.prob_correct(theta))
        return probs

    def prob_correct(self, theta):
        # 1. Find logistic exponent (logit)
        logit = self.find_logit(theta)

        # 2. Compute logistic function
        logistic = self.find_logistic(logit)

        # 3. Scale for guessing and return
        return self.scale_guessing(logistic)

    def prob_incorrect(self, theta):
        return float(1 - self.prob_correct(theta))

    def find_logit(self, theta):
        return self.a * (theta - self.b)

    def find_logistic(self, logit):
        # return 1.0 / (1 + np.exp(-logit))
        return np.exp(logit) / (1 + np.exp(logit))

    def scale_guessing(self, logistic):
        return self.c + (1 - self.c) * logistic

