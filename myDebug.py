class DebugPrint:
	def __init__(self):
		self.debug = True
	
	def setDebug(self,v):
		self.debug = v
	
	def line(self,s):
		if self.debug == True:
			print "DEBUG: ",s
