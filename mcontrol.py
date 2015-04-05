from mdb import *

# Main measurement control loop
#
# interacts with the database to pick the next measurements
# and stores the results
#
# runs indefinetly

# mControl input:
# - seriesNames: list of seriesNames
# - mfun: measurement function that takes a (seriesName, configurationId) and returns a map with measurement results
def mControl(seriesNames, mfun, delay):
	assertSeries(seriesNames)
	currentSeriesIdx = 0
	currentSeries = seriesNames[currentSeriesIdx]
	errorCounter = 0
	totalTime = 0
	totalCount = 0
	while True:
		# change series after 20 errors
		if errorCounter>0 and (errorCounter % 20 == 0) and len(seriesNames)>1:
			currentSeriesIdx = (currentSeriesIdx + 1) % len(seriesNames)
			currentSeries = seriesNames[currentSeriesIdx]
			print "#switching to series "+currentSeries
		nextConfigId = claimNextMeasurement(currentSeries)
		if nextConfigId == None:
			errorCounter += 1
			wait = 1
			#slowly increasing waits between errors
			if errorCounter > 10:
				wait = 5
			if errorCounter > 20:
				wait = 10
			if errorCounter > 30:
				wait = 30
			if errorCounter > 100:
				wait = 120
			print("#no next measurement found, waiting {0} seconds".format(wait))
			time.sleep(wait)
		else:
			#no error, so let's measure
			errorCounter = 0
			t1= time.time()
			mresult = mfun(currentSeries, nextConfigId)
			if mresult!=None:
				storeMeasurements(currentSeries, nextConfigId, mresult)
			t2=time.time()
			totalCount += 1	
			totalTime += (t2-t1)
			remainingTime = (totalTime/totalCount)*countRemainingMeasurements(seriesNames)
			print("#analysis time: "+str(t2-t1)+"s, estimated remaining: "+(remainingTime/60/60)+"h")


def assertSeries(seriesNames):
	#check that series exist
	for s in seriesNames:
		getSeriesId(s)

