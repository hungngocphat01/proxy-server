from os import replace
import socket
from logging_module import *
import traceback

BUFFER_SIZE = 1024

def parse_header(request_content: bytes) -> dict:

    headers = request_content[0:request_content.find(b"\r\n\r\n")]
    str_request = headers.decode("utf-8")
    lst_request = str_request.split('\r\n')

    # Get url of the request
    pos1 = lst_request[0].find('/')
    pos2 = lst_request[0].find('HTTP')
    str_url = lst_request[0][pos1:pos2-1]
    dict_headers = {"URI":str_url}

    # Get host information
    lst_host = lst_request[1].split(':')
    # If host contains port number
    if len(lst_host) == 3:
        dict_headers.update({lst_host[0]:lst_host[1]+':'+lst_host[2]})
    else:
        dict_headers.update({lst_host[0]:lst_host[1]})

    # Get method information
    if any("GET" in s for s in lst_request):
        method = "GET"
    elif any("POST" in s for s in lst_request):
        method = "POST"
    else:
        method = "UNK"
    dict_headers.update({"Method": method})

    # Add other values to dict
    splitedlist = [i.split(':') for i in lst_request]
    i = 2
    while i < len(splitedlist):
        dict_headers.update({splitedlist[i][0]: splitedlist[i][1]})
        i = i + 1
    return dict_headers

def send_403_forbidden(client_socket: socket.socket):
    client_socket.send(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 160\r\n\r\n<html>\r\n<title>403 Forbidden</title>\r\n<body>\r\n\
<h1>Error 403: Forbidden</h1>\r\n<p>The requested websit violates our administrative policies.</p>\
</body>\r\n</html>\r\n')
    client_socket.close()

def is_blocked(url: str) -> bool:
    pass
    

def get_target_info(header: dict) -> dict:
    pass

def recvall(s: socket.socket) -> bytes:
    pass


def handle_http_request(c: socket.socket, a: tuple):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        # Receive data from client
        request_content = recvall(c)

        if (len(request_content) == 0):
            log(f"{a} Empty request. Ignoring...", color="yellow")
            raise UserWarning
        
        # parse request header
        request_headers = parse_header(request_content)
        dict_hostPort = get_target_info(request_headers)

        # Log request header
        req_log(request_headers)
        
        # Check method whether it is POST or GET
        method = request_headers["Method"]
        if(method != "GET" and method != "POST"):
            log(f"{a} Method unsupported.", color="yellow")
            raise UserWarning

        # Check if the url is blocked or not
        isBlocked = is_blocked(request_headers["URI"])
        if isBlocked:
            send_403_forbidden(c)
            log(f"{a} Forbidden website: {request_headers['URI']}", color="yellow")
            return

        # Get host and port of the destination server
        host = dict_hostPort["host"].strip()
        port = dict_hostPort["port"]
        
        # Send request data of client to destination server
        server_socket.connect((host, port))
        server_socket.sendall(request_content)
        
        # Forward server's reply to client
        log(f"{a} Forwarding: {request_headers['URI']}", color="magenta")
        with server_socket:
            while True:
                # Transfering 4 KB can't be slower than 1.5s in normal condition
                server_socket.settimeout(1.5)
                reply = b""
                try:
                    reply = server_socket.recv(BUFFER_SIZE)
                except socket.timeout:
                    pass
                if not reply:
                    break
                c.sendall(reply)
        log(f"{a} Forwarded: {request_headers['URI']}", color="green")
    
    except UserWarning:
        pass
    except Exception:
        log(traceback.format_exc(), color="red")
    finally:
        # Close connection
        server_socket.close()
        c.close()

        log(f"{a} Connection closed.\n", color="yellow")
        return