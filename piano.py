import configparser
import os
import pickle
import random
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import time
import threading

from note import Note, notes, total_notes, export_to_midi, convert_to_fluidsynth, open_synth


note_width = 40
note_height = 20
grid_spacing = 20


class ColorScheme:
    def __init__(self, config_section):
        self.black_keys = '#' + config_section['black_keys']
        self.white_keys = '#' + config_section['white_keys']
        self.c_keys = '#' + config_section['c_keys']
        self.grid_bg_black = '#' + config_section['grid_bg_black']
        self.grid_bg_white = '#' + config_section['grid_bg_white']
        self.grid_lines_vert = '#' + config_section['grid_lines_vert']
        self.grid_lines_vert_4 = '#' + config_section['grid_lines_vert_4']
        self.grid_lines_vert_16 = '#' + config_section['grid_lines_vert_16']
        self.grid_lines_horiz = '#' + config_section['grid_lines_horiz']
        self.grid_lines_horiz_octave = '#' + config_section['grid_lines_horiz_octave']
        self.note = '#' + config_section['note']


config = configparser.ConfigParser()
config.read('config.ini')
scheme = config['Main']['color_scheme']
cs = ColorScheme(config[scheme])


class MenuControls(tk.Frame):
    def __init__(self, parent, synth):
        super().__init__(parent)
        self.parent = parent
        self.synth = synth
        self.create_widgets()

    def create_widgets(self):
        self.midi_export_btn = ttk.Button(self, text='Export as MIDI', command=self.export_as_midi)
        self.midi_export_btn.grid(row=0, column=0)

        self.reset_btn = ttk.Button(self, text='Reset', command=self.reset)
        self.reset_btn.grid(row=0, column=1)

        self.export_btn = ttk.Button(self, text='Export', command=self.export_notes)
        self.export_btn.grid(row=0, column=2)

        self.import_btn = ttk.Button(self, text='Import', command=self.import_notes)
        self.import_btn.grid(row=0, column=3)

        self.tempo_label = ttk.Label(self, text='Tempo')
        self.tempo_label.grid(row=0, column=4)

        self.tempo_var = tk.IntVar()
        self.tempo_var.set(120)
        self.tempo = ttk.Spinbox(self, from_=1, to=300, textvariable=self.tempo_var)
        self.tempo.grid(row=0, column=5)

        self.playing = tk.StringVar()
        self.playing.set("Stopped")

        self.play_btn = ttk.Button(self, text='Play', command=self.play)
        self.play_btn.grid(row=0, column=6)

        self.stop_btn = ttk.Button(self, text='Stop', command=self.stop)
        self.stop_btn.grid(row=0, column=7)

        self.playing_text = tk.Label(self, textvariable=self.playing)
        self.playing_text.grid(row=0, column=8)
    
    def export_as_midi(self):
        export_to_midi(self.parent.note_entry.notes, self.tempo_var)

    def reset(self):
        self.parent.note_entry.notes = []
        self.parent.note_entry.draw()

    def export_notes(self):
        extension = ".notes"
        filename = filedialog.asksaveasfilename(initialdir = os.getcwd(), title = "Select file", filetypes = (("note files", "*.notes"), ("All files", "*.*")))
        if filename:
            if not filename.endswith(extension):
                filename += extension
            with open(filename, 'wb') as f:
                pickle.dump(self.parent.note_entry.notes, f)
        else:
            messagebox.showerror("Error", "No file selected")

    def import_notes(self):
        filename = filedialog.askopenfilename(initialdir = os.getcwd(), title = "Select file", filetypes = (("note files", "*.notes"), ("All files", "*.*")))
        if filename:
            with open(filename, 'rb') as f:
                self.parent.note_entry.notes = pickle.load(f)
            self.parent.note_entry.draw()
        else:
            messagebox.showerror("Error", "No file selected")

    def play(self):
        # run in a separate thread so the GUI doesn't freeze
        t = threading.Thread(
            target=convert_to_fluidsynth,
            args=(self.parent.note_entry.notes, self.tempo_var, self.playing, self.synth),
        )
        t.start()

    def play_single_note(self, note):
        # run in a separate thread so the GUI doesn't freeze
        # create new note with the start time as 0
        new_note = Note(
            name=note.name,
            start_time=0,
            end_time=note.duration,
        )
        t = threading.Thread(
            target=convert_to_fluidsynth,
            args=([new_note], self.tempo_var, self.playing, self.synth),
        )
        t.start()
    
    def stop(self):
        self.playing.set("Stopped")
        

