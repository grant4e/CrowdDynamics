import hoomd
import math
import numpy as np

#------------------ Exit Locating Active Force --------------------------------
#
# This custom updater directly edits the velocity of particles such that 
#   they are directed towards the exit.
#
# NOTE: This updater cannot be used with HOOMD's brownian integration method
#   because hoomd.md.methods.Brownian directly overwrites velocities in 
#   order to preserve the specified kT of the system. I think  it is called 
#   "overdamped" in the documentation for that reason.
#
#------------------------------------------------------------------------------

class smartForce(hoomd.custom.Action):

    def __init__(self, energy, numActive, exitWidth):
        self.energy = energy
        self.numActive = numActive
        self.exitWidth = exitWidth

    def escapeDirectionUnit(self, x, y):
        mag = math.sqrt(x*x + y*y)
        if x > 0:
            uvX = 1                                                             # proceed directly out
            uvY = 0
        elif mag < self.exitWidth/2:                                            # If particle is within an exit radius from the origin:
            uvX = 1                                                             # proceed directly out (rightwards)
            uvY = 0
        else:                                                                   # Else head towards the exit/origin
            uvX = -x / mag     
            uvY = -y / mag
        return np.array([uvX, uvY, 0])

    def act(self, timestep):
        with self._state.cpu_local_snapshot as snap:
            for i in range(self.numActive):
                x = snap.particles.position[i][0]
                y = snap.particles.position[i][1]
                dir = self.escapeDirectionUnit(x, y)
                vel = dir * self.energy                                         # Multiply escape vector by chosen energy
                snap.particles.velocity[i] = vel
