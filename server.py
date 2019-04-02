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
        return rd.server_id_get(server_id) 
        #return vm.get_vm(server_id)
    
    def put(self, server_id):
        req = request.get_json(force=True)
        if 'size' in req:
            size = req['size']
            vm_name = vm.set_vm_size(server_id, size)
            return create_response(server_id, 'vm', size, vm_name)

    def delete(self, server_id):
        resources.delete_resource_group(server_id)
        return create_response(server_id, '', '')

class ServerAction(Resource):
    def post(self, server_id):
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
        return vm.get_volumes(server_id)

    def post(self, server_id):
        req = request.get_json(force=True)
        size = int(req['size'])
        return vm.create_volume(server_id, size)

class VolumeById(Resource):
    def get(self, server_id, volume_id):
        return vm.get_volume_by_lun(server_id, int(volume_id))
    
    def put(self, server_id, volume_id):
        print('PUT: ' + server_id + ' and ' + volume_id)
        req = request.get_json(force=True)
        size = int(req['size'])
        return vm.set_volume(server_id, int(volume_id), size)

    def delete(self, server_id, volume_id):
        print('DELETE: ' + server_id + ' and ' + volume_id)
        return vm.delete_volume(server_id, int(volume_id))

class DeleteById(Resource):
    def delete(self, server_id):
        vm.delete_vm(server_id) 
        return {
            'server': {
                'server_id': server_id
            }
        }

class AllBills(Resource):
    def get(self):
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
        req = request.get_json(force=True)
        fromInt = int(req['from'])
        toInt = int(req['to'])

        fromDateTime = convert_datetime(fromInt)
        toDateTime = convert_datetime(toInt)
        print("From: " + str(fromDateTime))
        print("To: " + str(toDateTime))
        return billing.get_consumption(server_id, fromDateTime, toDateTime)

class Prices(Resource):
    def get(self):
        return billing.get_all_prices()

api.add_resource(Servers, '/servers')
api.add_resource(ServerAction, '/servers/<server_id>/action')
api.add_resource(VolumesAction, '/servers/<server_id>/volumes')
api.add_resource(VolumeById, '/servers/<server_id>/volumes/<volume_id>')
api.add_resource(ServerById, '/servers/<server_id>')
api.add_resource(AllBills, '/bills')
api.add_resource(Bills, '/bills/<server_id>')
api.add_resource(Prices, '/prices')

if __name__ == '__main__':
     app.run(port='5002')