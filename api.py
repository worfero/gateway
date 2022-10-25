from pymodbus.version import version
from pymodbus.server.asynchronous import StartTcpServer, StartSerialServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.datastore.remote import RemoteSlaveContext
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder

from opcua import ua, Client, Server

from wtforms import Form, BooleanField, StringField, PasswordField, SelectField, validators

from flask import Flask, request, render_template, url_for, redirect
from flask_restful import Api, Resource, reqparse, marshal, fields
from flask_sqlalchemy import SQLAlchemy
from multiprocessing import Process

import multiprocessing
import logging
import requests
import threading
import json
import os
import sys
import time
import subprocess
import time
import datetime

sys.path.insert(0, "..")

# from pymodbus.transaction import ModbusRtuFramer, ModbusBinaryFramer

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

#modes
TCP_TO_SERIAL = 0
SERIAL_TO_TCP = 1
TCP_TO_OPC = 2
OPC_TO_TCP = 3

# --------------------------------------------------------------------------- #
# configuration form structure
# --------------------------------------------------------------------------- #
# modbus TCP/modbus serial conversion settings form
class ModbusConfigs(Form):
    ip = StringField('IP', [validators.Length(min=0, max=15)])
    port = StringField('Port', [validators.Length(min=0, max=6)])
    serial_port = StringField('SerialPort', [validators.Length(min=0, max=8)])
    baudrate = SelectField(u'Baudrate', coerce=int, choices=[(4800, "4800"), (9600, "9600"), 
        (19200, "19200"), (57600, "57600"), (115200, "115200")])
    parity = StringField('Parity', [validators.Length(min=0, max=4)])
    bytesize = StringField('Bytesize', [validators.Length(min=0, max=1)])
    stopbits = StringField('Stopbits', [validators.Length(min=0, max=1)])

# modbus/OPCUA conversion settings form
class OPC_to_TCP_Configs(Form):
    name = StringField('Tag Name', [validators.Length(min=0, max=100)])
    register = StringField('Register', [validators.Length(min=0, max=6)])
    var_type = SelectField(u'Variable Type', coerce=str, choices=[("int", "int"), ("float", "float"), ("bit", "bit")])
    opc_object = StringField('OPC UA Object', [validators.Length(min=0, max=100)])
    slave_ip = StringField('Server IP', [validators.Length(min=0, max=15)])
    unit_id = StringField('Unit ID', [validators.Length(min=0, max=3)])

# mode selection form
class Mode(Form):
    #Opens json file to extract last submitted values
    mode = SelectField(u'Mode', coerce=int, choices=[(TCP_TO_SERIAL, 'Modbus TCP to Serial'),
        (SERIAL_TO_TCP, 'Modbus Serial to TCP'), (TCP_TO_OPC, 'Modbus TCP to OPC UA'), (OPC_TO_TCP, 'OPC UA to Modbus TCP')])

