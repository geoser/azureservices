import uuid

from helper import ServiceType
import resources
import vm
import sql.sql_deployment as sql

class ServiceTypeDoesNotExistError(BaseException): pass

def servers_get():
    return resources.get_all_tks_resource_groups()

def servers_post(request_json):
    service_type = request_json['service_type']
    if not ServiceType.__dict__.__contains__(service_type.lower()):
        raise ServiceTypeDoesNotExistError(service_type)

    server_id = str(uuid.uuid4())
    
    resources.create_resource_group(server_id, ServiceType.__dict__[service_type.lower()])

    if service_type.lower() == ServiceType.vm.name:
        vmInfo = vm.VmCreationInfo()
        vmInfo.name = request_json['name']
        vmInfo.size = request_json['service_name']
        vmInfo.user_name = request_json['user_name']
        vmInfo.password = request_json['password']
        vmInfo.os_type = vm.OsType[request_json['os_type']]

        print(vmInfo)

        vm.create_vm(server_id, vmInfo)

        return {
            "server_id": server_id,
            "service_type": ServiceType.vm.name,
            "service_name": vmInfo.size
        }
    elif service_type.lower() == ServiceType.sql.name:
        sql_params = sql.SqlParameters()
        if 'administrator_login' in request_json: sql_params.administrator_login = request_json['administrator_login']
        sql_params.administrator_password = request_json['administrator_password']
        if 'collation' in request_json: sql_params.collation = request_json['collation']
        if 'database_name' in request_json: sql_params.database_name = request_json['database_name']

        sql.deploy(server_id, sql_params)

        return {
            "server_id": server_id,
            "service_type": ServiceType.sql.name,
            "service_name": "sql_database"
        }