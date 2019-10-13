
# --> Sample Functions
from SALib.sample import saltelli
from SALib.sample import sobol_sequence


# --> Evaluates sample functions
from SALib.test_functions import Ishigami


# --> Analyze functions with results
from SALib.analyze import sobol


import numpy as np
import pprint







def main():
    pp = pprint.PrettyPrinter(indent=2)

    # ------- Create the Problem -------
    # --> We will have to take input and create a problem for either
    problem = {
        'num_vars': 3,
        'names': ['x1', 'x2', 'x3'],
        'bounds': [[0, 1],
                   [0, 1],
                   [0, 10]]
    }
    pp.pprint(problem)



    # --> Create samples of the problem with output for each sample (this will already be done, as we have architectures with results already)
    param_values = saltelli.sample(problem, 10)
    Y = Ishigami.evaluate(param_values)



    # --> Take the samples and their evaluations and analyze them
    Si = sobol.analyze(problem, Y)
    pp.pprint(Si)
















if __name__ == '__main__':
    main()