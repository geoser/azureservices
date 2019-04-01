import os
from azure.common.credentials import ServicePrincipalCredentials

def get_credentials():
    subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
    credentials = ServicePrincipalCredentials(
        client_id=os.environ['AZURE_CLIENT_ID'],
        secret=os.environ['AZURE_CLIENT_SECRET'],
        tenant=os.environ['AZURE_TENANT_ID']
    )
    return credentials, subscription_id

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

_credentials, _subscription_id = get_credentials()

class AuthInfo():
    credentials = _credentials
    subscription_id = _subscription_id