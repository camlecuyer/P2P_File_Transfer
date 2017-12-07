# Cameron L'Ecuyer
# PeerFileTransfer.py

from Peer import *

import time

LISTOFFILES = "LIST"
ADDPEER = "JOIN"
GETFILE = "FGET"
PEERQUIT = "QUIT"
REPLY = "REPL"
REPLYFILE = "RPLF"
REPLYFILEEND = "RPLE"
ERROR = "ERRO"

"""
Handles dealing with the file transfer portion, and high level functions
of the P2P network
"""

class PeerFileTransfer(Peer):
    
    def __init__(self, serverPortNum, maxNumPeers):

        # constructor
        
        Peer.__init__(self, serverPortNum, maxNumPeers)

        self.availableFileList = {}

        # creates handler list
        commHandlers = {
                    LISTOFFILES : self.__handlelistoffiles,
		    ADDPEER : self.__handleaddpeer,
		    GETFILE: self.__handlegetfile,
                    REPLYFILE: self.__handlereplyfile,
		    PEERQUIT: self.__handlequit
		   }

        for handle in commHandlers:
            self.addhandler(handle, commHandlers[handle])
            
    # end constructor

    def __handleaddpeer(self, peer, data):

        # handler for adding a peer to the peerlist

        self.peersLock.acquire()
        
        try:
            peerID = data
            hostName, portNum = data.split(':')

            if self.getnumberofpeers() >= self.getmaxnumberofpeers():
                print("Max number of peers reached")
                peer.sendmessage(ERROR, "Join: max number of peers reached")
                return

            if peerID not in self.getpeerids() and peerID != self.ID:
                self.addpeer(peerID, hostName, portNum)
                peer.sendmessage(REPLY, "Join: peer added: {}".format(peerID))
            else:
                peer.sendmessage(ERROR, "Join: peer already exists: {}".format(peerID))

        except:
            print("Unexpected error in handleaddpeer:", sys.exc_info()[0])
            peer.sendmessage(ERROR, "Join: invalid arguments")
        finally:
            self.peersLock.release()

    # end __handleaddpeer

    def __handlelistoffiles(self, peer, data):

        # handler for getting the list of files

        files = []
        
        try:
            
            for file in self.availableFileList:
                peerID = self.availableFileList[file]

                if not peerID:
                    files.append("{}:{}".format(file, self.ID))
                else:
                    files.append("{}:{}".format(file, peerID))

            peer.sendmessage(REPLY, "{} {}".format(len(self.availableFileList), files))
          
        except:
            print("Unexpected error in handlelistoffiles:", sys.exc_info()[0])

    # end __handlelistoffiles

    """def __handlegetfile(self, peer, data):

        # handler for getting a file

        fileName = data
        info = ''

        if fileName not in self.availableFileList:
            peer.sendmessage(ERROR, "File not found")
            return
        
        try:
            fileData = open(fileName, 'r')
            
            while True:
                dat = fileData.read(2048)

                if not len(dat):
                    break

                info += dat

            fileData.close()
        except KeyboardInterrupt:
            raise
        except:
            print("Unexpected error in handlegetfile:", sys.exc_info()[0])
            peer.sendmessage(ERROR, "Error reading file")
            return

        peer.sendmessage(REPLY, info)

    # end __handlegetfile"""

    def __handlegetfile(self, peer, data):

        # handler for getting a file

        fileName = data

        # if file does not exist send error message
        # else send fileName and Reply to trigger getFile option
        if fileName not in self.availableFileList:
            peer.sendmessage(ERROR, "File not found")
            return

        peer.sendmessage(REPLY, fileName)

    # end __handlegetfile

    def getfile(self, file, hostName, portNum, peerID):

        # receives a file and gathers it to create it

        try:
            peer = PeerConnect(peerID, hostName, portNum)
            peer.sendmessage(REPLYFILE, file)

            fileData = open(file, 'wb')

            while True:
                dat = peer.sock.recv(2048)

                fileData.write(dat)

                if not len(dat):
                    break

            fileData.close()
            peer.closeconnect()
            
        except KeyboardInterrupt:
            raise
        except:
            print("Unexpected error in handlegetfile:", sys.exc_info()[0])
            peer.sendmessage(ERROR, "Error reading file")
            return
                
    # end getfile

    def __handlereplyfile(self, peer, data):

        # handler for sending a file

        fileName = data

        try:
            fileData = open(fileName, 'rb')
            
            while True:
                dat = fileData.read(2048)

                print(dat)

                peer.sock.send(dat)

                if not len(dat):
                    break
                
        except KeyboardInterrupt:
            raise
        except:
            print("Unexpected error in handlegetfile:", sys.exc_info()[0])
            peer.sendmessage(ERROR, "Error reading file")
        finally:
            fileData.close()
            return

        #peer.sendmessage(REPLYFILEEND, fileName)

    # end __handlereplyfile

    def __handlequit(self, peer, data):

        # handler for a peer leaving

        self.peersLock.acquire()
        
        try:
            peerID = data.lstrip().rstrip()

            if peerID in self.getpeerids():
                peer.sendmessage(REPLY, "Quit: peer removerd {}".format(peerID))
                self.removepeer(peerID)
            else:
                peer.sendmessage(ERROR, "Quit: peer not found: {}".format(peerID))
        except:
            print("Unexpected error in handlequit:", sys.exc_info()[0])
        finally:
            self.peersLock.release()

    # end __handlequit

    def addfile(self, fileName):

        # add a file to the file list

        self.availableFileList[fileName] = None

    # end addfile
                
# end class PeerFileTransfer
