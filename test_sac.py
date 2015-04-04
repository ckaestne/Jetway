import subprocess
import sys
import os.path
import os
import binascii
import time
import hashlib

timeout = "20m"

def ex(p):
	subprocess.call(p, shell=True)

if len(sys.argv)==2:
	runid = sys.argv[1]
else :
	runid = binascii.hexlify(os.urandom(4))
resultdir = "sac_results/"+runid+"/"
ex("mkdir -p "+resultdir)

print("reporting results in "+resultdir+"\n")



def start():
	print("Starting up...\n")
	print("Initializing Power Meter...\n")
	subprocess.call("./power_meter.sh -start", shell=True) # Activate Power Meter
	print("Initializing CPU Monitor...\n")
	subprocess.call("./CPU_monitor.sh -start", shell=True) # Activate CPU Monitor


def stop():
	print("All tasks complete.\n")
	print("Turning Off Power Meter...\n")
	subprocess.call(["./power_meter.sh -stop"], shell=True) #Deactivate Power Meter
	print("Turning Off CPU Monitor...\n")
	subprocess.call(["./CPU_monitor.sh -stop"], shell=True) #Deactivate CPU Monitor


def measure(key, cmd):
        command = "time -f \"real:%e\nuser:%U\nsys:%S\nexit:%x\nioin:%I\nioout:%O\nmaxmem:%M\navgmem:%K\" -o "+resultdir+key+" -a timeout " + timeout + " " + cmd 

	subprocess.call(">Power_Consumption.txt; > CPU-Utilization.txt", shell=True)
	subprocess.call("echo " + key + ">> "+resultdir+key, shell=True)

	exitcode = subprocess.call(command, shell=True)

	subprocess.call("cp Power_Consumption.txt _power.txt", shell=True)
	subprocess.call("cp CPU-Utilization.txt _CPU_usage.txt", shell=True)
	subprocess.call(["grep -o M..all........ _CPU_usage.txt | sed -e 's/M  all   //' > _CPU.txt"], shell=True)
	f = open("_CPU.txt")
	fline = f.readline()
	ftotal = 0
	fcount = 0
	while fline:
		fcount = fcount + 1
		ftotal = ftotal + float(fline)
		fline = f.readline()
	g = open("_power.txt")
	gline = g.readline()
	gtotal = 0
	gcount = 0
	while gline:
		gcount = gcount + 1
		gtotal = gtotal + float(gline)
		gline = g.readline()
	if gcount > 0:
		power = str( gtotal / gcount)
	else: 
		power = "-1"
	if fcount > 0:
		cpu = str( ftotal / fcount)
	else: 
		cpu = "-1"

	subprocess.call("echo cpu:" + cpu + " >> "+resultdir+key, shell=True)
	subprocess.call("echo power:" + power + " >> "+resultdir+key, shell=True)
	return exitcode

def shouldskip(key):
	return os.path.isfile(resultdir+"compile-"+key)

def analyze(key, param):
	print("***** running " + key +" /"+runid+"\n")
	if os.path.isfile("1024_bodies_dynamic.sacbugreport"):
		subprocess.call("rm 1024_bodies_dynamic.sacbugreport", shell=True)
	exitcode = measure("compile-"+key, "./sac-compile.sh "  + param)
	if os.path.isfile("1024_bodies_dynamic.sacbugreport") or (exitcode != 0):
		print("compilation failed.\n")
		ex("mv 1024_bodies_dynamic.sacbugreport "+resultdir+"compile-"+key+".sacbugreport")
	else:
		ex("wc -c nbody/tmp.out >> "+resultdir+"compile-"+key) 
		sys.stdout.write("done"),
		time.sleep(5)
		print(".\n")
		measure("run-"+key, "./sac-run.sh")
        sys.stdout.write("done"),
	time.sleep(5)
	print(".\n")



#run a list of tasks (each a tuple of key and parameter)
def runall(todos):
	num = len(todos)
	count = 0
	starttime = time.time()
	for todo in todos:
		if shouldskip(todo[0]):
			print("*** skipping "+todo[0])
			num = num - 1
		else:
			t1 = time.time()
			analyze(todo[0],todo[1])
			t2 = time.time()
			count = count + 1
			estimatedtotaltime = (t2-starttime)/count*num
			print("analysis time: "+str(t2-t1)+"s, estimated remaining: "+str((estimatedtotaltime - (t2-starttime))/60/60)+"h")


todos = []
with open("sac.list") as f:
	lines = f.readlines()
	for idx in range(0, (len(lines)/3 - 1)):
		key = lines[idx*3+1].strip()
		if len(key) > 255:
			newkey = hashlib.md5(key).hexdigest()
			ex("echo \""+key+"\" > "+resultdir+"/"+newkey+".key")
			key = newkey
		param = lines[idx*3+2].strip()
		todos.append( (key, param) )

start()
runall(todos)
print("All tasks complete.\n")
stop()

