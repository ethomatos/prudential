from datadog import initialize, api
from argparse import ArgumentParser
import sys
import json
import time
from os import environ

# set debug and active flags
debug = False
active = True

# Read in API keys from a file
# The file format should be like this:
# apiKey:123456789
# appKey:123456789
def getAPIkeys(file):
	apiKey = None
	appKey = None
	with open(file) as apis:
		for line in apis:
			line.rstrip()	
			tag = line.split(':')
			if (tag[0] == "apiKey"):
				apiKey = tag[1]
				if (debug):
					print("apiKey = " + apiKey, end="")
			elif (tag[0] == "appKey"):
				appKey = tag[1]
				if (debug):
					print("appKey = " + appKey, end="")
	return(apiKey, appKey)

# Initialize the API
def initAPI():
	# Initialize Datadog API
	(apiKey, appKey) = getAPIkeys(apifile)
	options = {
		'api_key':apiKey.rstrip(),
		'app_key':appKey.rstrip()
	}
	initialize(**options)

# Create the log monitors
def createMonitor(type, query, tags):
	# Create a new monitor
	monitor_options = {
		"notify_no_data": True,
		"no_data_timeframe": 20
	}
	j = 1
	for q in query: 
		print(type + " monitor " + str(j) + " using query " + q)
		api.Monitor.create(
			type="log alert",
			query=q,
			name="Example " + type + " log monitor " + str(j),
			message="some message Notify: @servicenow",
			priority=3,
			tags=tags,
			options=monitor_options
		)
		j += 1

def getMonitorQueries():
	# Simulated capture of queries from an external system
	# place a list of queries for each source into a dictionary for that source
	# Example query: 'logs("service:foo AND type:error").index("main").rollup("count").by("source").last("2m") > 2'
	collector = {}
	query_syslog = [
		'logs("source:syslog AND kernel AND apparmor=\"DENIED\"").index("main").rollup("count").last("2m") > 5'
		'logs("source:syslog systemd AND run-docker-runtime").index("main").rollup("count").last("2m") > 5'
	]
	collector["syslog"] = query_syslog
	query_cw = [
		'logs("source:cloudwatch AND *heptio*").index("main").rollup("count").last("2m") > 5'
		'logs("source:cloudwatch @sourceIPs:10.*").index("main").rollup("count").last("2m") > 5'
	]
	collector["cw"] = query_cw
	query_audit = [
		'logs("source:audit AND denied_mask=\"r\"").index("main").rollup("count").last("2m") > 5'
		'logs("source:audit @journald.SYSLOG_FACILITY:4").index("main").rollup("count").last("2m") > 5'
	]
	collector["audit"] = query_audit
	query_kernel = [
		'logs("source:kernel AND type=1400").index("main").rollup("count").last("2m") > 5'
		'logs("source:kernel @journald.SYSLOG_FACILITY:0").index("main").rollup("count").last("2m") > 5'
	]
	collector["kernel"] = query_kernel
	return(collector)

# Main routine of the program
def main(apifile):
	initAPI()
	# Simulate acquiring queries from external system
	collectQueries = getMonitorQueries()

	# Tag and create the log monitors using the API
	if active:
		for key in collectQueries.keys():
			# Add tags
			tags = ["creator:api", "project:prudential"]
			tags.append("type:" + key)
			createMonitor(key, collectQueries[key], tags)

# Only executed as a standalone program, not from an import from another program
if __name__ == "__main__":
	parser = ArgumentParser(description='Create a monitor using the Datadog API.')
	helpText = "Enter a file to read in the API and APP keys each one on a separate line with this format:\n"
	helpText += "apiKey:123   appKey:123\n"
	parser.add_argument('-i', help=helpText, required=True)
	args = parser.parse_args()
	apifile = args.i if args.i else 'apikeys'
	main(apifile)
