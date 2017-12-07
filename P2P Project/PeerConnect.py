# Cameron L'Ecuyer
# PeerConnect.py

import socket
import struct
import sys
#import ssl

"""
Class handles communicating between Peers, creates a socket to communicate,
sends a message, makes a message, reads the message, and closes the connection
"""

class PeerConnect:
    
    def __init__(self, peerID, peerHost, peerPort, sock = None):

        # constructor

        self.peerID = peerID
        self.peerHost = peerHost
        self.peerPort = peerPort
        self.connected = False

        # if a socket was not passed in, create a socket
        if not sock:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #self.sock = ssl.wrap_socket(self.sock, cert_reqs = ssl.CERT_NONE, ssl_version = ssl.PROTOCOL_SSLv23)
            
            try:
                self.sock.connect((self.peerHost, int(self.peerPort)))
                self.connected = True
            except:
                print("No connection established")
        else:
            self.sock = sock

        #print("PeerConnect: {} {} {} {}".format(peerID, peerHost, peerPort, sock))

        self.sockDoc = self.sock.makefile('rwb', None)

    # end __init__

    def __makemessage(self, msgType, msgData):

        # creates a message to send

        # encodes a message then decodes it
        msgData = msgData.encode('utf-8').strip()
        msgData = msgData.decode('utf-8')

        # packs a message for sending
        msgLength = len(msgData)
        msg = struct.pack("!4sL%ds" % msgLength, bytes(msgType, 'utf-8'), msgLength, bytes(msgData, 'utf-8'))
        return msg
    
    # end __makemessage

    def sendmessage(self, msgType, msgData):

        # attempts to send a message to a peer

        print("Send message: {}".format(msgData))
    
        try:
            msg = self.__makemessage(msgType, msgData)
            self.sockDoc.write(msg)
            self.sockDoc.flush()
        except KeyboardInterrupt:
            raise
        except:
            print("Unexpected error in sendmessage:", sys.exc_info()[0])
            return False
        
        return True

    # end sendmessage

    def collectmessage(self):

        # receives a message and attempts to read it
        
        try:
            # reads the handler type
            msgType = self.sockDoc.read(4)
            
            if not msgType:
                return (None, None)

            # reads the length of the message
            stringLength = self.sockDoc.read(4)

            # unpacks the message
            #msgLength = int(struct.unpack("!L", bytes(stringLength, 'utf-8'))[0])
            msgLength = int(struct.unpack("!L", stringLength)[0])
            msg = b""

            # reads the message
            while len(msg) != msgLength:
                data = self.sockDoc.read(min(2048, msgLength - len(msg)))
                
                if not len(data):
                    break
                
                msg += data
                print("message: {} {} {}".format(msg, len(msg), msgLength))

            if len(msg) != msgLength:
                return (None, None)

        except KeyboardInterrupt:
            raise
        except:
            print("Unexpected error in collectmessage:", sys.exc_info()[0])
            return (None, None)

        print("Collected: {} {}".format(msgType, msg))
        
        return (msgType.decode('utf-8'), msg.decode('utf-8'))

    # end collectmessage

    def closeconnect(self):

        # closes a connection

        self.sock.close()
        self.sock = None
        self.sockDoc = None

    # end closeconnect
    
# end class PeerConnect
