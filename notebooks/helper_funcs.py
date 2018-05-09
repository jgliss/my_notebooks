"""Helper methods for notebooks"""
from pandas import DataFrame
import numpy as np

def read_file_custom(fpath, verbose=False):
    """Custom ASCII conversion method 
    
    Parameters
    ----------
    fpath : str
        path to file location
    verbose : bool
        if True, print output (defaults to False)
    Returns
    -------
    Dataframe 
        pandas data frame ready for further analysis
    """
    with open(fpath, encoding="latin-1") as f:
        lines = f.read().splitlines()
    test_case = None
    control_case = None
    
    data = []

    in_data = False
    problem_vars = ["FSNTOAC_CERES-EBAF","FSNTOA_CERES-EBAF"]
    for line in lines:
        line.strip()
        if "TEST CASE:" in line:
            spl = line.split("TEST CASE:")[1].strip().split("(yrs ")
            test_case = spl[0]
            years = spl[1].split(")")[0]
            header = ["Variable", "Run", "Years", "Model", "Obs", "Bias", 
                      "RMSE"]
        elif "CONTROL CASE:" in line:
            control_case = line.split("CONTROL CASE:")[1].strip()
        elif "Variable" in line:
            in_data =True
        elif in_data:
            line_data = []
            is_problem_var = False
            for var in problem_vars:
                if var in line:
                    spl = line.split(var)
                    is_problem_var = True
                    _var = var
                    if verbose:
                        print("Problem case {}".format(_var))
            if is_problem_var:
                spl = spl[1].split()
            else:
                spl = line.split()
                _var = spl.pop(0)
            if len(spl) == 4:
                line_data.append(_var)
                line_data.append(test_case)
                line_data.append(years)
                for item in spl:
                    val = float(item)
                    if val == -999:
                        val = np.nan
                    line_data.append(val)
                data.append(line_data)
        else:
            if verbose:
                print("Ignoring line: {}".format(line))
                #variables.append(_var)
    df = DataFrame(data, columns=header)
    df.set_index(["Variable", "Run", "Years"], inplace=True)
    if verbose:
        print("Test case: {}".format(test_case))
        print("Control case: {}".format(control_case))
    return df

if __name__ == "__main__":
    import os
    import pandas as pd
    
    data_dir = "./data/michael_ascii_read/"
    files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if 
             f.endswith(".webarchive")]
    
    df0 = read_file_custom(files[0])
    df1 = read_file_custom(files[1])
    
    concat = pd.concat([df0, df1], axis=0)
    df0.head()
    
    
    
    
    
    
    
    