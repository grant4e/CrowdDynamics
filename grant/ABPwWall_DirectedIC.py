# Initial imports
import sys
import os
import math

# Run Time Params
hoomdPath, gsdPath = ["nas/longleaf/home/grant4e/hoomd-v2.9.7/build", "nas/longleaf/home/grant4e/test_runs/"] 
runFor, partNum = [5, 1000]

                                # fraction of particles that are A
peA = 50                        # activity of A particles
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

# Set some constants
kT = 1.0                        # temperature
threeEtaPiSigma = 1.0           # drag coefficient
sigma = 1.0                     # particle diameter
D_t = kT / threeEtaPiSigma      # translational diffusion constant
D_r = (3.0 * D_t) / (sigma**2)  # rotational diffusion constant
tauBrown = (sigma**2) / D_t     # brownian time scale (invariant)

def roundUp(n, decimals=0):
    '''Round up size of bins to account for floating point inaccuracy'''
    multiplier = 10 ** decimals
    return math.ceil(n * multiplier) / multiplier
    
def getNBins(length, minSz=(2**(1./6.))):
    "Given box size, return number of bins"
    initGuess = int(length) + 1
    nBins = initGuess
    # This loop only exits on function return
    while True:
        if length / nBins > minSz:
            return nBins
        else:
            nBins -= 1

def findBins(lookN, currentInd, maxInds):
    '''Get the surrounding bin indices'''
    maxInds -= 1
    left = currentInd - lookN
    right = currentInd + lookN
    binsList = []
    for i in range(left, right):
        ind = i
        if i > maxInds:
            ind -= maxInds
        binsList.append(ind)
    return binsList

def computeVel(activity):
    "Given particle activity, output intrinsic swim speed"
    # This gives:
    # v_0 = Pe * sigma / tau_B = Pe * sigma / 3 * tau_R
    velocity = (activity * sigma) / (3 * (1/D_r))
    return velocity

def computeActiveForce(velocity):
    "Given particle activity, output repulsion well depth"
    # This is multiplied by Brownian time and gives:
    #          Pe = 3 * v_0 * tau_R / sigma
    # the conventional description of the Peclet number
    activeForce = velocity * threeEtaPiSigma
    return activeForce

def computeTauLJ(epsilon):
    "Given epsilon, compute lennard-jones time unit"
    tauLJ = ((sigma**2) * threeEtaPiSigma) / epsilon
    return tauLJ

# Compute parameters from activities
if peA != 0:                        # A particles are NOT Brownian
    vA = computeVel(peA)
    FpA = computeActiveForce(vA)
else:                               # A particles are Brownian
    vA = 0.0
    FpA = 0.0

tauLJ = computeTauLJ(eps)    
dt = 0.000001 * tauLJ                       # timestep size.  I use 0.000001 for dt=tauLJ* (eps/10^6) generally
simLength = runFor * tauBrown               # how long to run (in tauBrown)
simTauLJ = simLength / tauLJ                # how long to run (in tauLJ)
totTsteps = int(simLength / dt)             # how many tsteps to run
numDumps = float(simLength / 0.01)          # dump data every 0.01 tauBrown.  
dumpFreq = float(totTsteps / numDumps)      # normalized dump frequency.  
dumpFreq = int(dumpFreq)                    # ensure this is an integer

print("Brownian tau in use:"+str(tauBrown))
print("Lennard-Jones tau in use:"+str(tauLJ))
print("Timestep in use:"+str(dt))
print("Epsilon in use:"+str(eps))
print("Total number of timesteps:"+str(totTsteps))
print("Total number of output frames:"+str(numDumps))
print("File dump frequency:"+str(dumpFreq))

# Initialize system

# Calculate desired box area given particle number and density
box_area = (partNum*math.pi*(1/4))/phi

#Calculate desired box dimensions
box_edge = np.sqrt(box_area)


#Number of particles per 1 unit of distance, i.e. wall_part_diam=1/5->5
# particles per 1 unit of distance, that will be generated in order
# to make an impenetrable wall
wall_part_diam = (1/5)

# Calculates number of particles in total for the wall to span the box length
num_wall_part = np.ceil(box_edge/wall_part_diam)

# Total number of particles in simulation
tot_part = int(partNum + num_wall_part)

# List to store particle positions and types
pos = []
typ = []
rOrient = []
pe=[]
activity = []

#starting x location of wall
x_val = -box_edge/2