# --------------------------------------------------------------------------- #
# Class with methods for mode selection at start
# --------------------------------------------------------------------------- #
class Starters():
    # modbus TCP to modbus serial conversion mode
    def startTCPtoSerial():
        with open('config/TCP_to_Serial.json', 'r') as openfile:
            payload = json.load(openfile)
        try:
            r = requests.get('http://127.0.0.1:5000/')
            if r.status_code == 200:
                print('Starting server...')
                pay = payload
                head = {'content-type': 'application/json'}
                startForwarder = threading.Thread(target=Starters.serialForwarderStart, args=(pay, head,))
                startForwarder.start()
                not_started = False
        except:
            print('Server not yet started')
            not_started = True
        return not_started

    # modbus serial to modbus TCP conversion mode
    def startSerialToTCP():
        with open('config/Serial_to_TCP.json', 'r') as openfile:
            payload = json.load(openfile)
        try:
            r = requests.get('http://127.0.0.1:5000/')
            if r.status_code == 200:
                print('Starting server...')
                pay = payload
                head = {'content-type': 'application/json'}
                startForwarder = threading.Thread(target=Starters.tcpForwarderStart, args=(pay, head,))
                startForwarder.start()
                not_started = False
        except:
            print('Server not yet started')
            not_started = True
        return not_started

    # modbus TCP to OPC UA conversion mode
    def startTCPtoOPC():
        with open('config/TCP_to_OPC.json', 'r') as openfile:
            payload = json.load(openfile)
        try:
            r = requests.get('http://127.0.0.1:5000/')
            if r.status_code == 200:
                print('Starting server...')
                pay = payload
                head = {'content-type': 'application/json'}
                startOPCUA = threading.Thread(target=Starters.opcServerStart, args=(head,))
                startOPCUA.start()
                startModbus = threading.Thread(target=Starters.modbusTCPServerStart, args=(pay, head,))
                startModbus.start()
                not_started = False
        except:
            print('Server not yet started')
            not_started = True
        return not_started
    
    # OPC UA to modbus TCP conversion mode
    def startOPCtoTCP():
        try:
            r = requests.get('http://127.0.0.1:5000/')
            if r.status_code == 200:
                print('Starting server...')
                head = {'content-type': 'application/json'}
                startTCPClient = threading.Thread(target=Starters.modbusTCPClientStart, args=(head,))
                startTCPClient.start()
                not_started = False
        except:
            print('Server not yet started')
            not_started = True
        return not_started

    def modbusTCPServerStart(pay, head):
        req = requests.post('http://localhost:5000/modbus-explorer/api/tcp/server', data=json.dumps(pay), 
                                headers = head)

    def modbusTCPClientStart(head):
        req = requests.post('http://localhost:5000/modbus-explorer/api/tcp/tcpclient', data=None, 
                                headers = head)

    def opcClientStart(head):
        req = requests.post('http://localhost:5000/modbus-explorer/api/tcp/opcuaclient', data=None, 
                                headers = head)

    def opcServerStart(head):
        req = requests.post('http://localhost:5000/modbus-explorer/api/tcp/opcuaserver', data=None, 
                                headers = head)
    
    def serialForwarderStart(pay, head):
        req = requests.post('http://localhost:5000/modbus-explorer/api/tcp/mbusSerialforwarder', data=json.dumps(pay), 
                                headers = head)
    
    def tcpForwarderStart(pay, head):
        req = requests.post('http://localhost:5000/modbus-explorer/api/tcp/mbusTCPforwarder', data=json.dumps(pay), 
                                headers = head)

# --------------------------------------------------------------------------- #
# API Resources
# --------------------------------------------------------------------------- #
class ModbusTcpForwarder(Resource):
    # --------------------------------------------------------------------------- #
    # gateway resource structure
    # --------------------------------------------------------------------------- #

    def __init__(self):
        # --------------------------------------------------------------------------- #
        # argument parsing
        # --------------------------------------------------------------------------- #
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('ip', type=str, required=True, location='json',
                                   help='No IP address provided')
        self.reqparse.add_argument('port', type=int, required=True, location='json',
                                   help='No port provided')
        self.reqparse.add_argument('serial_port', type=str, required=True, location='json',
                                   help='No serial port provided')
        self.reqparse.add_argument('baudrate', type=int, required=True, location='json',
                                   help='No baudrate provided')
        self.reqparse.add_argument('bytesize', type=int, required=True, location='json',
                                   help='No bytesize provided')
        self.reqparse.add_argument('parity', type=str, required=True, location='json',
                                   help='No parity provided')
        self.reqparse.add_argument('stopbits', type=int, required=True, location='json',
                                   help='No stopbits provided')
        super(ModbusTcpForwarder, self).__init__()

    def post(self):
        # --------------------------------------------------------------------------- #
        # argument parsing query
        # --------------------------------------------------------------------------- #
        query = self.reqparse.parse_args()

        client = ModbusTcpClient(port=query['ip'], baudrate=query['port'])
        
        store = {unit_number: RemoteSlaveContext(client, unit=unit_number) 
                    for unit_number in range(1, 248)}
        context = ModbusServerContext(slaves=store, single=False)

        # --------------------------------------------------------------------------- #
        # start redirecting process
        # --------------------------------------------------------------------------- #
        StartSerialServer(context, port=query['serial_port'], framer=ModbusRtuFramer, baudrate=query['baudrate'],
                        bytesize=query['bytesize'], parity=query['parity'], stopbits=query['stopbits'])  

