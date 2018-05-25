import os
from collections import OrderedDict as od
import ipywidgets as ipw
from copy import deepcopy
import pandas as pd
import traitlets
from tkinter import Tk, filedialog
import helper_funcs as helpers
from traceback import format_exc
import numpy as np

### WORKING

class SaveAsButton(ipw.Button):
    """A file widget that leverages tkinter.filedialog.
    
    Based on and modified from ``SelectFilesButton`` (see below) or here: 
        
    https://codereview.stackexchange.com/questions/162920/file-selection-button-for-jupyter-notebook
    
    """

    def __init__(self, save_dir=None):
        super(SaveAsButton, self).__init__()
        # Add the selected_files trait
        self.add_traits(files=traitlets.traitlets.List())
        
        if not save_dir:
            save_dir = os.getcwd()
        self.save_dir = save_dir
        # Create the button.
        self.description = "Save as"
        self.icon = "square-o"
        self.style.button_color = "orange"
        self.file_name = ""
        # Set on click behavior.
        self.on_click(self.save_as)


    def save_as(self, b):
        """Generate instance of tkinter.asksaveasfilename

        Parameters
        ----------
        b : obj:
            An instance of ipywidgets.widgets.Button 
        """
        # Create Tk root
        root = Tk()
        # Hide the main window
        root.withdraw()
        # Raise the root to the top of all windows.
        root.call('wm', 'attributes', '.', '-topmost', True)
        # List of selected fileswill be set to b.value
        self.file_name = filedialog.asksaveasfilename(initialdir=self.save_dir,
                                                      title = "Save as",
                                                      filetypes = (("csv files","*.csv"),("all files","*.*")))

        self.description = "Files Selected"
        self.icon = "check-square-o"
        self.style.button_color = "lightgreen"
        
