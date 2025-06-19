#!/usr/bin/python3
import time
from flask import Flask, render_template, escape
#from __future__ import print_function
import pyslurm
import hostlist


def getjobs():
	a = pyslurm.job()
	joblist = a.get()
	stats = str(len(joblist))
	
	pending = str(len(a.find("job_state", "PENDING")))
	running = str(len(a.find("job_state", "RUNNING")))
	
	return stats,pending,running


def getnodedetail():
	nodedict = {}
	nodes = pyslurm.node()
	nodelist = nodes.get()
	#print(nodelist)
	
	meta_fields = [
		"partitions",
		"state",
		"reason",

	]


	for key, value in nodelist.items():
		#print(key, value)
		nodedeets = []
		for sub_key in value.keys():
			if sub_key in meta_fields:

				nodedeets.append(str(value[sub_key]))
					
		nodedict[key] = nodedeets
		#print(nodedict)

		
	return nodedict 

def getstats():
	statslist = []
	temp = pyslurm.statistics()
	stats = temp.get()
	statlist = ""

	meta_fields = [

		"jobs_submitted",
		"jobs_started",
		"jobs_completed",
		"jobs_canceled",
		"jobs_failed",
		"jobs_pending",
		"jobs_running",

	]
	date_fields = [
		"req_time_start",
	]

	for key, value in stats.items():
		if key in meta_fields:
			statlist += key + ": " + str(value)
			statslist.append(value)
		if key in date_fields:
			ddate = pyslurm.epoch2date(value)
			statlist += key + ": " + str(ddate)
			statslist.append(str(ddate))
	
	#print(statlist)
	return statslist



def getjobdetail():
	jobdict = {}
	a = pyslurm.job()
	joblist = a.get()
	#return joblist
	meta_fields = [
		"command",
		"nodes",
		"partition",
		"workdir",
		"num_tasks",
		"job_state",
	]
	date_fields = [
		"start_time",
		"end_time",
		"elligible_time",
	]
	
	nodelist = [
		"nodes",
	]
	
	for key, value in joblist.items():
		#print(key, value)#jobdeets.append(key)
		jobdeets = []
		for part_key in sorted(value.keys()):
			#print (part_key, value[part_key])
			if part_key in date_fields:
				#print("arse " + str(value[part_key]))
				ddate = pyslurm.epoch2date(value[part_key])
				if "1970" in str(ddate):
					jobdeets.append("2020,07,07,11,01,01")
				
				else: 
					jobdeets.append(time.strftime('%Y,%m,%d,%H,%M,%S', time.localtime(value[part_key])) )
				#jobdeets.append("\t{0:20} : {0}".format(ddate))
			if part_key in meta_fields:
				jobdeets.append(str(value[part_key]))
			
		jobdict[key] = jobdeets		
	#print(jobdict)
	return jobdict
		


app = Flask(__name__)


@app.route('/')
def index():
	stats,pending,running = getjobs()
	newjobdict = getjobdetail()
	statlist = getstats() 
	corelist = []
	counter = 0
	jobcounter = 0
	allocated = 0
	totalcores = 0
	mixed = 0
	down = 0
	idle = 0
	IandD = 0
	reserved = 0
	idlelist = ""
	downlist = ""
	IandDlist = ""
	reservedlist = ""
	#return 'total jobs: ' + stats + ' Pending: ' + pending + ' running: ' + running 
	nodestats = getnodedetail()
	statusupdate = "Since: " + str(statlist[0]) + "<br />" + "Submitted: " + str(statlist[1]) + "<br />" + "Started: " + str(statlist[2]) + "<br />" + "Completed: " + str(statlist[3]) + "<br />" + "Canceled: " + str(statlist[4]) + "<br />" + "Failed: " + str(statlist[5]) + "<br />" + "Pending: " + str(statlist[6]) + "<br />" + "Running: " + str(statlist[7]) + "<br />" 

	for i in range(1281):
		corelist.append(0)
	
	for jobs in newjobdict:
		#print (corelist)
		if newjobdict[jobs][2] == "RUNNING":
			jobcounter += 1
			corelist[int(newjobdict[jobs][4])] += 1	
			totalcores += int(newjobdict[jobs][4])
	charttotalcores = int((totalcores/20000) * 100)
	#charttotalcores = totalcores
	coreschart = "['Cores', 'Number of jobs'],"
	coreschart2 = "['Cores', 'Number of jobs'],"
	for value in corelist:
		counter += 1
		if value >= 1:
			coreschart += "[ '" + str(counter - 1) + " core jobs', " + str( value * (counter - 1) ) + "],"
			coreschart2 += "[ '" + str(counter - 1) + " core jobs', " + str(value) + "],"
	
	coreschart += "[ 'Idle cores', " + str( (20000 - totalcores) ) + "],"

	for node in nodestats:
		
		if nodestats[node][2] == "ALLOCATED":
			allocated += 1
		if nodestats[node][2] == "MIXED":
			mixed += 1
		if nodestats[node][2] == "DOWN*":
			down += 1
			downlist += node + ": " + nodestats[node][1] + "<br /> "
		if nodestats[node][2] == "IDLE":
			idle += 1
			idlelist += node + ": " + nodestats[node][1] + "<br /> "
		if nodestats[node][2] == "IDLE+DRAIN":
			IandD += 1
			IandDlist += node + ": " + nodestats[node][1] + "<br /> "
		if nodestats[node][2] == "RESERVED":
			reserved += 1
			reservedlist += node + ": " + nodestats[node][1] + "<br /> "

	

	nodestatus = "<hr />Allocated nodes: " + str(allocated) + "<hr />" + "Mixed nodes: " + str(mixed) + "<hr />" + "Down nodes: " + str(down) + "<br>" + downlist + "<hr />" + "Idle nodes: " + str(idle) + "<br>" + idlelist + "<hr />" + "Drained nodes: " + str(IandD) + "<br>" + IandDlist + "<hr />" + "Reserved nodes: " + str(reserved) + "<br>" + reservedlist + "<hr />"
	return render_template('index_slurm.html', stats=stats, running=running, pending=pending, nodes=nodestatus, statlist=statusupdate, totalcores=charttotalcores, coreschart=coreschart, coreschart2=coreschart2)



@app.route('/partitions')
def partitions():
	newjobdict = getjobdetail()
	bob = ""
	for jobs in newjobdict:
		#print(newjobdict[jobs])	
		bob = bob + '["' + newjobdict[jobs][5] + '", "' + str(jobs) + '", new Date (' + newjobdict[jobs][6] + '), new Date (' + newjobdict[jobs][1] + ') ],\n'
		#bob = escape(bob)
	return render_template('nodelist2.html', joblist=str(bob))	
	#return bob




@app.route('/nodes')
def nodes():
        newjobdict = getjobdetail()
        bob = ""
        for jobs in newjobdict:
                #print(newjobdict[jobs])
                bob = bob + '["' + newjobdict[jobs][3] + '", "' + str(jobs) + '", new Date (' + newjobdict[jobs][6] + '), new Date (' + newjobdict[jobs][1] + ') ],\n'
                #bob = escape(bob)
        return render_template('nodelist2.html', joblist=str(bob))
        #return bob
	


if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0')


