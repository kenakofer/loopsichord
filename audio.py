from random import random
import pyaudio as pa
from constants import *
import numpy as np
from time import sleep
from tkinter import filedialog
from loop import *
import wave
import math

class AudioPlayer:

    def __init__(self, music_maker):
        self.music_maker = music_maker
        self.percent_through_period = 0
        self.callback_flag = pa.paContinue
        self.active_loop_index = 0
        self.loop_length = BUFFERS_PER_MEASURE
        self.loops = [Loop(self.loop_length)]
        self.loop_buffer_index = 0
        self.previous_volume = 0
        self.base_volume = VOLUME
        self.volume = 0
        self.freq = 440
        self.playing = False
        self.loop_playing = True
        self.loop_recording = False
        self.stream = self.get_stream()

    def get_stream(self):
        global stream
        p = pa.PyAudio()
        stream = p.open(format=pa.paFloat32,
                    channels=1,
                    rate=44100,
                    frames_per_buffer = BUFFER_SIZE,
                    stream_callback = self.callback,
                    output=True)
        stream.pos=0
        return stream

    def stop_stream(self):
        self.callback_flag = pa.paComplete

    def run(self):
        while self.stream.is_active():
            ## Saving the loops must go here because opening a filedialog apparently must happen in the main thread
            if keys and pygame.key.get_mods() & CTRL and keys[K_S]:
                filename = filedialog.asksaveasfilename(filetypes=(("Audio Files", ".wav"), ("All Files", "*.*")))
                if filename:
                    self.write_loop(filename)
            sleep(0.1)
        self.stream.close()

    def callback(self, in_data, frame_count, time_info, flag):
        try:
            if flag:
                print("Playback error: %i" % flag)
            self.freq = AudioPlayer.musical_pitch_to_hertz(self.music_maker.pitch)

            ## Do step is where all the action happens
            self.music_maker.do_step()

            if self.volume != 0:
                ## Generate a sin wave with overtones, starting at the percent through a period where the previous one left off. Return the samples and the percent through the period that the samples ends
                new_samples, self.percent_through_period = AudioPlayer.sin(self.freq, sample_count=frame_count, fs=FS, volume=self.volume, previous_volume=self.previous_volume, percent_through_period=self.percent_through_period, overtones = MY_OVERTONES)
            else:
                new_samples = np.zeros(frame_count).astype(np.float32)
            self.previous_volume = self.volume
            samples = np.copy(new_samples)

            ## Increment the buffer counter whenever we are playing or recording
            self.loop_buffer_index += 1
            self.loop_buffer_index %= self.loop_length

            ## If playing loops, then add all the unmuted loops to the samples
            if self.loop_playing:
                for loop in self.loops:
                    if not loop.muted:
                        samples += loop.volume * loop.buffers[self.loop_buffer_index]

            ## Save the new samples to the active loop
            if self.loop_recording:
                if self.volume > 0:
                    active_loop = self.loops[self.active_loop_index]
                    active_loop.buffers[self.loop_buffer_index] += new_samples
                    active_loop.add_recorded_note(self.loop_buffer_index, self.music_maker.pitch, self.volume, self.music_maker.scale)
                    active_loop.has_recorded = True
            
            ## Generate metronome ticks
            if self.music_maker.metronome.is_beat(self.loop_buffer_index) and self.music_maker.metronome.sound:
                samples += np.random.rand(frame_count).astype(np.float32) * VOLUME * METRONOME_RELATIVE_VOLUME


            return (samples, self.callback_flag)

        except pygame.error:
            print("Aborting...")
            return (None, pa.paAbort)

    def do_action(self, action):
        if action == ACTION_ARTICULATE_NOTE:
            if not self.playing:
                self.volume = ARTICULATION_FACTOR * self.adjusted_base_volume()
                self.previous_volume = self.volume
                self.playing=True
            else:
                print("A note is already sounding")

        elif action == ACTION_START_LOOP_REC and not self.loop_recording:
            self.loop_recording = True
            print("starting recording")
        elif action == ACTION_STOP_LOOP_REC:
            self.active_loop_index += 1
            self.loop_recording = False
            self.loop_playing = True
            if self.active_loop_index + 1 >= len(self.loops):
                self.loops.append(Loop(self.loop_length))
            print("stopping recording")

        elif action == ACTION_START_LOOP_PLAY and not self.loop_playing:
            self.loop_playing = True
            print("starting playing")
        elif action == ACTION_STOP_LOOP_PLAY:
            self.loop_playing = False
            print("stopping playing")

    def settle_to_volume(self):
        self.volume = (self.volume + self.adjusted_base_volume() * ARTICULATION_DECAY) / (ARTICULATION_DECAY + 1)

    def volume_decay(self):
        self.playing=False
        self.volume *= REVERB
        if self.volume < CUTOFF:
            self.volume = 0

    def adjusted_base_volume(self):
        return volume_factor_by_freq(self.freq)*self.base_volume

    def increase_volume(self):
        self.base_volume *= 1.1

    def decrease_volume(self):
        self.base_volume *= .9

    def write_loop(self, filename, frame_rate=44100, sample_width=4, volume_adjustment=.8):
        ## Filter out loops which haven't been used
        save_loops = list(filter(lambda l: l.has_recorded, self.loops))
        ## Concatenate buffers within each loop
        loop_samples = [np.concatenate(loop.buffers)*loop.volume for loop in save_loops]
        ## Put the samples together in the way the channels will be saved
        samples = AudioPlayer.interleave_samples(loop_samples)
        ## Default volume adjustment
        samples *= volume_adjustment

        #Prevent clipping
        samples_max = max(abs(x) for x in samples)
        if samples_max * 1.1 > 1:
            samples /= samples_max * 1.1

        #Convert to int32
        samples = (samples * 2**31).astype(np.int32)
        channels = len(save_loops)
        with wave.open(filename, 'wb') as writer:
            writer.setnchannels(channels)
            writer.setframerate(frame_rate)
            writer.setsampwidth(sample_width)
            writer.setnframes(len(samples)//channels)
            writer.writeframes(samples)

    def interleave_samples(sample_channels):
        s1 = sample_channels[0]
        ss = np.empty((s1.size * len(sample_channels),), dtype=s1.dtype)
        for i in range(0,len(sample_channels)):
            ss[i::len(sample_channels)] = sample_channels[i]
        return ss

    def musical_pitch_to_hertz(mp):
        return (2**(mp/12)) * 440.0

    def sin(freq, sample_count=FS, fs=FS, volume=1, previous_volume=1, percent_through_period=0, overtones=[1]):
        count = sample_count
        samples = [
            (overtones[i] * np.sin(2*np.pi*np.arange(count)*freq*(i+1)/fs + percent_through_period*2*np.pi*(i+1))).astype(np.float32)
            for i in range(len(overtones))
            ]
        new_ptp = (percent_through_period + count*freq/fs) % 1
        samples = np.sum(samples, axis=0)
        samples *= np.linspace(previous_volume, volume, num=count)
        samples = samples.astype(np.float32)
        return  samples, new_ptp
