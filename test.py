
import os
import json
from datetime import datetime,timedelta
import urllib.parse

import vm
import billing
import sql.sql_deployment as sql

sql.set_firewall_rule("65ff2fd7-81e7-4a99-8251-dafdaa7d89f2", 
    "tks-dbserver-51db26ad-da2b-49b9-a14d-908bf96e3aeb)", "0.0.0.0", "255.255.255.255")
#res = sql.get_sqldb("65ff2fd7-81e7-4a99-8251-dafdaa7d89f2")

#usage = vm.get_usage(datetime(2019, 2, 28, 15), datetime(2019, 3, 27, 18))
#consumptions = billing.get_all_consumptions(datetime(2019, 3, 3, 15), datetime(2019, 3, 27, 15))
#server_consumption = vm.get_consumption('adec8d18-9110-4e1b-8747-51543ed8474b', datetime(2019, 3, 1, 1), datetime(2019, 3, 27, 22))
print(res)
#r = [u for u in usage]
pass

#res = vm.get_billing_periods()
#res = vm.get_latest_invoice() 
#print(res)
#res = vm.get_all_vms()

#res = vm.set_volume('27e04963-7918-4e4f-bba7-3beb85fa0c30', 0, 115)
#print(res)
#pass
#res = vm.create_volume('27e04963-7918-4e4f-bba7-3beb85fa0c30', 113)
#pass
#lun = vm.get_available_lun('27e04963-7918-4e4f-bba7-3beb85fa0c30')
#pass
#vm.stop_vm('none', False)

#res = vm.get_all_flavors(False)
#res = vm.get_volumes('27e04963-7918-4e4f-bba7-3beb85fa0c30')
#print(res)

#res = vm.get_vm('adec8d18-9110-4e1b-8747-51543ed8474b')
#print(res)
#res = vm.create_volume('27e04963-7918-4e4f-bba7-3beb85fa0c30', 100)
#vms = vm.get_all_vms()
#res = list()
#for v in vms:
#    item = v.name
#    res.append(item)

#res = vm.create_vm('test6', 'Standard_NC6')
#print(res)
#print(res['server']['server_id'])