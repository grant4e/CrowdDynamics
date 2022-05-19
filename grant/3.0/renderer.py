import warnings
import fresnel
import IPython
import packaging.version
import math
import warnings

# This renderer is mostly boilerplate /template code from the HOOMD 3.0 tutorials found in the glotzerlab official docs

class Renderer():

    FRESNEL_MIN_VERSION = packaging.version.parse("0.13.0")
    FRESNEL_MAX_VERSION = packaging.version.parse("0.14.0")

    if ('version' not in dir(fresnel) or packaging.version.parse(
                fresnel.version.version) < FRESNEL_MIN_VERSION
                or packaging.version.parse(
                    fresnel.version.version) >= FRESNEL_MAX_VERSION):
            warnings.warn(
                f"Unsupported fresnel version {fresnel.version.version} - expect errors."
            )

    def __init__(self, numActive, numWall, activeColor, wallColor):
        self.device = fresnel.Device()
        self.tracer = fresnel.tracer.Path(device=self.device, w=2000, h=2000)
        self.nA = numActive
        self.nW = numWall
        self.aCol = activeColor                                                 # Colors are floating point 0 to 1 values of the form (r,g,b)
        self.wCol = wallColor


    def render(self, snapshot):
        W = snapshot.configuration.box[0]
        L = snapshot.configuration.box[1]
        scene = fresnel.Scene(self.device)
        geometry = fresnel.geometry.Sphere(scene,
                                        N=len(snapshot.particles.position),
                                        radius=0.5)
        geometry.material.solid = 0.0     
        geometry.material.primitive_color_mix = 1.0                                   
        geometry.color[:self.nA] = fresnel.color.linear(self.aCol)
        geometry.color[self.nA:] = fresnel.color.linear(self.wCol)
        geometry.position[:] = snapshot.particles.position[:]
        geometry.outline_width = 0.04

        # NOTE: Z dimension of box has been reduced, else box is way too big (2D constrained).

        box = fresnel.geometry.Box(scene, [W, L, 2, 0, 0, 0], box_radius=.02)

        scene.lights = [
            fresnel.light.Light(direction=(0, 0, 1),
                                color=(0.8, 0.8, 0.8),
                                theta=math.pi),
            fresnel.light.Light(direction=(1, 1, 1),
                                color=(1.1, 1.1, 1.1),
                                theta=math.pi / 3)
        ]
        scene.camera = fresnel.camera.Orthographic(position=(L * 2, L, L * 2),
                                                look_at=(0, 0, 0),
                                                up=(0, 1, 0),
                                                height=L * 1.4 + 1)
        scene.background_color = (1, 1, 1)
        
        # Currently this outputs an image to an IPython session. File writing is also possible
        return IPython.display.Image(self.tracer.sample(scene, samples=1000)._repr_png_())