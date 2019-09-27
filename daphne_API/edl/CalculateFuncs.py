import re
import numpy as np, scipy.io

def equation_parser(equation_string, matfile_path):
    variables = scipy.io.whosmat(matfile_path)
    variables_in_mat = [i[0] for i in variables]

    valid = re.compile(r"([A-Za-z]\w*)(?![\(\w])")
    matches = valid.findall(equation_string)
    matches.remove('ans')
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