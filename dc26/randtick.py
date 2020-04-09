# Short little time randomness dot generator
# By Farkes

import dcfurs
import random
import time

class randtick:
	def __init__(self):
		self.count = 0
		self.reset = 60
		self.interval = 1000
	def draw(self):
		if(self.count<self.reset):
			self.count+=1
			row = random.randint(0,6)
			col = random.randint(0,17)
			value = random.randint(0,255)
			dcfurs.set_pixel(col,row,value)
		else:
			self.count=0
			dcfurs.clear()
