import json
import deployment
import resources
from auth_helper import AuthInfo
from helper import ServiceType
from azure.mgmt.sql import SqlManagementClient
from .sql_parameters import SqlParameters

def get_parameters(server_id:str, params:SqlParameters):
    paramJson = json.load(open("sql/sql_parameters.json"))
    parametersSection = paramJson["parameters"]
    parametersSection["administratorLogin"]["value"] = params.administrator_login
    parametersSection["administratorLoginPassword"]["value"] = params.administrator_password
    parametersSection["collation"]["value"] = params.collation
    parametersSection["databaseName"]["value"] = params.database_name
    parametersSection["serverName"]["value"] = "tks-db-" + server_id

    return parametersSection

def get_template():
    return json.load(open("sql/sql_template.json"))

def deploy(server_id:str, sql_params:SqlParameters):
    deployment_params = get_parameters(server_id, sql_params)
    deployment_template = get_template()
    validationResult = resources.validate_deployment(server_id, deployment_template, deployment_params)
    print(str(validationResult))
    resources.create_deployment(server_id, deployment_template, deployment_params)

def get_sqlserver(server_id:str):
    servers = [s for s in sql_client.servers.list_by_resource_group(server_id)]
    if (len(servers) == 0): return None
    return servers[0]

def get_sqldb(server_id):
    server = get_sqlserver(server_id)
    if server is None: return None
    dbs = [db.name for db in sql_client.databases.list_by_server(server_id, server.name)]
    return {
        "server": {
            "service_type": ServiceType.sql.name,
            "server_name": server.name,
            "fqdn": server.fully_qualified_domain_name,
            "kind": server.kind,
            "type": server.type,
            "administrator_login": server.administrator_login,
            "database": dbs
        }
    }

def set_firewall_rule(server_id:str, start_ip, end_ip):
    server = get_sqlserver(server_id)
    if server is None: return
    rule_name = start_ip + "_" + end_ip
    sql_client.firewall_rules.create_or_update(server_id, server.name, rule_name, start_ip, end_ip)

sql_client = SqlManagementClient(AuthInfo.credentials, AuthInfo.subscription_id)