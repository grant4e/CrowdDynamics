# Run Time Params
hoomdPath, gsdPath = ["nas/longleaf/home/grant4e/hoomd-v2.9.7/build", "nas/longleaf/home/grant4e/test_runs/"] 
runFor, partNum = [5, 1000]

import sys
import os
import math
from myUtils import *

peA = 50                        # activity of particles
intPhi = 60                     # system area fraction (integer, i.e. 45, 65, etc.)
phi = float(intPhi) / 100.0     # system area fraction (decimal, i.e. 0.45, 0.65, etc.)
eps = 1.0                       # epsilon (potential well depth for LJ potential)

# Remaining imports
sys.path.insert(0,hoomdPath)    # insert specified path to hoomdPath as first place to check for hoomd

import hoomd                    # import hoomd functions based on path
from hoomd import md
from hoomd import deprecated
import numpy as np
from numpy import random

#---------------------------------Set/Compute Simulation Parameters--------------------------------
kT = 1.0                        # temperature
threeEtaPiSigma = 1.0           # drag coefficient
sigma = 1.0                     # particle diameter
D_t = kT / threeEtaPiSigma      # translational diffusion constant
D_r = (3.0 * D_t) / (sigma**2)  # rotational diffusion constant
tauBrown = (sigma**2) / D_t     # brownian time scale (invariant)

def computeTauLJ(epsilon):
    "Given epsilon, compute lennard-jones time unit"
    tauLJ = ((sigma**2) * threeEtaPiSigma) / epsilon
    return tauLJ

tauLJ = computeTauLJ(eps)
dt = 0.000001 * tauLJ                       # timestep size.  I use 0.000001 for dt=tauLJ* (eps/10^6) generally
simLength = runFor * tauBrown               # how long to run (in tauBrown)
simTauLJ = simLength / tauLJ                # how long to run (in tauLJ)
totTsteps = int(simLength / dt)             # how many tsteps to run
numDumps = float(simLength / 0.01)          # dump data every 0.1 tauBrown.  
dumpFreq = float(totTsteps / numDumps)      # normalized dump frequency.  
dumpFreq = int(dumpFreq)                    # ensure this is an integer

print("Brownian tau in use:"+str(tauBrown))
print("Lennard-Jones tau in use:"+str(tauLJ))
print("Timestep in use:"+str(dt))
print("Total number of timesteps:"+str(totTsteps))
print("Total number of output frames:"+str(numDumps))
print("File dump frequency:"+str(dumpFreq))

#----------------------------------------Initialize system-----------------------------------------
box_area = (partNum*math.pi*(1/4))/phi              # Calculate desired box area given particle number and density
box_edge = np.sqrt(box_area)                        #Calculate desired box dimensions

#Number of particles per 1 unit of distance, i.e. wall_part_diam=1/5->5
# particles per 1 unit of distance, that will be generated in order
# to make an impenetrable wall
wall_part_diam = (1/5)
num_wall_part = np.ceil(box_edge/wall_part_diam)    # Calculates number of particles in total for the wall to span the box length            # Total number of particles in simulation
                                
pos = []                                            # Lists to store particle parameters
typ = []                                            #
rOrient = []                                        #
pe=[]                                               #
activity = []                                       #

x_val = -box_edge/2                                 # starting x location of wall
r_cut = 2**(1/6)                                    # Cut off distance of LJ potential

#---------------------------------------Initialize Particles---------------------------------------
topLeft = (box_edge*0.1, box_edge*0.1)
bottomRight = (box_edge*0.4, box_edge*0.9)
spaceBetween = sigma*1.5                            # Dist between each particle (in x and in y) is 1.5 times diameter

pos.append(makeGrid(topLeft, bottomRight, spaceBetween))  
partNum = len(pos)                                  # Using this grid method means we no longer can guarantee numParticles     
tot_part =  int(num_wall_part + len(pos))           # So recalculate the numbers to iterate over

