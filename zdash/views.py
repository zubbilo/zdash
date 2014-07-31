from django.http import HttpResponse
from django.utils import simplejson
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib import messages

from zdash.settings import logger, ZABBIX, ZDASH_URL
from zdash.action import alarms, ZabbixAlarms

def home(request):
    try:
	data = alarms()
	#data = sorted(data.items(), key=lambda (k, v): v[1], reverse=True)
    except ZabbixAlarms,e:
	messages.error(request, e)
	data = None
    except Exception,e:
	messages.error(request, 'Server Error! %s'%e)
	data = None

    return render_to_response('home.html', {'alarms':data, 'ZABBIX_URL':ZABBIX['url'], 'ZDASH_URL':ZDASH_URL}, context_instance=RequestContext(request))
