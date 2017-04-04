import numpy as np
import math
from scipy.optimize import minimize

def optimize_distance(a1, a2, intersection):
    
    #Compute radii
    r1 = math.sqrt(a1/math.pi)
    r2 = math.sqrt(a2/math.pi)
    
    #Compute area
    #a1 = math.pi*(r1**2)
    #a2 = math.pi*(r2**2)
    
    #print('a1:{0}, a2:{1}, intersection:{2}'.format(a1,a2,intersection))
    
    #Define the objective function
    def obj(x):
        return abs(r1**2*np.arccos((x**2+r1**2-r2**2)/(2*x*r1)) + r2**2*np.arccos((x**2+r2**2-r1**2)/(2*x*r2)) - 1/2*math.sqrt((-x+r1+r2)*(x+r1-r2)*(x-r1+r2)*(x+r1+r2)) - intersection)

    #Set bounds for x
    bnds = ((0, r1+r2-1e4),)
    
    guess = 1/2*(r1+r2)
    
    #Run optimization
    res = minimize(obj, guess, bounds = bnds, tol=1e-6)
    
    return res
    
    
def compute_intersection(a1, a2, d):
    
    #Compute radii
    r1 = math.sqrt(a1/math.pi)
    r2 = math.sqrt(a2/math.pi)
    
    x = d
    #Define the objective function
    return r1**2*np.arccos((x**2+r1**2-r2**2)/(2*x*r1)) + r2**2*np.arccos((x**2+r2**2-r1**2)/(2*x*r2)) - 1/2*math.sqrt((-x+r1+r2)*(x+r1-r2)*(x-r1+r2)*(x+r1+r2))
    
    