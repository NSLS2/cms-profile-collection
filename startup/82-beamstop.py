#Add by Siyu 2025/04/14

import json
import time
from pathlib import Path
from datetime import datetime

# folder = '/home/xf11bm/.ipython/profile_collection/startup/'

class Beamstop:
    default_config_file = bluesky_path('cfg/beamstop_config.cfg')

    def __init__(self, name, config_file=None):
        self.name = name
        self.config_file = Path(config_file or self.default_config_file)
        self.positions = self._load_config()
        self._sync()
        self.load()

    def _sync(self):
        self.bsx = bsx.position
        self.bsy = bsy.position
        self.bsphi = bsphi.position

    @classmethod
    def get(cls, name, config_file=None):
        print(f"Set current beamstop to '{name}' without moving.")
        return cls(name, config_file=config_file)

    @classmethod
    def goto(cls, name, config_file=None):
        bs = cls(name, config_file=config_file)
        # bs._move()
        RE(bs._move())
        beam.setTransmission(1e-6)
        print('Transmission set to 1e-6!')
        print('Gradually ramp to 1 while monitoring using SAXS detector!')

        return bs

    def _load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.positions, f, indent=2)

    def _simulate_move(self):
        print(f"[OFFLINE] Moving motors to {self.name} position:")
        print(f"  bsx -> {self.bsx}, bsy -> {self.bsy}, bsphi -> {self.bsphi}")

    # def _move(self):
    #     print(f"Moving motors to {self.name} position:")
    #     bsx.move(0)
    #     bsy.move(0)
    #     print(f"  bsx -> {0}, bsy -> {0}")
    #     time.sleep(2)
    #     bsphi.move(self.bsphi)
    #     print(f"  bsphi -> {self.bsphi}")
    #     time.sleep(5)
    #     bsx.move(self.bsx)
    #     bsy.move(self.bsy)
    #     print(f"  bsx -> {self.bsx}, bsy -> {self.bsy}")
    #     time.sleep(2)
    #     self.show()
    #     config_update()
    #     config_load()


    def _move(self):
        print(f"Moving motors to {self.name} position:")
        yield from bps.mv(bsx, 0, bsy, 0)
        print(f"  bsx -> {0}, bsy -> {0}")
        yield from bps.mv(bsphi, self.bsphi)
        print(f"  bsphi -> {self.bsphi}")
        yield from bps.mv(bsx, self.bsx, bsy, self.bsy)
        print(f"  bsx -> {self.bsx}, bsy -> {self.bsy}")
        self._sync()
        self.show()
        config_update()
        print("config_update() done!")
        config_load()
        print("config_load() done!")

    # def move(self):
    #     RE(self._move())

    def x(self):
        print(f"bsx = {self.bsx}")
        return self.bsx

    def y(self):
        print(f"bsy = {self.bsy}")
        return self.bsy

    def phi(self):
        print(f"bsphi = {self.bsphi}")
        return self.bsphi

    def xr(self, delta):
        self._sync()
        self.bsx += delta
        bsx.move(self.bsx)
        # yield from bps.mv(bsx, self.bsx)
        print(f"bsx moved relatively by {delta} mm -> {self.bsx}")

    def yr(self, delta):
        self._sync()
        self.bsy += delta
        bsy.move(self.bsy)
        # yield from bps.mv(bsy, self.bsy)
        print(f"bsy moved relatively by {delta} mm -> {self.bsy}")

    def phir(self, delta):
        self._sync()
        self.bsphi += delta
        bsphi.move(self.bsphi)
        # yield from bps.mv(bsphi, self.bsphi)
        print(f"bsphi moved relatively by {delta} deg -> {self.bsphi}")

    def xabs(self, value):
        self.bsx = value
        bsx.move(self.bsx)
        # yield from bps.mv(bsx, self.bsx)
        print(f"bsx moved to {value} mm")

    def yabs(self, value):
        self.bsy = value
        bsy.move(self.bsy)
        # yield from bps.mv(bsy, self.bsy)
        print(f"bsy moved to {value} mm")

    def phiabs(self, value):
        self.bsphi = value
        bsphi.move(self.bsphi)
        # yield from bps.mv(bsphi, self.bsphi)
        print(f"bsphi moved to {value} deg")

    def save(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            'bsx': self.bsx,
            'bsy': self.bsy,
            'bsphi': self.bsphi,
            'timestamp': timestamp
        }
        self.positions.setdefault(self.name, []).append(entry)
        self._save_config()
        print(f"Saved current position for '{self.name}' at {timestamp}.")

        config_update()
        print("config_update() done!")
        config_load()
        print("config_load() done!")

    def load(self):
        entries = self.positions.get(self.name)
        if entries:
            latest = entries[-1]
            self.bsx = latest['bsx']
            self.bsy = latest['bsy']
            self.bsphi = latest['bsphi']
            print(f"Loaded last position for '{self.name}' from {latest.get('timestamp', 'unknown')}")
        else:
            print(f"No saved position found for '{self.name}'.")

    def show(self):
        self._sync()
        print(f"Beamstop '{self.name}':")
        print(f"  bsx = {self.bsx}")
        print(f"  bsy = {self.bsy}")
        print(f"  bsphi = {self.bsphi}")

    @staticmethod
    def clear_cfg(config_file=None):
        path = Path(config_file or Beamstop.default_config_file)
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
            for key in data:
                if isinstance(data[key], list) and len(data[key]) > 0:
                    data[key] = [data[key][-1]]
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            print("Configuration file cleaned: only latest entries retained.")
        else:
            print("Config file does not exist.")