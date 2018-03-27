#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
|============================================================================
| DXC100: definition of various classes
| (c) Arthur Kalverboer 2018
|============================================================================
"""

import re, sys
import dxc100_config as C
import socket
from dxc100_moves import Move

class State:
   # A state of the application
   # - pos: position as defined in Position
   # - color: color to move (0:WHITE, 1:BLACK)
   # - time_elapsed
   # 

   game = {}
   game['started'] = False
   game['myColor'] = C.WHITE
   game['engineName'] = "draughts server"   # follower name
   game['startingTime'] = 0
   game['result'] = "0"  # unknown (0) OR I give up (1) OR draw (2) OR I win (3)

   def __init__(self, pos, color):
      self.pos = pos      # "One-color" position. White always moves.
      self.color = color  # Player to move

   def clone(self):
      return State(self.pos, self.color)

   #def pos_to_fen(self):

# *** END class State ***

class MySocket:
   # Socket class
   # New since Python 2.3: sock = socket.create_connection( (host,port), timeout=10 )
   #    It will try to resolve hostname for both AF_INET and AF_INET6
   #

   def __init__(self):
      self.sock = None

   def test(self, txt):
      print(txt)

   def open(self):
      try:
         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      except:
         self.sock = None
         raise Exception("socket exception: failed to open")
      return self
   # def open(self)

   def connect(self, host, port):
      self.sock.settimeout(2)  # timeout for connection
      try:
         self.sock.connect((host, port))
      except socket.error as msg:
         #self.sock.close()
         self.sock = None
         raise Exception("connection exception: failed to connect")
      if self.sock != None:
         self.sock.settimeout(None)  # default
      return self
   # def connect(self)

   def send999(self, imsg):
      #sent = self.sock.send(msg)  # simple send
      msg =  imsg + "\0"
      msgLen = len(msg)
      totalsent = 0
      while totalsent < msgLen:
         try:
            sent = self.sock.send(msg[totalsent:])
         except:
            raise Exception("send exception: no connection")
            return None
         if sent == 0:
            raise Exception("send exception: socket connection broken")
            break
         totalsent = totalsent + sent
      # end while
      return None
   # def send999(self)

   def send(self, msg):
      try:
         self.sock.send(msg + "\0")
      except:
         raise Exception("send exception: no connection")
      return None
   # def send(self)

   def receive(self):
      msg = ""
      while True:
         # Collect message chunks until null character found
         try:
            chunk = self.sock.recv(1024)
         except:
            raise Exception("receive exception: no connection")
            return None

         if chunk == "":
            raise Exception("receive exception: socket connection broken")
            return None
         msg += chunk
         if msg.find("\0") > -1: break
         if len(msg) > 128: break   # too long, no null char

      #print("final msg: " + msg)
      msg = msg.replace("\0","")   # remove all null chars

      # Use strip to remove all whitespace at the start and end.
      # Including spaces, tabs, newlines and carriage returns.
      msg = msg.strip()
      return msg
   # def receive(self)

# *** END class MySocket ***

class DamExchange:
   # Singleton object for damexchange functions.
   # -

   def __init__(self):
      pass

   def parse(self, msg):
      # Parse incoming DXP message. Returns relevant items depending on mtype.
      result = {}
      mtype = msg[0:1]
      if mtype == "C":  # CHAT
         result['type'] = "C"
         result['text'] = msg[1:127]
      elif mtype == "R":  # GAMEREQ (only received by FOLLOWER)
         result['type'] = "R"
         result['name'] = msg[3:35].strip()  # initiator
         result['fColor'] = msg[35:36]  # color of follower
         result['gameTime'] = msg[36:40]
         result['numMoves'] = msg[40:44]
         result['posInd'] = msg[44:45]
         if result['posInd'] != "A":
            result['mColor'] = msg[45:46]   # color to move for position
            result['pos'] = msg[46:96]
      elif mtype == "A":  # GAMEACC
         result['type'] = "A"
         result['engineName'] = msg[1:33].strip()   # follower name
         result['accCode'] = msg[33:34]
      elif mtype == "M":  # MOVE
         result['type'] = "M"
         result['time'] = msg[1:5]
         result['from'] = msg[5:7]
         result['to'] = msg[7:9]
         result['nCaptured'] = msg[9:11]
         result['captures'] = []
         for i in range(int(result['nCaptured'])):
            s = i * 2
            result['captures'].append(msg[11+s:13+s])
      elif mtype == "E":  # GAMEEND
         result['type'] = "E"
         result['reason'] = msg[1:2]
         result['stop'] = msg[2:3]
      elif mtype == "B":  # BACKREQ
         result['type'] = "B"
         result['moveId'] = msg[1:4]
         result['mColor'] = msg[4:5]
      elif mtype == "K":  # BACKACC
         result['type'] = "K"
         result['accCode'] = msg[1:2]
      else:
         result['type'] = "?"
      return result
   # parse

   def msg_chat(self, str):
      # Generate CHAT message. Example: CWhat do you think about move 35?
      msg = "C" + str
      return msg
   # msg_chat

   def msg_gamereq(self, myColor, gameTime, numMoves, pos=None, colorToMove=None ):
      # Generate GAMEREQ message. Example: R01Tornado voor Windows 4.0        W060065A
      gamereq = []
      gamereq.append("R")   # header
      gamereq.append("01")  # version

      gamereq.append(C.INITIATOR.ljust(32)[:32])  # iName: fixed length padding spaces
      gamereq.append('Z' if myColor == C.WHITE else 'W')  # fColor: color of follower (server)
      gamereq.append(str(gameTime).zfill(3))      # gameTime: time limit of game (ex: 090)
      gamereq.append(str(numMoves).zfill(3))      # numMoves: number of moves of time limit (ex: 050)
      if pos == None or colorToMove == None:
         gamereq.append("A")   # posInd == A: use starting position
      else:
         gamereq.append("B")   # posInd == B: use parameters pos and colorToMove
         gamereq.append("W" if colorToMove == C.WHITE else "Z")  # mColor
         gamereq.append(self.dxpBoard(pos, colorToMove))   # board

      msg = ""
      for item in gamereq: msg = msg + item
      return msg
   # msg_gamereq

   def msg_move(self, rmove, timeSpend):
      # Generate MOVE message. Example: M001205250422122320
      # Parm rmove is a "two-color" move
      move = []
      move.append("M")   # header
      move.append(str(timeSpend%10000).zfill(4))      # mTime: 0000 .. 9999
      move.append(str(rmove.steps[0]%100).zfill(2))   # mFrom
      move.append(str(rmove.steps[-1]%100).zfill(2))  # mTo
      move.append(str(len(rmove.takes)%100).zfill(2)) # mNumCaptured: number of takes (captures)
      for k in rmove.takes:
         move.append(str(k%100).zfill(2))   # mCaptures

      msg = ""
      for item in move: msg = msg + item
      return msg
   # msg_move

   def msg_gameend(self, reason):
      # Generate GAMEEND message. Example: E00
      gameend = []
      gameend.append("E")   # header
      gameend.append(str(reason)[0] )   # reason:  0 > unknown  1 > I lose  2 > draw  3 > I win
      gameend.append("1")               # stop code: 0 > next game preferred  1: > no next game
      msg = ""
      for item in gameend: msg = msg + item
      return msg
   # msg_gameend

   def msg_backreq(self, moveId, colorToMove):
      # Generate BACKREQ message. Example: B005Z
      backreq = []
      backreq.append("B")
      backreq.append(str(moveId%1000).zfill(3))               # moveId
      backreq.append("W" if colorToMove == C.WHITE else "Z")  # mColor
      msg = ""
      for item in backreq: msg = msg + item
      return msg
   # msg_backreq

   def msg_backacc(self, accCode):
      # Generate BACKREQ message. Example: K1
      backreq = []
      backreq.append("K")
      backreq.append(str(accCode[0]))   # accCode
      msg = ""
      for item in gameend: msg = msg + item
      return msg
   # msg_backacc

   def dxpBoard(self, pos, color):
      pcode = {'P': 'w', 'K': 'W', 'p': 'z', 'k': 'Z', '.': 'e'}  # dxp spec
      rpos = pos.clone() if color == C.WHITE else pos.rotate()  # mutual, real version
      ##########board = [pcode[elem] for elem in rpos.setup[1:-1]]    # output list save for reuse
      board = ''.join( str(pcode[elem]) for elem in rpos.setup[1:-1] )  # exclude 0's at begin and end
      return board

# *** END class DamExchange ***

class Moving:
   # Singleton object for moving functions.

   def mreal_move(self, color, move):
      # Parameter move is a "one-color" move with steps and takes.
      # Output is a "two-color" move with steps and takes.
      if move is None: return ''
      steps = move.steps if color == C.WHITE else map(lambda i: 51-i, move.steps)
      takes = move.takes if color == C.WHITE else map(lambda i: 51-i, move.takes)
      rmove = Move(steps, takes)
      return rmove

   def mrender_move(self, color, move):
      # Render move to move in user format (mutual version)
      if move is None: return ''
      rmove = self.mreal_move(color, move)
      return self.render_move(rmove)

   def mparse_move(self, color, umove):
      # Parameter move in user format like 17-14 or 10x17 (user move).
      # Return list of steps of move/capture in numeric format  (mutual version)
      nsteps = self.parse_move(umove)
      return ( nsteps if color == C.WHITE else map(lambda i: 51-i, nsteps) )

   def parse_move(self, umove):
       # Parameter move in user format like 32-28 or 26x37.
       # Return list of steps of move/capture in number format.
       nsteps = map( int, re.split('[-x]', umove) )
       return nsteps

   def render_move(self, move):
       # Render move to move in user format
       d = '-' if len(move.takes) == 0 else 'x'
       return str(move.steps[0]) + d + str(move.steps[-1])

# *** END class Moving ***

#*******************************************************************************************
def main():
   print('nothing to do')
   return 0

if __name__ == '__main__':
    main()


