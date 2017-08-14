#!/usr/bin/env python

import configparser
import graphitesend
import glob
import time
import commands
import json
import socket
import os
import sys
import multiprocessing as mp
from shutil import copyfile
from shutil import copytree
from optparse import OptionParser


verbose=True
values_to_log=False

parser = OptionParser()

parser.add_option("-c", "--config", dest="configpath",
		help="Path to config file", metavar="FILE")

(options, args) = parser.parse_args()

if options.configpath:
	suff="/"
	if not options.configpath.endswith(suff):
		options.configpath=options.configpath+"/"

	print "configpath is " + options.configpath
else: 
	options.configpath=""


if not os.path.isfile(options.configpath + 'config.ini'):
	copyfile("config.ini.example", options.configpath + 'config.ini')

if not os.path.isdir(options.configpath + 'stats.d'):
	copytree("stats.d.examples", options.configpath + 'stats.d')


# Read config values from config.ini. Might switch to yml config
config = configparser.ConfigParser()
config.read_file(open(options.configpath + 'config.ini'))
HOST = config['statsfeeder']['Graphite_Host']
PORT = config['statsfeeder']['Graphite_Port']
FREQ = config['statsfeeder']['Frequency']
STATSDIR = config['statsfeeder']['Stats_dir']
ENV = config['statsfeeder']['Env']

qstatsfeeder_stats = mp.Queue()
qstatsfeeder_statsdata= mp.Queue()

 
if ENV == "DEV":
	dryrun=True
else:
	dryrun=False

def main():

	# Test Graphite Connection
	while check_server(HOST,int(PORT)) is False:
		print "Error connecting to " + HOST + " on port " + PORT
		time.sleep(3)

	# Get a list of modules in the modules directory
	enabled_stats = [w.replace(str(STATSDIR), "") for w in glob.glob(str(STATSDIR+"*"))]

	print "Starting with the following modules:"
	print enabled_stats

	if verbose: 
		print str(time.asctime( time.localtime(time.time()) )) + " Inserting metrics every " + FREQ + " secs"

	while True:
		totalStartTime=time.time()

		#Re-read modules directory in case new ones were added
		enabled_stats = [w.replace(str(STATSDIR), "") for w in glob.glob(str(STATSDIR+"*"))]

		g = graphitesend.init(graphite_server=HOST, prefix='', system_name='')

		statsdata = {}
		statsfeeder_stats = {}

		statsdataall, statsfeeder_statsall = get_stat_info(enabled_stats)

		# Remove empty
		statsdatalist = [x for x in statsdataall if x != {}]
		statsfeeder_statslist = [x for x in statsfeeder_statsall if x != {}]

		# Transform list into dict
		for d in statsdatalist:
			statsdata.update(d)
		for s in statsfeeder_statslist:
			statsfeeder_stats.update(s)

		totalDuration=round(time.time()-totalStartTime,2)
		statsfeeder_stats['totalttime'] = totalDuration
		if verbose:
			print statsdata
			print statsfeeder_stats

		if not dryrun:
			print "Sending data do graphite.."
			g.send_dict(statsdata)
			g.disconnect()
		else:
			print "Dryrun enabled. Not sending data to graphite"

		if verbose: 
			print "-> Metricts gathering took " + str(totalDuration) + " s"
			#print statsfeeder_stats

		if not dryrun:
			selfg = graphitesend.init(graphite_server=HOST, prefix='graphitesend', system_name='')
			selfg.send_dict(statsfeeder_stats)
			selfg.disconnect()

		else:
			print "Dryrun enabled. Not sending perfdata to graphite"
		
		sys.stdout.flush()
		time.sleep(float(FREQ))

def mp_stats(nr,all_stats):
	statsdata = {}
	statsfeeder_stats = {}
	stat=all_stats[nr]
	startTime=time.time()	
	if os.access(STATSDIR+stat, os.X_OK):
		x = commands.getstatusoutput(STATSDIR+stat )	
		isfloat=True
		isjson=True
		try:
			float(x[1])	
			statsdata[stat] = x[1]
		except ValueError:
			isfloat=False
			try:
				json_values = json.loads(x[1])
			except ValueError:
				isjson = False
				print str(stat) + "not accepted value, skipping stat" + str(x[1])
				pass
		if isfloat:
			statsdata[stat] = x[1]

			if verbose or values_to_log:
				print stat + " " + x[1]
		elif isjson:
			#json_values = json.loads(x[1])
			for jv in json_values:
				jvpath = stat + "." + jv
				jvvalue = json_values[jv]

				if verbose or values_to_log:
					print jvpath + " " + str(jvvalue)

				statsdata[jvpath] = jvvalue
		else:
			print str(stat) + "not accepted value, skipping stat" + str(x[1])
			pass
				
	else:
		print STATSDIR+str(stat) + " not executable ignoring..."
		pass

	duration=time.time()-startTime
	statsfeeder_stats[stat.replace(".","_")] = round(duration, 2)
	if statsfeeder_stats[stat.replace(".","_")] == 0.0:
		del statsfeeder_stats[stat.replace(".","_")]
	qstatsfeeder_statsdata.put(statsdata)
	qstatsfeeder_stats.put(statsfeeder_stats)

def get_stat_info(enabled_stats):
	statsdata = {}
	statsfeeder_stats = {}


	processes = [mp.Process(target=mp_stats, args=(x,enabled_stats)) for x in range(len(enabled_stats))]

	for p in processes:
		p.start()

	for p in processes:
		p.join()

	statsdata_results = [qstatsfeeder_statsdata.get() for p in processes]
	statsfeeder_stats_results = [qstatsfeeder_stats.get() for p in processes]
		
	return (statsdata_results, statsfeeder_stats_results)

def check_server(address, port):
	# Create a TCP socket
	s = socket.socket()
	print "Attempting to connect to %s on port %s" % (address, port)
	try:
		s.connect((address, port))
		print "Connected to %s on port %s" % (address, port)
		return True
	except socket.error, e:
		print "Connection to %s on port %s failed: %s. Check graphite is running or the config has the correct values." % (address, port, e)
		return False

if __name__ == "__main__":
	sys.exit(main())
