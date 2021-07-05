import time as tm
import requests
import shutil
import base64
import json
import os
import sys


def watcher(route, header):
    urlApi = "https://api.alegra.com/api/v1/"
    while True:
        content = os.listdir(route)
        for data in content:
            if(len(data) >= 10 and data[:10] == "DhWWjQeATv" and data[-3:] == "txt"):
                # Read TXT
                routeData = route+data
                f = open(routeData, "r")
                txt = f.read()
                f.close()
                # Decode to Json
                dataReturn = ""

                jsonRead = json.loads(txt)

                #dataReturn = str(jsonRead)
                try:
                    dataQuery = jsonRead['data']
                    typeQuery = jsonRead['data']['type_cons']
                
                    if (typeQuery == "newFactura"):
                        dataDate = dataQuery['date']
                        dataDueDate = dataQuery['dueDate']
                        dataClient = dataQuery['client']
                        dataItems = dataQuery['items']
                        statusData = dataQuery['status']
                        dataPayments = dataQuery['payments']
                        idClient = dataClient['id']
                        dataPaymentMethod = dataQuery['paymentMethod']
                        dataPaymentForm = dataQuery['paymentForm']
                        returnItems = {}

                        if(idClient != None):
                            # Registered user -> Update DB
                            print('Registered User')

                            del dataClient['id']
                            # Request
                            r = requests.put(
                                urlApi+'contacts/'+str(idClient), headers=header, data=json.dumps(dataClient, indent=4))
                            print(r.json())
                        else:
                            print('Unregistered')
                            # Unregistered user -> Add DB
                            del dataClient['id']

                            # Request
                            r = requests.post(
                                urlApi+'contacts', headers=header, data=json.dumps(dataClient, indent=4))
                            print(r.json())
                            idClient = r.json()['id']

                        for item in dataItems:
                            if (item["id"] != None):
                                # Registered product -> Update DB
                                print("Registered product")
                                nameItem = item['name']
                                priceItem = item['price']  # Price default
                                quantityItem = item['quantity']
                                discountItem = item['discount']
                                taxItem = item['tax']

                                dataItem = {
                                    "name": item['name'],
                                    "price": item['price'],
                                    "status": "active"
                                }

                                # Request
                                r = requests.put(
                                    urlApi+'items/'+str(item['id']), headers=header, data=json.dumps(dataItem, indent=4))
                                print(r.json())
                                if (discountItem == None):
                                    discountItem = 0

                                if (taxItem != None):
                                    returnItems[r.json()['id']] = {
                                        'id': r.json()['id'],
                                        'name': r.json()['name'],
                                        'price': priceItem,
                                        'quantity': quantityItem,
                                        'discount': discountItem,
                                        'tax': taxItem
                                    }
                                else:
                                    returnItems[r.json()['id']] = {
                                        'id': r.json()['id'],
                                        'name': r.json()['name'],
                                        'price': priceItem,
                                        'quantity': quantityItem,
                                        'discount': discountItem,
                                    }
                            else:
                                # Unregistered product -> Add DB
                                print("Unregistered product")

                                nameItem = item['name']
                                priceItem = item['price']  # Price default
                                quantityItem = item['quantity']
                                discountItem = item['discount']
                                taxItem = item['tax']

                                if (discountItem == None):
                                    discountItem = 0

                                dataItem = {
                                    'name': nameItem,
                                    'price': priceItem
                                }
                                # Request
                                r = requests.post(
                                    urlApi+'items', headers=header, data=json.dumps(dataItem, indent=4))
                                print(r.json())

                                if (taxItem != None):
                                    returnItems[r.json()['id']] = {
                                        'id': r.json()['id'],
                                        'name': r.json()['name'],
                                        'price': priceItem,
                                        'quantity': quantityItem,
                                        'discount': discountItem,
                                        'tax': taxItem
                                    }
                                else:
                                    returnItems[r.json()['id']] = {
                                        'id': r.json()['id'],
                                        'name': r.json()['name'],
                                        'price': priceItem,
                                        'quantity': quantityItem,
                                        'discount': discountItem,
                                    }

                        newFactura = "{"
                        newFactura += f'"date": "{dataDate}",'
                        newFactura += f'"dueDate": "{dataDueDate}",'
                        newFactura += f'"client": {idClient},'
                        newFactura += f'"status": "{statusData}",'
                        newFactura += f'"paymentMethod": "{dataPaymentMethod}",'
                        newFactura += f'"paymentForm": "{dataPaymentForm}",'
                        newFactura += f'"items": ['

                        cont = 0
                        for item in returnItems:
                            if(cont > 0 and cont < len(returnItems)):
                                newFactura += ","
                            newFactura += str(json.dumps(returnItems[item]))
                            cont += 1

                        newFactura += '],'

                        newFactura += '"payments": [{'

                        for paymentData in dataPayments:
                            newFactura += '"date": "'+paymentData['date']+'",'
                            for accountDetail in paymentData['account']:
                                if accountDetail['id'] == None:

                                    # Unregistered account payment -> Create data in DB
                                    del accountDetail['id']
                                    # Request
                                    r = requests.post(
                                        urlApi+'bank-accounts', headers=header, data=json.dumps(accountDetail, indent=4))
                                    print(r.json())
                                    idAccount = r.json()['id']
                                else:
                                    # Registered account payment -> Update DB
                                    idAccount = paymentData['account'][0]['id']
                            newFactura += '"account": { "id": ' + \
                                str(idAccount)+' },'
                            newFactura += '"amount": ' + \
                                str(paymentData['amount'])+''
                        #print("///////// \n"+str(json.dumps(dataPayments)))
                        #newFactura += str(json.dumps(dataPayments))
                        newFactura += '}]'
                        newFactura += '}'

                        print(json.dumps(json.loads(newFactura), indent=4))
                        print('////////////ENVIANDO FACTURA A API////////////')

                        r = requests.post(
                            urlApi+'invoices', headers=header, data=json.dumps(json.loads(newFactura), indent=4))
                        print('////////////RESPUESTA////////////')
                        print(r.json())
                        dataReturn = r.json()['id'] #Id factura
                        dataReturn += "\n"
                        dataReturn += str(idAccount) #Id de tipo de pago
                        dataReturn += "\n"
                        dataReturn += str(idClient)  #Id de cliente
                        dataReturn += "\n"
                        dataReturn += "{"
                        cont = 0
                        for item in returnItems:
                            if(cont > 0 and cont < len(returnItems)):
                                dataReturn += ","
                            dataReturn += str(json.dumps(returnItems[item]))
                            cont += 1
                        dataReturn += "}"

                    ##Other type of query
                    elif (typeQuery == "consFactura"):
                        idConsult = dataQuery['id']
                        r = requests.get(
                            urlApi+'invoices/'+str(idConsult), headers=header)
                        dataReturn = str(json.dumps(r.json(), indent=4))

                    ##Other type of query
                    elif (typeQuery == "allFacturas"):
                        r = requests.get(
                            urlApi+'invoices/', headers=header)
                        dataReturn = str(json.dumps(r.json(), indent=4))
                    
                    ##Other type of query
                    else:
                        dataReturn = "Ingresa un type_cons correcto"
                except:
                    dataReturn = "Error al consultar"   
                # Send data to file Return
                routeReturn = "return/"+data
                fReturn = open(routeReturn, "w+")
                fReturn.write(dataReturn)
                fReturn.close()

                # Move file of Data to sended folder
                routeSended = "sended/"+data
                shutil.move(routeData, routeSended)

                # Delete the file of Data
                # os.remove(routeData)

        tm.sleep(10)


if __name__ == '__main__':
    # Auth new connection
    print("Starting...")
    try:
        if(sys.argv[1] == "contrasena"):
            email = sys.argv[2]
            apiKey = sys.argv[3]
            auth = f"{email}:{apiKey}"
            authBytes = auth.encode("ascii")
            encodedAuth = base64.b64encode(authBytes)
            messageAuth = encodedAuth.decode('ascii')
            header = {
                "Authorization": "Basic "+messageAuth
            }
            watcher('wait/', header)
    except:
        print("Parámetros erróneos")
