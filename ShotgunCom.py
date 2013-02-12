import sys
from shotgun_api3 import Shotgun

class ShotgunServer(object):

	def __init__(self, url, appName, apiKey):
		self.url = url
		self.appName = appName
		self.apiKey = apiKey
		

	def connect(self):	
		#Connect to server or output the error
		try:
			self.sg = Shotgun(self.url, self.appName, self.apiKey)
			return self.sg;
		except Exception, e:
			print "ERROR: %s" % (e)
			#raw_input("Press a key to exit the program")
			sys.exit()
			
	def addShot(self, clip, seq, sc):
		# find the task template
		filters = [ ['code','is', 'El Americano shot template' ] ]
		template = self.sg.find_one('TaskTemplate',filters)
		#find the seq
		filters = [ ['code','is', seq ] ]
		sg_sequence = self.sg.find_one('Sequence',filters)
		#find the scene
		filters = [ ['code','is', sc ] ]
		sg_scene = self.sg.find_one('Scene',filters)

		cutDuration = int(clip.outPoint) - int(clip.inPoint)


		#add a new Shot
		data = { 
				'project': {'type':'Project','id':64},
	         	'code': clip.name,
	         	'task_template': template,
	         	'sg_head_in': 0,
	         	'sg_cut_in' : clip.inPoint,
	         	'sg_cut_out' : clip.outPoint,
	         	'sg_tail_out' : clip.duration,
	         	'sg_cut_duration': cutDuration,
	         	'sg_scene' : sg_scene,
	         	'sg_sequence' : sg_sequence
	 			}
		try:
			result = self.sg.create('Shot', data)
		except Exception, e:
			print "Error Creating Shor: %s" % (e)
		else:
			return result


	def uploadThumbnail(self, id, path):
		
		try:
			result = self.sg.upload_thumbnail('Shot', id, path)
		except Exception, e:
			print "Error uploading thumbnail: %s" % (e)
		else:
			return result



		
	

