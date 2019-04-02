from datetime import datetime, timedelta
from enum import Enum
import urllib.parse

class ServiceType(Enum):
    vm      = 1
    sql     = 2

def convert_datetime(time_stamp:int):
    exact_value = datetime(1970, 1, 1) + timedelta(milliseconds=time_stamp)
    return datetime(exact_value.year, exact_value.month, exact_value.day, exact_value.hour)

def encode_datetime(d:datetime):
    dstr = d.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    return urllib.parse.quote(dstr)

def create_response(server_id:str, service_type:str, service_name:str, name:str = ''):
    return {
        "server": {
            "server_id": server_id, 
            "service_type": service_type,
            "service_name": service_name,
            "name": name
        }
    }