import os
import traceback
import uuid
from enum import Enum
from datetime import datetime, timedelta
import adal
import requests
import urllib.parse
import json
import re

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import DiskCreateOption
from azure.mgmt.billing import BillingManagementClient

from msrestazure.azure_exceptions import CloudError

from haikunator import Haikunator
haikunator = Haikunator()

class OsType(Enum):
    WINDOWS = 1
    LINUX = 2

class ServiceType(Enum):
    VM = 1

class VmCreationInfo:
    location = 'westeurope'
    name = 'tksvm'
    size = 'Standard_NC6'
    user_name = 'userLogin'
    password = 'Pa$$w0rd91'
    os_type:OsType = OsType.WINDOWS

class ServerDoesNotExistError(BaseException): pass
class NoAvailableLunsError(BaseException): pass
class LunNotFoundError(BaseException): pass

GLOBAL_PREFIX = 'tks-'

VM_REFERENCE = {
    'LINUX': {
        'publisher': 'Canonical',
        'offer': 'UbuntuServer',
        'sku': '16.04.0-LTS',
        'version': 'latest'
    },
    'WINDOWS': {
        'publisher': 'MicrosoftWindowsServer',
        'offer': 'WindowsServer',
        'sku': '2016-Datacenter',
        'version': 'latest'
    }
}

def get_credentials():
    subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
    credentials = ServicePrincipalCredentials(
        client_id=os.environ['AZURE_CLIENT_ID'],
        secret=os.environ['AZURE_CLIENT_SECRET'],
        tenant=os.environ['AZURE_TENANT_ID']
    )
    return credentials, subscription_id

def create_public_ip_address(location, groupName):
    public_ip_addess_params = {
        'location': location,
        'public_ip_allocation_method': 'Dynamic',
        'dns_settings': {
            'domain_name_label': 'tks' + groupName
        }
    }
    creation_result = network_client.public_ip_addresses.create_or_update(
        groupName,
        'tksIPAddress',
        public_ip_addess_params
    )

    return creation_result.result()

def get_public_ip_address(group_name):
    return network_client.public_ip_addresses.get(
        group_name,
        'tksIPAddress'
    )

def create_nic(location, groupName):
    # Create public ip
    creation_result = create_public_ip_address(location, groupName)
    print("------------------------------------------------------")
    print(creation_result)

    VNET_NAME = GLOBAL_PREFIX + 'vnet'
    SUBNET_NAME = GLOBAL_PREFIX + 'subnet'
    IP_CONFIG_NAME = GLOBAL_PREFIX + 'ip-config'
    NIC_NAME = GLOBAL_PREFIX + 'nic'

    # Create VNet
    print('\nCreate Vnet')
    async_vnet_creation = network_client.virtual_networks.create_or_update(
        groupName,
        VNET_NAME,
        {
            'location': location,
            'address_space': {
                'address_prefixes': ['10.0.0.0/16']
            }
        }
    )
    async_vnet_creation.wait()

    # Create Subnet
    print('\nCreate Subnet')
    async_subnet_creation = network_client.subnets.create_or_update(
        groupName,
        VNET_NAME,
        SUBNET_NAME,
        {'address_prefix': '10.0.0.0/24'}
    )
    subnet_info = async_subnet_creation.result()

    # Getting IP
    print('\nGetting ip address')
    publicIPAddress = get_public_ip_address(groupName)

    # Create NIC
    print('\nCreate NIC')
    async_nic_creation = network_client.network_interfaces.create_or_update(
        groupName,
        NIC_NAME,
        {
            'location': location,
            'ip_configurations': [{
                'name': IP_CONFIG_NAME,
                'public_ip_address': publicIPAddress,
                'subnet': {
                    'id': subnet_info.id
                }
            }]
        }
    )
    return async_nic_creation.result()

def create_vm_parameters(server_id, nic_id, vm_reference, location, vmName, userName, password, size):
    """Create the VM parameters structure.
    """
    return {
        'location': location,
        'tags': {
            'server_id': server_id
        },
        'os_profile': {
            'computer_name': vmName,
            'admin_username': userName,
            'admin_password': password
        },
        'hardware_profile': {
            'vm_size': size
        },
        'storage_profile': {
            'image_reference': {
                'publisher': vm_reference['publisher'],
                'offer': vm_reference['offer'],
                'sku': vm_reference['sku'],
                'version': vm_reference['version']
            },
        },
        'network_profile': {
            'network_interfaces': [{
                'id': nic_id,
            }]
        },
    }