class ModbusSerialForwarder(Resource):
    # --------------------------------------------------------------------------- #
    # gateway resource structure
    # --------------------------------------------------------------------------- #

    def __init__(self):
        # --------------------------------------------------------------------------- #
        # argument parsing
        # --------------------------------------------------------------------------- #
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('ip', type=str, required=True, location='json',
                                   help='No IP address provided')
        self.reqparse.add_argument('port', type=int, required=True, location='json',
                                   help='No port provided')
        self.reqparse.add_argument('serial_port', type=str, required=True, location='json',
                                   help='No serial port provided')
        self.reqparse.add_argument('baudrate', type=int, required=True, location='json',
                                   help='No baudrate provided')
        self.reqparse.add_argument('bytesize', type=int, required=True, location='json',
                                   help='No bytesize provided')
        self.reqparse.add_argument('parity', type=str, required=True, location='json',
                                   help='No parity provided')
        self.reqparse.add_argument('stopbits', type=int, required=True, location='json',
                                   help='No stopbits provided')
        super(ModbusSerialForwarder, self).__init__()

    def post(self):
        # --------------------------------------------------------------------------- #
        # argument parsing query
        # --------------------------------------------------------------------------- #
        query = self.reqparse.parse_args()

        client = ModbusSerialClient(method='rtu', port=query['serial_port'], baudrate=query['baudrate'],
                                    bytesize=query['bytesize'], parity=query['parity'], stopbits=query['stopbits'])
        
        store = {unit_number: RemoteSlaveContext(client, unit=unit_number) 
                    for unit_number in range(1, 248)}
        context = ModbusServerContext(slaves=store, single=False)

        # --------------------------------------------------------------------------- #
        # start redirecting process
        # --------------------------------------------------------------------------- #
        StartTcpServer(context, address=(query['ip'], query['port']))

class ModbusTCPServer(Resource):
    # --------------------------------------------------------------------------- #
    # gateway resource structure
    # --------------------------------------------------------------------------- #

    def __init__(self):
        # --------------------------------------------------------------------------- #
        # argument parsing
        # --------------------------------------------------------------------------- #
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('ip', type=str, required=True, location='json',
                                   help='No IP address provided')
        self.reqparse.add_argument('port', type=int, required=True, location='json',
                                   help='No port provided')
        self.reqparse.add_argument('serial_port', type=str, required=True, location='json',
                                   help='No serial port provided')
        self.reqparse.add_argument('baudrate', type=int, required=True, location='json',
                                   help='No baudrate provided')
        self.reqparse.add_argument('bytesize', type=int, required=True, location='json',
                                   help='No bytesize provided')
        self.reqparse.add_argument('parity', type=str, required=True, location='json',
                                   help='No parity provided')
        self.reqparse.add_argument('stopbits', type=int, required=True, location='json',
                                   help='No stopbits provided')
        super(ModbusTCPServer, self).__init__()

    def post(self):
        # --------------------------------------------------------------------------- #
        # argument parsing query
        # --------------------------------------------------------------------------- #
        query = self.reqparse.parse_args()

        initval = 0
        max_regs = 20000

        store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [initval]*max_regs),
            co=ModbusSequentialDataBlock(0, [initval]*max_regs),
            hr=ModbusSequentialDataBlock(0, [initval]*max_regs),
            ir=ModbusSequentialDataBlock(0, [initval]*max_regs)
        )
        context = ModbusServerContext(slaves=store, single=True)

        # --------------------------------------------------------------------------- #
        # start redirecting process
        # --------------------------------------------------------------------------- #
        StartTcpServer(context, address=(query['ip'], query['port']))

