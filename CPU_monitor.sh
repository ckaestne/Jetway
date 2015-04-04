if [ -e "CPU-PID.txt" ] ; then # Checks if the file CPU-PID.txt exists
	echo stopping CPU monitor
	kill -9 "$(cat CPU-PID.txt)"	# Kills the PID stored in CPU-PID.txt
	rm CPU-PID.txt	# Deletes the temporary file CPU-PID.txt containing the PID
else
	echo starting CPU monitor
	nohup ./run_CPU.sh > /dev/null 2>&1 & 	# Activates the CPU Monitor
	echo $! > CPU-PID.txt	# Stores the PID in a temporary file CPU-PID.txt
fi	