class TableView(object):        
    _base_layout = ipw.Layout(flex='0 1 auto', width='200px')
    _btn_width = "75px"
    def __init__(self, df, save_dir=None, **plot_settings):
        
        if save_dir is None:
            save_dir = os.getcwd()
        
        self.save_as_funcs = dict(csv = self.save_csv, 
                                  xlsx = self.save_xlsx)
        self.save_dir = save_dir
        self.df = df
        self.df_edit = self.check_shape_init(df)
        
        self.disp_settings = od(cmap="bwr",
                                cmap_shifted=True,)
        self.disp_table = ipw.Output()
        self.output = ipw.Output()
        self.init_layout()
        self.disp_current()
        
        self.disp_settings.update(plot_settings)
        
    @property
    def column_names(self):
        return list(self.df_edit.columns)
    
    @property
    def index_level_names(self):
        return self.df_edit.index.names
    
    @property
    def index_level_col_names(self):
        return self.df_edit.columns.names[1:]
    
    def init_layout(self):
        # create widgets
        btn_reset = ipw.Button(description = "Reset", layout=ipw.Layout(width=self._btn_width))
        btn_reset.on_click(self.on_reset)
        
        # COLUMN TO INDEX
        col2idx_header = ipw.Label("Column to index")
        col2idx_descr = ipw.Label("Add selected columns to Multiindex")
        self.col2idx_select =  ipw.SelectMultiple(description='', 
                                                  options=self.column_names, 
                                                  value=(), 
                                                  layout=self._base_layout)
        col2idx_btn_apply = ipw.Button(description = "Add", layout=ipw.Layout(width=self._btn_width))
        col2idx_btn_apply.on_click(self.on_add_col)
        col2idx_btn_apply.style.button_color = 'lightgreen'
        
        col2idx_layout = ipw.VBox([col2idx_header,
                                   col2idx_descr,
                                   self.col2idx_select,
                                   ipw.HBox([btn_reset, col2idx_btn_apply])])
        
        # UNSTACKING
        unstack_header = ipw.Label("Unstack index")
        unstack_descr = ipw.Label("Put selected indices into columns")
        self.unstack_select =  ipw.SelectMultiple(description='', 
                                                  options=self.index_level_names, 
                                                  value=(), 
                                                  layout=self._base_layout)
        unstack_btn_apply = ipw.Button(description = "Apply", layout=ipw.Layout(width=self._btn_width))
        unstack_btn_apply.on_click(self.on_unstack)
        unstack_btn_apply.style.button_color = 'lightgreen'
        
        unstack_layout = ipw.VBox([unstack_header,
                                   unstack_descr,
                                   self.unstack_select,
                                   ipw.HBox([btn_reset, unstack_btn_apply])])
        
        
        # STACKING
        stack_header = ipw.Label("Stack index")
        stack_descr = ipw.Label("Put selected indices into rows")
        self.stack_select =  ipw.SelectMultiple(description='', 
                                                  options=self.index_level_col_names,
                                                  value=(), 
                                                  layout=self._base_layout)
        stack_btn_apply = ipw.Button(description = "Apply", layout=ipw.Layout(width=self._btn_width))
        stack_btn_apply.on_click(self.on_stack)
        stack_btn_apply.style.button_color = 'lightgreen'
        
        stack_layout = ipw.VBox([stack_header,
                                 stack_descr,
                                 self.stack_select,
                                 ipw.HBox([btn_reset, stack_btn_apply])])
        
        ### Further options
        opts = []
        save_as_btn = ipw.Button(description="Save as", 
                                tooltip="Save current Dataframe as file",
                                layout=ipw.Layout(width=self._btn_width))
        save_as_btn.style.button_color = 'lightgreen'
        save_as_btn.on_click(self.on_saveas)
        
        opts.append(save_as_btn)
        
        opts_layout = ipw.VBox(opts)
        
        
        edit_ui = ipw.HBox([col2idx_layout, 
                            unstack_layout, 
                            stack_layout,
                            opts_layout])
        
        
        
        self.layout = ipw.VBox([edit_ui, 
                                self.disp_table,
                                self.output])
    
        
        
    def on_add_col(self, b):
        var_names = list(self.col2idx_select.value)
        self.add_to_index(var_names)
        self.update_ui()
    
    def on_unstack(self, b):
        level_names = list(self.unstack_select.value)
        self.unstack(level_names)
        self.update_ui()
        
    def on_stack(self, b):
        level_names = list(self.stack_select.value)
        self.stack(level_names)
        self.update_ui()
        
    def on_saveas(self, b):
        self.save_as()

        
    def on_reset(self, b):
        self.reset()
        self.update_ui()

                                   
    def update_ui(self):
        """Recreate user interface"""
        if isinstance(self.df_edit.columns, pd.MultiIndex):
            self.col2idx_select.options = ("N/A", "Current dataframe is unstacked")
            self.col2idx_select.disabled = True
        else:
            self.col2idx_select.options = self.column_names
            self.col2idx_select.value=()
            self.col2idx_select.disabled = False
        
        self.unstack_select.options = self.index_level_names
        self.unstack_select.value = ()
        
        self.stack_select.options = self.index_level_col_names
        self.stack_select.value = ()
        
        self.disp_table.clear_output()
        self.disp_current()
        
    def check_shape_init(self, df):
        if isinstance(df.columns, pd.MultiIndex):
            #print("Initial Dataframe is unstacked, stacking back")
            return helpers.stack_dataframe_original_idx(df)
        return deepcopy(df)
    
    def add_to_index(self, var_names):
        if isinstance(var_names, str):
            var_names = [var_names]
        for item in var_names:
            self.df_edit = self.df_edit.set_index([self.df_edit.index, item])
    
    def unstack(self, level_names):
        self.df_edit = self.df_edit.unstack(level_names)
        
    def stack(self, level_names):
        self.df_edit = helpers.stack_dataframe(self.df_edit, level_names)
        
    def reset(self):
        self.df_edit = self.check_shape_init(self.df)
        
    def disp_current(self):
        #self.output.append_display_data(ipw.Label("PREVIEW current selection", fontsize=22))
        preview = helpers.my_table_display(self.df_edit)
        self.disp_table.append_display_data(self.df_edit.head().style.set_caption("PREVIEW"))
        #self.output
        
    def save_csv(self, fpath):
        self.df_edit.to_csv(fpath)
    
    def save_xlsx(self, fpath):
        writer = pd.ExcelWriter(fpath)
        self.df_edit.to_excel(writer)
        writer.save()
        writer.close()
        
        
    def save_as(self):
        """Generate instance of tkinter.asksaveasfilename
        """
        # Create Tk root
        root = Tk()
        # Hide the main window
        root.withdraw()
        # Raise the root to the top of all windows.
        root.call('wm', 'attributes', '.', '-topmost', True)
        # List of selected fileswill be set to b.value
        filename = filedialog.asksaveasfilename(initialdir=self.save_dir,
                                                title = "Save as",
                                                filetypes = (("csv files","*.csv"),
                                                             ("Excel files","*.xlsx")))

        msg = "Could not save {}. Invalid file type".format(filename)
        for ftype, func in self.save_as_funcs.items():
            if filename.lower().endswith(ftype):
                try:
                    func(filename)
                    msg = "Succesfully saved: {}".format(filename)
                except Exception as e:
                    msg = ("Failed to save {}. Error {}".format(filename, repr(e)))
        
        self.output.append_display_data(msg)
      
    def __call__(self):
        return self.layout
    
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
        self.apply_changes()
        
    @property
    def names(self):
        #return sorted(self.df.index.get_level_values(self.level).unique().values)
        return self.df.index.get_level_values(self.level).unique().values
    @property
    def df_edit(self):
        return deepcopy(self._df_edit)
    
    def init_widgets(self):
        
        self.btn_apply = ipw.Button(description='Apply')
        self.btn_apply.style.button_color = "lightgreen"
        
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
    def __init__(self, df, level, preconfig_file=None, default_group=None):
        #df.sort_index(inplace=True)
        self.df = df
        self._df_edit = df
        self.level = level
        
        self.groups = od()
        self.groups["flagged"] = self.flagged_vars
        if preconfig_file:
            self.groups.update(helpers.load_varconfig_ini(preconfig_file))
        if default_group is None:
            default_group = "flagged"
        
        if not default_group in self.groups:
            raise ValueError("No default group with ID {} in file {}".format(default_group, preconfig_file))
            
        self.default_selection = self.groups[default_group]
        
        self.vals = self.df.index.get_level_values(self.level).unique().values
        
        
        self._base_layout = ipw.Layout(flex='0 1 auto', height='250px', min_height='250px', width='auto')
    
        self.init_widgets()
        self.init_actions()
        self.init_layout()
        
        self.select_current_group()
        self.print_current(1)
        self.crop_selection()
        self.disp_current()
        
        
    
    @property
    def df_edit(self):
        return deepcopy(self._df_edit)
    
    @property
    def flagged_vars(self):
        return list(self.df[self.df.Flag].index.get_level_values(self.level).unique().values)
    
    def init_widgets(self):
        
        self.btn_unselect_all = ipw.Button(description='Unselect all')
        self.btn_select_all = ipw.Button(description='Select all')
        self.btn_flagged = ipw.Button(description="Flagged")
        self.btn_apply = ipw.Button(description='Apply')
        self.btn_apply.style.button_color = 'lightgreen'

        self.var_selector = ipw.SelectMultiple(description='', 
                                               options=self.vals, 
                                               value=self.flagged_vars, 
                                               min_width='150px',
                                               layout=self._base_layout)
        
        self.current_disp = ipw.Textarea(value='', 
                                         description='', 
                                         disabled=True, 
                                         layout=self._base_layout)
        
        #groups = [key for key, val in self.groups.items()]
        
        self.group_selector = ipw.Dropdown(options=self.groups,
                                           value=self.default_selection,
                                            description='',
                                            disabled=False,)
        #self.output = ipw.Output()
        
    def init_actions(self):
        #what happens when the state of the selection is changed (display current selection)
        self.var_selector.observe(self.print_current)
        self.group_selector.observe(self.on_change_dropdown)
        #what happens when buttons are clicked
        self.btn_select_all.on_click(self.on_select_all_vars_clicked)
        self.btn_unselect_all.on_click(self.on_unselect_all_vars_clicked)
        self.btn_apply.on_click(self.on_click_apply)
    
    def init_layout(self):
        
        self.btns = ipw.VBox([self.btn_select_all, 
                              self.btn_unselect_all,
                              ipw.Label(),
                              self.btn_apply])
    
        self.edit_area = ipw.HBox([ipw.VBox([ipw.Label("Predefined"), self.group_selector]),
                                   ipw.VBox([ipw.Label("Index level {}".format(self.level)), self.var_selector]), 
                                   ipw.VBox([ipw.Label("Current selection"), self.current_disp]), 
                                   self.btns])
        
        self.layout = ipw.VBox([self.edit_area, self.output])
    
    def on_unselect_all_vars_clicked(self, b):
        self.unselect_all()
    
    def on_select_all_vars_clicked(self, b):
        self.select_all()
    
    def on_change_dropdown(self, b):
        self.select_current_group()
        
    def unselect_all(self):
        self.var_selector.value = ()
    
    def select_all(self):
        self.var_selector.value = self.var_selector.options
    
    def select_current_group(self):
        self.var_selector.value = self.group_selector.value
        
    def disp_current(self):
        self.output.clear_output()
        #self.output.append_display_data(ipw.Label("PREVIEW current selection", fontsize=22))
        self.output.append_display_data(self._df_edit.head().style.set_caption("PREVIEW HEAD"))
        self.output
        
    def crop_selection(self):
        try:
            self._df_edit = helpers.crop_selection_dataframe(self.df, 
                                                             self.var_selector.value, 
                                                             levels=self.level)
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
        
        self.btn_save.style.button_color = "lightgreen"
        
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
        helpers.save_varinfo_dict_csv(self.var_dict, self.csv_loc)
        
    def load_csv(self):
        if self.csv_loc is None or not os.path.exists(self.csv_loc):
            raise IOError("Please provide path to csv file")
        try:
            self.var_dict = helpers.load_varinfo_dict_csv(self.csv_loc)
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
    
    

