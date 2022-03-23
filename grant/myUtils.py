import numpy as np

# Creates a 2D simple cubic lattice from topLeft to bottomRight
# where each point is vertically and horizontally spaceBetween away from its neighbour 
# Inputs:   float (topLeft, bottomRight, spaceBetween)
# Outputs:  Array of (x,y,z) tuples
def makeGrid(topLeft, bottomRight, spaceBetween):
    X, Y = np.meshgrid(np.arange(start=topLeft[0], stop=bottomRight[0], step=spaceBetween),
                        np.arange(start=topLeft[1], stop=bottomRight[1], step=spaceBetween))
    X = X.ravel()                                       # Flatten both ndarrays
    Y = Y.ravel()          
    Z = [0.5]*len(X)                                    # Z Hard Coded to 0.5             
    return list(zip(X, Y, Z)) 

if __name__ == "__main__":    
    print(makeGrid((1,1), (3,3), 0.2))