class ModbusTCPClient(Resource):
    def post(self):
        server = Server()
        server.set_endpoint("opc.tcp://127.0.0.1:4880")
        # setup our own namespace, not really necessary but should as spec
        uri = "Gateway"
        idx = server.register_namespace(uri)
        # get Objects node, this is where we should put our nodes
        objects = server.get_objects_node()

        tags = OPC_to_TCP_Tags.query.all()
        distinct_objs = OPC_to_TCP_Tags.query.with_entities(OPC_to_TCP_Tags.opc_object).distinct()
        index = 0
        obj_index = 0
        n_tags = len(tags)
        n_objects = distinct_objs.count()
        tag_name = [None] * n_tags
        slave_ip = [None] * n_tags
        unit_id = [None] * n_tags
        tag_register = [None] * n_tags
        object_name = [None] * n_objects
        opc_objects = [None] * n_objects
        # populating our address space
        for tag in distinct_objs:
            object_name[obj_index] = tag.opc_object
            opc_objects[obj_index] = objects.add_object(idx, str(tag.opc_object))
            obj_index += 1
        obj_index = 0
        for tag in tags:
            for opc_obj in opc_objects:
                if tag.opc_object == object_name[obj_index]:
                    tag_name[index] = opc_obj.add_variable(idx, str(tag.name), 1)
                    tag_name[index].set_writable()
                obj_index += 1
            index += 1
            obj_index = 0
        # starting!
        server.start()
        #head = {'content-type': 'application/json'}
        #startOPCUA = threading.Thread(target=Starters.opcClientStart, args=(head,))
        #startOPCUA.start()
        try:
            while True:
                index = 0
                for tag in tags:
                    tag_name_find = "2:" + str(tag.name)
                    tag_object_find = "2:" + str(tag.opc_object)
                    myData = tag_name[index].get_value()
                    mbus_client = ModbusTcpClient(tag.slave_ip, 502)
                    mbus_client.connect()
                    if tag.var_type == "int":
                        count = 1
                        mbus_client.write_registers(int(tag.register), int(myData), unit=int(tag.unit_id))
                    elif tag.var_type == "bit":
                        count = 1
                        mbus_client.write_coils(int(tag.register), int(myData), unit=int(tag.unit_id))
                    #elif tag.var_type == "float":
                        #count = 2
                        #data[index] = mbus_client.read_holding_registers(tag_register[index], count, unit=tag.unit_id)
                    mbus_client.close()
        finally:
            #close connection, remove subcsriptions, etc
            server.stop()

class OPCUAClient(Resource):
    # --------------------------------------------------------------------------- #
    # gateway resource structure
    # --------------------------------------------------------------------------- #

    def post(self):
        opc_client = Client("opc.tcp://127.0.0.1:4880")
        try:
            # connecting!
            opc_client.connect()
            # Client has a few methods to get proxy to UA nodes that should always be in address space
            root = opc_client.get_root_node()
            tags = TCP_to_OPC_Tags.query.all()
            distinct_objs = TCP_to_OPC_Tags.query.with_entities(TCP_to_OPC_Tags.opc_object).distinct()
            index = 0
            n_tags = len(tags)
            n_objects = distinct_objs.count()
            tag_name = [None] * n_tags
            tag_object = [None] * n_tags
            myData = [None] * n_tags
            obj = [None] * n_tags
            tag_register = [None] * n_tags
            for tag in tags:
                tag_name[index] = "2:" + str(tag.name)
                tag_object[index] = "2:" + str(tag.opc_object)
                myData[index] = root.get_child(["0:Objects", tag_object[index], tag_name[index]])
                obj[index] = root.get_child(["0:Objects", tag_object[index]])
                tag_register[index] = int(tag.register)
                index += 1
            mbus_client = ModbusTcpClient("127.0.0.1", 502)
            mbus_client.connect()
            data = [None] * n_tags
            while True:
                index = 0
                register = None
                for tag in tags:
                    if tag.var_type == "int":
                        count = 1
                        data[index] = mbus_client.read_holding_registers(tag_register[index], count, unit=1)
                    elif tag.var_type == "bit":
                        count = 1
                        data[index] = mbus_client.read_coils(tag_register[index], count, unit=1)
                    elif tag.var_type == "float":
                        count = 2
                        data[index] = mbus_client.read_holding_registers(tag_register[index], count, unit=1)
                    if tag.var_type == "int":
                        register = data[index].registers[0]
                    if tag.var_type == "bit":
                        register = data[index].bits[0]
                    elif tag.var_type == "float":
                        decoder = BinaryPayloadDecoder.fromRegisters(data[index].registers, Endian.Big, wordorder=Endian.Little)
                        register = decoder.decode_32bit_float()
                    myData[index].set_value(register)
                    i = index + 1 + n_objects
                    node = "ns=2;i=" + str(i)
                    print(node)
                    print(opc_client.get_node(node).get_value())   
                    index += 1       
        finally:
            opc_client.disconnect()

