# Gateway entre Modbus TCP e OPC UA

Protótipo de um gateway open source entre Modbus TCP e OPC UA desenvolvido em Python como Trabalho de Conclusão de Curso em Engenharia Mecatrônica.

O gateway suporta conversões tanto de Modbus para OPC UA quanto de OPC UA para Modbus, e de quebra ainda possui funcionalidade de conversão entre Modbus TCP e Modbus RTU. Além disso, possui uma interface gráfica para configuração de parâmetros.

Por ora, a aplicação foi testada apenas em Windows.

## Dependências

Para que o código seja compilado corretamente, é necessário instalar algumas dependências, conforme a lista abaixo:

pymodbus: pip install pymodbus  
Free OPC UA: pip install opcua

## Execução

Para inicializar o gateway, é necessário baixar o repositório e executar o comando py api.py através do cmd dentro da pasta local.
