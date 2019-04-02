import os
import json
from azure.common.credentials import ServicePrincipalCredentials

def get_credentials():
    subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
    credentials = ServicePrincipalCredentials(
        client_id=os.environ['AZURE_CLIENT_ID'],
        secret=os.environ['AZURE_CLIENT_SECRET'],
        tenant=os.environ['AZURE_TENANT_ID']
    )
    return credentials, subscription_id

auth_json = json.load(open("auth_passwords.json"))
auth_info = auth_json["msinternal"]

os.environ['AZURE_SUBSCRIPTION_ID'] = auth_info["subscription_id"]
os.environ['AZURE_CLIENT_ID'] = auth_info["client_id"]
os.environ['AZURE_CLIENT_SECRET'] = auth_info["client_secret"]
os.environ['AZURE_TENANT_ID'] = auth_info["tenant_id"]

_credentials, _subscription_id = get_credentials()

class AuthInfo():
    credentials = _credentials
    subscription_id = _subscription_id