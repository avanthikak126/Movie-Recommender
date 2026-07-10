import numpy as np
import time
from sklearn.neighbors import BallTree

print("Generating data...")
matrix = np.random.rand(3706, 6040).astype(np.float64)
print("Data generated.")
start = time.time()
tree = BallTree(matrix, leaf_size=40, metric='euclidean')
print(f"BallTree build time: {time.time() - start:.4f} seconds")
