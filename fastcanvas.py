import tkinter as tk
from dataclasses import dataclass
from typing import Optional


@dataclass
class Rectangle:
    args: tuple
    kwargs: dict
    tk_id: Optional[int] = None

@dataclass
class Line:
    args: tuple
    kwargs: dict
    tk_id: Optional[int] = None

@dataclass
class Text:
    args: tuple
    kwargs: dict
    tk_id: Optional[int] = None


class FastCanvas(tk.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_rectangles = []
        self.active_lines = []
        self.active_texts = []
        self.inactive_rectangles = []
        self.inactive_lines = []
        self.inactive_texts = []

    @property
    def n_active_rectangles(self):
        return len(self.active_rectangles)

    @property
    def n_active_lines(self):
        return len(self.active_lines)

    @property
    def n_active_texts(self):
        return len(self.active_texts)

    def invalidate(self):
        """Sets all rectangles, lines, and texts to not be active,
        so they can be reused.
        """
        for rect in self.active_rectangles:
            self.itemconfigure(rect.tk_id, state=tk.HIDDEN)
        
        for line in self.active_lines:
            self.itemconfigure(line.tk_id, state=tk.HIDDEN)

        for text in self.active_texts:
            self.itemconfigure(text.tk_id, state=tk.HIDDEN)
        
        self.inactive_rectangles = self.active_rectangles
        self.active_rectangles = []
        self.inactive_lines = self.active_lines
        self.active_lines = []
        self.inactive_texts = self.active_texts
        self.active_texts = []

    def create_item(
        self, 
        item, 
        active_list, 
        inactive_list, 
        create_func,
        *args, 
        **kwargs
    ):
        if inactive_list:
            item = inactive_list.pop()
            item.args = args
            item.kwargs = kwargs
            self.itemconfigure(item.tk_id, state=tk.NORMAL)
            super().coords(item.tk_id, *args)
            super().itemconfig(item.tk_id, **kwargs)
            self.tag_raise(item.tk_id)  # draw order matters here...
        else:
            item = item(args, kwargs, create_func(*args, **kwargs))

        active_list.append(item)
        return item.tk_id

    def create_rectangle(self, *args, **kwargs):
        """Creates a rectangle. Tries to reuse old rectangles.
        
        If all rectangles are in use, creates a new one.
        """
        return self.create_item(Rectangle, self.active_rectangles, self.inactive_rectangles, super().create_rectangle, *args, **kwargs)

    def create_line(self, *args, **kwargs):
        """Creates a line. Tries to reuse old lines.
        
        If all lines are in use, creates a new one.
        """
        return self.create_item(Line, self.active_lines, self.inactive_lines, super().create_line, *args, **kwargs)
    
    def create_text(self, *args, **kwargs):
        """Creates a text. Tries to reuse old texts.
        
        If all texts are in use, creates a new one.
        """
        return self.create_item(Text, self.active_texts, self.inactive_texts, super().create_text, *args, **kwargs)
