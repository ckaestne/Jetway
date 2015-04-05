#!/usr/bin/python
import MySQLdb
import ConfigParser

configParser = ConfigParser.RawConfigParser()   
configFilePath = r'.dbconfig'
configParser.read(configFilePath)

db = MySQLdb.connect(host="feature.isri.cmu.edu", # your host, usually localhost
                     user=configParser.get('db','user'), # your username
                      passwd=configParser.get('db','passwd'), # your password
                      db="measurement") # name of the data base
cur = db.cursor() 


seriesIdCache = {}
nfpIdCache = {}


def execSqlOne(sql):
	cur.execute(sql)
	r=cur.fetchone()
	if r==None:
		return None
	return r[0]

#looks up the series. fails if series does not exist
def getSeriesId(seriesname):
	if seriesname not in seriesIdCache:
		cur.execute('select SeriesId from Series where name="'+seriesname+'"')
		r=cur.fetchone()
		if r==None:
			print "Series "+seriesname+" not found in measurement database. Quitting."
			sys.exit(1)
		seriesIdCache[seriesname]=r[0]
	return seriesIdCache[seriesname]

#looks up an NFP, creates that NFP if it does not exist
def getNFPId(nfp):
	if nfp not in nfpIdCache:
		cur.execute('select ID from NFP where name="'+nfp+'"')
		r=cur.fetchone()
		if r==None:
			cur.execute('insert into NFP (Name) values ("'+nfp+'")')
			cur.execute('select ID from NFP where name="'+nfp+'"')
			cur.commit()
			r=cur.fetchone()
		nfpIdCache[seriesname]=r[0]
	return nfpIdCache[seriesname]




#resultmap is a map from NFP-names to string values representing results
def storeMeasurements(seriesName, configId, resultMap):
	global cur
	assert resultMap.size()>0
	sql = 'insert into MResults (ConfigurationID, SeriesID, NFPID, Value) values '
	for k, v in resultMap:
		sql += '({0}, {1}, {2}, "{3}"), '.format(configId, getSeriesId(seriesName), getNFPId(k), v)
	cur.execute(sql[:-2])
	db.commit()


#finds the next available measurement in the todo table
#returns the configurationId or None if there is no remaining configuration (or if there is a concurrency issue)
#deletes the entry from the todo table, so that it's not claimed again
def claimNextMeasurement(seriesName):
	db.commit()
	try:
		sid=getSeriesId(seriesName)
		nextConfig = execSqlOne("select ConfigurationID from Todos where SeriesId={0} order by priority, ConfigurationID Limit 1".format(sid))
		if nextConfig != None:
			cur.execute("delete from Todos where SeriesId={0} and ConfigurationId={1}".format(sid,nextConfig))
		db.commit();
		return nextConfig
	except Exception, e:
		print e
		db.rollback()
		return None

def countRemainingMeasurements(seriesNames):
	return execSqlOne("select count(*) from Todos, Series where "+
		" or ".join(map((lambda x: '(Series.Name="'+x+')'),seriesNames)))


def getConfigParams(configId):
	return execSqlOne("select CompilerOptions from Configurations where ID="+configId)	
