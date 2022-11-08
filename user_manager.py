try:
    from opcua import ua, uamethod, Server
    from opcua.server.user_manager import UserManager
    from time import sleep
except ImportError as e:
    print(e)

users_db =  {
                'admin': 'admin'
            }

def user_manager(isession, username, password):
    isession.user = UserManager.User
    return username in users_db and password == users_db[username]

if __name__ == "__main__":
    """
    OPC-UA-Server Setup
    """
    server = Server()

    endpoint = "opc.tcp://127.0.0.1:4840"
    server.set_endpoint(endpoint)

    servername = "Python-OPC-UA"
    server.set_server_name(servername)
    address_space = server.register_namespace("http://example.net/UA")
    
    uri = "urn:opcua:python:server"
    server.set_application_uri(uri)
    
    #server.load_certificate("cert.pem")
    #server.load_private_key("key.pem")
    #server.set_security_policy([
                                    # ua.SecurityPolicyType.NoSecurity,
                                    #ua.SecurityPolicyType.Basic128Rsa15_Sign,
                                    # ua.SecurityPolicyType.Basic128Rsa15_SignAndEncrypt,
                                    #ua.SecurityPolicyType.Basic256Sha256_Sign,
                                    #ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt
                                #])
    policyIDs = ["Username"]
    server.set_security_IDs(policyIDs)
    server.user_manager.set_user_manager(user_manager)

    """
    OPC-UA-Modeling
    """
    root_node = server.get_root_node()
    object_node = server.get_objects_node()
    server_node = server.get_server_node()


    """
    OPC-UA-Server Start
    """
    server.start()

    try:
        while 1:
            sleep(1)
    except KeyboardInterrupt:
        server.stop()