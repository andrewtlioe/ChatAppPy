from tkinter import *
from tkinter import ttk
from tkinter import font
import sys
import socket
import json
import os
import time
import _thread

#
# Global variables
#
MLEN=1000      #assume all commands are shorter than 1000 bytes
USERID = None
NICKNAME = None
SERVER = None
SERVER_PORT = None #change to port40860-40869 later

clientSocket = None
peerListPrint = ""
uidToNickname = {}
recvrRun = False
connected = False

#
# Functions to handle user input
#

def receiver():
  global peerListPrint, uidToNickname, recvrRun
  recvrRun = True
  
  while True:
     
    if clientSocket == None:
      break #client left
  
    try:
      recvData = (clientSocket.recv(MLEN)).decode('ascii')
      console_print("Received data from the server: "+str(recvData))
      
    except socket.error as emsg:
      console_print("Connection error: "+ str(emsg))
      
    recvInfo = json.loads(recvData)
    
    if (recvInfo["CMD"] == "ACK"):
    
      if (recvInfo["TYPE"] == "OKAY"):
        console_print("Received an \"OKAY\" ACK")
      elif (recvInfo["TYPE"] == "FAIL"):
        console_print("Received an \"FAIL\" ACK")
        #fail ack code implement
        
    elif (recvInfo["CMD"] == "LIST"):
    
      for userDetail in recvInfo["DATA"]:
        uidToNickname[userDetail["UID"]] = userDetail["UN"]
        peerListPrint += (userDetail["UN"] + " " + "(" + str(userDetail["UID"]) + "), ")
      
      list_print(peerListPrint[:-2])
      peerListPrint = "" #clear for updating later
      
    elif (recvInfo["CMD"] == "MSG"):
    
      if (recvInfo["TYPE"] == "ALL"):
        chat_print("["+uidToNickname[recvInfo["FROM"]]+"] " + recvInfo["MSG"], 'bluemsg') #change userid to nickname
        
      elif (recvInfo["TYPE"] == "PRIVATE"):
        chat_print("["+uidToNickname[recvInfo["FROM"]]+"] " + recvInfo["MSG"], 'redmsg')
        
      elif (recvInfo["TYPE"] == "GROUP"):
        chat_print("["+uidToNickname[recvInfo["FROM"]]+"] " + recvInfo["MSG"], 'greenmsg')
      
      elif (recvInfo["TYPE"] == "N/A"):
        chat_print("Peer does not exist")
  
  recvrRun = False
  list_print("") #clear peer list when leave
  print ("Thread killed")
  

def do_Join():
  console_print("Press do_Join()")
  
  if not recvrRun:

    global clientSocket
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #clientSocket.settimeout(2.0)

    try:
      clientSocket.connect((SERVER, SERVER_PORT))
      connected = True

    except socket.error as emsg:
      console_print("Socket connect error: "+ str(emsg))
      chat_print("Chatserver unreachable! Try Again")
      connected = False
      
    if connected:

      joinDetails = {"CMD": "JOIN", "UN": NICKNAME, "UID": USERID}
      joinDetailsToSend = json.dumps(joinDetails)
      chat_print("You joined.")
      
      clientSocket.send(joinDetailsToSend.encode('ascii'))
      console_print ("Sent " + joinDetailsToSend)
      
      _thread.start_new_thread(receiver, () ) #receiving thread for handling recv()
  
  else:
    chat_print("Already connected to server!")
  

def do_Send():
  printTo = ""
  console_print("Press do_Send()")
  
  sendDetails = {"CMD": "SEND", "MSG": get_sendmsg(), "TO": get_tolist().split(','), "FROM": USERID}
  console_print ("Send details: "+str(sendDetails))
  
  try:
    for uid in sendDetails["TO"]:
      printTo += str(uidToNickname[uid]) + ", "
    chat_print("[TO: "+( printTo[:-2] )+"] "+sendDetails["MSG"])
  except:
    printTo = "ALL"
    chat_print("[TO: "+( printTo )+"] "+sendDetails["MSG"])
  
  sendDetailsToSend = json.dumps(sendDetails)
  clientSocket.send(sendDetailsToSend.encode('ascii'))
  

def do_Leave():
  global clientSocket, recvrRun
  
  if recvrRun:
    chat_print("You left.")
    list_print("") #clear peer list when leave
    clientSocket.close()
    
    recvrRun = False
    clientSocket = None
  
  else:
    chat_print("You cannot leave before joining.")
  
  


  


#################################################################################
#These are for the UI                                                            #
#################################################################################

#for displaying all log or error messages to the console frame
def console_print(msg):
  console['state'] = 'normal'
  console.insert(1.0, "\n"+msg)
  console['state'] = 'disabled'

#for displaying all chat messages to the chatwin message frame
#message from this user - justify: left, color: black
#message from other user - justify: right, color: red ('redmsg')
#message from group - justify: right, color: green ('greenmsg')
#message from broadcast - justify: right, color: blue ('bluemsg')
def chat_print(msg, opt=""):
  chatWin['state'] = 'normal'
  chatWin.insert(1.0, "\n"+msg, opt)
  chatWin['state'] = 'disabled'

#for displaying the list of users to the ListDisplay frame
def list_print(msg):
  ListDisplay['state'] = 'normal'
  #delete the content before printing
  ListDisplay.delete(1.0, END)
  ListDisplay.insert(1.0, msg)
  ListDisplay['state'] = 'disabled'

#for getting the list of recipents from the 'To' input field
def get_tolist():
  msg = toentry.get()
  toentry.delete(0, END)
  return msg