def pick_dumb_word():
    words = [
        'dumb',
        'stupid',
        'lousy',
        'bad',
        'terrible',
        'awful',
        'horrible',
        'garbage',
        'trash',
        'useless',
        'pointless',
        'worthless',
    ]
    return random.choice(words)


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f'{pick_dumb_word()} piano thing')
        self.create_widgets()

    def canvas_yviews(self, *args, **kwargs):
        # print(args, kwargs)
        self.piano_roll.yview(*args, **kwargs)
        self.note_entry.yview(*args, **kwargs)

    def create_widgets(self):
        self.frame = tk.Frame(self)
        self.frame.grid(row=0, column=0, sticky='nsew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.synth = open_synth()

        self.piano_roll = PianoRoll(self.frame, mainapp=self)
        self.piano_roll.grid(row=0, column=0, sticky='nsew')
        self.frame.grid_rowconfigure(0, weight=1)
        self.piano_roll.update()

        self.note_entry = NoteEntry(self.frame, mainapp=self, synth=self.synth)
        self.note_entry.grid(row=0, column=1, sticky='nsew')
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.note_entry.update()
        self.note_entry.draw()

        self.piano_roll.bind('<MouseWheel>', self.scroll_canvases)
        self.note_entry.bind('<MouseWheel>', self.scroll_canvases)

        self.vertical_scrollbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.canvas_yviews)
        self.vertical_scrollbar.grid(row=0, column=2, sticky='ns')

        self.horizontal_scrollbar = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL, command=self.set_x_offset)
        self.horizontal_scrollbar.grid(row=1, column=0, columnspan=2, sticky='ew')
        self.horizontal_scrollbar.set(0.25, 0.75)

        pr_bb = self.piano_roll.bbox('all')
        pr_width = pr_bb[2] - (pr_bb[0] if pr_bb[0] >= 0 else 0)
        pr_height = pr_bb[3] - (pr_bb[1] if pr_bb[1] >= 0 else 0) - 1
        ne_bb = self.note_entry.bbox('all')
        ne_width = ne_bb[2] - (ne_bb[0] if ne_bb[0] >= 0 else 0)
        ne_height = ne_bb[3] - (ne_bb[1] if ne_bb[1] >= 0 else 0) - 1

        self.piano_roll.configure(yscrollcommand=self.vertical_scrollbar.set)
        self.piano_roll.configure(scrollregion=(0, 0, pr_width, pr_height))
        self.note_entry.configure(yscrollcommand=self.vertical_scrollbar.set)
        self.note_entry.configure(scrollregion=(0, 0, ne_width, ne_height))


        self.menu_controls = MenuControls(self, synth=self.synth)
        self.menu_controls.grid(row=1, column=0)
    
    def scroll_canvases(self, event):
        self.piano_roll.yview_scroll(int(-1*(event.delta/120)), "units")
        self.note_entry.yview_scroll(int(-1*(event.delta/120)), "units")
        self.vertical_scrollbar.set(*self.piano_roll.yview())

    def set_x_offset(self, *args):
        if args[0] == 'scroll':
            direction = int(args[1])

            if args[2] == 'pages':
                direction *= 4
            
            self.note_entry.x_offset += 20 * direction
        # elif args[0] == 'moveto':
            # self.note_entry.x_offset -= int((0.25 - float(args[1])) * 10)
        
        if self.note_entry.x_offset < 0:
            self.note_entry.x_offset = 0
        
        self.note_entry.draw()




