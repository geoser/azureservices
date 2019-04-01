import os
import traceback
import uuid
from enum import Enum
from datetime import datetime, timedelta
import adal
import requests
import json
from auth_helper import AuthInfo
import resources

from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import DiskCreateOption

from msrestazure.azure_exceptions import CloudError

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

GLOBAL_PREFIX = 'tks-'

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

def create_vm_resize_parameters(size):
    return {
        'hardware_profile': {
            'vm_size': size
        }
    }

def set_vm_size(server_id:str, size:str):
    params = create_vm_resize_parameters(size)
    vm_name = get_vm_name(server_id)
    compute_client.virtual_machines.update(server_id, vm_name, params)
    return vm_name

def create_vm(vmInfo: VmCreationInfo):
    server_id = str(uuid.uuid4())
    
    # Create Resource group
    print('\nCreate Resource Group')
    resources.create_resource_group(server_id)

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

    return server_id

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
    resources.delete_resource_group(server_id)
    
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

def delete_volume(server_id:str, lun:int):
    vmObj = get_vm_internal(server_id)

    vol = get_volume_by_lun_internal(vmObj, server_id, lun)
    disk_name = vol['name']

    print('Detaching disk ' + str(lun))
    detach = detach_volume_internal(vmObj, server_id, lun)

    print('Deleting disk ' + str(lun))
    compute_client.disks.delete(server_id, disk_name)
    return "ok"

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


compute_client = ComputeManagementClient(AuthInfo.credentials, AuthInfo.subscription_id)
network_client = NetworkManagementClient(AuthInfo.credentials, AuthInfo.subscription_id)