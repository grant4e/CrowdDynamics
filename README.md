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

<h2>Getting Started</h2>

You can replicate my Conda environment with:

```
conda env create --file hoomd3-conda-env.txt 
```

I've tried to keep my code fairly modular and well commented. In addition I have diagrammed the structure of HOOMD 3.0's newly restructured API:

![Code Structure Diagram](/code_structure.png)

Start with main.py, which imports and uses some other modules to place particles in their initial condition, or to render images of the simulation state, as examples.