class PianoRoll(tk.Canvas):
    def __init__(self, parent, mainapp, **kwargs):
        super().__init__(parent, width=note_width, height=400, borderwidth=0, highlightthickness=0, **kwargs)
        self.parent = parent
        self.mainapp = mainapp
        self.draw()

    def draw(self):
        for i, note in enumerate(notes[::-1]):
            x = 0
            y = i * note_height
            fill = cs.black_keys if note[1] == '#' else cs.white_keys if note[0] != 'C' else cs.c_keys
            # print(note, x, y)
            self.create_rectangle(x, y, x+note_width, y+note_height+1, fill=fill)
            # if note is C, draw the note name
            if note[:-1] == 'C':
                # print(note, x, y)
                self.create_text(x+note_width - 4, y+note_height/2, text=note, anchor='e')



class NoteEntry(tk.Canvas):
    def __init__(self, parent, mainapp, synth=None, **kwargs):
        self.width = 800
        self.height = 400
        self.x_offset = 0
        self.new_note_width = 40
        self.synth = synth
        self.notes = []
        super().__init__(parent, width=self.width, height=self.height, borderwidth=0, highlightthickness=0, **kwargs)
        self.parent = parent
        self.mainapp = mainapp

        self.bind('<Button-1>', self.left_click_handler)
        self.bind('<B1-Motion>', self.left_click_drag_handler)
        self.bind('<Button-3>', self.right_click_handler)
        self.bind('<B3-Motion>', self.right_click_drag_handler)
        self.bind('<Motion>', lambda e: self.check_hover(e.x, e.y))
        self.bind('<Configure>', self.resize_canvas)

    def draw(self):
        self.delete('all')

        self.width = self.winfo_width()

        for i, note in enumerate(notes[::-1]):
            x = 0
            y = i * note_height
            fill = cs.grid_bg_black if note[1] == '#' else cs.grid_bg_white
            self.create_rectangle(0, y, self.width, y+note_height, fill=fill, width=0)

        # Draw the grid
        for x in range(0, self.width, grid_spacing):
            adjusted_x = x + self.x_offset
            fill = cs.grid_lines_vert_16 if adjusted_x % 64 == 0 else cs.grid_lines_vert_4 if adjusted_x % 16 == 0 else cs.grid_lines_vert
            self.create_line(x, 0, x, total_notes * note_height, fill=fill)
    
        for y in range(0, total_notes+1):
            y = y * note_height
            self.create_line(0, y, self.width, y, fill=cs.grid_lines_horiz_octave if y % (note_height * 12) == 0 else cs.grid_lines_horiz)

        # Draw the notes
        for note in self.notes:
            # handle notes that are partially on the screen
            if note.start_time < self.x_offset and note.end_time > self.x_offset:
                # draw what we can
                partial_width = note.end_time - self.x_offset
                note_x = 0
                note_y = total_notes * note_height - (notes.index(note.name) + 1) * note_height
                self.create_rectangle(note_x, note_y, partial_width, note_y+note_height, fill=cs.note)

                # add note text
                self.create_text(note_x + 6, note_y+note_height/2, text=note.name, anchor='w')

            elif note.start_time >= self.x_offset and note.start_time < self.x_offset + self.width:
                note_x = note.start_time - self.x_offset
                note_y = total_notes * note_height - (notes.index(note.name) + 1) * note_height
                self.create_rectangle(note_x, note_y, note_x+note.duration, note_y+note_height, fill=cs.note)

                # add note text
                self.create_text(note_x + 6, note_y+note_height/2, text=note.name, anchor='w')
        
    def add_note(self, note):
        self.notes.append(note)
        self.draw()
    
    def remove_note(self, note):
        self.notes.remove(note)
        self.draw()

    def is_inside_note(self, x, y):
        resize_gap = 8

        note_x = int((x // grid_spacing) * grid_spacing)
        note_y = int((y // grid_spacing) * grid_spacing)

        for note in self.notes:
            inside_note = (
                note_x >= note.start_time 
                and note_x < note.end_time 
                and note_y >= total_notes * note_height - (notes.index(note.name) + 1) * note_height
                and note_y <= total_notes * note_height - (notes.index(note.name) + 1) * note_height
            )
            if inside_note:
                # print(note_x, note.start_time, note.end_time, note.end_time - x)
                if note.end_time - x < resize_gap:
                    # print('resize')
                    return note, 'resize'
                else:
                    # print('move')
                    return note, 'move'
        else:
            return (False, False)

    def check_hover(self, x, y):
        x, y = x + self.canvasx(0) + self.x_offset, y + self.canvasy(0)

        note, action = self.is_inside_note(x, y)

        if note:
            if action == 'resize':
                self.config(cursor='sb_h_double_arrow')
            elif action == 'move':
                self.config(cursor='fleur')
        else:
            self.config(cursor='arrow')
    
    def resize_canvas(self, event):
        bb = self.bbox('all')
        if bb is not None:
            ne_width = bb[2] - (bb[0] if bb[0] >= 0 else 0)
            ne_height = bb[3] - (bb[1] if bb[1] >= 0 else 0) - 1
            self.config(scrollregion=(0, 0, ne_width, ne_height))
            self.update()
            self.draw()
    
    @staticmethod
    def left_click_handler(event):
        # print(event)

        canvas = event.widget

        orig_x, orig_y = event.x, event.y
        x, y = event.x + canvas.canvasx(0) + canvas.x_offset, event.y + canvas.canvasy(0)
        grid_x = int((x // grid_spacing) * grid_spacing)
        grid_y = int((y // grid_spacing) * grid_spacing)

        note, canvas.action = canvas.is_inside_note(x, y)

        if not note:
            note_name = notes[total_notes - grid_y // note_height - 1]
            note = Note(note_name, grid_x, grid_x+canvas.new_note_width)
            canvas.add_note(note)
            canvas.active_note = note
            canvas.action = 'move'
            canvas.active_note_offset = grid_x - note.start_time
            canvas.check_hover(orig_x, orig_y)
            canvas.config(cursor='fleur')
        else:
            canvas.active_note = note
            canvas.active_note_offset = grid_x - note.start_time
            canvas.new_note_width = note.duration

        canvas.mainapp.menu_controls.play_single_note(note)
        canvas.last_played_note = canvas.active_note.name
    
    @staticmethod
    def left_click_drag_handler(event):
        canvas = event.widget
        x, y = event.x + canvas.canvasx(0) + canvas.x_offset, event.y + canvas.canvasy(0)
        grid_x = int((x // grid_spacing) * grid_spacing)
        grid_y = int((y // grid_spacing) * grid_spacing)

        if canvas.active_note:
            # print(canvas.action)
            if canvas.action == 'move':
                duration = canvas.active_note.duration
                canvas.active_note.start_time = grid_x - canvas.active_note_offset
                if canvas.active_note.start_time < 0:
                    canvas.active_note.start_time = 0
                canvas.active_note.end_time = canvas.active_note.start_time + duration
                canvas.active_note.name = notes[total_notes - grid_y // note_height - 1]
                if canvas.active_note.name != canvas.last_played_note:
                    canvas.mainapp.menu_controls.play_single_note(canvas.active_note)
                    canvas.last_played_note = canvas.active_note.name
            elif canvas.action == 'resize':
                canvas.active_note.end_time = grid_x
                if canvas.active_note.duration <= 0:
                    canvas.active_note.end_time = canvas.active_note.start_time + 20
                canvas.new_note_width = canvas.active_note.duration
            canvas.draw()

    @staticmethod
    def right_click_handler(event):
        canvas = event.widget
        x, y = int(event.x + canvas.canvasx(0) + canvas.x_offset), int(event.y + canvas.canvasy(0))
        for note in canvas.notes:
            if note.start_time <= x <= note.end_time and note.name == notes[total_notes - y// note_height - 1]:
                canvas.remove_note(note)
                break
    
    @staticmethod
    def right_click_drag_handler(event):
        canvas = event.widget
        x, y = int(event.x + canvas.canvasx(0) + canvas.x_offset), int(event.y + canvas.canvasy(0))
        for note in canvas.notes:
            if note.start_time <= x <= note.end_time and note.name == notes[total_notes - y// note_height - 1]:
                canvas.remove_note(note)
                break


if __name__ == '__main__':
    app = MainApp()
    app.mainloop()