def create_vm(vmInfo: VmCreationInfo):
    server_id = str(uuid.uuid4())
    
    # Create Resource group
    print('\nCreate Resource Group')
    resource_client.resource_groups.create_or_update(server_id, {'location': vmInfo.location})

    try:
        # Create a NIC
        nic = create_nic(vmInfo.location, server_id)

        # Create Windows VM
        print('\nCreating Windows Virtual Machine')

        vm_parameters = create_vm_parameters(
            server_id, 
            nic.id, 
            VM_REFERENCE[vmInfo.os_type.name], 
            vmInfo.location, 
            vmInfo.name, 
            vmInfo.user_name, 
            vmInfo.password, 
            vmInfo.size)

        async_vm_creation = compute_client.virtual_machines.create_or_update(server_id, vmInfo.name, vm_parameters)
        #async_vm_creation.wait()
    except CloudError:
        print('A VM operation failed:\n{}'.format(traceback.format_exc()))
    else:
        print('All example operations completed successfully!')
    #finally:
        # Delete Resource group and everything in it
        #print('\nDelete Resource Group')
        #delete_async_operation = resource_client.resource_groups.delete(GROUP_NAME)
        #delete_async_operation.wait()
        #print("\nDeleted: {}".format(GROUP_NAME))

    result = {
        'server': {
            'server_id': server_id,
            'service_type': ServiceType.VM.name,
            'service_name': vmInfo.size
        }
    }

    return result

def convert_vm_internal(virtual_machine):
    return {
        'server': {
            'server_id': virtual_machine.tags['server_id'],
            'service_type': ServiceType.VM.name,
            'service_name': virtual_machine.hardware_profile.vm_size,
            'name': virtual_machine.name
        }
    }

def get_all_vm_sizes():
    return [size for size in compute_client.virtual_machine_sizes.list('westeurope')]

def get_all_vms():
    allMachines = compute_client.virtual_machines.list_all()
    return [convert_vm_internal(vm) for vm in allMachines if 'server_id' in vm.tags]

def get_vm_name(server_id:str):
    vms = compute_client.virtual_machines.list(server_id)
    vmList = list()
    for v in vms: vmList.append(v)
    
    if (len(vmList) == 0): 
        raise ServerDoesNotExistError(server_id)
    
    return vmList[0].name

def set_vm_password(server_id:str, new_password:str):
    vmObj = get_vm_internal(server_id)
    vmObj.os_profile.password = new_password
    async_update = compute_client.virtual_machines.create_or_update(server_id, vmObj.name, vmObj)
    async_update.wait()
    return {
        'server': {
            'server_id': server_id
        }
    }

def get_all_vm_luns(virtual_machine):
    return [d.lun for d in virtual_machine.storage_profile.data_disks]

def get_available_lun(virtual_machine):
    luns = get_all_vm_luns(virtual_machine)
    availableLuns = [l for l in range(0, 15) if l not in luns]
    
    if (len(availableLuns) == 0):
        raise NoAvailableLunsError(virtual_machine.name)
    
    return availableLuns[0]

def get_vm_internal(server_id, instance_view:bool = False):
    vmName = get_vm_name(server_id)

    if (instance_view):
        return compute_client.virtual_machines.get(server_id, vmName, expand='instanceView')
    
    return compute_client.virtual_machines.get(server_id, vmName)

def get_vm(server_id:str):
    vmObj = get_vm_internal(server_id, True)

    disks = [{'id': d.lun,'size':d.disk_size_gb,'azure_id': d.managed_disk.id} 
        for d in vmObj.storage_profile.data_disks]

    vmInstanceView = vmObj.instance_view

    ipAddress = get_public_ip_address(server_id)

    if len(vmInstanceView.statuses) > 1:
        status = vmInstanceView.statuses[1].display_status
    else:
        status = vmInstanceView.statuses[0].display_status

    return {
        'server': {
            'server_id': server_id,
            'service_type': ServiceType.VM.name,
            'service_name': vmObj.hardware_profile.vm_size,
            'name': vmObj.name,
            'status': status,
            'accessIPv4': ipAddress.ip_address,
            'ip_allocation_method': ipAddress.public_ip_allocation_method,
            'fqdn': ipAddress.dns_settings.fqdn,
            'volumes': disks
        }
    }

def stop_vm(server_id:str, hard:bool = False):
    vmName = get_vm_name(server_id)

    if hard:
        compute_client.virtual_machines.power_off(server_id, vmName)
    else:
        compute_client.virtual_machines.deallocate(server_id, vmName)
    return {
        'server': {
            'server_id': server_id
        }
    }

def start_vm(server_id:str):
    vmName = get_vm_name(server_id)
    compute_client.virtual_machines.start(server_id, vmName)
    return {
        'server': {
            'server_id': server_id
        }
    }

def restart_vm(server_id:str):
    vmName = get_vm_name(server_id)
    compute_client.virtual_machines.restart(server_id, vmName)
    return {
        'server': {
            'server_id': server_id
        }
    }

