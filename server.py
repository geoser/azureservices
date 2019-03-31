import os
from flask import Flask, request
from flask_restful import reqparse, Resource, Api
from sqlalchemy import create_engine
from flask_jsonpify import jsonify
import json

from conversions_helper import convert_datetime, encode_datetime

import vm
import billing

app = Flask(__name__)
api = Api(app)

class Servers(Resource):
    def get(self):
        return vm.get_all_vms()

    def post(self):
        req = request.get_json(force=True)
        server = req['server']

        service_type = server['service_type']
        '''
        
        POST <server_url>/servers

        sample input:

        {
            "server": {
                "name": "test10",
                "service_type": "VM",
                "service_name": "Standard_NC6",
                "user_name": "userlogin",
                "password": "Pa$$w0rd91",
                "os_type": "WINDOWS"
            }
        }
        '''
        if service_type == vm.ServiceType.VM.name:
            vmInfo = vm.VmCreationInfo()
            vmInfo.name = server['name']
            vmInfo.size = server['service_name']
            vmInfo.user_name = server['user_name']
            vmInfo.password = server['password']
            vmInfo.os_type = vm.OsType[server['os_type']]

            print(vmInfo)

            result = vm.create_vm(vmInfo)

            return {
                "server": {
                    "server_id": result['server']['server_id'], 
                    "service_type": result['server']['service_type'],
                    "service_name": result['server']['service_name'],
                    "name": vmInfo.name
                }
            }

class ServerById(Resource):
    def get(self, server_id):
        return vm.get_vm(server_id)

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

class FlavorsWithDetails(Resource):
    def get(self):
        return billing.get_all_flavors(True)

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