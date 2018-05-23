"""Helper methods for notebooks"""
import pandas as pd
import numpy as np
import os
import xlrd
import matplotlib.cm as colormaps
import matplotlib.colors as colors
from collections import OrderedDict as od
from configparser import ConfigParser

def print_dict(dictionary):
    for k, v in dictionary.items():
        print("{}: {}".format(k, v))
        
def shifted_color_map(vmin, vmax, cmap = None):
    """Shift center of a diverging colormap to value 0
    
    .. note::
    
        This method was found `here <http://stackoverflow.com/questions/
        7404116/defining-the-midpoint-of-a-colormap-in-matplotlib>`_ 
        (last access: 17/01/2017). Thanks to `Paul H <http://stackoverflow.com/
        users/1552748/paul-h>`_ who provided it.
    
    Function to offset the "center" of a colormap. Useful for
    data with a negative min and positive max and if you want the
    middle of the colormap's dynamic range to be at zero level
    
    :param vmin: lower end of data value range
    :param vmax: upper end of data value range
    :param cmap: colormap (if None, use default cmap: seismic)
    
    :return: 
        - shifted colormap
        
    """

    if cmap is None:
        cmap = colormaps.seismic
    elif isinstance(cmap, str):
        cmap = colormaps.get_cmap(cmap)

    midpoint = 1 - abs(vmax)/(abs(vmax) + abs(vmin))
    cdict = {
        'red': [],
        'green': [],
        'blue': [],
        'alpha': []
    }

    # regular index to compute the colors
    reg_index = np.linspace(0, 1, 257)

    # shifted index to match the data
    shift_index = np.hstack([
        np.linspace(0.0, midpoint, 128, endpoint=False), 
        np.linspace(midpoint, 1.0, 129, endpoint=True)
    ])

    for ri, si in zip(reg_index, shift_index):
        r, g, b, a = cmap(ri)

        cdict['red'].append((si, r, r))
        cdict['green'].append((si, g, g))
        cdict['blue'].append((si, b, b))
        cdict['alpha'].append((si, a, a))

    return colors.LinearSegmentedColormap('shiftedcmap', cdict)

def _background_gradient_list(s, m, M, cmap='bwr', low=0, high=0):
    """Method that can be used to apply contidional formatting to whole list
    
    See :func:`my_table_display` for usage example
    """
    rng = M - m
    low = m - (rng * low)
    high = M + (rng * high)
    cm = shifted_color_map(vmin=low, vmax=high, cmap=cmap)
    norm = colors.Normalize(low, high)
    normed = norm(s.values)
    c = [colors.rgb2hex(x) for x in cm(normed)]
    return ['background-color: %s' % color for color in c]

def my_table_display(df, cmap="bwr", low=0.5, high=0.5, c_nans="white",
                     num_digits=2):
    """Custom display of table 
    
    Currently applies conditional color formatting with a shifted colormap
    (cf. :func:`shifted_color_map`) and number formatting of a dataframe.
    
    Note
    ----
    Only for viewing
    
    Parameters
    ----------
    df : DataFrame
        table to be displayed
    cmap : 
        string ID of a diverging colormap (center colour preferably white)
    low : float
        "stretch" factor for colour / range mapping for lower end of value 
        range (increase and coulours of left end get less intense)
    high : float
        "stretch" factor for colour / range mapping for upper end of value 
        range (increase and coulours of left end get less intense)
    c_nans : str
        colour of NaN values
    num_digits : int
        number of displayed digits for table values
        
    Returns
    -------
    Styler
        pandas Styler object ready for display
    """
    num_fmt = "{:." + str(num_digits) + "f}"
    return df.style.apply(_background_gradient_list,
                          cmap=cmap,
                          m=df.min().min(),
                          M=df.max().max(),
                          low=low, 
                          high=high).highlight_null(c_nans).format(num_fmt)
    
def exponent(num):
    """Get exponent of input number
        
    Parameters
    ----------
    num : :obj:`float` or iterable
        input number
    
    Returns
    -------
    :obj:`int` or :obj:`ndarray` containing ints
        exponent of input number(s)
        
    Example
    -------
    >>> from pyaerocom.mathutils import exponent
    >>> exponent(2340)
    3
    """
    return np.floor(np.log10(abs(np.asarray(num)))).astype(int)

def load_varconfig_ini(fpath):
    cfg = ConfigParser(allow_no_value=True)
    cfg.read(fpath)
    sections = cfg.sections()
    vals_raw = cfg._sections
    result = od()
    for key in sections:
        result[key] = list(vals_raw[key].keys())
    return result
        
