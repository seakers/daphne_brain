import re
import numpy as np, scipy.io
from re import search

def equation_parser(equation_string, matfile_path):
    variables = scipy.io.whosmat(matfile_path)
    variables_in_mat = [i[0] for i in variables]
    if search('(i)', equation_string):
        equation_string = equation_string.replace('(i)', "")

    valid = re.compile(r"([A-Za-z_b]\w*)(?![\(\w])")
    matches = valid.findall(equation_string)
    matches.remove('ans')
    # matches.remove('i')
    matches.append('output_case')
    if 'e3' in matches:
        matches.remove('e3')
    filtered_list = [i for i in matches if len(i)>3] # every variable has more than one letter in its name. One letter results are a
    for variable in filtered_list:
        if variable not in variables_in_mat:
            print('Not all variables are in the matfile')
            warning = "not all variables are in matfile"
        else:
            warning = 'none'

    return filtered_list, warning