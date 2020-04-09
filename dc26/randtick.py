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
			if row == 0:
				col = random.randint(1,16)
			elif row == 5:
				col = random.choice(list(range(0,8))+list(range(11,18)))
			elif row == 6:
				col = random.choice(list(range(1,7))+list(range(12,17)))
			else:
				col = random.randint(0,18)
			value = random.randint(50,255)
			dcfurs.set_pixel(col,row,value)
			# print(col," ",row)
		else:
			self.count=0
			dcfurs.clear()