def rename_index_dataframe(df, level=0, new_names=None, prefix=None, 
                           lead_zeros=1):
    
    if prefix is None:
        prefix = ""
    #names = sorted(df.index.get_level_values(level).value_counts().index.values)
    names = df.index.get_level_values(level).value_counts().index.values
    if new_names is not None and len(new_names) == len(names):
        repl = new_names
    else:
        nums = range(len(names))
        repl = []
        for num in nums:
            num_str = str(num+1).zfill(lead_zeros)
            repl.append("{}{}".format(prefix, num_str))
    
    d = od(zip(names, repl))
    
    df.rename(index=d, level=0, inplace=True)
    mapping = od()
    for k, v in d.items():
        mapping[v] = k
    df.test_case = pd.Series(mapping)
    return df


 
def read_and_merge_all(file_list, var_info_dict=None, 
                       replace_runid_prefix=None, verbose=False):
    """Read and merge list of result files into one pandas Dataframe
    
    Loops over files in input filelist and calls :func:`read_file_custom` which
    returns a pandas.Dataframe, that is appended to a list, which is ultimately
    concatenated into one big, Dataframe. Run IDs (Test case IDs) may be 
    replaced using input parameter replace_runid_prefix (since they tend to 
    be long and mess up the readability of the table preview)
    
    Parameters
    ----------
    file_list : list
        list containing valid file paths
    var_info_dict : dict
        optinal dictionary that contains description strings for each of the 
        variables (e.g. retrieved using :func:`read_var_info_michaels_excel`)
    replace_runid_prefix : str, optional
        string prefix for specifying index of individual Runs / files 
        (corresponds to test case IDs, e.g. N1850_f09_tn14_230218) 
        will not be used as index, but instead a unique numerical identifier 
        for each run. E.g. if input parameter `file_list` contains 3 files, 
        e.g.:
        
            `file_list = [N1850_f09_tn14_230218 (yrs 1-20).webarchive,
                          N1850_f19_tn14_r227_ctrl (yrs 185-215).webarchive,
                          N1850_f19_tn14_r227_ctrl (yrs 310-340).webarchive]`
            
        and parameter `replace_runid_prefix="Run"`, then two indices will be 
        created, i.e. "Run1" -> test case N1850_f09_tn14_230218
                 and  "Run2" -> N1850_f19_tn14_r227_ctrl (two files)
    verbose : bool
        if True, print output (defaults to False)
        
    Returns
    -------
    Dataframe
        pandas data frame containing concatenated results from individual 
        files. NOTE: the returned Dataframe contains a custom attribute 
        test_case that is a mapping of run IDs in table preview and 
        corresponding test_case IDs (only relevant if input parameter 
        replace_runid_prefix is specified)
    
    """
    dfs = []
    lead_zeros = exponent(len(file_list)) + 1
    for fpath in file_list:
        try:
            dfs.append(read_file_custom(fpath, var_info_dict, 
                                        verbose=verbose))
        except:
            print("Failed to read file {}".format(fpath))
    df = pd.concat(dfs)
    if replace_runid_prefix:
        df = rename_index_dataframe(df, level=0, prefix=replace_runid_prefix,
                                    lead_zeros=lead_zeros)
    else:
        df.test_case = pd.Series()
    #df.sort_index(inplace=True)
    #df.sortlevel(inplace=True)
    return df


def read_file_custom(fpath, var_info_dict=None, run_id=None, verbose=False):
    """Custom ASCII conversion method 
    
    Parameters
    ----------
    fpath : str
        path to file location
    var_info_dict : dict
        optinal dictionary that contains description strings for each of the 
        variables (e.g. retrieved using :func:`read_var_info_michaels_excel`)
    run_id : str, int or dict
        string or integer that may be used as index specifying the model run 
        and that should be used in the Dataframe for the index specifying the 
        model run (only relevant if multiple files are loaded and concatenated 
        into one dataframe). If None, the "TEST CASE" ID, specified in the 
        file header is used for the index.
    verbose : bool
        if True, print output (defaults to False)
        
    Returns
    -------
    Dataframe 
        pandas data frame ready for further analysis. NOTE: the returned 
        Dataframe contains a custom attribute test_case that maps run_id and
        test_case and may be used to access the model run identifier (only 
        relevant if custom ID for run is specified using input parameter 
        `run_id`)
    """
    with open(fpath, encoding="latin-1") as f:
        lines = f.read().splitlines()
    test_case = ''
    control_case = ''
    
    if not var_info_dict:
        var_info_dict = {}
    data = []

    in_data = False
    problem_vars = ["FSNTOAC_CERES-EBAF","FSNTOA_CERES-EBAF"]
    obs_zero_val = ["RESTOM", "RESSURF"]
    for line in lines:
        line.strip()
        
        if "TEST CASE:" in line:
            spl = line.split("TEST CASE:")[1].strip().split("(yrs ")
            test_case = spl[0].strip()
            if not run_id:
                run_id = test_case
            years = spl[1].split(")")[0]
            header = ["Run", "Years", "Variable", "Description", "Flag",
                      "Model", "Obs", "Bias", "RMSE"]
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
                line_data.extend([run_id, years, _var])
                try:
                    var_info = var_info_dict[_var]
                    if not var_info:
                        raise ValueError("No description available for "
                                         "variable {}".format(_var))
                    flag = True
                except:
                    var_info = ""
                    flag = False
                line_data.extend([var_info, flag])
                #Variable is RESTOM or RESSURF
                if _var in obs_zero_val:
                    val = float(spl[0])
                    #
                    line_data.extend([val, 0, val, np.nan])
                else:
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
    df = pd.DataFrame(data, columns=header)
    df.set_index(["Run", "Years", "Variable", "Description"], 
                 inplace=True)
    df.test_case = test_case
    if verbose:
        print("Test case: {}".format(test_case))
        print("Control case: {}".format(control_case))
    return df

