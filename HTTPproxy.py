
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

userList = []                       #holding variety users
cacheList = {}                      #list of the cache
blocklist = []                      #list of the blocked domain
proxy_cache = False                 #to check if caching is enable or disable
proxy_block = False                 #to check if blocking is enable or disable

#   PA-Final part.
#   getting order about caching and apply 
def proxy_cache_order(order):
    global proxy_cache 
    if order == "flush":            #clear cachelist
        cacheList.clear()
    elif order == "enable":         #enable caching
        proxy_cache = True
    elif order == "disable":        #disable caching
        proxy_cache = False
    message = "200 OK"
    return message.encode()

#   PA-Final part.
#   getting order about the blocking and apply
def proxy_block_order(path):
    global proxy_block
    path_split = path.split("/")
    order = path_split[3]
    if len(path_split) > 4:                 #if order is add or remove
        if order == "add":
            blocklist.append(path_split[4]) #adding the given string to the list
        elif order == "remove":
            blocklist.remove(path_split[4]) #remove the given string in the list
    if order == "enable":                   #enable blocklist
        proxy_block = True
    elif order == "disable":                #disable blocklist
        proxy_block = False
    elif order == "flush":                  #clear blocklist
        blocklist.clear()

# Signal handler for pressing ctrl-c
def ctrl_c_pressed(signal, frame):
    sys.exit(0)

#   Implement a HTTP/1.0 proxy with basic object-caching and domain-blocking features.
#   It serves multiple concurrent request by threading and it only supports the HTTP 
#   GET method.
def proxy_work(client_socket, client_addr):
    bin = False
    checkData = ""
    header = ''
    global proxy_cache

    # keep receiving while user enter twice 
    while(1) :
        readData = client_socket.recv(2048).decode()
        
        print("Check Error Here: ", repr(readData))
        sys.stdout.flush()
        checkData += readData
        if checkData[-4:] == "\r\n\r\n":             
            break

    tempSplit = checkData.split("\r\n")

    tempSplit = tempSplit[:-2]
    
    mainForm = tempSplit[0]

    split_readData = mainForm.split(' ')

    # check 
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
                return
        header += "\r\n" +x

    # check if length is below than 3
    if len(split_readData)<3 or len(split_readData) >3:
        error = "HTTP/1.0 400 Bad Request"
        sys.stderr.write(error)
        client_socket.send(error.encode())        
        client_socket.close()
        bin = True
        return
        
    method = split_readData[0]
    URL = split_readData[1]
    URL_Version = split_readData[2]
    
    #   check if URL_Version is valid or not. if not, send 400 error
    if(URL_Version != "HTTP/1.0"):
        error = "HTTP/1.0 400 Bad Request"
        sys.stderr.write(error)
        client_socket.send(error.encode())        
        client_socket.close()
        return
    #   check if method is valid or not. if not, send 501 error
    if(method != "GET"):
        error = "HTTP/1.0 501 Not Implemented"
        sys.stderr.write(error)
        client_socket.send(error.encode())
        client_socket.close()
        return

    format['METHOD'] = method

    URL_Parse = urlparse(split_readData[1])
    #   to check if domain blocking is enable and
    #   check if host is blocked 
    if(proxy_block == True):
        for block in blocklist:
            if block in URL_Parse.netloc:
                error = "403 Forbidden" + "\r\n"
                sys.stderr.write(error)
                client_socket.send(error.encode())
                client_socket.close()
    #   check scheme is valid or not
    if(not URL_Parse.scheme):
        error = "HTTP/1.0 400 Bad Request"
        sys.stderr.write(error)
        client_socket.send(error.encode())
        client_socket.close()
        return
    #   check path is valid or not
    if(not URL_Parse.path):
        error = "HTTP/1.0 400 Bad Request"
        sys.stderr.write(error)
        client_socket.send(error.encode())
        client_socket.close()
        return
    
    if(URL_Parse.hostname == 'localhost'):
        URL = 'localhost'
        PATH = URL_Parse.path
    else:
        URL = URL.replace("http://", "")  # Remove the http://
        temp = URL.find('/')
        PATH = URL[temp:]                 # split the extra html
        URL = URL[:temp]                  # only html
    
    if "proxy/" in PATH:
        path_split = PATH.split("/")
        if path_split[2] == "cache":
            client_socket.send(proxy_cache_order(path_split[3]))
        elif path_split[2] == "blocklist":
            proxy_block_order(PATH)
        client_socket.close()
        return
    format['HOST'] = URL
    
    format['HTTP_VERSION'] = URL_Version + '\r\n'
    
    print("==========Send to server process is on =========")
    
    #   If host is in cachelist, check if it's modified
    #   else send normal request formatting
    if proxy_cache == True:
        if URL_Parse.netloc in cacheList:
            tempDate = cacheList[URL_Parse.netloc].decode().split("\r\n")
            modifier = tempDate[2].replace("Date: ", "")
            sendServer = format['METHOD']+ " "  + PATH + " "  + format['HTTP_VERSION'] + "Host: " + format['HOST']+ "\r\n"+ "If-Modified-Since: "+ modifier+ "\r\n" + "Connection: close" + header + "\r\n\r\n"
        else:
            sendServer = format['METHOD']+ " "  + PATH + " "  + format['HTTP_VERSION'] + "Host: " + format['HOST']+ "\r\n" + "Connection: close" + header + "\r\n\r\n"
    else:
        sendServer = format['METHOD']+ " "  + PATH + " "  + format['HTTP_VERSION'] + "Host: " + format['HOST']+ "\r\n" + "Connection: close" + header + "\r\n\r\n"
        
    print("==========Sending to server==========")
    print(sendServer)
    print("==============================")

    #   create new socket for server
    originServer = socket(AF_INET, SOCK_STREAM)

    port_number = 80
    #   connect with server, host name should be
    if(URL_Parse.port):
        port_number = URL_Parse.port
    
    originServer.connect((format['HOST'], port_number))
    #   Send data to server
    originServer.sendall(sendServer.encode())
    value = b''
    not_modified = False
    while True:
        temp = originServer.recv(2048)  #receive from originServer
        if temp == b'':                 #if temp is not valid, break it
            break 
        value += temp                   #keep adding recv from the orginServer
        if proxy_cache == True:         #If cached is not changed, origin server send 304
            if "304 Not Modified" in temp.decode():
                not_modified = True
                break
    if proxy_cache == True:
        if not_modified == True:                            #if it is not modified,send cache to client
            client_socket.send(cacheList[URL_Parse.netloc])
        else:
            cacheList[URL_Parse.netloc] = value             #adding cache in proxy
            client_socket.send(value)                       #send to client like normaly
    else:
        client_socket.send(value)
        
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
    
    threading.Thread(target=proxy_work, args=(connectionSocket, addr)).start()