from socket import *
import signal
import time
# import logging

'''
Project 1 - Simple Python HTTP Server
Computer Networks
COSC3344.01
26 February 2014

Hunter Skrasek, Molly Thurin, Adela Arreola
'''
class Server:

	def __init__(self, port = 12618):
		self.host = 'localhost'
		self.port = port
		self.baseDir = '.'

	def startServer(self):
		print("Starting server on ", self.host, ":", self.port, ".....")
		self.socket = socket(AF_INET, SOCK_STREAM)
		try:
			print("Binding Socket")
			self.socket.bind((self.host, self.port))
		except Exception as e:
			print("Failed to bind to port ", str(self.port), "on host ", self.host, "!")
			print(e)
			self.shutdown()
			import sys
			sys.exit(1)

		print("Server successfully started on ", self.host, ":", self.port)
		print("Ctrl+c to shutdown the server.")
		self.listenForConnections()

	def shutdown(self):
		try:
			print("Shutting down server....")
			self.socket.shutdown(SHUT_RDWR)

		except Exception as e:
			print("Could not shut down the socket. Maybe it was already closed?",e)

	def _generateHeaders(self, code):
		h = ''
		if (code == 200):
			h = 'HTTP/1.1 200 OK\r\n'
		elif (code == 404):
			h = 'HTTP/1.1 404 Not Found\r\n'
		elif (code == 400):
			h = 'HTTP/1.1 400 Bad Request\r\n'
		elif (code == 405):
			h = 'HTTP/1.1 405 Method Not Allowed\r\n'
		elif (code == 418):
			h = 'HTTP/1.1 418 I\'m a teapot\r\n'
		elif (code == 505):
			h = 'HTTP/1.1 505 HTTP Version Not Supported\r\n'
		elif (code == 500):
			h = 'HTTP/1.1 500 Internal Server Error\r\n'

		currentDate = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
		h += 'Date: ' + currentDate + "\r\n"
		h += 'Server: Python-HTTP-Server\r\n'
		h += 'Connection: close\r\n'

		return h

	def listenForConnections(self):
		while True:
			print("Waiting on a connection...")
			self.socket.listen(3) # One connection... for now.
			conn, addr = self.socket.accept()

			print("Connection established. Connecting host: ", addr)
			data = conn.recv(2048)
			decodedData = bytes.decode(data)

			if (len(decodedData.split()) == 0):
				conn.send(self._generateHeaders(400).encode())
				continue

			request = Request(original = decodedData)
			request.parseRequestHeaders()

			if not request.isAValidRequest():
				print("Invalid Request")
				conn.send(self._generateHeaders(400).encode())
			elif not request.isProperVersion():
				print("Invalid HTTP Version")
				conn.send(self._generateHeaders(505).encode())
			elif request.isUnknownMethod():
				print("Unknown Method:", request.getRequestMethod())
				conn.send(self._generateHeaders(405).encode())
			elif request.isTeapot():
				print("Sending I'm a Teapot")
				conn.send(self._generateHeaders(418).encode())
			else:
				print("Method: ", request.getRequestMethod())
				print("Request Body: ", decodedData.split('\r\n'))
				try:
					fileHander = open(self.baseDir + request.getRequestedFile(), 'rb')
					if (request.getRequestMethod() == 'GET'):
						responseBody = fileHander.read()
					fileHander.close()
					responseHeaders = self._generateHeaders(200)
				except Exception as e:
					print("File not found, responing with 404. Error: ", e)
					if (request.getRequestMethod() == 'GET'):
						responseBody = b"<html><body><h1>Error 404: File not found</h1><p>Python HTTP server</p></body></html>"
					responseHeaders = self._generateHeaders(404)

				fullResponse = responseHeaders.encode()
				if (request.getRequestMethod() == 'GET'):
					fullResponse += "Content-Length: {0}\r\n".format(len(responseBody)).encode()
					import mimetypes
					mimeType = mimetypes.guess_type(self.baseDir + request.getRequestedFile())
					fullResponse += "Content-Type: {0}\r\n".format(mimeType[0]).encode()
					fullResponse += b"\n" + responseBody

				conn.send(fullResponse)
				
			print("Closing connection with client.")
			conn.close()

class Request:
	
	def __init__(self, original):
		self.original = original
		self.headers = dict()
		self.headers['eof'] = 0

	# Split on \r\n first, then iterate through each item and attempt to split on : if the item isnt an empty string.
	# For each subsequent split, [0] => Key, [1] => Value of the Request Headers.
	# Could possibly assume that the first item would always be the Request Method, Request File, and Version.
	def parseRequestHeaders(self):
		carriageSplit = self.original.split('\r\n')
		for line in carriageSplit:
			# print("Parsing:", line)
			if line == '':
				self.headers['eof'] += 1
			elif len(line.split(':')) > 1:
				parts = line.split(':')
				if parts[0] == 'Host':
					if len(parts) == 3:
						self.headers[parts[0]] = parts[1] + ":" + parts[2]
					else:
						self.headers[parts[0]] = parts[1]
				else:
					self.headers[parts[0]] = parts[1]
			else:
				requestFile = line.split(' ')
				self.method = requestFile[0]
				if requestFile[1] == '/':
					self.requestedFile = '/index.html'	
				else:
					self.requestedFile = requestFile[1]
				print("Version:", requestFile[2])
				self.version = requestFile[2].split('/')
		
	def isAValidRequest(self):
		if 'Host' not in self.headers:
			return False
		if not self.headers['eof'] or self.headers['eof'] != 2:
			return False
		if not self.method:
			return False
		if not self.requestedFile:
			return False
		if not self.version:
			return False
		return True
		
	def isProperVersion(self):
		return self.version[1] == '1.1'

	def getRequestedFile(self):
		return self.requestedFile

	def getRequestMethod(self):
		return self.method

	def isUnknownMethod(self):
		return not (self.method == 'GET') and not (self.method == 'HEAD')
	
	def isTeapot(self):
		return (self.requestedFile.lower() == 'teapot')

def gracefulShutdown(sig, dumb):
	server.shutdown()
	import sys
	sys.exit(1)

if __name__ == '__main__':
	# logging.basicConfig(filename='server.log',loglevel=logging.DEBUG, format='[%(asctime)s] %(loglevel)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
	signal.signal(signal.SIGINT, gracefulShutdown)
	print("Starting")
	server = Server(port = 12618)
	server.startServer()