def save_varinfo_dict_csv(data, fpath):
    """Save dictionary containing"""
    with open(fpath, 'w') as f:
        for key, value in data.items():
            f.write('%s, %s\n' % (key, value))
    f.close()

def load_varinfo_dict_csv(fpath):
    """Load variable info from csv
    """
    data = od()
    if not os.path.exists(fpath):
        raise IOError("File not found {}".format(fpath))
    try:
        with open(fpath) as f:
            for item in f:
                if ',' in item:
                    key, val = item.split(',')
                    
                    data[key.strip()] = val.strip()
                else:
                    pass # deal with bad lines of text here
    except Exception as e:
        raise IOError("Failed to load info from file. Error: {}".format(repr(e)))
    return data

def read_var_info_michaels_excel(xlspath):
    """Read short description strings for variables
    
    The strings are available for some of the variables in Michaels analysis
    excel table (column 3, sheet "DATA")
    
    Parameters
    ----------
    xlspath : location of excel spreadsheet
    
    Returns
    -------
    dict 
        dictionary containing all variable names (keys) and corresponding
        description strings (if applicable, else empty string)
    """
    workbook = xlrd.open_workbook(xlspath)
    sheet = workbook.sheet_by_name('DATA')
    
    result = od()
    for i, cell in enumerate(sheet.col(1)):
        if cell.value:
            result[cell.value] = sheet.col(2)[i].value
       
    return result

def load_varinfo(try_path, catch_excel_michael=None):
    """Read short description strings for variables
    
    Load long names of variables. Tries to load information from csv file
    specified by input parameter ``try_path`` and if this fails, the information
    is imported from Michaels Excel table, in which case the csv file will be 
    created at location ``try_path``.
    
    Parameters
    ----------
    try_path : str
        location of csv file
    catch_excel_michael : str
        path to Michaels Excel (optional)
    
    Returns
    -------
    dict 
        dictionary containing all variable names (keys) and corresponding
        description strings (if applicable, else empty string)
    """
    if not os.path.exists(try_path):
        print("File {} does not exist. Loading variable info from "
              "Excel at {}".format(try_path, catch_excel_michael))
        var_info_dict = read_var_info_michaels_excel(catch_excel_michael)
        save_varinfo_dict_csv(var_info_dict, try_path)
        return var_info_dict
    return load_varinfo_dict_csv(try_path)
    
    
if __name__ == "__main__":
    
    data_dir = "./data/michael_ascii_read/"
    files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if 
             f.endswith(".webarchive")]
    
    df0 = read_file_custom(files[0])
    df1 = read_file_custom(files[1])
    
    concat = pd.concat([df0, df1], axis=0)
    df0.head()
    
    from glob import glob
    
    xlspath = glob("./data/michael_ascii_read/*.xlsx", recursive=True)[0]
    
    var_info = read_var_info_michaels_excel(xlspath)
    
    
    save_varinfo_dict_csv(var_info, 'data/var_info.csv')
    
    df2 =  read_file_custom(files[3], run_id="Run1")
    
    df_all = read_and_merge_all(files)
    
    test_cases = df_all.index.get_level_values(0).value_counts().index.values
    
    repl = ["Run{}".format(x+1) for x in range(len(test_cases))]
    
    d = dict(zip(test_cases, repl))
    print(d)
    
    df_all.rename(index=d, level=0, inplace=True)

    df_all.head()    
    
    
    df11 = read_and_merge_all(files, replace_runid_prefix="Bla")
    
    var_info_load = load_varinfo_dict_csv('data/var_info.csv')
    
    
    
    