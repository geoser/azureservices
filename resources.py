from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
from auth_helper import AuthInfo
import json

def test():
    pass

def create_resource_group(name:str):
    resource_client.resource_groups.create_or_update(name, {'location': "westeurope"})

def delete_resource_group(name:str):
    resource_client.resource_groups.delete(name)

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
    group = [r for r in resource_client.resource_groups.list(filter="name eq '" + server_id + "'")]
    if len(group) > 0 and 'service_type' in group[0].tags:
        return group[0].tags['service_type']

resource_client = ResourceManagementClient(AuthInfo.credentials, AuthInfo.subscription_id)
