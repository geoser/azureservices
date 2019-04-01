import resources

def servers_get():
    return resources.get_all_tks_resource_groups()

def servers_post(request_json):
    service_type = request_json['service_type']
    if service_type == vm.ServiceType.VM.name:
            vmInfo = vm.VmCreationInfo()
            vmInfo.name = request_json['name']
            vmInfo.size = request_json['service_name']
            vmInfo.user_name = request_json['user_name']
            vmInfo.password = request_json['password']
            vmInfo.os_type = vm.OsType[request_json['os_type']]

            print(vmInfo)

            server_id = vm.create_vm(vmInfo)

            return server_id