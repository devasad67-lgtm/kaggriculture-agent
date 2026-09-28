"""Cross-turn state carried on the Brain instance. Reset automatically when
`step` goes backwards (a fresh game in the same process, e.g. during bench.py
runs that reuse a loaded module)."""


class Memory:
    def __init__(self):
        self.last_step = -1
        self.last_day = -1
        self.layout = {}              # (x,y) -> {"role": "CROP", "crop": ...} | {"role": "COOP"/"PASTURE", "animal": ...}
        self.layout_quadrants = None  # unlocked_quadrants tuple the layout was built for
        self.errors = []
        self.hired_today = 0
        self.animal_targets = {}      # animal -> target count, recomputed occasionally
        self.commitments = {}         # uid -> {"pos": (x,y), "kind": set-name} sticky travel targets

    def reset(self):
        self.__init__()

    def note_error(self, stage, exc):
        self.errors.append((stage, repr(exc)))
        if len(self.errors) > 200:
            self.errors = self.errors[-200:]

    def update(self, state):
        if state.step < self.last_step:
            self.reset()
        if state.day != self.last_day:
            self.hired_today = 0
        self.last_step = state.step
        self.last_day = state.day