### DOWNLOADED
        
class SelectFilesButton(ipw.Button):
    """A file widget that leverages tkinter.filedialog.
    
    
    Downloaded here: https://codereview.stackexchange.com/questions/162920/file-selection-button-for-jupyter-notebook
    
    """

    def __init__(self):
        super(SelectFilesButton, self).__init__()
        # Add the selected_files trait
        self.add_traits(files=traitlets.traitlets.List())
        # Create the button.
        self.description = "Select Files"
        self.icon = "square-o"
        self.style.button_color = "orange"
        # Set on click behavior.
        self.on_click(self.select_files)

    @staticmethod
    def select_files(b):
        """Generate instance of tkinter.filedialog.

        Parameters
        ----------
        b : obj:
            An instance of ipywidgets.widgets.Button 
        """
        # Create Tk root
        root = Tk()
        # Hide the main window
        root.withdraw()
        # Raise the root to the top of all windows.
        root.call('wm', 'attributes', '.', '-topmost', True)
        # List of selected fileswill be set to b.value
        b.files = filedialog.askopenfilename(multiple=True)

        b.description = "Files Selected"
        b.icon = "check-square-o"
        b.style.button_color = "lightgreen"
        
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

### UNDER DEVELOPMENT
class SelectVariableNew(object):
    output = ipw.Output()
    def __init__(self, df, num_cols=3):
        #df.sort_index(inplace=True)
        self.df = df
        #self.vals = tuple(self.df.index.levels[2].values)
        self.vals = self.df.index.get_level_values("Variable").unique().values
        self._df_edit = df
        self.num_cols = num_cols
        self.init_widgets()
        self.init_actions()
        self.init_layout()
        
        #self.print_current(1)
        self.highlight_selection(1)
        #self.crop_selection()
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
        self.btn_apply.style.button_color = 'lightgreen'
        
        self.items = []
        self.input_fields = []
    
        for num, name in enumerate(self.vals):
            ipt = ipw.Button(description=name, disabled=True, layout=ipw.Layout(width='150px'))
            order = ipw.Text(value=str(num+1), disabled=False, layout=ipw.Layout(width='50px'))
            order.observe(self.on_change_input_field)
            self.items.append(ipt)
            self.input_fields.append(order)
            
        #self.output = ipw.Output()
    
    def init_actions(self):
        #what happens when the state of the selection is changed (display current selection)
        #self.var_selector.observe(self.print_current)
        #what happens when buttons are clicked
        self.btn_select_all.on_click(self.on_select_all_vars_clicked)
        self.btn_unselect_all.on_click(self.on_unselect_all_vars_clicked)
        self.btn_flagged.on_click(self.on_flagged_clicked)
        self.btn_apply.on_click(self.on_click_apply)
    
        
    def init_layout(self):
        
        self.btns = ipw.HBox([self.btn_select_all, 
                              self.btn_unselect_all,
                              self.btn_flagged,
                              self.btn_apply])
        
        self.init_input_area()
        
        self.layout = ipw.VBox([self.btns, self.edit_area, self.output])
        
    def init_input_area(self):
        
        num_cols = self.num_cols
        items = self.items
        input_fields = self.input_fields
    
        col_vals = np.array_split(np.arange(len(items)), num_cols)
        
        cols = []
        for ival in col_vals:
            col_rows = []
            for val in ival:
                col_rows.append(ipw.HBox([items[val], input_fields[val]]))
            cols.append(ipw.VBox(col_rows))
            
        self.edit_area = ipw.HBox(cols)

    
    def on_unselect_all_vars_clicked(self, b):
        self.unselect_all()
    
    def on_select_all_vars_clicked(self, b):
        self.select_all()
    
    def on_flagged_clicked(self, b):
        self.select_flagged()
        
    def on_change_input_field(self, b):
        print(b.new.value)
        
    @property
    def current_order(self):
        nums = []
        for item in self.input_fields:
            nums.append(item.value)
        
    def highlight_selection(self, b):
        for i, item in enumerate(self.input_fields):
            try:
                int(item.value)
                self.items[i].style.button_color = "#e6ffee"
            except:
                self.items[i].style.button_color = "white"
                
    def unselect_all(self):
        pass
        #self.var_selector.value = ()
    
    def select_all(self):
        pass
        #self.var_selector.value = self.var_selector.options
    
    def select_flagged(self):
        pass
        #self.var_selector.value = self.flagged_vars
        
    def disp_current(self):
        self.output.clear_output()
        #self.output.append_display_data(ipw.Label("PREVIEW current selection", fontsize=22))
        self.output.append_display_data(self._df_edit.head().style.set_caption("PREVIEW HEAD"))
        self.output
        
    def crop_selection(self):
        raise NotImplementedError
    
    def on_click_apply(self, b):
        self.crop_selection()
        self.disp_current()
    
    def __repr__(self):
        return repr(self.layout)
    
    def __call__(self):
        return self.layout
    
class ReshapeAndSelect(object):
    """Widget that can be used to reshape a Dataframe and select individual data columns"""
    output = ipw.Output()
    def __init__(self, df):
        
        raise NotImplementedError()
        self.df = df
        self._df_edit = df
        
        self.index_names = df.index.names
        self.col_names = df.columns
    
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
        self.btn_apply.style.button_color = 'lightgreen'

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