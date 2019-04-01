from datetime import datetime, timedelta
import adal
import requests
import auth_helper

class GatewayError(BaseException): pass

def get_token(tenant_id, client_id, client_secret):
    context = adal.AuthenticationContext('https://login.microsoftonline.com/' + tenant_id)
    token = context.acquire_token_with_client_credentials('https://management.azure.com/', client_id, client_secret)
    return {
        "bearer": token['accessToken'], 
        "expiresOn": datetime.strptime(token['expiresOn'], '%Y-%m-%d %H:%M:%S.%f') 
    }

def rest_internal(url:str, verb:str, payload_json = ''):
    global __token__
    if __token__ is None or (__token__ is not None and __token__['expiresOn'] < (datetime.now() - timedelta(minutes=5))):
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

def rest_get(url:str = None):
    while url:
        print("REST GET: " + url)
        result =  rest_internal(url, 'get')
        if "value" in result and result["value"] is not None:
            print('yield from result["value"]')
            yield from result["value"]
            if "nextLink" in result:
                url = result["nextLink"]
            else:
                url = None
        if "error" in result:
            print(result['error'])
            raise GatewayError(result['error'])
        else:
            url = None

def rest_login():
    global __token__
    __token__ = get_token(credentials._tenant, credentials.id, credentials.secret)

credentials, subscription_id = auth_helper.get_credentials()
__token__ = None