class OPCUAServer(Resource):
    def post(self):
        server = Server()
        server.set_endpoint("opc.tcp://127.0.0.1:4880")
        # setup our own namespace, not really necessary but should as spec
        uri = "Gateway"
        idx = server.register_namespace(uri)
        # get Objects node, this is where we should put our nodes
        objects = server.get_objects_node()

        tags = TCP_to_OPC_Tags.query.all()
        distinct_objs = TCP_to_OPC_Tags.query.with_entities(TCP_to_OPC_Tags.opc_object).distinct()
        index = 0
        obj_index = 0
        n_tags = len(tags)
        n_objects = distinct_objs.count()
        tag_name = [None] * n_tags
        object_name = [None] * n_objects
        opc_objects = [None] * n_objects
        # populating our address space
        for tag in distinct_objs:
            object_name[obj_index] = tag.opc_object
            opc_objects[obj_index] = objects.add_object(idx, str(tag.opc_object))
            obj_index += 1
        obj_index = 0
        for tag in tags:
            for opc_obj in opc_objects:
                if tag.opc_object == object_name[obj_index]:
                    tag_name[index] = opc_obj.add_variable(idx, str(tag.name), 0)
                    tag_name[index].set_writable()
                obj_index += 1
            index += 1
            obj_index = 0
        # starting!
        server.start()
        head = {'content-type': 'application/json'}
        startOPCUA = threading.Thread(target=Starters.opcClientStart, args=(head,))
        startOPCUA.start()
        try:
            while True:
                pass
        finally:
            #close connection, remove subcsriptions, etc
            server.stop()

# --------------------------------------------------------------------------- #
# API definition
# --------------------------------------------------------------------------- #
# application instance
app = Flask(__name__)

# tags databases instance
app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/tcp_to_opc.sqlite3'
app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/opc_to_tcp.sqlite3'
db = SQLAlchemy(app)

# api and resources instance
api = Api(app)
api.add_resource(ModbusTCPServer, '/modbus-explorer/api/tcp/server')
api.add_resource(ModbusTCPClient, '/modbus-explorer/api/tcp/tcpclient')
api.add_resource(OPCUAClient, '/modbus-explorer/api/tcp/opcuaclient')
api.add_resource(OPCUAServer, '/modbus-explorer/api/tcp/opcuaserver')
api.add_resource(ModbusSerialForwarder, '/modbus-explorer/api/tcp/mbusSerialforwarder')
api.add_resource(ModbusTcpForwarder, '/modbus-explorer/api/tcp/mbusTCPforwarder')

