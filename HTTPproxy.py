import signal
import sys
import threading
from optparse import OptionParser
from socket import *
from time import *
from urllib.parse import urlparse


#   Dictionary for formatting.
Host_List = ['User-Agent', 'Accept', 'Referer', 'Header']

#   Dictionary for formatting.
format = {'METHOD' : '', 'HOST': '','HTTP_VERSION': '', 'CONNECTION': '',}

userList = []

# Signal handler for pressing ctrl-c
def ctrl_c_pressed(signal, frame):
    sys.exit(0)

def handle_client(client_socket, client_addr):
   
    bin = False
    endFlag = False
    checkData = ""
    header = ''
    extraHTML = ''
    headerList = ''
    
    while(endFlag == False) :
        # keep receiving while user enter twice
        readData = client_socket.recv(2048).decode()

        print("Check Error Here: ", repr(readData))
        sys.stdout.flush()

        checkData += readData

        if checkData[-4:] == "\r\n\r\n":
            break

    #index 0 = format index 1 = header
    tempSplit = checkData.split("\r\n")

    tempSplit = tempSplit[:-2]
    
    mainForm = tempSplit[0]

    split_readData = mainForm.split(' ')

    #====================================

    for x in tempSplit[1:]:
        
        if "Connection: " in x:
            continue
        if(len(tempSplit) > 1):
            checker = x.split(':')
            if(checker[0] not in Host_List):
                error = "HTTP/1.0 400 Bad Request"
                sys.stderr.write(error)
                client_socket.send(error.encode())        
                client_socket.close()
                bin = True
                break
        header += "\r\n" +x
    if(bin):
        return;    
    # print(header)
    
    # if first is not get = 
    # if first is get = 400

    # check if length is below than 3
    if len(split_readData)<3 or len(split_readData) >3:
        error = "HTTP/1.0 400 Bad Request"
        sys.stderr.write(error)
        client_socket.send(error.encode())        
        client_socket.close()
        bin = True
        return
        
    # at least length is longer than 3.
    method = split_readData[0]
    
    URL = split_readData[1]
    
    URL_Version = split_readData[2]
    
    if(URL_Version != "HTTP/1.0"):
        error = "HTTP/1.0 400 Bad Request"
        sys.stderr.write(error)
        client_socket.send(error.encode())        
        client_socket.close()
        bin = True
        return
    
    
    if(method != "GET"):
        error = "HTTP/1.0 501 Not Implemented"
        sys.stderr.write(error)
        client_socket.send(error.encode())
        client_socket.close()
        bin = True
        return
    # adding header 

    #check if there's header or not.

    format['METHOD'] = method

    URL_Parse = urlparse(split_readData[1])
    

    
    if(not URL_Parse.scheme):
        print("URL scheme checking ", repr(URL_Parse.scheme))
        sys.stdout.flush()
        
        error = "HTTP/1.0 400 Bad Request"
        sys.stderr.write(error)
        client_socket.send(error.encode())
        client_socket.close()
        bin = True
        return
    
    if(not URL_Parse.path):
        error = "HTTP/1.0 400 Bad Request"
        sys.stderr.write(error)
        client_socket.send(error.encode())
        client_socket.close()
        bin = True
        return
        
    
    if(URL_Parse.hostname == 'localhost'):
        URL = 'localhost'
        PATH = URL_Parse.path
    else:
        URL = URL.replace("http://", "")  # Remove the http://
        temp = URL.find('/')
        PATH = URL[temp:]  # split the extra html
        URL = URL[:temp]        # only html
            
    format['HOST'] = URL

    format['HTTP_VERSION'] = URL_Version + '\r\n'

    if(bin == False):
        print("==========Send to server process is on =========")
        sendServer = format['METHOD']+ " "  + PATH + " "  + format['HTTP_VERSION'] + "Host: " + format['HOST']+ "\r\n" + "Connection: close" + header + "\r\n\r\n"
        
        
        print("===========After adding======")
        print(sendServer)
        print("==============================")

        #   create new socket for server
        originServer = socket(AF_INET, SOCK_STREAM)

        protNumber = 80
        #   connect with server, host name should be
        if(URL_Parse.port):
            protNumber = URL_Parse.port
        
        originServer.connect((format['HOST'], protNumber))
        #   Send data to server
        originServer.sendall(sendServer.encode())
        while True:
            temp = originServer.recv(2048)  #receive from originServer
            #   if temp is not valid, break it
            # print(temp)
            if temp == b'':
                break
        #   send 
            client_socket.send(temp)
        originServer.close()
        client_socket.close()
    
    
    for i in range(len(userList)):
        sleep(1)
        print(f'Handling request from client {client_addr}')
    print('Client request handled')
    client_socket.close()


# TODO: Put function definitions here

# Start of program execution
# Parse out the command line server address and port number to listen to
parser = OptionParser()
parser.add_option('-p', type='int', dest='serverPort')
parser.add_option('-a', type='string', dest='serverAddress')
(options, args) = parser.parse_args()

port = options.serverPort   #! server port
address = options.serverAddress #! server address
if address is None:
    address = 'localhost'
if port is None:
    port = 2100

# Set up signal handling (ctrl-c)
signal.signal(signal.SIGINT, ctrl_c_pressed)

#   Create socket FOR Client side (getting data )
#   an INET, STREAmin, firstPar = socket IPv4 secondPar = TCP socket
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
# Bind the IP address and the port number.
clientSocket.bind((address, port))

#   Listen for incoming connections maximum 1 queued connection.
clientSocket.listen(1)


print('Proxy is ready to receive')
#   Once a client has connectd, the proxy should read data from the client and then check for 
#   a properly formatted HTTP request.

while True:
#   waiting for user and accept
    (connectionSocket, addr) = clientSocket.accept()
    userList.append(connectionSocket)
    
    threading.Thread(target=handle_client, args=(connectionSocket, addr)).start()
    
