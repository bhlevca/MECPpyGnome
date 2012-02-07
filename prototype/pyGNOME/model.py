 
import numpy
import random                
from map import gnome_map
import os
import sys
from math import floor
import collections
from cyGNOME import c_gnome
from basic_types import *
    
class Model:
    
    """ Documentation goes here. """

    def __init__(self):
        self.movers = collections.deque()
        self.minimap = None
        self.particles = collections.deque()
        self.live_particles = collections.deque()
        self.start_time = None
        self.stop_time = None
        self.duration = None
        self.interval_seconds = None
        self.num_timesteps = None
        self.time_step = 0
        
    def add_map(self, image_size, bna_filename):
        self.minimap = gnome_map(image_size, bna_filename)
    
    def add_wind_mover(self, constant_wind_value):
        self.movers.append(c_gnome.wind_mover(constant_wind_value))
        
    def add_random_mover(self, diffusion_coefficient):
        self.movers.append(c_gnome.random_mover(diffusion_coefficient))
        
    def set_run_duration(self, start_time, stop_time):
        if not start_time < stop_time:
            return
        self.start_time = start_time
        self.stop_time = stop_time
        self.duration = stop_time - start_time
    
    def set_timestep(self, interval_seconds):
        if self.duration == None:
            return
        self.interval_seconds = interval_seconds
        self.num_timesteps = floor(self.duration / self.interval_seconds)

    def set_spills(self, coords, num_particles_array, release_time_array):
        if self.minimap == None:
            return
        map(self.minimap.set_spill, coords, num_particles_array, release_time_array)

    def disperse_particles(self):
        pass
    
    def reset_steps(self):
    	self.time_step = 0
    	
    def release_particles(self, time_step):
        temp_queue = collections.deque()
        release = self.live_particles.append
        keep = temp_queue.append
        pop = self.particles.popleft
        current_time = self.start_time + self.interval_seconds*self.time_step
        while len(self.particles):
            spill = pop()
            if spill[1] <= current_time:
                tmp_list = spill[0]
                for i in xrange(0, tmp_list.size):
                    tmp_list[i]['status_code'] = status_in_water
                release(spill)
            else:
                keep(spill)
        self.particles = temp_queue
                
    def refloat_particles(self, time_step):
    	if not len(self.live_particles):
    		return
        spills = zip(*self.live_particles)[0]
        map(self.minimap.agitate_particles, [time_step]*len(spills), spills)
        
    def move_particles(self, time_step):
    	if not len(self.live_particles):
    		return
        spills = zip(*self.live_particles)[0]
        for mover in self.movers:
            map(mover.get_move, [time_step]*len(spills), spills)
                
    def step(self):
        if(self.duration == None):
            return False
        if(self.interval_seconds == None):
            return False
        if not len(self.movers) > 0:
            return False
        if self.time_step >= self.num_timesteps:
        	return False
        self.release_particles(self.interval_seconds)
        self.refloat_particles(self.interval_seconds)
        self.move_particles(self.interval_seconds)
        self.time_step += 1
        