# Cut off distance of LJ potential
r_cut = 2**(1/6)

#Binning particles to speed up placement and checking for overlap

#Number of bins along either axis given box dimension and bin size of the LJ
# cut off length

NBins = getNBins(box_edge, r_cut)

#Size of bin
sizeBin = roundUp(((box_edge) / NBins), 6)

#Array corresponding to spatial bins.  Stores index of particle
binParts = [[[] for b in range(NBins)] for a in range(NBins)]

#Loop over all particles
for i in range(0, tot_part):
    
    # Checks if particle ID is less than the number of active/mobile particles
    if i < partNum:
        
        #Checks if particle is first to be placed
        if i > 0:
            
            # Initiate 'fail' function to start while loop.  fail=1 labels whether
            # there is too great of particle overlap. fail=0 labels sufficient particle
            # overlap to break loop and save particle location
            fail=1
            
            while fail==1:
                
                # Default value. Labels no overlap before we start to check
                fail=0
                
                #Randomize x and y-location to half of rectangular box (box_edge x 2*box_edge)
                #Be sure particles will not overlap with particle-wall or planar walls (hence -0.7)
                x_loc = (random.rand()-0.5)*(box_edge-0.7)
                y_loc = (random.rand()-1.0)*(box_edge-0.7)
                
                #Convert x and y-locations to positive values spanning 0 to box_edge
                x_loc_temp = x_loc+0.5*(box_edge-1)
                y_loc_temp = y_loc+1.0*(box_edge-1)
                
                # Convert x and y-locations to bin indices
                x_ind = int(x_loc_temp/ sizeBin)
                y_ind = int(y_loc_temp/ sizeBin)
                
                
                #Employ periodic boundary conditions for bins and defines search range
                # to immediate neighbors of bins to check overlap
                if x_ind == 0:
                    x_range = [NBins-1, 0, 1]
                elif x_ind == (NBins-1):
                    x_range = [NBins-2, NBins-1, 0]
                else:
                    x_range = [x_ind-1, x_ind, x_ind+1]
                    
                if y_ind == 0:
                    y_range = [NBins-1, 0, 1]
                elif y_ind == (NBins-1):
                    y_range = [NBins-2, NBins-1, 0]
                else:
                    y_range = [y_ind-1, y_ind, y_ind+1]
                    
                #Loops over neighboring bins
                for ix in x_range:
                    for iy in y_range:
                        
                        #Check if particles in neighboring bin
                        if len(binParts[ix][iy]) != 0:
                            
                            #Loop over particles in neighboring bin
                            for h in range(0, len(binParts[ix][iy])):
                                
                                #Calculate distance between reference particle and particles in neighboring bins
                                r_dist = ((pos[binParts[ix][iy][h]][0]-x_loc)**2 + (pos[binParts[ix][iy][h]][1]-y_loc)**2)**0.5
                                
                                # If overlap is too great, label fail=1 to re-randomize reference particle
                                # location
                                if r_dist<0.7:
                                    fail=1

        else:
            
            #Randomize location and bin first particle
            
            x_loc = (random.rand()-0.5)*(box_edge-1)
            y_loc = (random.rand()-1.0)*(box_edge-1)
            
            x_loc_temp = x_loc+0.5*(box_edge-1)
            y_loc_temp = y_loc+1.0*(box_edge-1)
            
            x_ind = int(x_loc_temp/ sizeBin)
            y_ind = int(y_loc_temp/ sizeBin)
            
        #As it's in a good location, add particle index to bin
        binParts[x_ind][y_ind].append(i)
        
        #Random value to determine particle type (activity, softness, etc.)
        typ_val = random.rand()
        
        #Random active force orientation
        angle = - (math.Atan2(y_loc, x_loc) - math.Atan2(0, 1))
        
        #Zero active force in z-dimension
        f_z = 0.

        #Label particle type
        typ.append(0)
        
        #Calculate x and y activity given angle and activity
        f_x = (np.cos(angle)) * peA
        f_y = (np.sin(angle)) * peA
        
        #Label particle activity
        pe.append(peA)
   
        #Save location vector of particle given that it passed overlap criterion
        pos.append((x_loc, y_loc, 0.5))
        
        #Save activity vector of particle
        tuple = (f_x, f_y, f_z)
        activity.append(tuple)
    else:
        #Particle is part of impenetrable wall that spans x-axis
        
        #Checks to be sure particle isn't in location of wall opening
        if np.abs(x_val)>1.0:
            
            #Saves position if not in opening
            pos.append((x_val, 1.0, 0.5))
            typ.append(1)

            #Zero activity for immovable particles
            tuple = (0, 0, 0)
            activity.append(tuple)
            pe.append(0)
            
            #Increase x-location by frequency of particles defined
            x_val+=wall_part_diam
        else:
            #In opening of wall, so merely increase x-location by frequency of particles
            # defined
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

