
import matplotlib as mpl
mpl.use('TkAgg')

import numpy as np
import matplotlib.pyplot as plt
import os

from sklearn.metrics.pairwise import rbf_kernel

from sklearn.cluster import SpectralClustering
from sklearn.cluster import KMeans

class Clustering():

	def __init__(self, samples):
		self.samples = samples
		self.affinity = None

	def generateAffinityMatrix(self):
		A = []
		X = []
		nrows = len(self.samples)
		ncols = len(self.samples[0])

		for i in range(nrows):
			X.append(self.samples[i])

		A = rbf_kernel(X,X, gamma=None)	
		return A

	def spectralClustering(self, n_clusters=3):

		# affinity = self.generateAffinityMatrix()

		method = SpectralClustering(n_clusters=n_clusters, eigen_solver=None)

		labels = method.fit_predict(self.samples)

		return labels

	def kMeans(self, n_clusters=3):

		method = KMeans(n_clusters=n_clusters)

		labels = method.fit_predict(self.samples)

		return labels

def readData():
	dir_path = os.path.dirname(os.path.realpath(__file__))

	id_list = []
	data = []

	with open(os.path.join(dir_path, "data.csv"), "r") as file:
		content = file.read().split("\n")
		for row in content:

			if row == "":
				continue

			items = row.split(",")
			id_list.append(items[0])

			values = items[1:]
			temp = []
			for val in values:
				temp.append(float(val))

			data.append(temp)

	return id_list, data

def writeLabels(labels, id_list = None):

	dir_path = os.path.dirname(os.path.realpath(__file__))

	with open(os.path.join(dir_path, "labels.csv"), "w") as file:

		if id_list is not None:
			zipped = zip(id_list, labels)
			out = [",".join([str(a[0]),str(a[1])]) for a in zipped]
		else:
			out = [str(a) for a in labels]
		
		out = "\n".join(out)
		file.write(out)

	return True


if __name__ == "__main__":

	id_list, data = readData()

	clustering = Clustering(data)

	clustering.spectralClustering()


