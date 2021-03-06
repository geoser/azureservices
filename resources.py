from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
from auth_helper import AuthInfo
from helper import ServiceType
import json

def create_resource_group(name:str, service_type:ServiceType):
    print("Creating resource group " + name + " for service " + str(service_type))

    resource_client.resource_groups.create_or_update(name, 
        {
            'location': "westeurope",
            'tags': {
                'service_type': str(service_type.name)
            }
        }
    )

def delete_resource_group(name:str):
    resource_client.resource_groups.delete(name)

def validate_deployment(server_id:str, template, params):
    properties = {
        'mode': DeploymentMode.incremental,
        'template': template,
        'parameters': params
    }

    return resource_client.deployments.validate(server_id, "deployment_" + server_id, properties)

def create_deployment(server_id:str, template, params):
    properties = {
        'mode': DeploymentMode.incremental,
        'template': template,
        'parameters': params
    }

    resource_client.deployments.create_or_update(server_id, "deployment_" + server_id, properties)

def get_all_tks_resource_groups():
    paged = resource_client.resource_groups.list(filter="tagName eq 'service_type'")
    return [{"server_id": g.name,"service_type": g.tags["service_type"]} for g in paged]

def get_resource_service_type(server_id:str):
    print("get service_type for " + server_id)
    group = resource_client.resource_groups.get(server_id)
    if group is not None and 'service_type' in group.tags:
        tagValue = group.tags['service_type']
        print("value is " + tagValue)
        return ServiceType[tagValue]
    print("group is None or no service_type tag")

resource_client = ResourceManagementClient(AuthInfo.credentials, AuthInfo.subscription_id)
