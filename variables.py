import random

import numpy as np
import sounddevice as sd

import note
import overtone as ov
from chord import chord
from random_matrix import *
from overtone_matrix import *


class variables:
    def __init__(self, gui, static):
        self.__maxiter = 200
        self.__iter = 0
        self.__fadetime = 0.1
        self.static = static

        self.scale_txt = str(gui.scale_instance._preset.get())
        self.__overtone_matrix = self.__read_overtones(gui)
        self.__notes = int(gui.scale_instance.notes)
        self.__scale = self.__read_scale(gui)

        test_type = gui.settings_instance._test_type.get()
        self.__melodybool = bool(
            test_type == "Melodie" or test_type == "Melodie und Harmonie"
        )
        self.__harmonybool = bool(
            test_type == "Harmonie" or test_type == "Melodie und Harmonie"
        )

        self.__static_keynote = bool(
            gui.settings_instance._keynote.get() == "fester Grundton"
        )

        up_down = gui.settings_instance._up_down.get()
        self.__ascending = bool(
            up_down == "aufsteigend" or up_down == "auf- und absteigend"
        )
        self.__descending = bool(
            up_down == "absteigend" or up_down == "auf- und absteigend"
        )

        self.questions = int(gui.settings_instance._questions.get())
        self.harmonycount = int(gui.settings_instance._harmonycount.get())

        self.__freq_range_from = float(
            gui.settings_instance._freq_range_from.get()
        )
        self.__freq_range_to = float(
            gui.settings_instance._freq_range_to.get()
        )

        if self.__freq_range_to / self.__freq_range_from < pow(2, 1 / 12):
            self.__freq_range_to = self.__freq_range_from * pow(2, 1 / 12)

        self.melodycount = int(
            gui.settings_instance.rhythm_instance._rows.get()
        )

        if not self.melodybool:
            self.melodycount = 1

        if not self.harmonybool:
            self.harmonycount = 1

        if not self.melodybool and not self.harmonybool:
            self.melodycount = 2
            self.__melodybool = True

        self.__random_rhythm = (
            gui.settings_instance._random_rhythm.instate(["selected"])
        )

        self.__rhythm_vector = []

        for i in range(self.melodycount):
            if self.__random_rhythm:
                t = random.choice([2, 3, 4, 5, 6, 7, 8])
                t = t / 4
                self.__rhythm_vector.append(float(t))
            else:
                t = float(
                    gui.settings_instance.rhythm_instance._entries[i].get()
                )

                if t < 2 * self.__fadetime + 0.1:
                    t = 2 * self.__fadetime + 0.1

                self.__rhythm_vector.append(t)

        self.__rhythm_cutter()
        self.__get_intervals(gui)
        self.__create_firstnote()
        self.create_random_matrix()
        self.__harmonysolution()
        self.__melodysolution()

    def __rhythm_cutter(self):
        while sum(self.__rhythm_vector) > 10:
            r = []

            for t in self.__rhythm_vector:
                r.append(0.8 * t)

            self.__rhythm_vector = r

    @property
    def melodybool(self):
        return self.__melodybool

    @property
    def harmonybool(self):
        return self.__harmonybool

    def __get_intervals(self, gui):
        self.intervals = gui.settings_instance._intervals.get()
        self.intervals = self.intervals.split(",")

        for i in range(len(self.intervals)):
            self.intervals[i] = int(self.intervals[i])

        faktors = []

        for i in self.intervals:
            for current_note in self.__scale.chord:
                if (
                    current_note.no == i
                    and current_note.faktor
                    > self.__freq_range_to / self.__freq_range_from
                ):
                    self.intervals.remove(i)

    def play(self, frequency, time):
        sd.default.samplerate = 44100

        samples = np.arange(time * 44100) / 44100
        wave = 0 * samples

        for overt in self.__overtone_matrix:
            f = (
                overt.frequency
                * frequency
                / self.__overtone_matrix[0].frequency
            )

            wave = wave + overt.amp * np.sin(
                2
                * np.pi
                * f
                * (samples - 2 * np.pi * overt.phi)
            )

        wave = 10000 * wave / max(wave)
        wave = self.__smooth(
            samples,
            time,
            wave,
            self.__fadetime,
            32767,
        )

        wav_wave = np.array(wave, dtype=np.int16)
        sd.play(wav_wave, blocking=True)

    def __smooth(self, samples, time, wave, fadeouttime, resolution):
        if 2 * fadeouttime > time:
            return wave

        a = 1 / fadeouttime * np.log(1 / resolution)
        t_diff = time - fadeouttime

        fadeout = np.minimum(
            1,
            np.exp(a * (samples - t_diff)),
        )
        fadein = np.minimum(
            1,
            np.exp(-a * samples),
        )

        return (wave * fadeout) * fadein

    def __play_harmony(self, frequencies, time):
        sd.default.samplerate = 44100

        samples = np.arange(time * 44100) / 44100
        wave = 0 * samples

        for frequency in frequencies:
            for row in self.__overtone_matrix:
                wave = wave + row.amp * np.sin(
                    2
                    * np.pi
                    * row.frequency
                    * frequency
                    / self.__overtone_matrix[0].frequency
                    * (samples - 2 * np.pi * row.phi)
                )

        wave = 10000 * wave / max(wave)
        wave = self.__smooth(
            samples,
            time,
            wave,
            self.__fadetime,
            32767,
        )

        wav_wave = np.array(wave, dtype=np.int16)
        sd.play(wav_wave, blocking=True)

    def play_all(self):
        self.__create_freq_matrix()

        for i in range(self.melodycount):
            self.__play_harmony(
                self.__freq_matrix[i],
                self.__rhythm_vector[i],
            )

    def __create_firstnote(self):
        if type(self.static) == type(0) or not self.__static_keynote:
            self.firstnote = random.choice(self.__scale.chord)
        else:
            self.firstnote = self.static

        if self.scale_txt == "indisch":
            self.firstnote = self.__scale.chord[0]

    def __create_firstnote_freq(self):
        if self.scale_txt in [
            "mitteltönig",
            "pythagoraeisch",
            "gleichstufig",
            "rein",
            "mikrotonal",
            "wohltemperiert (Werckmeister III)",
        ]:
            faktor = self.__find_a()
            self.__firstnote_freq = 220 / faktor

        elif self.scale_txt == "indisch":
            self.__firstnote_freq = 128

            if self.__freq_range_to < 2 * self.__freq_range_from:
                self.__freq_range_to = 2 * self.__freq_range_from

        else:
            faktor = 2 ** (2 / 3)
            self.__firstnote_freq = 220 / faktor

    def __find_a(self):
        for current_note in self.__scale.chord:
            if current_note.no == 8:
                return current_note.faktor

        return None

    def __random_note(self, previous_note, harm):
        interval = random.choice(self.intervals)

        if not harm:
            if self.__ascending and self.__descending:
                signum = random.choice([-1, 1])
            elif self.__ascending:
                signum = 1
            elif self.__descending:
                signum = -1
            else:
                signum = 1
        else:
            signum = 1

        interval = signum * interval

        i = self.__scale.chord.index(previous_note)
        scale_notes = len(self.__scale.chord)

        octaves = (
            (i + interval) // scale_notes
            + previous_note.octave
        )

        random_note = self.__scale.chord[
            (i + interval) % scale_notes
        ]

        return note.note(
            random_note.no,
            random_note.faktor,
            octaves,
        )

    def __max_matrix(self, matrix):
        lol = []

        for r in matrix:
            lol.append(max(r))

        return max(lol)

    def __min_matrix(self, matrix):
        lol = []

        for r in matrix:
            lol.append(min(r))

        return min(lol)

    def __reset(self):
        self.__iter += 1

        if (
            self.__iter < self.__maxiter
            or self.__iter > self.__maxiter * 2
            or (
                self.__iter > self.__maxiter
                and self.__iter < self.__maxiter * 2
            )
        ):
            if not self.__static_keynote:
                self.create_random_matrix()
                self.__create_freq_matrix()
                self.__harmonysolution()
                self.__melodysolution()
            else:
                self.create_random_matrix()
                self.__create_freq_matrix()
                self.__harmonysolution()
                self.__melodysolution()

        elif self.__iter == self.__maxiter:
            self.__freq_range_to = max(
                self.__freq_range_to,
                self.__freq_range_from * 2,
            )

            print(...)

            self.create_random_matrix()
            self.__create_freq_matrix()
            self.__harmonysolution()
            self.__melodysolution()

        elif self.__iter == self.__maxiter * 2:
            self.__freq_range_to = max(
                self.__freq_range_to,
                self.__freq_range_from * 4,
            )

            print(...)

            self.create_random_matrix()
            self.__create_freq_matrix()
            self.__harmonysolution()
            self.__melodysolution()

    def __multiply_matrix(self, matrix, faktor):
        for i in range(len(matrix)):
            for j in range(len(matrix[0])):
                matrix[i][j] = matrix[i][j] * faktor

        return matrix

    def __create_freq_matrix(self):
        self.__create_firstnote_freq()
        self.__freq_matrix = []

        for akkord in self.__random_matrix:
            akk = []

            for n in akkord:
                oktave = n.octave
                faktor = n.faktor

                akk.append(
                    self.__firstnote_freq * faktor * 2**oktave
                )

            self.__freq_matrix.append(akk)

        maxF = self.__max_matrix(self.__freq_matrix)
        minF = self.__min_matrix(self.__freq_matrix)

        fmax = self.__freq_range_to
        fmin = self.__freq_range_from

        if (maxF > fmax and minF <= fmin) or (
            maxF >= fmax and minF < fmin
        ):
            self.__reset()

        elif maxF > fmax and minF >= fmin:
            while minF > fmin * 2:
                self.__freq_matrix = self.__multiply_matrix(
                    self.__freq_matrix,
                    1 / 2,
                )

                maxF = self.__max_matrix(self.__freq_matrix)
                minF = self.__min_matrix(self.__freq_matrix)

            if maxF >= fmax:
                self.__reset()

        elif minF < fmin and maxF <= fmax:
            while maxF < fmax / 2:
                self.__freq_matrix = self.__multiply_matrix(
                    self.__freq_matrix,
                    2,
                )

                maxF = self.__max_matrix(self.__freq_matrix)
                minF = self.__min_matrix(self.__freq_matrix)

            if minF < fmin:
                self.__reset()

    @property
    def freq_matrix(self):
        return self.__freq_matrix

    def create_random_matrix(self):
        random_matrix = []

        for i in range(self.melodycount):
            random_matrix.append([])

            for j in range(self.harmonycount):
                if i == 0 and j == 0:
                    self.__create_firstnote()
                    random_matrix[i].append(self.firstnote)

                elif i != 0 and j == 0:
                    random_matrix[i].append(
                        self.__random_note(
                            random_matrix[i - 1][0],
                            False,
                        )
                    )

                else:
                    random_matrix[i].append(
                        self.__random_note(
                            random_matrix[i][j - 1],
                            True,
                        )
                    )

        self.__random_matrix = random_matrix

    @property
    def random_matrix(self):
        return self.__random_matrix

    def melodysub(self, gui):
        melodyentries = gui.dialog_instance.melodyentries
        melodysub = []

        for entry in melodyentries:
            try:
                melodysub.append(int(entry.get()))
            except (TypeError, ValueError):
                melodysub.append(0)

        self.melodysub = melodysub

    def harmonysub(self, gui):
        harmonyentries = gui.dialog_instance.harmonyentries
        harmonysub = []

        if self.harmonybool and self.melodybool:
            for i in range(len(harmonyentries)):
                try:
                    harmonysub.append([])

                    for entry in harmonyentries[i]:
                        try:
                            harmonysub[i].append(int(entry.get()))
                        except (TypeError, ValueError):
                            harmonysub[i].append(0)

                except TypeError:
                    try:
                        harmonysub.append(int(entry.get()))
                    except (TypeError, ValueError):
                        harmonysub.append(0)

        else:
            for entry in harmonyentries:
                try:
                    harmonysub.append(int(entry.get()))
                except (TypeError, ValueError):
                    harmonysub.append(0)

        self.harmonysub = harmonysub

    def __melodysolution(self):
        scale_notes = len(self.__scale.chord)
        melodysolution = []

        for i in range(self.melodycount - 1):
            melodysolution.append(
                self.__random_matrix[i][0].interval(
                    self.__random_matrix[i + 1][0],
                    scale_notes,
                )
            )

        if not self.melodybool:
            melodysolution = []

        self.melodysolution = melodysolution

    def __harmonysolution(self):
        scale_notes = len(self.__scale.chord)
        harmonysolution = []

        for i in range(self.melodycount):
            harmonysolution.append([])

            for j in range(self.harmonycount - 1):
                harmonysolution[i].append(
                    self.__random_matrix[i][j].interval(
                        self.__random_matrix[i][j + 1],
                        scale_notes,
                    )
                )

        if not self.harmonybool:
            harmonysolution = []

        if not self.melodybool:
            harmonysolution = harmonysolution[0]

        self.harmonysolution = harmonysolution

    def print_solution(self):
        print("melodysolution")
        print(self.melodysolution)

        print("harmonysolution")
        print(self.harmonysolution)

        print("melodysub")
        print(self.melodysub)

        print("harmonysub")
        print(self.harmonysub)

    def __read_overtones(self, gui):
        self.__overtones = int(gui.overtones_instance._rows.get())
        overtone_matrix = []

        for i in range(self.__overtones):
            no = i
            frequency = gui.overtones_instance._entries[i][0]
            amp = gui.overtones_instance._entries[i][1]
            phi = gui.overtones_instance._entries[i][2]

            frequency = float(frequency.get())
            phi = float(phi.get()) * 2 * np.pi
            amp = float(amp.get())

            overtone = ov.overtone(
                no,
                frequency,
                amp,
                phi,
            )

            overtone_matrix.append(overtone)

        return overtone_matrix

    def __read_scale(self, gui):
        scale = []

        for i in range(self.__notes):
            entr = gui.scale_instance._entries[i][0]
            no = float(entr.get())

            entr = gui.scale_instance._entries[i][1]
            faktor = float(entr.get())

            octave = 0
            note1 = note.note(
                no,
                faktor,
                octave,
            )

            scale.append(note1)

        return chord(scale)