# --------------------------------------------------------------------------- #
# modbus TCP to OPC UA tags database
# --------------------------------------------------------------------------- #
class TCP_to_OPC_Tags(db.Model):
    id = db.Column('tag_id', db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    register = db.Column(db.String(10))  
    var_type = db.Column(db.String(10))
    opc_object = db.Column(db.String(100))

    def __init__(self, name, register, var_type, opc_object):
        self.name = name
        self.register = register
        self.var_type = var_type
        self.opc_object = opc_object

# --------------------------------------------------------------------------- #
# OPC UA to modbus TCP tags database
# --------------------------------------------------------------------------- #
class OPC_to_TCP_Tags(db.Model):
    id = db.Column('tag_id', db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    register = db.Column(db.String(10))  
    var_type = db.Column(db.String(10))
    opc_object = db.Column(db.String(100))
    slave_ip = db.Column(db.String(10))
    unit_id = db.Column(db.String(4))

    def __init__(self, name, register, var_type, opc_object, slave_ip, unit_id):
        self.name = name
        self.register = register
        self.var_type = var_type
        self.opc_object = opc_object
        self.slave_ip = slave_ip
        self.unit_id = unit_id

# application restart flag
restart = 0

# --------------------------------------------------------------------------- #
# index page
# --------------------------------------------------------------------------- #
@app.route("/", methods=['GET', 'POST'])
def hello():
    global restart
    with open('config/Mode.json', 'r') as openfile:
        lastConfig = json.load(openfile)
    form = Mode(request.form, mode=lastConfig['mode'])
    if request.method == 'POST' and form.validate():
        mode = form.mode.data

        payload = {'mode': mode}
        mode_config = json.dumps(payload)
        if request.form['action'] == 'Apply':
            with open("config/Mode.json", "w") as outfile:
                outfile.write(mode_config)
            return redirect(url_for('hello'))
        elif request.form['action'] == 'Reset':
            restart = 1
            return redirect(url_for('hello'))
        elif request.form['action'] == 'Configuration':
            if mode == TCP_TO_SERIAL:
                return redirect(url_for('tcp_to_serial'))
            elif mode == SERIAL_TO_TCP:
                return redirect(url_for('serial_to_tcp'))
            elif mode == TCP_TO_OPC:
                return redirect(url_for('tcp_to_opc'))
            elif mode == OPC_TO_TCP:
                return redirect(url_for('opc_to_tcp'))
    return render_template('index.html', form=form)

# --------------------------------------------------------------------------- #
# modbus TCP to modbus serial configuration page
# --------------------------------------------------------------------------- #
@app.route('/tcp_to_serial', methods=['GET', 'POST'])
def tcp_to_serial():
    global restart
    with open('config/TCP_to_Serial.json', 'r') as openfile:
        lastConfig = json.load(openfile)
    form = ModbusConfigs(request.form, ip=lastConfig['ip'], port=str(lastConfig['port']), 
            serial_port=lastConfig['serial_port'], baudrate=str(lastConfig['baudrate']), parity=lastConfig['parity'], 
            bytesize=str(lastConfig['bytesize']), stopbits=str(lastConfig['stopbits']))
    if request.method == 'POST' and form.validate():
        if request.form['action'] == 'Apply':
            ip = form.ip.data
            port = int(form.port.data)
            serial_port = form.serial_port.data
            baudrate = int(form.baudrate.data)
            bytesize = int(form.bytesize.data)
            parity = form.parity.data
            stopbits = int(form.stopbits.data)

            payload = {'ip': ip, 'port': port, 'serial_port': serial_port, 'baudrate': baudrate, 
                        'bytesize': bytesize, 'parity': parity, 'stopbits': stopbits}
            gw_config = json.dumps(payload)
            with open("config/TCP_to_Serial.json", "w") as outfile:
                outfile.write(gw_config)
            return redirect(url_for('tcp_to_serial'))

        elif request.form['action'] == 'Reset':
            restart = 1
            return redirect(url_for('hello'))
            
        elif request.form['action'] == 'Back':
            return redirect(url_for('hello'))

    return render_template('tcp_to_serial.html', form=form)

# --------------------------------------------------------------------------- #
# modbus serial to modbus tcp configuration page
# --------------------------------------------------------------------------- #
@app.route('/serial_to_tcp', methods=['GET', 'POST'])
def serial_to_tcp():
    global restart
    with open('config/Serial_to_TCP.json', 'r') as openfile:
        lastConfig = json.load(openfile)
    form = ModbusConfigs(request.form, ip=lastConfig['ip'], port=str(lastConfig['port']), 
            serial_port=lastConfig['serial_port'], baudrate=str(lastConfig['baudrate']), parity=lastConfig['parity'], 
            bytesize=str(lastConfig['bytesize']), stopbits=str(lastConfig['stopbits']))
    if request.method == 'POST' and form.validate():
        if request.form['action'] == 'Apply':
            ip = form.ip.data
            port = int(form.port.data)
            serial_port = form.serial_port.data
            baudrate = int(form.baudrate.data)
            bytesize = int(form.bytesize.data)
            parity = form.parity.data
            stopbits = int(form.stopbits.data)

            payload = {'ip': ip, 'port': port, 'serial_port': serial_port, 'baudrate': baudrate, 
                        'bytesize': bytesize, 'parity': parity, 'stopbits': stopbits}
            gw_config = json.dumps(payload)
            with open("config/Serial_to_TCP.json", "w") as outfile:
                outfile.write(gw_config)
            return redirect(url_for('serial_to_tcp'))

        elif request.form['action'] == 'Reset':
            restart = 1
            return redirect(url_for('hello'))
            
        elif request.form['action'] == 'Back':
            return redirect(url_for('hello'))

    return render_template('serial_to_tcp.html', form=form)

# --------------------------------------------------------------------------- #
# modbus TCP to OPC UA configuration page
# --------------------------------------------------------------------------- #
@app.route('/tcp_to_opc', methods=['GET', 'POST'])
def tcp_to_opc():
    global restart
    with open('config/TCP_to_OPC.json', 'r') as openfile:
        lastConfig = json.load(openfile)
    form = ModbusConfigs(request.form, ip=lastConfig['ip'])
    if request.method == 'POST':
        if request.form['action'] == 'Apply':
            ip = form.ip.data
            payload = {'ip': ip, 'port': 502}
            gw_config = json.dumps(payload)
            with open("config/TCP_to_OPC.json", "w") as outfile:
                outfile.write(gw_config)
            return redirect(url_for('tcp_to_opc'))

        elif request.form['action'] == 'Add Tag':
            return redirect(url_for('new_tcp_to_opc_tag'))

        elif request.form['action'] == 'Delete Tag':
            tag_id = request.form['tagID']
            obj = TCP_to_OPC_Tags.query.filter_by(id=int(tag_id)).one()
            db.session.delete(obj)
            db.session.commit()
            time.sleep(1)
            return redirect(url_for('tcp_to_opc'))

        elif request.form['action'] == 'Delete All':
            db.session.query(TCP_to_OPC_Tags).delete()
            db.session.commit()
            time.sleep(1)
            return redirect(url_for('tcp_to_opc'))

        elif request.form['action'] == 'Reset':
            restart = 1
            return redirect(url_for('hello'))
        
        elif request.form['action'] == 'Back':
            return redirect(url_for('hello'))
    return render_template('tcp_to_opc.html', tags = TCP_to_OPC_Tags.query.all(), form=form)

# --------------------------------------------------------------------------- #
# OPC UA to modbus TCP configuration page
# --------------------------------------------------------------------------- #
@app.route('/opc_to_tcp', methods=['GET', 'POST'])
def opc_to_tcp():
    global restart
    if request.method == 'POST':
        if request.form['action'] == 'Add Tag':
            return redirect(url_for('new_opc_to_tcp_tag'))
            
        elif request.form['action'] == 'Delete Tag':
            tag_id = request.form['tagID']
            obj = OPC_to_TCP_Tags.query.filter_by(id=int(tag_id)).one()
            db.session.delete(obj)
            db.session.commit()
            time.sleep(1)
            return redirect(url_for('opc_to_tcp'))

        elif request.form['action'] == 'Delete All':
            db.session.query(OPC_to_TCP_Tags).delete()
            db.session.commit()
            time.sleep(1)
            return redirect(url_for('opc_to_tcp'))

        elif request.form['action'] == 'Reset':
            restart = 1
            return redirect(url_for('hello'))

        elif request.form['action'] == 'Back':
            return redirect(url_for('hello'))
    return render_template('opc_to_tcp_all.html', tags = OPC_to_TCP_Tags.query.all() )

# --------------------------------------------------------------------------- #
# modbus TCP to OPC UA tag creation page
# --------------------------------------------------------------------------- #
@app.route('/new_tcp_to_opc_tag', methods = ['GET', 'POST'])
def new_tcp_to_opc_tag():
    form = OPC_to_TCP_Configs(request.form, name="", register="", var_type="", opc_object="")
    if request.method == 'POST' and form.validate():
        name = form.name.data
        register = form.register.data
        var_type = form.var_type.data
        opc_object = form.opc_object.data

        tag = TCP_to_OPC_Tags(name, register, var_type, opc_object)

        db.session.add(tag)
        db.session.commit()
        return redirect(url_for('tcp_to_opc'))
    return render_template('new_tcp_to_opc_tag.html', form=form)

# --------------------------------------------------------------------------- #
# OPC UA to modbus TCP tag creation page
# --------------------------------------------------------------------------- #
@app.route('/new_opc_to_tcp_tag', methods = ['GET', 'POST'])
def new_opc_to_tcp_tag():
    form = OPC_to_TCP_Configs(request.form, name="", register="", var_type="", opc_object="", slave_ip="", unit_id="")
    if request.method == 'POST' and form.validate():
        name = form.name.data
        register = form.register.data
        var_type = form.var_type.data
        opc_object = form.opc_object.data
        slave_ip = form.slave_ip.data
        unit_id = form.unit_id.data

        tag = OPC_to_TCP_Tags(name, register, var_type, opc_object, slave_ip, unit_id)

        db.session.add(tag)
        db.session.commit()
        return redirect(url_for('opc_to_tcp'))
    return render_template('new_opc_to_tcp_tag.html', form=form)

# --------------------------------------------------------------------------- #
# application start method
# --------------------------------------------------------------------------- #
def start_runner():
    def start_loop():
        not_started = True
        while not_started:
            print('In start loop')

            # reads selected mode from mode selection file
            with open('config/Mode.json', 'r') as openfile:
                mode = json.load(openfile)
            
            # modbus TCP to modbus serial conversion mode
            if mode['mode'] == TCP_TO_SERIAL:
                not_started = Starters.startTCPtoSerial()

            # modbus serial to modbus TCP conversion mode
            elif mode['mode'] == SERIAL_TO_TCP:
                not_started = Starters.startSerialToTCP()

            # modbus TCP to OPC UA conversion mode
            elif mode['mode'] == TCP_TO_OPC:
                not_started = Starters.startTCPtoOPC()

            # OPC UA to modbus TCP conversion mode
            elif mode['mode'] == OPC_TO_TCP:
                not_started = Starters.startOPCtoTCP()
            # --------------------------------------------------------------------------- #
            # exception
            # --------------------------------------------------------------------------- #
            else:
                print('Invalid mode selected.')

    print('Started runner')
    start_api = threading.Thread(target=start_loop)
    start_api.start()

# --------------------------------------------------------------------------- #
# application boot function
# --------------------------------------------------------------------------- #
def boot(event):
    # sets the event for the api to restart with new config
    def reset():
        global restart
        while True:
            if restart == 1:
                time.sleep(0.5)
                event.set()
    # Assures the reset check loop will only start after application start
    reset_check = threading.Thread(target=reset)
    reset_check.start()
    # starts the application
    start_runner()
    app.run()

# --------------------------------------------------------------------------- #
# calls the app boot function and waits for rebooting request
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    db.create_all()
    event = multiprocessing.Event()
    p = Process(target=boot, args=(event,))
    tags = TCP_to_OPC_Tags.query.all()
    p.start()
    while True:
        if event.is_set():
            p.terminate()
            args = [sys.executable] + [sys.argv[0]]
            subprocess.call(args)