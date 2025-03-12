# Gateway between Modbus TCP and OPC UA

Prototype of an open source gateway between Modbus TCP protocol and OPC UA developed using Python as a project for Final Paper in my Mechatronics Engineering graduation.

It is able to convert both Modbus to OPC UA and OPC UA to Modbus data structure and communication parameters and also has a feature that converts Modbus TCP to serial based and vice versa. Besides, it has a simple HTML based user interface for parameter configuration and mode selection.

For now, the application is Windows only.

## Dependencies

For the code to be properly compiled, there are some necessary dependencies. Besides of Python itself, the following packages are needed:

pymodbus: pip install pymodbus  
Free OPC UA: pip install opcua

## Execution

To start the application, simply use the command py api.py with cmd within the folder it is downloaded. The user interface can be accessed at localhost in any web browser.

## Further Development

It was intended for the application to run embedded in a Raspberry Pi, but due to time limitations related to finishing the final paper, it was not developed. Feel free to try though.
