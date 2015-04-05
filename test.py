from mdb import *
from mcontrol import mControl
 
# Main measurement util for SaC
#
# assumes one or more measurement series as parameter
# will process series sequentially

print "starting measuring process. make sure power readings are activated"
ex("sh CPU_monitor.sh start")

#use symbolic links to map powermeter readings to local files if necessary
powermeterPath = "energy.log"
cpumeterPath = "cpu.log"

tmpPowermeterPath = ".energy.log.tmp"
tmpCpumeterPath = ".cpu.log.tmp"

def ex(p):
	return subprocess.call(p, shell=True)

def readAvgLogValue(logFile):
	f = open("_CPU.txt")
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
	assert os.path.isfile(filename)
	with open(filename) as myfile:
		for line in myfile:
			name, var = line.partition(":")[::2]
			myvars[name.strip()] = var.strip()
	return myvars
	

def measure(logfile, cmd, extraGatherResults):
        command = "time -f \"real:%e\nuser:%U\nsys:%S\nexit:%x\nioin:%I\nioout:%O\nmaxmem:%M\navgmem:%K\" -o "+resultdir+key+" -a timeout " + timeout + " " + cmd 
	#discard old powermeter measurements
	ex(">{0}; >{1}".format(powermeterPath, cpumeterPath)

	exitcode = ex(command)

	ex("cat {0} |sed -e 's/^.*, \([0-8]*\),.*/\1/' | grep \"^[0-9]*$\" > {1}".format(powermeterPath, tmpPowermeterPath))
	ex("cp {0} {1}".format(cpumeterPath, tmpCpumeterPath))
	avgCpu=readAvgLogValue(tmpCpumeterPath)
	avgPower=readAvgLogValue(tmpPowermeterPath)
	results += { "cpu": avgCpu, "power":avgPower, "exit": exitcode }
	if extraGatherResults!=None:
		results.update(extraGatherResults())
	results.update(readLogFile(logfile))
	return results




def measureSaC(seriesName, configId):
	param = getConfigParams(configId)
	print "\n*** measuring {0} ({1})".format(configId, param)

	time.sleep(5)	
	compileResults = measure(".compilelog."+seriesName,"./sac-compile.sh "+param)
	if compileResult["exit"] != 0:
		print "compilation failed."
		runResults = {}
	else:
		compileResults["size"]=os.path.getsize("nbody/tmp.out")
		time.sleep(5)
		runResults = measure(".runlog."+seriesName, "./sac-run.sh")
	results = {}
	results.update(dict(("compile-"+k, v) for (k,v) in compileResults.items())
	results.update(dict(("run-"+k, v) for (k,v) in runResults.items())
	print str(results)
	return results



if len(sys.argv)<=0:
	print "expecting measurement series as parameter"
	sys.exit(1)

mControl(sys.argv, measureSaC)
