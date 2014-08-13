# -*- coding:utf-8 -*-
from zabbix_api import ZabbixAPI
from zdash.settings import ZABBIX, logger
#import traceback

import time
import re

WARNING = 2
AVERAGE = 3
PROBLEM = 4
DISASTER = 5

DELAY = {
	"forday:":79200,
	"formonth:":2505600,
	"forquarter:":7603000,
	"forhalfyear:":15700000,
	}

def api_connect():
    """Connect to Zabbix API"""
    try:
    	zapi = ZabbixAPI(server=ZABBIX['url'])
    	zapi.login(ZABBIX['user'], ZABBIX['pass'])
    except Exception,e:
    	logger.error("Can't login to zabbix server: %s" %(e))
	raise ZabbixAlarms, "Can't login to zabbix server: %s" %(e)
    else:
    	return zapi

def alarms():
    try:
        c = api_connect()
    except ZabbixAlarms,e:
	raise ZabbixAlarms, "Unable to connect to Zabbix Server! Please contact Zdash administrators."

    data, full_result, evts, hosts, defmacro = {}, [], [], [], []
    try:
# Get ALL current active triggers
	ahid = c.trigger.get({
			     "output":"extend",
			     "monitored":"true",
			     "min_severity":"2",
			     "selectHosts":"extend",
			     "selectGroups":"extend",
			     "selectLastEvent":"extend",
			     "filter":{ "value": "1" },
			     "maintenance":"false",
			     "skipDependent":"true",
			    })

	for g in ahid:
#	    logger.info("TRIGGER full data: %s" %(g))

# Example of filtering TrigerIDs list, based on GroupNames: ALL_servers, ALL_routers, ALL_etc...
# Feel free to write here Your own filter.
#	    if g['groups']:
#		groups = [grp['name'] for grp in g['groups']]
#		selectedgrp = [grp for grp in groups if grp.startswith('ALL')]
#		if len(selectedgrp) == 0: continue

# Building LastEventIDs for Acknowledges selection on this events
	    if ( len(g['lastEvent'])>0 and len(g['hosts'])>0 ):
		evts.append(g['lastEvent']['eventid'])

    except Exception,e:
	logger.error("Problem while getting Triggers: %s" %(e))
	raise ZabbixAlarms(e)

    try:
# Get Acknowledges for TriggerIDs
        heid = c.event.get({
			"output": "extend",
			"select_acknowledges": "extend",
			"sortfield": "eventid",
			"sortorder": "DESC",
			"eventids": evts,
			"acknowledged":"true",
			"limit": 20
			})

# START building DATA from Triggers + Events + ACKs
	for g in ahid:

# Example of filtering TrigerIDs list, based on GroupNames: ALL_servers, ALL_routers, ALL_etc...
# Feel free to write here Your own filter.
#	    if g['groups']:
#		groups = [grp['name'] for grp in g['groups']]
#		selectedgrp = [grp for grp in groups if grp.startswith('ALL')]
#		if len(selectedgrp) == 0: continue

# Problem Duration
	    utime = problem_duration(time.strftime("%d %b %Y %H:%M:%S", time.localtime(int(g['lastchange']))))

# Trigger's comment encoded to UTF-8 (setting up in .../triggers.php in option 'Description')
	    comment = str(g['comments'].encode('utf-8'))

# PreBuild Parameters
	    eventid = 0
	    if len(g['lastEvent'])>0:
		eventid=int(g['lastEvent']['eventid'])
	    ack = "None"
	    ack_duration = 15800000
	    ack_author = "Last comment"

# Gathering ACK parameters (ack_duration, ack_author, ack) for acnowledged triggers
	    for e in heid:
#	    	logger.info("EVENT full data: %s" %(e))
		if ( int(e['acknowledged'])==1 and int(e['objectid'])==int(g['triggerid']) and len(e['acknowledges'])>0):
		    ack = str(e['acknowledges'][0]['message'].encode('utf-8'))
		    ack_duration = problem_duration_sec(time.strftime("%d %b %Y %H:%M:%S", time.localtime(int(e['acknowledges'][0]['clock']))))
		    ack_author = str(e['acknowledges'][0]['alias'].encode('utf-8'))
		    break

# Filtering Triggers based on DELAY parameter
	    display = True
	    for delay_name, delay_sec in DELAY.items():
		if int(ack_duration) < 3600:
		    display = False
		if (ack.startswith(delay_name) and int(ack_duration) < delay_sec):
		    display = False