#Labels each particle with particles types of 0, 1, and 2 as 'A', 'B', and 'C' respectively for hoomd
char_types = []
for i in typ:
    char_types.append( chr(ord('@') + i+1) )
    
#Label possible particles types of 0, 1, and 2 as 'A', 'B', and 'C' respectively for hoomd.
# Length of array corresponds to number of possible types
unique_char_types=['A', 'B']

# total number of particles placed (smaller than tot_part as some were excluded due to wall opening)
real_tot_part = len(pos)

#Initialize hoomd
hoomd.context.initialize()

#Create data step that initiates a simulation box with given number of particles
snap = hoomd.data.make_snapshot(N = real_tot_part,
                                box = hoomd.data.boxdim(Lx=box_edge,
                                                        Ly=box_edge*2,
                                                        dimensions=2),
                                particle_types = unique_char_types)

#Define and label locations and types of particles for HOOMD
snap.particles.position[:] = pos[:]
snap.particles.typeid[:] = typ[:]
snap.particles.types[:] = char_types[:]

#Input locations and types of particles into data step for HOOMD
system = hoomd.init.read_snapshot(snap)

#Define repulsive strength of boundary walls
eps_wall=1.0

#Define planar walls that span simulation box border (non-periodic boundary conditions)
wallstructure=md.wall.group()
wall_x = wallstructure.add_plane((box_edge/2, 0.0, 0.0),normal=(-1.0, 0.0, 0.0), inside=True)
wall_mx = wallstructure.add_plane((-box_edge/2, 0.0, 0.0),normal=(1.0, 0.0, 0.0), inside=True)
wall_y = wallstructure.add_plane((0.0, box_edge, 0.0),normal=(0.0, -1.0, 0.0), inside=True)
wall_my = wallstructure.add_plane((0.0, -box_edge, 0.0),normal=(0.0, 1.0, 0.0), inside=True)

#Define forces of all walls on each particle type
wall_force_fslj=md.wall.slj(wallstructure, r_cut=2**(1/6), name='p')
wall_force_fslj.force_coeff.set('A', epsilon=1.0, sigma=1.0, r_cut=2**(1/6))
wall_force_fslj.force_coeff.set('B', epsilon=1.0, sigma=1.0, r_cut = 2**(1/6))

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
lj.pair_coeff.set('A', 'B', epsilon=eps_wall, sigma=1.0)
lj.pair_coeff.set('B', 'B', epsilon=1.0, sigma=1.0)

# Brownian integration
brownEquil = 10000

hoomd.md.integrate.mode_standard(dt=dt)

#Calculate movement of only mobile particles
bd = hoomd.md.integrate.brownian(group=gA, kT=kT, seed=1)

hoomd.run(brownEquil)

#Define active forces set earlier
hoomd.md.force.active(group=all,
                      seed=1,
                      f_lst=activity,
                      rotation_diff=D_r,
                      orientation_link=False,
                      orientation_reverse_link=True)

gsdName = "ABPwWall" + ".gsd"

# Remove .gsd files if they exist
try:
    os.remove(gsdName)
except OSError:
    pass

#Specify how often and what to save
    
# Options for what to save (dynamic)
# 'attribute' important quantities: total particle number (N), types (types), which particles are each type (typeid),
#  diameter of particle (diameter)
#'property' important quantities: particle position (position), particle orientation in quaternions (orientation)
#'momentum': I save this but it's unimportant.  It saves velocity, angular momentum, and image.  I looked into this and the v
# velocity calculation is incorrect in my current version of hoomd.  THe newer version seems to have fixed this I believe. They mis-calculated
# the quaternions to angles.
#'topology' is another option for working with molecules.
    
hoomd.dump.gsd(gsdName,
               period=dumpFreq,
               group=all,
               overwrite=False,
               phase=-1,
               dynamic=['attribute', 'property', 'momentum'])

#Number of time steps to run simulation for.
hoomd.run(totTsteps)