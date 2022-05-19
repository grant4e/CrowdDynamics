import hoomd
import gsd.hoomd
import numpy as np
import particlePlacer
import renderer
import smartForce

#------------------ Setting up some simulation parameters ---------------------
#
# Here are all of the constants needed by the integrator.
#
#------------------------------------------------------------------------------

sig = 0.5                                                                       # Sigma is diameter of particles
eps = 1                                                                         # Epsilon is a constant affecting Lennard Jones function steepness/energy
kT = 1                                                                        
dt = 0.0001                                                                     # Size of a timestep (If timesteps are too big, particles could escape!)
cell = hoomd.md.nlist.Cell(buffer=0.5)                                          # A cell based neighbour list object used by HOOMD to avoid N^2 behaviour.

#------------------ Designing the initial condition ---------------------------
#
# 1. Pick the size of the box. 
#
# 2. Pick the (smaller) box in which particles will be populated.
#
# 3. Draw some straight wall segments.
#
# PS. The HOOMD simulation box is centered at (0,0,0), 
# so x and y span [-L/2, L/2].
#
#------------------------------------------------------------------------------

L = 50
worldBox = [L,L,0,0,0,0]                                                        # [Width, Height, Length, x0, y0, z0]
boundaryWalls = [hoomd.wall.Plane(origin=(-L/2,0,0), normal=(1,0,0)),
                 hoomd.wall.Plane(origin=(L/2,0,0), normal=(-1,0,0)),
                 hoomd.wall.Plane(origin=(0,L/2,0), normal=(0,-1,0)),
                 hoomd.wall.Plane(origin=(0,-L/2,0), normal=(0,1,0))]           # These are traditional HOOMD planar walls 
particleBox = [-L/3, L/3, -L/6, -L/3]                                           # [topLeftX, topLeftY, bottomLeftX, bottomLeftY]
walls = [(0, L/2, 0, 1), (0, -1, 0, -L/2)]                                      # [(startX, startY, endX, endY)] of the particle based walls

particlePositions = \
    particlePlacer.createCoordinates(*particleBox, spaceBetween=0.75)
nA = len(particlePositions)

wallPositions = []
for w in walls:
    wallPositions += particlePlacer.createCoordinates(*w, spaceBetween=0.2)
nW = len(wallPositions)

rng = np.random.default_rng()
randomOrientations = [(rng.random(),0,0,0) for i in range(nA + nW)] 
aimedOrientations = [(0,0,0,0)] * (nA + nW)

s = gsd.hoomd.Snapshot()
s.particles.N = nA + nW
s.particles.position = particlePositions + wallPositions
s.particles.orientation = aimedOrientations
s.particles.typeid = ([0] * nA) + ([1] * nW)
s.particles.types = ["A", "W"]
s.configuration.box = worldBox

with gsd.hoomd.open(name='IC.gsd', mode='wb') as f:
    f.append(s)

print(f"IC:\n\tActiveParticles: {nA}\n\tWallParticles: {nW}")

#------------------ Create Some Forces To Add to the Simulation! --------------
#
# 1. Pair forces apply to all particles and have to be defined for every 
#       possible particle pairing.
#
# 2. Generic forces are per particle. The one used here is an active force
#       which lets you pick a force vector and optionally a rotational 
#       diffusion.
#
#------------------------------------------------------------------------------

lj = hoomd.md.pair.LJ(nlist=cell, default_r_cut=0.75,)
boundaryLJ = hoomd.md.external.wall.ForceShiftedLJ(walls=boundaryWalls)

lj.params[('A', 'A')] = dict(epsilon=eps, sigma=sig)
lj.params[('A', 'W')] = dict(epsilon=eps, sigma=sig)
lj.params[('W', 'W')] = dict(epsilon=eps, sigma=sig)

boundaryLJ.params['A', 'W'] = dict(epsilon=eps, sigma=sig, r_cut=1)

active = hoomd.md.force.Active(filter=hoomd.filter.Type('A'))
active.active_force['A'] = [1,0,0]
diffusion = active.create_diffusion_updater(trigger=1, rotational_diffusion=0.01)

smart = smartForce.smartForce(energy=10, numActive=nA, exitWidth=2)             # For now this force is only suitable for vertical walls in the middle of the box, with a gap at the origin.
smartUpdater = hoomd.update.CustomUpdater(action=smart, trigger=1)

#------------------ Initializing the simulation -------------------------------
#
#   1. Create the integrator with your integration method of choice ( I use
#       Brownian) and populate it with our constants and forces. 
#   
#   2. Create the simulation using our initial condition state we built above
#
#------------------------------------------------------------------------------

computer = hoomd.device.auto_select()
sim = hoomd.Simulation(device=computer, seed=1)
sim.create_state_from_gsd(filename='IC.gsd')

integrator = hoomd.md.Integrator(dt)
langevin = hoomd.md.methods.Langevin(kT=kT, filter=hoomd.filter.Type('A'))      # By excluding W particles in the integration method, they never receive new positions (are static)
integrator.methods.append(langevin)

integrator.forces.append(lj)
integrator.forces.append(boundaryLJ)
integrator.forces.append(active)                                                # The random active force (move with constant velocity + rotational diffusion)

sim.operations.integrator = integrator
sim.operations.add(diffusion)                                                   

gsd_writer = hoomd.write.GSD(filename='run.gsd',
                             trigger=hoomd.trigger.Periodic(100),
                             mode='wb',
                             filter=hoomd.filter.All())
sim.operations.writers.append(gsd_writer)

#sim.run(5000)                                                                    # An opportunity to do some brownian randomization of the IC
#sim.operations.updaters.append(smartUpdater)                                     # Our custom force is technically a custom updater (less strict set of capabilities, similar performance)
sim.run(50_000)

r = renderer.Renderer(nA, nW, (0.8, 0.8, 0.05), (0.8, 0.05, 0.05))               # Initialize our Fresnel renderer with colors for Active and Wall particles
r.render(sim.state.get_snapshot())                                               # Render of final state