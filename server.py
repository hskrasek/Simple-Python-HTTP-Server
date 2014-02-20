from socket import *
import signal
import time
import logging

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
			self.socket.listen(1) # One connection... for now.
			conn, addr = self.socket.accept()

			print("Connection established. Connecting host: ", addr)
			data = conn.recv(2048)
			decodedData = bytes.decode(data)
			print("Decoded Data Length:", len(decodedData.split()))
			if (len(decodedData.split()) == 0):
				conn.send(self._generateHeaders(400).encode())
				continue

			httpVersion = decodedData.split(' ')[2].split('\r\n')[0].split('/')
			if (httpVersion[1] == '1.0'):
				conn.send(self._generateHeaders(505).encode())
				continue

			requestMethod = decodedData.split(' ')[0]
			print("Method: ", requestMethod)
			print("Request Body: ", decodedData.split(' '))
			endOfRequest = decodedData.split(' ')[-1].split('\r\n')
			# if (len(endOfRequest) < 3 )
			# print("Last Request Body Item:", decodedData.split(' ')[-1].split('\r\n'))

			if (requestMethod == 'GET') | (requestMethod == 'HEAD'):
				requestedFile = decodedData.split(' ')[1]

				if (requestedFile == '/'):
					requestedFile = '/index.html'
				requestedFile = self.baseDir + requestedFile

				print("Serving: ", requestedFile)

				if (requestedFile == './teapot'):
					print("Sending I'm a Teapot")
					conn.send(self._generateHeaders(418).encode())
					continue

				try:
					fileHander = open(requestedFile, 'rb')
					if (requestMethod == 'GET'):
						responseBody = fileHander.read()
					fileHander.close()

					responseHeaders = self._generateHeaders(200)
				except Exception as e:
					print("File not found, responing with 404. Error: ", e)
					if (requestMethod == 'GET'):
						responseBody = b"<html><body><p>Error 404: File not found</p><p>Python HTTP server</p></body></html>"
					responseHeaders = self._generateHeaders(404)

				fullResponse = responseHeaders.encode()
				if (requestMethod == 'GET'):
					fullResponse += "Content-Length: {0}\r\n".format(len(responseBody)).encode()
					import mimetypes
					mimeType = mimetypes.guess_type(requestedFile)
					fullResponse += "Content-Type: {0}\r\n".format(mimeType[0]).encode()
					fullResponse += b"\n" + responseBody

				conn.send(fullResponse)
			else:
				print("Unknown Method: ", requestMethod)
				conn.send(self._generateHeaders(405).encode())
			print("Closing connection with client.")
			conn.close()

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