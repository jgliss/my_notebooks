import os
from collections import OrderedDict as od
import ipywidgets as ipw
from copy import deepcopy
import pandas as pd
from helper_funcs import save_varinfo_dict_csv, load_varinfo_dict_csv
from traceback import format_exc

class IndexRenamer(object):
    output = ipw.Output()
    def __init__(self, df, level=0, suggestions=[]):
        self.df = df
        self._df_edit = df
        self.level = level
        
        self.suggestions = suggestions
      
        self.init_widgets()
        self.init_actions()
        self.init_layout()
        
        self.renamed_info = od()
        
    @property
    def names(self):
        #return sorted(self.df.index.get_level_values(self.level).unique().values)
        return self.df.index.get_level_values(self.level).unique().values
    @property
    def df_edit(self):
        return deepcopy(self._df_edit)
    
    def init_widgets(self):
        
        self.btn_apply = ipw.Button(description='Apply')
        self.btn_apply.style.button_color = "lime"
        
        self.input_rows = []
        self.input_fields = []
        
        for i, name in enumerate(self.names):
            try:
                val = self.suggestions[i]
            except:
                val = name
            ipt = ipw.Text(value=val, placeholder='Insert new name',
                            disabled=False, layout=ipw.Layout(width='300px'))
            row = ipw.HBox([ipw.Label(name, layout=ipw.Layout(width='300px')), ipt])
            self.input_fields.append(ipt)
            self.input_rows.append(row)
                                      
    def init_actions(self):
        #what happens when the state of the selection is changed (display current selection)
        self.btn_apply.on_click(self.on_click_apply)
        
    def init_layout(self):
        
        edit_area = ipw.HBox([ipw.VBox(self.input_rows), self.btn_apply])
        self.layout = ipw.VBox([edit_area, self.output])
        
    def on_click_apply(self, b):
        self.apply_changes()
        
    def disp_current(self):
        self.output.clear_output()
        #self.output.append_display_data(ipw.Label("PREVIEW current selection", fontsize=22))
        self.output.append_display_data(self._df_edit.style.set_caption("PREVIEW"))
        self.output
        
    def apply_changes(self):
        
        df = self.df 
        mapping = od()
        
        for i, name in enumerate(self.names):
            repl = str(self.input_fields[i].value)
            mapping[name] = repl
        self._df_edit = df.rename(index=mapping, level=self.level)
        
        self.disp_current()
        
    def __call__(self):
        return self.layout
    
class SelectVariable(object):
    output = ipw.Output()
    def __init__(self, df):
        #df.sort_index(inplace=True)
        self.df = df
        #self.vals = tuple(self.df.index.levels[2].values)
        self.vals = self.df.index.get_level_values("Variable").unique().values
        self._df_edit = df
        
        self.init_layout()
        self.init_widgets()
        self.init_actions()
        self.init_display()
        
        self.print_current(1)
        self.crop_selection()
        self.disp_current()
    
    @property
    def df_edit(self):
        return deepcopy(self._df_edit)
    
    @property
    def flagged_vars(self):
        return list(self.df[self.df.Flag].index.get_level_values("Variable").unique().values)
    
    def init_widgets(self):
        
        self.btn_unselect_all = ipw.Button(description='Unselect all')
        self.btn_select_all = ipw.Button(description='Select all')
        self.btn_flagged = ipw.Button(description="Flagged")
        self.btn_apply = ipw.Button(description='Apply')
        self.btn_apply.style.button_color = 'lime'

        self.var_selector = ipw.SelectMultiple(description="Variables", 
                                               options=self.vals, 
                                               value=self.flagged_vars, 
                                               min_width='150px',
                                               layout=self.box_layout)
        
        self.current_disp = ipw.Textarea(value='', 
                                         description='Current:', 
                                         disabled=True, 
                                         layout=self.box_layout)
        #self.output = ipw.Output()
        
    def init_actions(self):
        #what happens when the state of the selection is changed (display current selection)
        self.var_selector.observe(self.print_current)
        #what happens when buttons are clicked
        self.btn_select_all.on_click(self.on_select_all_vars_clicked)
        self.btn_unselect_all.on_click(self.on_unselect_all_vars_clicked)
        self.btn_flagged.on_click(self.on_flagged_clicked)
        self.btn_apply.on_click(self.on_click_apply)
        
    def init_layout(self):
        self.box_layout = ipw.Layout(flex='0 1 auto', height='250px', min_height='150px', width='auto')
        self.disp_layout = ipw.Layout(flex='0 1 auto', height='250px', min_height='150px', width='auto')
    
    def init_display(self):
        self.btns = ipw.VBox([self.btn_select_all, 
                              self.btn_unselect_all,
                              self.btn_flagged,
                              ipw.Label(),
                              self.btn_apply])
    
        self.edit_area = ipw.HBox([self.var_selector, 
                                   self.current_disp, 
                                   self.btns])
        
        self.layout = ipw.VBox([self.edit_area, self.output])
    
    def on_unselect_all_vars_clicked(self, b):
        self.unselect_all()
    
    def on_select_all_vars_clicked(self, b):
        self.select_all()
    
    def on_flagged_clicked(self, b):
        self.select_flagged()
        
    def unselect_all(self):
        self.var_selector.value = ()
    
    def select_all(self):
        self.var_selector.value = self.var_selector.options
    
    def select_flagged(self):
        self.var_selector.value = self.flagged_vars
        
    def disp_current(self):
        self.output.clear_output()
        #self.output.append_display_data(ipw.Label("PREVIEW current selection", fontsize=22))
        self.output.append_display_data(self._df_edit.head().style.set_caption("PREVIEW HEAD"))
        self.output
        
    def crop_selection(self):
        idx = pd.IndexSlice
        try:
            self._df_edit = self.df.loc[idx[:, :, self.var_selector.value, :], :]
        except Exception as e:
            print("WARNING: failed to extract selection.\nTraceback {}".format(format_exc()))
    
    def on_click_apply(self, b):
        self.crop_selection()
        self.disp_current()
        
    def print_current(self, b):
        s=""
        for item in self.var_selector.value:
            s += "{}\n".format(item)
        self.current_disp.value = s
    
    def __repr__(self):
        return repr(self.layout)
    
    def __call__(self):
        return self.layout
    
