import os
from flask import Flask, request
from flask_restful import reqparse, Resource, Api
from sqlalchemy import create_engine
from flask_jsonpify import jsonify
import json

print("current folder: " + os.getcwd())

from helper import convert_datetime, encode_datetime, create_response

import vm
import billing
import resources
import request_dispatcher as rd

app = Flask(__name__)
api = Api(app)

class Servers(Resource):
    def get(self):
        '''
        GET <server_url>/servers
        '''
        return rd.servers_get()

    def post(self):
        '''
        POST <server_url>/servers

        input for vm:

        {
            "server": {
                "service_type": "VM",
                "service_name": "Standard_NC6",
                "name": "test10",
                "user_name": "userlogin",
                "password": "Pa$$w0rd9100",
                "os_type": "WINDOWS"
            }
        }

        input for sql database:

        {
            "server": {
                "service_type": "SQL",
                "service_name": "sql_database",
                "administrator_login": "userlogin",
                "administrator_password": "Pa$$w0rd9100",
                "collation": "SQL_Latin1_General_CP1_CI_AS",
                "database_name": "testdatabase"
            }
        }
        '''

        req = request.get_json(force=True)
        server = req['server']

        result = rd.servers_post(server)
        return create_response(
                result['server_id'], 
                result['service_type'],
                result['service_name']
            )

class ServerById(Resource):
    def get(self, server_id):
        '''
        GET <server_url>/servers/65ff2fd7-81e7-4a99-8251-dafdaa7d89f2
        '''
        return rd.server_id_get(server_id) 
    
    def put(self, server_id):
        '''
        PUT <server_url>/servers/65ff2fd7-81e7-4a99-8251-dafdaa7d89f2

        {
            "size": "Standard_NC12"
        }
        '''
        req = request.get_json(force=True)
        if 'size' in req:
            size = req['size']
            vm_name = vm.set_vm_size(server_id, size)
            return create_response(server_id, 'vm', size, vm_name)

    def delete(self, server_id):
        '''
        DELETE <server_url>/servers/65ff2fd7-81e7-4a99-8251-dafdaa7d89f2
        '''
        resources.delete_resource_group(server_id)
        return create_response(server_id, '', '')

class ServerAction(Resource):
    def post(self, server_id):
        '''
        POST <server_url>/servers/adec8d18-9110-4e1b-8747-51543ed8474b/action

        {"os_start": ""}

        OR

        {"os_stop": {"type": "Soft"}}

        OR

        {"os_stop": {"type": "Hard"}}

        OR

        {"reboot": ""}
        '''
        req = request.get_json(force=True)
        if 'os_stop' in req:
            type = req['os_stop']['type']
            if type == 'HARD':
                print("Stop " + server_id + ". HARD.")
                vm.stop_vm(server_id, True)
            else:
                print("Stop " + server_id + ". SOFT.")
                vm.stop_vm(server_id, False)
            return "os stop"

        if 'os_start' in req:
            vm.start_vm(server_id)
            return "os start"
        
        if 'reboot' in req: 
            vm.restart_vm(server_id)
            return "os reboot"
        
        return "other"

class VolumesAction(Resource):
    def get(self, server_id):
        '''
        GET <server_url>/servers/adec8d18-9110-4e1b-8747-51543ed8474b/volumes
        '''
        return vm.get_volumes(server_id)

    def post(self, server_id):
        '''
        POST <server_url>/servers/adec8d18-9110-4e1b-8747-51543ed8474b/volumes

        Provide size in GB:

        { "size": 50 }
        '''
        req = request.get_json(force=True)
        size = int(req['size'])
        return vm.create_volume(server_id, size)

class VolumeById(Resource):
    def get(self, server_id, volume_id):
        '''
        GET <server_url>/servers/adec8d18-9110-4e1b-8747-51543ed8474b/volumes/0
        '''
        return vm.get_volume_by_lun(server_id, int(volume_id))
    
    def put(self, server_id, volume_id):
        '''
        PUT <server_url>/servers/adec8d18-9110-4e1b-8747-51543ed8474b/volumes/0

        Provide size in GB. Note that size decrease is not allowed. 

        { "size": 101 }
        '''
        print('PUT: ' + server_id + ' and ' + volume_id)
        req = request.get_json(force=True)
        size = int(req['size'])
        return vm.set_volume(server_id, int(volume_id), size)

    def delete(self, server_id, volume_id):
        '''
        DELETE <server_url>/servers/adec8d18-9110-4e1b-8747-51543ed8474b/volumes/0
        '''
        print('DELETE: ' + server_id + ' and ' + volume_id)
        return vm.delete_volume(server_id, int(volume_id))

class AllBills(Resource):
    def get(self):
        '''
        GET <server_url>/bills

        Provide datetime in milliseconds from 01.01.1970 00:00. Tha values will be truncated to the nearest hour. 

        {
            "to": 1553700885787,
            "from":   1551368356033
        }
        '''
        req = request.get_json(force=True)
        fromInt = int(req['from'])
        toInt = int(req['to'])

        fromDateTime = convert_datetime(fromInt)
        toDateTime = convert_datetime(toInt)
        print("From: " + str(fromDateTime))
        print("To: " + str(toDateTime))
        return billing.get_all_consumptions(fromDateTime, toDateTime)

class Bills(Resource):
    def get(self, server_id):
        '''
        GET <server_url>/bills/adec8d18-9110-4e1b-8747-51543ed8474b

        Provide datetime in milliseconds from 01.01.1970 00:00. Tha values will be truncated to the nearest hour. 

        {
            "to": 1553700885787,
            "from":   1551368356033
        }
        '''
        req = request.get_json(force=True)
        fromInt = int(req['from'])
        toInt = int(req['to'])

        fromDateTime = convert_datetime(fromInt)
        toDateTime = convert_datetime(toInt)
        print("From: " + str(fromDateTime))
        print("To: " + str(toDateTime))
        return billing.get_consumption(server_id, fromDateTime, toDateTime)

api.add_resource(Servers, '/servers')
api.add_resource(ServerAction, '/servers/<server_id>/action')
api.add_resource(VolumesAction, '/servers/<server_id>/volumes')
api.add_resource(VolumeById, '/servers/<server_id>/volumes/<volume_id>')
api.add_resource(ServerById, '/servers/<server_id>')
api.add_resource(AllBills, '/bills')
api.add_resource(Bills, '/bills/<server_id>')

if __name__ == '__main__':
     app.run(port='5002')