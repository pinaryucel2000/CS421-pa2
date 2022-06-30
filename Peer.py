import socket
import base64
import timeit
import sys
import datetime;
import time
import random
import os 

def currentTime():
	return str(datetime.datetime.now()).split(" ")[1].split(".")[0]

def currentMinute():
	return str(datetime.datetime.now()).split(" ")[1].split(".")[0].split(":")[1]

def currentSecond():
	return str(datetime.datetime.now()).split(" ")[1].split(".")[0].split(":")[2]
	
def Peer():
	# Acquire information from the file
	peerNo = int(sys.argv[2])
	peerCount = 0;
	peersThatWillConnect = []
	peersThatWillBeConnectedTo = []
	f = open("OverlayNetworkTopology.txt", "r")
	isFirstLine = True
	for line in f:
		line = line.split("\\r\\n\n")[0]
		
		if isFirstLine:
			peerCount= int(line)
			isFirstLine = False
			
		else:
			first = int(line.split("->")[0])
			second = int(line.split("->")[1])
			
			if first == peerNo:
				peersThatWillBeConnectedTo.append(second)
				
			if second == peerNo:
				peersThatWillConnect.append(first)
		
	# Define socket host and port
	SERVER_HOST = sys.argv[1]
	SERVER_PORT = 60000 + peerNo
	
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 100000)
	server_socket.bind((SERVER_HOST, SERVER_PORT))
	server_socket.listen(peerCount)

	# Connect to peers
	client_sockets = []
	for i in peersThatWillBeConnectedTo:
		client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # instantiate
		client_sockets.append(client_socket)
		
	i = 0
	for peer in peersThatWillBeConnectedTo:	
		cs = client_sockets[i]
		i += 1
		isConnected = False
		while isConnected == False:
			try:
				cs.connect((SERVER_HOST, 60000 + peer))  # connect to the server
				print("TCP connection established with peer " + str(peer) + ".")
				isConnected = True
			except socket.error:
				pass

		# Authentication
		username = "USER bilkentstu\r\n"
		password = "PASS cs421s2021\r\n"
		cs.send(username.encode())
		cs.send(password.encode())	
		
	client_connections= []
	
	# Confirm Authentications
	for peer in peersThatWillConnect:
		usernameReceived = False
		passwordReceived = False
		client_connection, client_address = server_socket.accept()
		
		while usernameReceived != True or passwordReceived != True :
			req = client_connection.recv(1024).decode()
						
			if req[0:4] == "USER":
				usernameReceived = True
			if req[0:4] == "PASS" or (req.split("\r\n")[1])[0:4] == "PASS":
				passwordReceived = True
		
		confirmation = "OK \r\n"
		client_connection.send(confirmation.encode())
		client_connections.append(client_connection)
	
	# Receive Authentication Confirmations
	peerIndex = 0;
	for peer in peersThatWillBeConnectedTo:
		response = client_sockets[peerIndex].recv(8192).decode()  # receive response
		
		while response == "":
			response = client_sockets[peerIndex].recv(8192).decode()  # receive response
		
		print("Authenticated to peer " + str(peer) + ".")
		peerIndex = peerIndex + 1
			
	# Wait for Minute Mark
	cm = currentMinute()
	
	while(cm == currentMinute()):
		pass

	secondArr = ["00", "05", "10", "15", "20", "25", "30"]
	
	messages = []
	receivedMessages = []
	
	for second in secondArr:
		while currentSecond() != second:
			pass
		
		message = "FLOD " + str(peerNo) + " " + currentTime() + "\r\n"
			
		for client_socket in client_sockets:
			client_socket.send(message.encode())
			

		messages.append(message)
		tmp = ""
		for cc in client_connections:
			tmp_ = cc.recv(8192).decode()
			tmp = tmp + tmp_
			
		while "FLOD" in tmp:
			message = tmp.split("FLOD ")[1].split("\r\n")[0]
			message = "FLOD " + message + "\r\n"
			receivedMessages.append(message)
			if message not in messages:
				messages.append(message)
				
				for client_socket in client_sockets:
					client_socket.send(message.encode())
			
			messageSize = len(message)
			tmp = tmp[messageSize:]
	

	time.sleep(2)
	# Send Exit Message
	for client_socket in client_sockets:
		exitMessage = "EXIT/r/n"
		client_socket.send(exitMessage.encode())
	
	# Handle remaining unreceived messages
	tmp = ""
	for cc in client_connections:
		tmp_ = cc.recv(8192).decode()
		tmp = tmp + tmp_
			
	while "FLOD" in tmp:
		message = tmp.split("FLOD ")[1].split("\r\n")[0]
		message = "FLOD " + message + "\r\n"
		receivedMessages.append(message)
		if message not in messages:
			messages.append(message)
				
			for client_socket in client_sockets:
				client_socket.send(message.encode())
			
		messageSize = len(message)
		tmp = tmp[messageSize:]
		
	print("Source Node ID | Timestamp | # of messages received")
	print("---------------------------------------------------")
		

	for message in receivedMessages:
		source = message.split(" ")[1].split(" ")[0]
		timestamp = message.split(" ")[2].split("\r\n")[0]
		print(f"{source:^15}" + "|" + f"{timestamp:^11}" + "|" + f"{1:^23}")
		
	for client_socket in client_sockets:
		client_socket.close()
		
	server_socket.close()
	

if __name__ == '__main__':
	Peer()
