
import os
import json
from datetime import datetime,timedelta
import urllib.parse

#MS Internal Credentials
os.environ['AZURE_SUBSCRIPTION_ID'] = 'f8e6bc83-6957-4025-8b48-8211b18ba585'
os.environ['AZURE_CLIENT_ID'] = '3273b819-1292-422f-8fdd-afd9932e5f34'
os.environ['AZURE_CLIENT_SECRET'] = 'hvBP0FdYiphUtf4S6FUl4nOavdB6L3YPqhTjaf5FS20='
os.environ['AZURE_TENANT_ID'] = '72f988bf-86f1-41af-91ab-2d7cd011db47'

#Personal Credentials
#os.environ['AZURE_SUBSCRIPTION_ID'] = '54a48a47-338e-41eb-b8dc-a25631869f15'
#os.environ['AZURE_CLIENT_ID'] = 'd9e797e6-443d-4310-94eb-f6ad556f5a78'
#os.environ['AZURE_CLIENT_SECRET'] = '(&tRAgXt*3)rSlC_o'
#os.environ['AZURE_TENANT_ID'] = '90959085-faf6-4346-80ef-b9acc36f11d1'

import vm


#consumptions = vm.get_all_consumptions(datetime(2019, 3, 1, 1), datetime(2019, 3, 1, 3))
server_consumption = vm.get_consumption('AZURE-SAMPLE-GROUP-VIRTUAL-MACHINES', datetime(2019, 3, 1, 1), datetime(2019, 3, 1, 22))

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