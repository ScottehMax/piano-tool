import time
from uuid import uuid4

import fluidsynth
import mido


notes = []
for octave in range(1, 9):
    notes += [f'{note}{octave}' for note in ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']]

total_notes = len(notes)


class Note:
    def __init__(self, name, start_time, end_time):
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.id = uuid4()
    
    def __repr__(self):
        return f'Note({self.name}, {self.start_time}, {self.end_time})'
    
    @property
    def duration(self):
        return self.end_time - self.start_time
    
    @property
    def value(self):
        return note_name_to_value(self.name)


def note_name_to_value(note_name):
    # note: A0 is 21, C8 is 108
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    note = note_name[:-1]
    octave = int(note_name[-1])
    return notes.index(note) + 12 * octave


def note_value_to_name(note_val):
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = note_val // 12 - 1
    note = notes[note_val % 12]
    return note + str(octave)


def notes_to_messages(notes):
    messages = []

    scale = 6

    # Add notes. the "time" in the mido.Message constructor is delta time, 
    # which is the time between the current message and the next message.
    for i, note in enumerate(notes):
        val = note_name_to_value(note.name)

        # message format: (time, on or off, value, velocity)
        messages.append((note.start_time*scale, 'note_on', val, 90))
        messages.append((note.end_time*scale, 'note_off', val, 90))
    
    return messages

def export_to_midi(notes, tempo):
    # Create a new MIDI file
    mid = mido.MidiFile()

    # Add a track to the MIDI file
    track = mido.MidiTrack()

    # get tempo
    tempo_val = tempo.get()
    tempo_val = int(tempo_val)
    tempo_val = 60000000 // tempo_val # convert to microseconds per beat

    # Add the tempo to the track
    track.append(mido.MetaMessage('set_tempo', tempo=tempo_val))

    # Add the track to the MIDI file
    mid.tracks.append(track)

    messages = notes_to_messages(notes)

    # Sort the messages by time
    messages.sort(key=lambda m: (m[0]))

    # Add the messages to the track
    for i, message in enumerate(messages):
        delta = message[0] - messages[i-1][0] if i > 0 else message[0]
        track.append(mido.Message(message[1], note=message[2], velocity=message[3], time=delta))

    # Save the MIDI file
    mid.save('test.mid')

    print('Saved MIDI file')


def open_synth():
    fs = fluidsynth.Synth(samplerate=44100.0)
    fs.start()

    sfid = fs.sfload("synthgms.sf2")
    fs.program_select(0, sfid, 0, 0)

    return fs


def convert_to_fluidsynth(notes, tempo, playing, synth=None):
    messages = notes_to_messages(notes)

    # Sort the messages by time
    messages.sort(key=lambda m: (m[0]))

    if synth is None:
        synth = fluidsynth.Synth(samplerate=44100.0)
        synth.start()

        sfid = synth.sfload("synthgms.sf2")
        synth.program_select(0, sfid, 0, 0)

    playing.set("Playing")

    for i, message in enumerate(messages):
        if playing.get() == "Playing":
            delta = message[0] - messages[i-1][0] if i > 0 else message[0]
            # take into account the tempo
            delta = delta * 120 / tempo.get()
            time.sleep(delta / 1000)
            if message[1] == 'note_on':
                synth.noteon(0, message[2], message[3])
            else:
                synth.noteoff(0, message[2])
    
    # print('Finished playing')
    playing.set("Stopped")