#for getting the outgoing message from the "Send" input field
def get_sendmsg():
  msg = SendMsg.get(1.0, END)
  SendMsg.delete(1.0, END)
  return msg

#for initializing the App
def init():
  global USERID, NICKNAME, SERVER, SERVER_PORT

  #check if provided input argument
  if (len(sys.argv) > 2):
    print("USAGE: ChatApp [config file]")
    sys.exit(0)
  elif (len(sys.argv) == 2):
    config_file = sys.argv[1]
  else:
    config_file = "config.txt"

  #check if file is present
  if os.path.isfile(config_file):
    #open text file in read mode
    text_file = open(config_file, "r")
    #read whole file to a string
    data = text_file.read()
    #close file
    text_file.close()
    #convert JSON string to Dictionary object
    config = json.loads(data)
    USERID = config["USERID"].strip()
    NICKNAME = config["NICKNAME"].strip()
    SERVER = config["SERVER"].strip()
    SERVER_PORT = config["SERVER_PORT"]
  else:
    print("Config file not exist\n")
    sys.exit(0)


if __name__ == "__main__":
  init()

#
# Set up of Basic UI
#
win = Tk()
win.title("ChatApp")

#Special font settings
boldfont = font.Font(weight="bold")

#Frame for displaying connection parameters
topframe = ttk.Frame(win, borderwidth=1)
topframe.grid(column=0,row=0,sticky="w")
ttk.Label(topframe, text="NICKNAME", padding="5" ).grid(column=0, row=0)
ttk.Label(topframe, text=NICKNAME, foreground="green", padding="5", font=boldfont).grid(column=1,row=0)
ttk.Label(topframe, text="USERID", padding="5" ).grid(column=2, row=0)
ttk.Label(topframe, text=USERID, foreground="green", padding="5", font=boldfont).grid(column=3,row=0)
ttk.Label(topframe, text="SERVER", padding="5" ).grid(column=4, row=0)
ttk.Label(topframe, text=SERVER, foreground="green", padding="5", font=boldfont).grid(column=5,row=0)
ttk.Label(topframe, text="SERVER_PORT", padding="5" ).grid(column=6, row=0)
ttk.Label(topframe, text=SERVER_PORT, foreground="green", padding="5", font=boldfont).grid(column=7,row=0)


#Frame for displaying Chat messages
msgframe = ttk.Frame(win, relief=RAISED, borderwidth=1)
msgframe.grid(column=0,row=1,sticky="ew")
msgframe.grid_columnconfigure(0,weight=1)
topscroll = ttk.Scrollbar(msgframe)
topscroll.grid(column=1,row=0,sticky="ns")
chatWin = Text(msgframe, height='15', padx=10, pady=5, insertofftime=0, state='disabled')
chatWin.grid(column=0,row=0,sticky="ew")
chatWin.config(yscrollcommand=topscroll.set)
chatWin.tag_configure('redmsg', foreground='red', justify='right')
chatWin.tag_configure('greenmsg', foreground='green', justify='right')
chatWin.tag_configure('bluemsg', foreground='blue', justify='right')
topscroll.config(command=chatWin.yview)

#Frame for buttons and input
midframe = ttk.Frame(win, relief=RAISED, borderwidth=0)
midframe.grid(column=0,row=2,sticky="ew")
JButt = Button(midframe, width='8', relief=RAISED, text="JOIN", command=do_Join).grid(column=0,row=0,sticky="w",padx=3)
QButt = Button(midframe, width='8', relief=RAISED, text="LEAVE", command=do_Leave).grid(column=0,row=1,sticky="w",padx=3)
innerframe = ttk.Frame(midframe,relief=RAISED,borderwidth=0)
innerframe.grid(column=1,row=0,rowspan=2,sticky="ew")
midframe.grid_columnconfigure(1,weight=1)
innerscroll = ttk.Scrollbar(innerframe)
innerscroll.grid(column=1,row=0,sticky="ns")
#for displaying the list of users
ListDisplay = Text(innerframe, height="3", padx=5, pady=5, fg='blue',insertofftime=0, state='disabled')
ListDisplay.grid(column=0,row=0,sticky="ew")
innerframe.grid_columnconfigure(0,weight=1)
ListDisplay.config(yscrollcommand=innerscroll.set)
innerscroll.config(command=ListDisplay.yview)
#for user to enter the recipents' Nicknames
ttk.Label(midframe, text="TO: ", padding='1', font=boldfont).grid(column=0,row=2,padx=5,pady=3)
toentry = Entry(midframe, bg='#ffffe0', relief=SOLID)
toentry.grid(column=1,row=2,sticky="ew")
SButt = Button(midframe, width='8', relief=RAISED, text="SEND", command=do_Send).grid(column=0,row=3,sticky="nw",padx=3)
#for user to enter the outgoing message
SendMsg = Text(midframe, height='3', padx=5, pady=5, bg='#ffffe0', relief=SOLID)
SendMsg.grid(column=1,row=3,sticky="ew")

#Frame for displaying console log
consoleframe = ttk.Frame(win, relief=RAISED, borderwidth=1)
consoleframe.grid(column=0,row=4,sticky="ew")
consoleframe.grid_columnconfigure(0,weight=1)
botscroll = ttk.Scrollbar(consoleframe)
botscroll.grid(column=1,row=0,sticky="ns")
console = Text(consoleframe, height='10', padx=10, pady=5, insertofftime=0, state='disabled')
console.grid(column=0,row=0,sticky="ew")
console.config(yscrollcommand=botscroll.set)
botscroll.config(command=console.yview)

win.mainloop()