class EditDictCSV(object):
    """Widget that can be used to interactively edit a CSV file
    
    The CSV is supposed to be created from a "simple" dictionary with entries
    strings.
    """
    output = ipw.Output()
    def __init__(self, csv_loc):
        self.csv_loc = csv_loc
        self.load_csv()
            
        self.init_widgets()
        self.init_actions()
        self.init_layout()
    
    def init_widgets(self):
        
        self.btn_update = ipw.Button(description='Update',
                                     tooltip=('Updates the current dictionary based on values in text fields'
                                              '(for further analysis, use Save csv button to write to CSV)'))
        self.btn_reload = ipw.Button(description='Reload',
                                     tooltip='Reloads information from file var_info.csv')
        self.btn_save = ipw.Button(description='Update and save',
                                     tooltip='Updates current selection and writes to CSV')
        
        self.btn_save.style.button_color = "lime"
        
        self.input_rows = []
        self.input_fields = {}
        
        for name,  val in self.var_dict.items():
            ipt = ipw.Text(value=val, placeholder='Insert new name',
                            disabled=False, min_width="200px")
            row = ipw.HBox([ipw.Label(name, minwidth="200px"), ipt])
            self.input_fields[name] = ipt
            self.input_rows.append(row)  
            
    def init_actions(self):
        self.btn_update.on_click(self.on_click_update)
        self.btn_reload.on_click(self.on_click_load_csv)
        self.btn_save.on_click(self.on_click_save)
        
    def init_layout(self):
        
        vbox_buttons = ipw.VBox([self.btn_reload,
                                 self.btn_update,
                                 self.btn_save])
        self.layout = ipw.HBox([ipw.VBox(self.input_rows), vbox_buttons, 
                                self.output])
        
    def on_click_update(self, b):
        self.apply_changes()
    
    def on_click_load_csv(self, b):
        self.load_csv()
        self.update_info_fields()
        
    def on_click_save(self, b):
        self.save_csv()
    
    def save_csv(self):
        self.apply_changes()
        save_varinfo_dict_csv(self.var_dict, self.csv_loc)
        
    def load_csv(self):
        if self.csv_loc is None or not os.path.exists(self.csv_loc):
            raise IOError("Please provide path to csv file")
        try:
            self.var_dict = load_varinfo_dict_csv(self.csv_loc)
        except Exception as e:
            self.write_to_output(format_exc())
    
    def update_info_fields(self):
        for key, val in self.var_dict.items():
            self.input_fields[key].value = val
    
    def write_to_output(self, msg):
        self.output.append_display_data(msg)
        self.output
        
    def apply_changes(self):
        
        new = od()
        for key, edit in self.input_fields.items():
            new[key] = edit.value
        
        self.var_dict = new
        
    def __call__(self):
        return self.layout
    
class FileBrowser(object):
    """Widget for browsing files interactively
    
    The widget was downloaded and modified from here:
        
        https://gist.github.com/DrDub/6efba6e522302e43d055#file-selectfile-py
        
    """
    def __init__(self, path=None):
        if path is None:
            path = os.getcwd()
        self.path = path
        self._update_files()
        
    def _update_files(self):
        self.files = list()
        self.dirs = list()
        if(os.path.isdir(self.path)):
            for f in os.listdir(self.path):
                ff = self.path + "/" + f
                if os.path.isdir(ff):
                    self.dirs.append(f)
                else:
                    self.files.append(f)
                    
    def _update(self, box):
        
        def on_click(b):
            if b.description == '..':
                self.path = os.path.split(self.path)[0]
            else:
                self.path = self.path + "/" + b.description
            self._update_files()
            self._update(box)
        
        buttons = []
        if self.files:
            button = ipw.Button(description='..', background_color='#d0d0ff')
            button.on_click(on_click)
            buttons.append(button)
        for f in self.dirs:
            button = ipw.Button(description=f, background_color='#d0d0ff')
            button.on_click(on_click)
            buttons.append(button)
        for f in self.files:
            button = ipw.Button(description=f)
            button.on_click(on_click)
            buttons.append(button)
        box.children = tuple([ipw.HTML("<h2>%s</h2>" % (self.path,))] + buttons)
        
    def __call__(self):
        box = ipw.VBox()
        self._update(box)
        return box
    