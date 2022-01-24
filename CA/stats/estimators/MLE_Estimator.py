from scipy.optimize import minimize_scalar



class MLE_Estimator:
    def __init__(self, item_response_vector):
        """
            item_response_vector -> a list of touples: (item answer, IIIPL item model)
        """
        self.item_response_vector = item_response_vector

    def likelihood_arr(self, thetas):
        values = []
        for theta in thetas:
            values.append(self.likelihood(theta) * -1.0)
        return values

    def likelihood(self, theta):
        result = 1.0

        for item_tuple in self.item_response_vector:
            answer = int(item_tuple[0])
            item = item_tuple[1]
            if answer == 1:
                result = result * item.prob_correct(theta)
            else:
                result = result * (1.0 - item.prob_correct(theta))

        return result * -0.1

    def estimate(self):
        return minimize_scalar(self.likelihood, bounds=(0, 1), method='bounded')
