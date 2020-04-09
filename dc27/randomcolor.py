## Random Colors!
#By Farkes(github.com/ByteWoofer/DC-fur-animations)
##

import dcfurs
import time
import random

class randomcolor:
	def __init__(self):
		self.columns = []
		self.rows = []
		self.interval = 50
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
			self.columns.append(list(range(0,19)))
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
			dcfurs.set_pix_hue(col,row,color)
			
		else:
			self.reset()
