import deployment
import resources

from .sql_parameters import SqlParameters
import json

def get_parameters(params:SqlParameters):
    paramJson = json.load(open("sql/sql_parameters.json"))
    parametersSection = paramJson["parameters"]
    parametersSection["administratorLogin"]["value"] = params.administrator_login
    parametersSection["administratorLoginPassword"]["value"] = params.administrator_password
    parametersSection["collation"]["value"] = params.collation
    parametersSection["databaseName"]["value"] = params.database_name
    parametersSection["serverName"]["value"] = params.server_name

    return parametersSection

def get_template():
    return json.load(open("sql/sql_template.json"))

def deploy(server_id:str, sql_params:SqlParameters):
    deployment_params = get_parameters(sql_params)
    deployment_template = get_template()
    validationResult = resources.validate_deployment(server_id, deployment_template, deployment_params)
    print(str(validationResult))
    resources.create_deployment(server_id, deployment_template, deployment_params)