def delete_vm(server_id:str):
    resource_client.resource_groups.delete(server_id)
    return {
        'server': {
            'server_id': server_id
        }
    }

def convert_disk_internal(disk):
    return {
        'id':disk.lun, 
        'azure_id': disk.managed_disk.id, 
        'size': disk.disk_size_gb,
        'name': disk.name
    }

def get_volume_by_lun_internal(virtual_machine, server_id:str, lun:int):
    if lun < 0 or lun > 15:
        raise AssertionError('lun must be between 0 and 15')
    
    data_disks = virtual_machine.storage_profile.data_disks
    filtered = [convert_disk_internal(d) for d in data_disks if d.lun == lun]
    if (len(filtered) == 0):
        raise LunNotFoundError(server_id)

    return filtered[0]

def get_volume_by_lun(server_id:str, lun:int):
    vmObj = get_vm_internal(server_id)
    return get_volume_by_lun_internal(vmObj, server_id, lun)

def get_volumes(server_id:str):
    vmObj = get_vm_internal(server_id, False)
    data_disks = vmObj.storage_profile.data_disks
    return [convert_disk_internal(d) for d in data_disks]

    #disks = compute_client.disks.list_by_resource_group(server_id)
    #result = [disk for disk in disks]
    #return result

def create_volume_internal(server_id:str, sizeGB:int):
    print('\nCreate (empty) managed Data Disk')
    async_disk_creation = compute_client.disks.create_or_update(
        server_id,
        'datadisk_' + str(uuid.uuid4()),
        {
            'location': 'westeurope',
            'disk_size_gb': sizeGB,
            'creation_data': {
                'create_option': DiskCreateOption.empty
            }
        }
    )
    data_disk = async_disk_creation.result()
    return data_disk

def detach_volume_internal(virtual_machine, server_id:str, lun:id):
    data_disk = get_volume_by_lun_internal(virtual_machine, server_id, lun)
    virtual_machine.storage_profile.data_disks[:] = [disk for disk in virtual_machine.storage_profile.data_disks if disk.lun != lun]

    async_attach = compute_client.virtual_machines.create_or_update(server_id, virtual_machine.name, virtual_machine)
    async_attach.wait()

    return data_disk

def attach_volume_internal(virtual_machine, server_id, id, name, lun):
    virtual_machine.storage_profile.data_disks.append({
        'lun': lun,
        'name': name,
        'create_option': DiskCreateOption.attach,
        'managed_disk': {
            'id': id
        }
    })

    async_attach = compute_client.virtual_machines.create_or_update(server_id, virtual_machine.name, virtual_machine)
    async_attach.wait()

def create_volume(server_id:str, sizeGB:int):
    data_disk = create_volume_internal(server_id, sizeGB)
    vmObj = get_vm_internal(server_id)
    lun = get_available_lun(vmObj)

    attach_volume_internal(vmObj, server_id, data_disk.id, data_disk.name, lun)

    return {
        'id': lun,
        'size': sizeGB,
        'azure_id': data_disk.id
    }

def set_volume(server_id:str, lun:int, sizeGB:int):
    vmObj = get_vm_internal(server_id)

    vol = get_volume_by_lun_internal(vmObj, server_id, lun)
    disk_name = vol['name']

    print('Detaching disk ' + str(lun))
    detach = detach_volume_internal(vmObj, server_id, lun)

    print('Getting disk')
    managed_disk = compute_client.disks.get(server_id, disk_name)
    print('Got id ' + str(managed_disk.id))

    print('Changing size to ' + str(sizeGB))
    managed_disk.disk_size_gb = sizeGB
    async_update = compute_client.disks.create_or_update(server_id, disk_name, managed_disk)
    async_update.wait()

    print('Attaching disk')
    attach_volume_internal(vmObj, server_id, detach['azure_id'], detach['name'], detach['id'])
    return 'ok'

def get_all_flavors(details):
    flavors = [
        {
            'size': 'Standard_NC6',
            'vcpus': 6,
            'ram': 56,
            'disk': 340,
            'gpu': 1
        },
        {
            'size': 'Standard_NC6s_v2',
            'vcpus': 6,
            'ram': 112,
            'disk': 736,
            'gpu': 1
        }
    ]
    if details:
        return flavors
    
    return [f['size'] for f in flavors]

def get_all_prices():
    return [
        {
            'size': 'Standard_NC6',
            'cost': '$1.387'
        },
        {
            'size': 'Standard_NC6s_v2',
            'cost': '$3.19'
        }
    ]

def get_billing_periods():
    return [p for p in billing_client.billing_periods.list()]

def get_latest_invoice():
    return billing_client.invoices.get_latest()

