import itertools
import numpy as np

# Small helper function that makes use of some itertools and numpy functions
# to neatly create a 2D coordinate grid.

def createCoordinates(x1, y1, x2, y2, spaceBetween):

    startX = min(x1, x2)
    endX = max(x1, x2)

    startY = min(y1, y2)
    endY = max(y1, y2)
    
    xVals = [x1] if x1 == x2 else np.arange(startX, endX, step=spaceBetween)
    yVals = [y1] if y1 == y2 else np.arange(startY, endY, step=spaceBetween)
    xyCoords = list(itertools.product(xVals, yVals))
    x,y = zip(*xyCoords)

    return list(zip(x,y, [0] * len(x)))

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    coordinateList = list(createCoordinates(0,0,5,5,0.2))
    print(coordinateList)
    x,y,z = zip(*coordinateList)
    plt.scatter(x, y)