#Loop over all particles
for i in range(0, tot_part):
    # Checks if particle ID is less than the number of active/mobile particles
    if i < partNum:        
        typ.append(0)                               #Label particle type 
        angle = np.random.rand() * 2 * np.pi        # Random active force orientation                        
        f_x = (np.cos(angle)) * peA                 # Calculate x and y activity given angle and activity
        f_y = (np.sin(angle)) * peA
        f_z = 0.                                    # Zero active force in z-dimension
        pe.append(peA)                              # Label particle activity
        
        #Save activity vector of particle
        activity_tuple = (f_x, f_y, f_z)
        activity.append(activity_tuple)
    else:
        #Particle is part of impenetrable wall that spans x-axis
        if np.abs(x_val)>1.0:                       #Checks to be sure particle isn't in location of wall opening
            pos.append((x_val, 1.0, 0.5))           #Saves position if not in opening
            typ.append(1)                           #Label particle type (Wall particles are Type 1, Active Particles are Type 0) 
            activity.append((0, 0, 0))              #Zero activity for immovable particles
            pe.append(0)
            x_val+=wall_part_diam                   #Increase x-location by frequency of particles defined
        else:
            #In opening of wall, so merely increase x-location by frequency of particles
            x_val+=wall_part_diam

# Label # types of each particle
uniqueTyp = []
for i in typ:
    if i not in uniqueTyp:
        uniqueTyp.append(i)
        
# Get the number of each type
particles = [ 0 for x in range(0, len(uniqueTyp)) ]
for i in range(0, len(uniqueTyp)):
    for j in typ:
        if uniqueTyp[i] == j:
            particles[i] += 1

#Labels each particle with particles types of 0 and 1 as 'A' and 'B' respectively for hoomd
char_types = []
for i in typ:
    char_types.append( chr(ord('@') + i+1) )

unique_char_types=['A', 'B']
real_tot_part = len(pos)                            # Number of particles actually placed
hoomd.context.initialize()                          #Initialize hoomd

#Create data step that initiates a simulation box with given number of particles
snap = hoomd.data.make_snapshot(N = real_tot_part,
                                box = hoomd.data.boxdim(Lx=box_edge,
                                                        Ly=box_edge*2,
                                                        dimensions=2),
                                particle_types = unique_char_types)

snap.particles.position[:] = pos[:]
snap.particles.typeid[:] = typ[:]
snap.particles.types[:] = char_types[:]

system = hoomd.init.read_snapshot(snap)             #Input locations and types of particles into data step for HOOMD

#Define planar walls that span simulation box border (non-periodic boundary conditions)
wallstructure=md.wall.group()
wall_x = wallstructure.add_plane((box_edge/2, 0.0, 0.0),normal=(-1.0, 0.0, 0.0), inside=True)
wall_mx = wallstructure.add_plane((-box_edge/2, 0.0, 0.0),normal=(1.0, 0.0, 0.0), inside=True)
wall_y = wallstructure.add_plane((0.0, box_edge, 0.0),normal=(0.0, -1.0, 0.0), inside=True)
wall_my = wallstructure.add_plane((0.0, -box_edge, 0.0),normal=(0.0, 1.0, 0.0), inside=True)

#Define forces of all walls on each particle type
wall_force_fslj = md.wall.slj(wallstructure, r_cut=2**(1/6), name='p')
wall_force_fslj.force_coeff.set('A', epsilon=1.0, sigma=1.0, r_cut=2**(1/6))

#Group particles together based on distance/nearest neighbors
all = hoomd.group.all()
groups = []
gA = hoomd.group.type(type = 'A', update=True)
gB = hoomd.group.type(type = 'B', update=True)

# Set particle potentials
nl = hoomd.md.nlist.cell()
lj = hoomd.md.pair.lj(r_cut=2**(1/6), nlist=nl)
lj.set_params(mode='shift')

lj.pair_coeff.set('A', 'A', epsilon=eps, sigma=1.0)
lj.pair_coeff.set('A', 'B', epsilon=1.0, sigma=1.0)

#---------------------------------------Brownian integration---------------------------------------
brownEquilSteps = 10000
hoomd.md.integrate.mode_standard(dt=dt)
hoomd.md.integrate.brownian(group=gA, kT=kT, seed=1)# Group A Particles get to equilibrate for a second
hoomd.run(brownEquilSteps)                               # Calculate movement of only mobile particles          

#----------------------------------------Full integration------------------------------------------
hoomd.md.force.active(group=all,                    # Define active forces set earlier
                      seed=1,
                      f_lst=activity,
                      rotation_diff=D_r,
                      orientation_link=False,
                      orientation_reverse_link=True)

name = "monodisperseBrowniansPlusWall"
gsdName = name + ".gsd"
try:
    os.remove(gsdName)                              # Remove .gsd files if they exist
except OSError:
    pass
 
hoomd.dump.gsd(gsdName,                             #Specify how often and what to save
               period=dumpFreq,
               group=all,
               overwrite=False,
               phase=-1,
               dynamic=['attribute', 'property', 'momentum'])

hoomd.run(totTsteps)                                #Number of time steps to run simulation for.