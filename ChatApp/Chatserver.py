from tkinter import *
from tkinter import ttk
from tkinter import font
import sys
import socket
import json
import os
import select

listen_port_number = 40860 #default port number


def feedToClients():
  if (rmsgDetails["TO"][0] == '' or rmsgDetails["TO"][0] == "ALL"):
    msgDetails = {"CMD": "MSG", "TYPE": "ALL", "MSG": rmsgDetails["MSG"], "FROM": rmsgDetails["FROM"]}
  elif (len(rmsgDetails["TO"]) == 1):
    msgDetails = {"CMD": "MSG", "TYPE": "PRIVATE", "MSG": rmsgDetails["MSG"], "FROM": rmsgDetails["FROM"]}
  elif (len(rmsgDetails["TO"]) > 1):
    msgDetails = {"CMD": "MSG", "TYPE": "GROUP", "MSG": rmsgDetails["MSG"], "FROM": rmsgDetails["FROM"]}
    
  msgDetailsToSend = json.dumps(msgDetails)
  
  if (msgDetails["TYPE"] != "ALL"): #not a broadcast
    try:
      for sendTo in rmsgDetails["TO"]:
        if (sendTo != rmsgDetails["FROM"]):
          WDict[sendTo].send(msgDetailsToSend.encode('ascii'))
          
    except: #if peer does not exist
      errorMsg = {"CMD": "MSG", "TYPE": "N/A"}
      WDict[rmsgDetails["FROM"]].send( (json.dumps(errorMsg)).encode('ascii') )
      
  else:
    for sendTo in listDetails["DATA"]:
      if (sendTo["UID"] != rmsgDetails["FROM"]):
        WDict[sendTo["UID"]].send(msgDetailsToSend.encode('ascii'))


def sendAck():

  ackDetails = {"CMD": "ACK", "TYPE": "OKAY"}
  ackDetailsToSend = json.dumps(ackDetails)
  
  newfd.send(ackDetailsToSend.encode('ascii'))
  print("Sent an \"OKAY\" ACK\n")
  

listDetails = {"CMD": "LIST", "DATA": []}
def addBroadcastList():

  listDetails["DATA"].append( {"UN": rmsgDetails["UN"], "UID": rmsgDetails["UID"]} )
  print("List details appended: ", listDetails)
  
  listDetailsToSend = json.dumps(listDetails)
  
  for peer in WList: #send LIST to ALL
    peer.send(listDetailsToSend.encode('ascii'))
  print("Sent updated list to ALL\n")
  

def remBroadcastList():
  
  for toRemove in listDetails["DATA"]:
    if WDict[toRemove["UID"]] == client: #if client address == address stored
      listDetails["DATA"].remove(toRemove)
  
  listDetailsToSend = json.dumps(listDetails)
  
  for peer in WList: #send LIST to ALL
    peer.send(listDetailsToSend.encode('ascii'))
  print("Sent updated list to ALL\n")


def main():

  global serverSocket
  serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  try:
    serverSocket.bind(("127.0.0.1", listen_port_number))
  except socket.error as emsg:
    print("Server socket bind error: "+ str(emsg)+"\n")

  serverSocket.listen(5)
  
  global RList, WDict, WList
  RList = [serverSocket] #sockets to read from clients
  WDict = {} #to look for UID's raddr
  WList = [] #sockets to write to clients

  global client
  while True: #constantly listen for clients' requests
    try:
      Rready, Wready, Eready = select.select(RList, [], [], 10)
      
    except select.error as emsg:
      print("At select, caught an exception:", emsg+"\n")
      sys.exit(1)
      
    except KeyboardInterrupt:
      print("At select, caught the KeyboardInterrupt\n")
      sys.exit(1)
      
    
    if Rready:
    
      for client in Rready:
        if client == serverSocket: #if new client requests for connection
        
          global newfd, clientAddress
          newfd, clientAddress = serverSocket.accept()
          print("A new client has arrived. It is at:", clientAddress)
          
          sendAck()
          
          RList.append(newfd)
          WList.append(newfd)
          
        else: #no new client, only particular existing clients sending data
        
          global rmsg
          rmsg = client.recv(1000)
          
          
          if rmsg:
            print("Received a message: ", rmsg.decode('ascii') +"\n")
              
            global rmsgDetails
            rmsgDetails = json.loads(rmsg.decode('ascii'))
            
            if (rmsgDetails["CMD"] == "JOIN"):
              addBroadcastList() #everytime invoked (arrival of new client), will send an updated LIST to ALL
              WDict[rmsgDetails["UID"]] = client #store address of client {"UID": addr}
              
            elif (rmsgDetails["CMD"] == "SEND"):
              feedToClients()
              
          else:
            print("A client connection is broken!\n")
            remBroadcastList()
            
            WList.remove(client)
            RList.remove(client)
            
      else:
        print("idling\n")
    
    
    

if __name__ == '__main__':
  
  if len(sys.argv) == 1:
      main()
  elif len(sys.argv) == 2:
      listen_port_number = int(sys.argv[1])
      main()
