# Cameron L'Ecuyer
# Peer.py

from PeerConnect import *

import socket
import threading
import sys
#import ssl

"""
Class handles dealing with a Peer, sending messages, connecting to peers,
holding peer information and the peer list
"""

class Peer:
    
    def __init__(self, serverPortNum, maxNumPeers = 1, ID = None, serverHost = None):

        # constructor
        
        self.maxNumPeers = int(maxNumPeers)
        self.serverPortNum = int(serverPortNum)

        # if a server host is specified use it, else attempt to connect to
        # an Internet host to determine IP address
        if serverHost:
            self.serverHost = serverHost
        else:
            # connects to Internet host to determine IP address
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(("www.google.com", 80))
            #self.serverHost = sock.getsockname()[0]
            self.serverHost = socket.gethostbyname(socket.gethostname())
            sock.close()

        # if peerID specified use it, else create peerID from serverHost and serverPortNum
        if ID:
            self.ID = ID
        else:
            self.ID = '{}:{}'.format(self.serverHost, self.serverPortNum)

        # creates a variable to handle locking a thread
        self.peersLock = threading.Lock()

        # list of peers
        self.peers = {}

        # shutdown flag
        self.shutdown = False

        # holds messages from peers based on type
        self.commHandlers = {}

    # end constructor

    def findpeerid(self, peerHost, peerPort):

        # finds the peerid based on peerHost and peerPort

        for peer in self.peers:
            
            tempHost, tempPort = peer.split(':')

            if tempHost == peerHost and tempPort == peerPort:
                return peer

    # end findpeerid

    def addpeer(self, peerID, peerHost, peerPort):

        # add a peer to the peer list if less than maxNumPeers

        if peerID not in self.peers and (self.getnumberofpeers() < self.maxNumPeers):
            self.peers[peerID] = (peerHost, int(peerPort))
            return True
        else:
            return False

    # end addpeer

    def removepeer(self, peerID):

        # removes a peer from the peers list
        
        if peerID in self.peers:
            del self.peers[peerID]

    # end removepeer

    def getpeer(self, peerID):

        # returns the peer information from the peers list
        
        return self.peers[peerID]

    # end getpeer

    def getpeerids(self):

        # returns list of peers

        return self.peers.keys()

    # end getpeerids

    def getnumberofpeers(self):

        # return number of peers

        return len(self.peers)

    # end numberofpeers

    def getmaxnumberofpeers(self):

        # return number of peers

        return self.maxNumPeers

    # end numberofpeers

    def addhandler(self, msgType, handler):

        # adds a handler to the commHandlers list
        
        self.commHandlers[msgType] = handler

    # end addhandlers

    def sendtopeer(self, hostName, portNum, msgType, msgData, peerID = None, waitReply = True):

        # sends a message to a peer and waits for a reply if needed

        msgReply = []

        print("Sending")

        try:
            peer = PeerConnect(peerID, hostName, portNum)
            peer.sendmessage(msgType, msgData)

            if waitReply:
                reply = peer.collectmessage()
                
                while(reply != (None, None)):
                    msgReply.append(reply)
                    reply = peer.collectmessage()
            peer.closeconnect()
            
        except KeyboardInterrupt:
            raise
        except:
            print("Unexpected error in sendtopeer:", sys.exc_info()[0])
            print("No message sent or received")

        return msgReply

    # end sendtopeer

    def checkifpeeralive(self):

        # checks if peers are alive and deletes them from peers list if not
        
        toDelete = []

        for peerID in self.peers:
            isConnected = False

            try:
                hostName, portNum = self.peers[peerID]
                peer = PeerConnect(peerID, hostName, portNum)

                if(peer.connected):
                    peer.sendmessage('PING', '')
                    isConnected = True
                else:
                    toDelete.append(peerID)
                    
            except:
                print("Unexpected error in checkifpeeralive:", sys.exc_info()[0])

            if isConnected:
                peer.closeconnect()

        self.peersLock.acquire()

        try:
            for peerID in toDelete:
                if peerID in self.peers:
                    del self.peers[peerID]
                    
        finally:
            self.peersLock.release()

    # end checkifpeeralive

    def __connecttopeer(self, peerSock):

        # attempts to connect to a peer

        hostName, portNum = peerSock.getpeername()
        peer = PeerConnect(None, hostName, portNum, peerSock)

        try:
            msgType, msgData = peer.collectmessage()
            
            if msgType: msgType = msgType.upper()
            
            if msgType not in self.commHandlers:
                print("{} Not in handlers".format(msgType))
            else:
                self.commHandlers[msgType](peer, msgData)
                
        except KeyboardInterrupt:
            raise
        except:
            print("Unexpected error in connecttopeer:", sys.exc_info()[0])
            print("Connect failed")

        peer.closeconnect()

    # end __connecttopeer

    def peerlisten(self):

        # creates a server socket that listens for peers
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.serverHost, self.serverPortNum))
        sock.listen(5)
        sock.settimeout(2)

        while not self.shutdown:
            try:
                clientsock, clientaddr = sock.accept()
                print("Accept")

                clientsock.settimeout(None)
                #clientsock = ssl.wrap_socket(clientsock, cert_reqs = ssl.CERT_NONE, ssl_version = ssl.PROTOCOL_SSLv23)

                thread = threading.Thread(target = self.__connecttopeer, args = [clientsock])
                thread.start()
            except socket.error as socketerror:
                #print(socketerror)
                continue
            except KeyboardInterrupt:
                print('Keyboard Interrupt: stopping peerloop')
                self.shutdown = True
                continue
            except:
                print("Unexpected error in peerlisten:", sys.exc_info()[0])
                
            # end try/catch
        # end loop

        sock.close()

    # end peerlisten
    
# end class Peer
