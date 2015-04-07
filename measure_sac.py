from mdb import *
import subprocess
import sys
import os.path
import os
import binascii
import time
from mcontrol import mControl
import hashlib
 
# Main measurement util for SaC
#
# assumes one or more measurement series as parameter
# will process series sequentially


def ex(p):
	return subprocess.call(p, shell=True)


#use symbolic links to map powermeter readings to local files if necessary
home = os.path.expanduser("~")+"/"
workingDir = home+"energy/"
powermeterPath = workingDir+"energy.log"
cpumeterPath = home+"/cpu.log"

tmpPowermeterPath = workingDir+".energy.log.tmp"
tmpCpumeterPath = workingDir+".cpu.log.tmp"

timeout = "20m"

msrDir = workingDir+"sac_results/"

SACOUT = workingDir+"nbody/tmp.out"
SACCOMPILE = workingDir+"sac-compile.sh"
SACRUN = workingDir+"sac-run.sh"

ex("sh CPU_monitor.sh start")
ex("mkdir -p "+workingDir)
ex("mkdir -p "+msrDir)
os.chdir(workingDir)
assert os.path.isfile(SACCOMPILE)
assert os.path.isfile(SACRUN)
print "starting measuring process. make sure power readings are activated and directed to "+powermeterPath

def readAvgLogValue(logFile):
	f = open(logFile)
	fline = f.readline()
	ftotal = 0
	fcount = 0
	while fline:
		fcount = fcount + 1
		ftotal = ftotal + float(fline)
		fline = f.readline()
	if fcount > 0:
		cpu = str( ftotal / fcount)
	else: 
		cpu = "-1"
	return cpu

def readLogFile(logfile):
	myvars = {}
	assert os.path.isfile(logfile)
	with open(logfile) as myfile:
		for line in myfile:
			if ":" in line:
				name, var = line.partition(":")[::2]
				myvars[name.strip()] = var.strip()
	return myvars
	

def hashfile(f):
        return hashlib.sha1(open(f, 'rb').read()).hexdigest()

def measure(logfile, cmd, extraGatherResults=None):
        command = "time -f \"real:%e\nuser:%U\nsys:%S\nexit:%x\nioin:%I\nioout:%O\nmaxmem:%M\navgmem:%K\" -o "+logfile+" -a timeout " + timeout + " " + cmd 
	#discard old powermeter measurements
	ex(">{0}; >{1}; >{2}".format(powermeterPath, cpumeterPath,logfile))

	exitcode = ex(command)

	ex("sed -e 's/^.*: \([0-9]*\)$/\\1/' < {0} | grep \"^[0-9]*$\" > {1}".format(powermeterPath, tmpPowermeterPath))
	ex("cat "+tmpPowermeterPath)
	ex("cp {0} {1}".format(cpumeterPath, tmpCpumeterPath))
	avgCpu=readAvgLogValue(tmpCpumeterPath)
	avgPower=readAvgLogValue(tmpPowermeterPath)
	results = { "cpu": avgCpu, "power":avgPower, "exit": exitcode }
	if extraGatherResults!=None:
		results.update(extraGatherResults())
	results.update(readLogFile(logfile))
	return results



#perform a measurement for a specific configuration (in a series) and 
#returns a list of measurement results (map from NFP name to value)
#
#the method is called by the mcontrol infrastructure
#the actual measurement depends heavily on the actual program
#being measured.
#in this case, both the compilation and the running of the compiled
#program are measured. it used measurements from `time` as well as
#measurement from external CPU meters and power meters
def measureSaC(seriesName, configId):
	param = getConfigParams(configId)
	print "\n*** measuring {0} ({1})".format(configId, param)

	time.sleep(5)	
	compileResults = measure(msrDir+".compilelog."+seriesName,SACCOMPILE+" "+param)
	if compileResults["exit"] != "0":
		print "compilation failed."
		runResults = {}
	else:
		compileResults["size"]=os.path.getsize(SACOUT)
		hashv=hashfile(SACOUT)
		compileResults["hash"]=hashv	
		runlogFile=msrDir+".runlog."+seriesName+"."+hashv
		if os.path.isfile(runlogFile):
			print "same binary measured earlier, skipping"
			runResults = {}
		else:
			time.sleep(5)
			runResults = measure(runlogFile, SACRUN)
	results = {}
	results.update(dict(("compile-"+k, v) for (k,v) in compileResults.items()))
	results.update(dict(("run-"+k, v) for (k,v) in runResults.items()))
	print str(results)
	return results



if len(sys.argv)<=1:
	print "expecting measurement series as parameter"
	sys.exit(1)
mControl(sys.argv[1:], measureSaC)