# Preparing data[] variable after all filters
# Template of data[]:
# [hostid][0]=str(Name)
# [hostid][1]=int(priority)
# [hostid][2]=[str(trigger.name)[:55], int(trigger.utime), str(trigger.comment), int(triggerid), int(eventid), str(acnowledge.ack), str(acknowledge.author)]

	    if display:
		if data.has_key(g['hosts'][0]['hostid']):
		    if int(g['priority']) > int(data[g['hosts'][0]['hostid']][1]):
			data[g['hosts'][0]['hostid']][1] = g['priority']
		    data[g['hosts'][0]['hostid']][2].append([str(g['description'])[:55],str(utime),str(comment),int(g['triggerid']),int(eventid),str(ack),str(ack_author)])
		else:
		    data[g['hosts'][0]['hostid']] = [g['hosts'][0]['host'],g['priority'],[[str(g['description'])[:55],str(utime),str(comment),int(g['triggerid']),int(eventid),str(ack),str(ack_author)]]]

    except Exception,e:
	logger.error("Problem while building data: %s" %(e))
	raise ZabbixAlarms(e)

    try:
# Get HOST information (IP-addresses, MACROSes, Templates)
        hiid = c.host.get({ "output": "extend",
			    "selectInterfaces":"extend",
			    "selectMacros":"extend",
			    "hostids": data.keys(),
			    "selectParentTemplates":"extend"
			})

# Building BASIC defmacro[] list for substituting strings in [hostid][2], [hostid][3]
        for hi in hiid:
#	    logger.info("HOSTS full data: %s" %(hi))
	    defmacro=[{'macro':'{HOSTNAME}', 'value':hi['host']}]
	    defmacro.append({'macro':'{HOST.NAME}','value':hi['host']})
	    data[hi['hostid']].append("")
	    ipval, dnsval = [], []
#====>>> FOR Zabbix 2.0
	    if ZABBIX['version']<2.2:
		for ikey in hi['interfaces'].keys():
		    if hi['interfaces'][ikey]['ip']:
			ipval.append(str(hi['interfaces'][ikey]['ip']))
		    if hi['interfaces'][ikey]['dns']:
			dnsval.append(str(hi['interfaces'][ikey]['dns']))
#====>>> FOR Zabbix 2.2
	    if ZABBIX['version']>=2.2:
		for ikey,item in enumerate(hi['interfaces']):
		    if hi['interfaces'][ikey]['ip']:
			ipval.append(str(hi['interfaces'][ikey]['ip']))
		    if hi['interfaces'][ikey]['dns']:
			dnsval.append(str(hi['interfaces'][ikey]['dns']))

	    data[hi['hostid']][3]=', '.join(ipval+dnsval)
	    defmacro.append({'macro':'{HOST.IP}','value':str(', '.join(ipval))})
	    defmacro.append({'macro':'{HOST.DNS}','value':str(', '.join(dnsval))})
	    templates=[]
	    if len(hi['parentTemplates'])>0:
		templates=[t['templateid'] for t in hi['parentTemplates']]

# Merging BASIC defmacros and host.macroses
	    if len(hi['macros'])>0:
		defmacro=defmacro+hi['macros']

# Get TEMPLATEs information (MACROSes)
	    tmac = c.template.get({ "selectMacros":"extend",
				    "templateids": templates,
				 })
	    for mac in tmac:
#		logger.info("Got Template info: %s" %(mac))
		if len(mac['macros'])>0:
		    defmacro=defmacro+mac['macros']

# Substituting MACROSes names to MACROSes values in strings of [hostid][2]
	    for ma in defmacro:
#		logger.info("MACROS full data: %s" %(ma))
		i=0
		for k in data[hi['hostid']][2]:
		    data[hi['hostid']][2][i][0] = k[0].replace(ma['macro'],ma['value'])
		    data[hi['hostid']][2][i][2] = k[2].replace(ma['macro'].encode('utf-8'),str(ma['value'].encode('utf-8')))
		    i=i+1

    except Exception,e:
	logger.error("Problem while getting Host data like Macroses, IP, DNS, etc..: %s" %(e))
	raise ZabbixAlarms(e)

    try:
# Logging result var before rendering
	logger.info(data)

# Prepaire the view
	for trigger in data:
	    result = {}
	    result['name'] = data[trigger][0]
	    result['fulllabel'] = data[trigger][2]
	    result['address'] = data[trigger][3]
# Calc status
	    states = int(data[trigger][1])
	    result['status'] = states

# THIS VARIABLE GOING TO BE ON DISPLAY
	    full_result.append(result)

    except Exception,e:
	logger.error("Error while preparing final result: %s" %(e))
	raise ZabbixAlarms(e)
    else:
        return full_result

def to_unixtime(date):
    unix = int(time.mktime(time.strptime(date, '%d %b %Y %H:%M:%S')))
    return unix

def seconds_to_hours(unix):
    totalMin = int(unix/60)
    hours = int(totalMin/60)
    minutes = "%02d" %(int(totalMin - (hours*60)))
    time = str(hours) + ":" + str(minutes)
    return time

def problem_duration(date):
    start_problem = to_unixtime(date)
    now = int(time.time())
    duration = now - start_problem
    duration = seconds_to_hours(duration)
    return duration

def problem_duration_sec(date):
    start_problem = to_unixtime(date)
    now = int(time.time())
    duration = now - start_problem
    return duration

class ZabbixAlarms(Exception):
    def __init__(self, value):
	self.value = value
    def __str__(self):
	return repr(self.value)
