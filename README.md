# CrowdDynamics

HOOMD3 simulations of particles attempting to escape through an exit.

Some notable features of the code contained in this repository:
<ul>
  <li>Various particle types:
    <ul>
      <li>Diffusive Brownian Particles</li>
      <li>Random Active Brownian Particles</li>
      <li>Brownian Particles that are biased towards the exit</li>
    </ul>
  </li>
  <li>The ability to generate starting conditions that are randomized by simulating grid aligned particles experiencing Brownian motion</li>
  <li>The placement of wall segments made up of static particles</li>
  <li>A template for writing custom updaters/behaviours for new particle types</li>
  
</ul>
