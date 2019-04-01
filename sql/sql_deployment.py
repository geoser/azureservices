import deployment
import resources

from .sql_parameters import SqlParameters
import json

def get_parameters(params:SqlParameters):
    paramJson = json.load(open("python/sql/sql_parameters.json"))
    parametersSection = paramJson["parameters"]
    parametersSection["administratorLogin"]["value"] = params.administrator_login
    parametersSection["administratorLoginPassword"]["value"] = params.administrator_password
    parametersSection["collation"]["value"] = params.collation
    parametersSection["databaseName"]["value"] = params.database_name
    parametersSection["serverName"]["value"] = params.server_name

    return parametersSection

def get_template():
    return json.load(open("python/sql/sql_template.json"))

def deploy(server_id:str, sql_template, sql_params):
    resources.create_resource_group(server_id)