def get_token(tenant_id, client_id, client_secret):
    context = adal.AuthenticationContext('https://login.microsoftonline.com/' + tenant_id)
    token = context.acquire_token_with_client_credentials('https://management.azure.com/', client_id, client_secret)
    return {
        "bearer": token['accessToken'], 
        "expiresOn": datetime.strptime(token['expiresOn'], '%Y-%m-%d %H:%M:%S.%f') 
    }

def rest_internal(url:str, verb:str, payload_json = ''):
    global __token__
    if __token__ is None or (__token__ is not None and __token__['expiresOn'] > (datetime.now() - timedelta(minutes=5))):
        rest_login()

    hed = {'Authorization': 'Bearer ' + __token__['bearer'], 'Content-Type': 'application/json'}
    if (verb == 'get'):
        response = requests.get(url, headers=hed, timeout=None)
    if (verb == 'post'):
        response = requests.post(url, headers=hed, timeout=None, json=payload_json)
    if (verb == 'put'):
        response = requests.put(url, headers=hed, timeout=None, json=payload_json)

    response.encoding = 'UTF8'
    return response.json()

def rest_get(url:str):
    return rest_internal(url, 'get')

def encode_datetime(d:datetime):
    dstr = d.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    return urllib.parse.quote(dstr)

def get_ratecard_url():
    global subscription_id
    return "https://management.azure.com/subscriptions/" \
        + subscription_id \
        + "/providers/Microsoft.Commerce/RateCard?api-version=2016-08-31-preview&" \
        + "$filter=OfferDurableId eq 'MS-AZR-0003P' and " \
        + "Currency eq 'RUB' and Locale eq 'en-EN' and RegionInfo eq 'RU'"

def get_usage_url(reportedStartTime:datetime, reportedEndTime:datetime):
    global subscription_id

    d_start = encode_datetime(reportedStartTime)
    d_end = encode_datetime(reportedEndTime)

    return "https://management.azure.com/subscriptions/" \
        + subscription_id \
        + "/providers/Microsoft.Commerce/UsageAggregates?api-version=2015-06-01-preview&reportedStartTime=" \
        + d_start \
        + "&reportedEndTime=" \
        + d_end \
        + "&aggregationGranularity=HOURLY"

def rest_login():
    global __token__
    __token__ = get_token(credentials._tenant, credentials.id, credentials.secret)

def get_usage(reportedStartTime:datetime, reportedEndTime:datetime):
    #temporaly read from file
    #f = open('usage1.json', 'r', encoding="utf-8")
    #content = f.read()
    #f.close()
    #return json.loads(content)

    url = get_usage_url(reportedStartTime, reportedEndTime)
    return rest_get(url)

def get_rates_cached():
    #read from file
    f = open('rates_en.json', 'r', encoding="utf-8")
    content = f.read()
    f.close()
    return json.loads(content)

def get_rates():
    url = get_ratecard_url()
    return rest_get(url)

def get_all_consumptions(reportedStartTime:datetime, reportedEndTime:datetime):
    rates = get_rates_cached()
    ratesDict = dict()
    for rate in rates['Meters']:
        ratesDict[rate['MeterId']] = rate

    usage = get_usage(reportedStartTime, reportedEndTime)
    for u in usage['value']:
        if 'instanceData' in u['properties']:
            instanceData = json.loads(u['properties']['instanceData'])
            u['resourceUri'] = instanceData['Microsoft.Resources']['resourceUri']
            u['quantity'] = u['properties']['quantity']
            u['usageStartTime'] = u['properties']['usageStartTime']
            u['usageEndTime'] = u['properties']['usageEndTime']

            rate = ratesDict[u['properties']['meterId']]
            u['rate_price'] = rate['MeterRates']['0']
            u['rate_category'] = rate['MeterCategory']

            u['rate_sum'] = u['rate_price'] * u['quantity']

            matchRes = re.search(r'/resourceGroups/([^/]+)/', u['resourceUri'])
            if matchRes is not None:
                u['resource_group'] = matchRes.groups()[0]

    return usage['value']

def get_consumption(server_id:str, reportedStartTime:datetime, reportedEndTime:datetime):
    all_consumptions = get_all_consumptions(reportedStartTime, reportedEndTime)
    server_consumption = [c for c in all_consumptions if 'resource_group' in c and c['resource_group'] == server_id]

    if (server_consumption is not None):
        t = [float(c['rate_sum']) for c in server_consumption if c['rate_sum'] is not None]
        result = {
            "sum": sum(t),
            "meters": server_consumption
        } 
        return result

credentials, subscription_id = get_credentials()
__token__ = None
resource_client = ResourceManagementClient(credentials, subscription_id)
compute_client = ComputeManagementClient(credentials, subscription_id)
network_client = NetworkManagementClient(credentials, subscription_id)
billing_client = BillingManagementClient(credentials, subscription_id)