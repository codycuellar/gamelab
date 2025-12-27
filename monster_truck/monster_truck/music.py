from pathlib import Path
import pygame


class Music:
    music_dir = Path("assets/music")
    auto_fade = 5.0  # seconds
    skip_fade = 2.0  # seconds
    volume = 0.7

    def __init__(self):
        self.tracks = [s for s in self.music_dir.iterdir()]
        self.sounds = [pygame.mixer.Sound(t) for t in self.tracks]
        self.lengths = [s.get_length() for s in self.sounds]
        self.channels = [pygame.mixer.Channel(0), pygame.mixer.Channel(1)]

        self.active = 0
        self.index = 0
        self.fading = False

        self.crossfading = False
        self.fade_time = 0.0
        self.fade_elapsed = 0.0

        self.play()

    def play(self):
        ch = self.channels[self.active]
        ch.set_volume(self.volume)
        ch.play(self.sounds[self.index])
        self.play_time = 0.0

    def _start_crossfade(self, fade_time):
        if self.crossfading:
            return

        next_index = (self.index + 1) % len(self.sounds)
        next_ch = self.channels[1 - self.active]

        next_ch.set_volume(0.0)
        next_ch.play(self.sounds[next_index])

        self.crossfading = True
        self.fade_time = fade_time
        self.fade_elapsed = 0.0

    def next(self):
        self._start_crossfade(self.skip_fade)

    def step(self, dt):
        self.play_time += dt

        # auto fade near end
        if not self.crossfading:
            remaining = self.lengths[self.index] - self.play_time
            if remaining <= self.auto_fade:
                self._start_crossfade(self.auto_fade)

        # handle crossfade
        if self.crossfading:
            self.fade_elapsed += dt
            t = min(self.fade_elapsed / self.fade_time, 1.0)

            out_ch = self.channels[self.active]
            in_ch = self.channels[1 - self.active]

            out_ch.set_volume(self.volume * (1.0 - t))
            in_ch.set_volume(self.volume * t)

            if t >= 1.0:
                out_ch.stop()
                self.active = 1 - self.active
                self.index = (self.index + 1) % len(self.sounds)

                self.crossfading = False
                self.play_time = 0.0
