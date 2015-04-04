import subprocess
import sys
import os.path
import os
import binascii
import time
import hashlib

timeout = "5m"

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


def stop():
	print("All tasks complete.\n")

def hashfile(f):
	return hashlib.md5(open(f, 'rb').read()).hexdigest()

def measure(key, cmd):
        command = "time -f \"real:%e\nuser:%U\nsys:%S\nexit:%x\nioin:%I\nioout:%O\nmaxmem:%M\navgmem:%K\" -o "+resultdir+key+" -a timeout " + timeout + " " + cmd 

	subprocess.call("echo " + key + ">> "+resultdir+key, shell=True)

	exitcode = subprocess.call(command, shell=True)

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
		ex("wc -c nbody/tmp.out") 
		ex("wc -c nbody/tmp.out >> "+resultdir+"compile-"+key) 
		hashc = hashfile("nbody/tmp.out")
		ex("echo bin-hash:"+hashc+" >> "+resultdir+"compile-"+key) 
		sys.stdout.write("done"),
		time.sleep(0.1)
		print(".\n")
		print(hashc)
		if os.path.isfile(resultdir+"run-"+hashc):
			print("already measured binary "+hashc)
		else:
			measure("run-"+hashc, "./sac-run.sh")
        sys.stdout.write("done"),
	time.sleep(0.1)
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

