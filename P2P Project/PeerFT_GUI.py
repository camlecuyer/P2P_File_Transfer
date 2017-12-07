# Cameron L'Ecuyer
# PeerFT_GUI.py

from PeerFileTransfer import *
from tkinter import *
from tkinter import filedialog
from random import *

import time
import threading
import os
import sys

"""
Class handles the GUI functionality of the P2P file transfer system



@@@TODO: Add SSL
         Add threading for messages and/or getfile
         Add a better selection system for files
"""

class PeerFT_GUI(Frame):

    def __init__(self, maxNumOfPeers = 3, serverPortNum = 5678, master=None):        

        # constructor

        Frame.__init__(self, master)
        self.master.geometry('500x300')
        self.grid()
        self.fileList = {}
        self.peerList = {}
        self.createwidgets()

        # creates the peer for the current machine
        self.Peer = PeerFileTransfer(serverPortNum, maxNumOfPeers)
        self.master.title("File Transfer Program {}:{}".format(self.Peer.serverHost, serverPortNum))

        self.bind("<Destroy>", self.__ondestroy)

        # Thread for listening for connections
        thread = threading.Thread(target = self.Peer.peerlisten, args = [])
        thread.start()

        # Thread for the timer for refresh
        timeThread = threading.Thread(target = self.timer, args = [])
        timeThread.start()

    # end constructor

    def timer(self):

        # automatically refreshes the peer list

        while(not self.Peer.shutdown):
            time.sleep(8)
            
            if(not self.Peer.shutdown):
                self.Peer.checkifpeeralive()

            if(not self.Peer.shutdown):
                self.onrefresh()

    # end timer

    def updatepeerlist(self):

        # updates the peer list

        # saves currently selected item
        select = self.peerList.curselection()

        # if peerList is not empty, empty it
        if self.peerList.size() > 0:
            self.peerList.delete(0, self.peerList.size() - 1)

        #  fill peerList
        for peer in self.Peer.getpeerids():
            self.peerList.insert(END, peer)

        # places currently selected item highlight
        if select:
            self.peerList.select_set(select)
            self.peerList.event_generate("<<ListboxSelect>>")

    # end updatepeerlist

    def updatefilelist(self):

        # updates the file list

        # saves currently selected item
        select = self.fileList.curselection()

        # if fileList is not empty, empty it
        if self.fileList.size() > 0:
            self.fileList.delete(0, self.fileList.size() - 1)

        # fill the fileList
        for file in self.Peer.availableFileList:
            peer = self.Peer.availableFileList[file]

            # if no peer associated with the file, it is on local
            if not peer:
                peer = "(on local)"

            # if the file is from an active peer or on local add it to the fileList
            if peer in self.Peer.getpeerids() or peer == "(on local)":
                self.fileList.insert(END, "{}:{}".format(file, peer))

        # places currently selected item highlight
        if select:
            self.fileList.select_set(select)
            self.fileList.event_generate("<<ListboxSelect>>")

    # end updatefilelist

    def __ondestroy(self, event):

        # stops the loop
        
        self.Peer.shutdown = True
        
    # end __onDestroy

    def ongetfile(self):

        # gets the selected file from the list

        # get the selected file
        select = self.fileList.curselection()

        if len(select) == 1:
            select = self.fileList.get(select[0]).split(':')

            # if there is the correct number of parts after split send a message to the peer for a file
            if len(select) > 2:
                fileName, hostName, portNum = select
                peerID = self.Peer.findpeerid(hostName, portNum)
                response = self.Peer.sendtopeer(hostName, portNum, GETFILE, fileName, peerID)

                if len(response) and response[0][0] == REPLY:
                    self.Peer.getfile(fileName, hostName, portNum, peerID)
                    #fileDoc = open(fileName, 'w')
                    #fileDoc.write(response[0][1])
                    #fileDoc.close()
                    #self.Peer.availableFileList[fileName] = None

    # end ongetfile

    def ongetfilelist(self):

        # gets the file list from the peers and adds it to the fileList

        # for every peer, get a list of files from the selected peer
        for peer in self.Peer.getpeerids():
            hostName, portNum = peer.split(':')
            response = self.Peer.sendtopeer(hostName, portNum, LISTOFFILES, '', peer)

            if len(response) and response[0][0] == REPLY:
                data = response[0][1]

                # split the list of files from the peer
                data = data.translate({ord(c): None for c in '"[],\''}).split()

                length = int(data[0])

                # add the file to the list if the file is not from the calling
                # peer or not already in the list
                for i in range(1, length+1):
                    file, host, port = data[i].split(':')
                    ID = '{}:{}'.format(host, port)

                    if ID != self.Peer.ID or (file not in self.Peer.availableFileList.keys()):
                        self.Peer.availableFileList[file] = ID
                
        self.updatefilelist()

    # end ongetfilelist

    def onaddfile(self):

        # adds a file to the list

        # gets the file with a dialog from the current directory
        filename =  filedialog.askopenfilename(initialdir = os.getcwd(),title = "Select a file",filetypes = [("All files","*.*")])

        # removes extra filepath name
        filename = filename[filename.rfind('/') + 1:]

        # if filename is not empty add to the list
        if filename.lstrip().rstrip():
            file = filename.lstrip().rstrip()
            self.Peer.addfile(file)

        self.updatefilelist()

    # end onaddfile

    def onrefresh(self):

        # refreshes the peer list
        
        self.updatepeerlist()
        self.ongetfilelist()

    # end onrefresh

    def onremove(self):

        # removes a peer from the peer list

        # get the selected peer
        select = self.peerList.curselection()

        # remove the selected peer
        if len(select) == 1:
            peerID = self.peerList.get(select[0])
            hostName, portNum = self.Peer.peers[peerID]
            self.Peer.sendtopeer(hostName, portNum, PEERQUIT, self.Peer.ID, peerID)
            self.Peer.removepeer(peerID)

    # end onremove

    def onjoin(self):
        
        # joins a peer network

        # get the name of the peer to join
        peer = self.txt_joinPeer.get()

        # if the peer is not empty add to the list and send a message to join
        if peer.lstrip().rstrip():
            peerID = peer.lstrip().rstrip()
            hostName, portNum = peerID.split(':')
            self.Peer.sendtopeer(hostName, portNum, ADDPEER, self.Peer.ID, peerID)
            self.Peer.addpeer(peerID, hostName, portNum)
            self.onrefresh()

        # empty the text box
        self.txt_joinPeer.delete(0, len(peer))
            
    # end onjoin

    def createwidgets(self):

        # creates objects for window

        fileFrame = Frame(self)
        peerFrame = Frame(self)
        
        fileFrame.grid(row = 0, column = 0, sticky = N+S)
        peerFrame.grid(row = 0, column = 1, stick = N+S)

        # File List
        Label(fileFrame, text = "File List").grid(row = 0, column = 0)

        fileScroll = Scrollbar(fileFrame, orient=VERTICAL)
        fileScroll.grid(row = 1, column = 1, sticky = N+S)

        self.fileList = Listbox(fileFrame, height = 5, width = 40, yscrollcommand = fileScroll.set)
        self.fileList.grid(row = 1, column = 0, stick = N+S)
        fileScroll["command"] = self.fileList.yview

        self.btn_getFile = Button(fileFrame, text = "Get File", command = self.ongetfile)
        self.btn_getFile.grid(row = 2, column = 0)

        self.btn_getFile = Button(fileFrame, text = "Add File", command = self.onaddfile)
        self.btn_getFile.grid(row = 4, column = 0)

        # Peer List
        Label(peerFrame, text = "Peer List").grid(row = 0, column = 0)

        peerScroll = Scrollbar(peerFrame, orient=VERTICAL)
        peerScroll.grid(row = 1, column = 1, sticky = N+S)

        self.peerList = Listbox(peerFrame, height = 5, width = 30, yscrollcommand = peerScroll.set)
        self.peerList.grid(row = 1, column = 0, stick = N+S)
        peerScroll["command"] = self.peerList.yview

        self.btn_refresh = Button(peerFrame, text = "Refresh", command = self.onrefresh)
        self.btn_refresh.grid(row = 2, column = 0)

        self.btn_remove = Button(peerFrame, text = "Remove", command = self.onremove)
        self.btn_remove.grid(row = 4, column = 0)

        # Join peer frame
        joinPeerFrame = Frame(peerFrame)
        joinPeerFrame.grid(row = 5, column = 0)
        
        self.txt_joinPeer = Entry(joinPeerFrame, width=25)
        self.txt_joinPeer.grid(row = 0, column = 0)
        self.btn_join = Button(joinPeerFrame, text='Join', command=self.onjoin)
        self.btn_join.grid(row = 0, column = 1)

    # end createwidgets
     
# end class PeerFT_GUI

def main():
    try:
        FTapp = PeerFT_GUI(2, 2000)
        FTapp.mainloop()
    except:
        return
# end main

if __name__=='__main__':
   main()
