## Random Colors!
#By Farkes(github.com/ByteWoofer/dcfurs-badge-scripts)
##

import dcfurs
import time
import random

class randomcolor:
	def __init__(self):
		self.columns = []
		self.intensity = 50
		self.rows = []
		self.interval = 20
		self.hueLow=0
		self.hueHigh=255
		print("Initialized randoms!")

	def reset(self):
		self.hueHigh = random.randint(10,255)
		self.hueLow = random.randint(0,self.hueHigh)
		print("hueLow: ",self.hueLow,"  --  hueHigh: ",self.hueHigh)
		self.rows = list(range(0,7))
		self.columns = []
		for i in range(0,7):
			if(i==0):
				self.columns.append(list(range(1,17)))
			if(i==5):
				self.columns.append(list(range(0,7)+range(11,18))
			if(i==6):
				self.columns.append(list(range(1,6)+range(12,17))
	def draw(self):
#		print(len(self.rows))
		if(len(self.rows) != 0):
			row = random.choice(self.rows)
			col = random.choice(self.columns[row])
#			print(self.columns)
			self.columns[row].remove(col)
			if(len(self.columns[row]) == 0):
				self.rows.remove(row)
			color = random.randint(self.hueLow,self.hueHigh)
			dcfurs.set_pix_hue(col,row,color,self.intensity)
			
		else:
			self.reset()
