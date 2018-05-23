import os
import ipywidgets as ipw

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
    