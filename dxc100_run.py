#!/usr/bin/env python

"""
|==============================================================================
| DXC100 is a DamExchange Draughts client for the 10x10 board.
|==============================================================================
| Written in Python and using a command line interface.
| It knows the rules of draughts but has no intelligence to play a game.
| You can connect to a draughts server and play a game against the server.
| Or without a connection you can play a game against yourself.
| Messages of client and server are exchanged over a TCP/IP socket connection.
| The DamExchange (DXP) protocol is used to interpret the messages.
| We tested our client using the MobyDam engine on a Linux Mint platform.
| The command line interface has an advanced logging and error control.
| Capture rules meets the standard of International Draughts for a 10x10 board.
| Squares are represented by numbers (not the alpha-num numbering system).
| Usage:
| - Download the DXC100 python files to a folder
| - Start from a terminal: python dxc100_run.py
| 
| (c) Arthur Kalverboer 2018
===============================================================================
"""

import re, sys, os, time
import dxc100_config as C
import threading
import logging
from dxc100_position import Position, parseFEN
from dxc100_classes import State, DamExchange, MySocket, Moving
from dxc100_moves import Move

def prompt() :
    sys.stdout.write('>>> ')
    sys.stdout.flush()

def initLogging():
   # Log names: ALERT, SYS, DXP
   # Levelnames: DEBUG, INFO, WARNING, ERROR and CRITICAL.
   global dxplog, syslog, alert

   dxplog = logging.getLogger('DXP')   # logfile
   syslog = logging.getLogger('SYS')   # logfile
   alert  = logging.getLogger('ALERT') # console + logfile

   formatter1 = logging.Formatter('%(levelname)-8s: %(message)s')
   formatter2 = logging.Formatter("%(name)-6s %(levelname)-6s %(asctime)s: %(message)s")
   formatter3 = logging.Formatter('%(name)-6s %(levelname)-6s: %(message)s')

   hConsole = logging.StreamHandler()
   hConsole.setFormatter(formatter1)
   hFileSys = logging.FileHandler(filename=C.SYSLOG_FILE, mode='a')
   hFileSys.setFormatter(formatter2)
   hFileDxp = logging.FileHandler(filename=C.DXPLOG_FILE, mode='a')
   hFileDxp.setFormatter(formatter2)

   alert.setLevel(logging.INFO)
   alert.addHandler(hConsole)
   alert.addHandler(hFileSys)

   syslog.setLevel(logging.DEBUG)
   syslog.addHandler(hFileSys)

   dxplog.setLevel(logging.DEBUG)
   dxplog.addHandler(hFileDxp)

   return None
#  initLogging()

def clearLogFiles():
   with open(C.SYSLOG_FILE, 'w'):
      pass
   with open(C.DXPLOG_FILE, 'w'):
      pass
   return None
#  clearLogFiles()

def printSubscript():
   # Subscript after displaying the board
   colorString = str(['white', 'black'][current.color]) + ' to move '
   if current.game['started'] == True:
      if current.game['myColor'] == current.color:
         player = " (You)"
      else:
         player = " (" + current.game['engineName'] + ")"
   else:
      player = ""  # no game

   print(colorString + player) 

   return None
#  printSubscript()

class ConsoleHandler(threading.Thread):
   # Subslass of Thread to handle console input from user.

   def __init__(self):
      threading.Thread.__init__(self)
      self.isRunning = False    # not used

   def run(self):
      # Handling console input from user.
      # Excutes when thread started. Overriding python threading.Thread.run()

      syslog.info("ConsoleHandler started")

      global current, mySock, lock
      stack = []
      stack.append('setup')          # initial board

      while True:
         if stack:
            comm = stack.pop()
         else:
            prompt()
            comm = sys.stdin.readline()   # blocked until user entered a message

         if comm.startswith('q') or comm.startswith('ex'):  # quit/exit
            syslog.info("Command terminate program: %s" %comm.strip() )
            os._exit(1)   # does no cleanups

         elif comm.startswith('legal'):  # show legal moves
            lock.acquire()   # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK
            syslog.info("Command show legal moves: %s" %comm.strip() )
            current.pos.mprint(current.color)
            printSubscript()
            lock.release()   # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK
            lstring = ''
            for lmove in current.pos.legalMoves():
               lstring += moving.mrender_move(current.color, lmove) + '  '
            print("Legal moves: " + lstring)

         elif comm.startswith('setup'):
            if current.game['started'] == True:
               print("Game started; setup not allowed")
               continue
            if len(comm.split()) == 1:
               # Setup starting position
               syslog.info("Command setup starting position: %s" %comm.strip() )
               b = 0  # TEST different positions
               if b == 0:
                  board = C.BOARD_START
               elif b == 1:
                  board = C.BOARD_TEST_02  # test position
               elif b == 2:
                  board = C.BOARD_PROBLEM_01   # test problem solving 1
               current = State(Position(board), C.WHITE)
            elif len(comm.split()) == 2:
               # Setup position with fen string (!!! without apostrophes and no spaces !!!)
               _, fen = comm.split(' ', 1)     # strip first word
               syslog.info("Command setup position with FEN string")
               syslog.info("FEN: %s" % fen.strip() )
               pos = parseFEN(fen)
               color = C.BLACK if fen[0] == 'B' else C.WHITE
               current = State(pos, color)
            else:
               continue

            lock.acquire()   # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK
            current.pos.mprint(current.color)
            printSubscript()
            lock.release()   # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK

         elif comm.startswith('fen'):  # show fen string
            syslog.info("Command show FEN string")
            fen = current.pos.toFEN(current.color)
            print("FEN: " + fen)

         elif comm.startswith('m'):
            if current.game['started'] == True and \
                  current.game['myColor'] != current.color:
               print("Move not allowed; server has to move")
               continue
            syslog.info("Command move piece: %s" %comm.strip() )
            if len(comm.split()) == 1:
               moves = current.pos.legalMoves()
               if len(moves) == 1:
                  lmove = moves[0]
               else:
                  print("Please enter a move like 32-28 or 26x37")
                  continue
            elif len(comm.split()) == 2:
               _, umove = comm.split()
               umove = umove.strip()
               match = re.match('(^([0-5]?[0-9][-][0-5]?[0-9])$|^([0-5]?[0-9]([x][0-5]?[0-9])+)$)', umove)
               if match:
                  steps = moving.mparse_move(current.color, umove)
                  lmove = current.pos.matchSteps(steps)
                  if not lmove in current.pos.legalMoves():
                     print("Illegal move; please enter a legal move")
                     continue
               else:
                  # Inform the user when invalid input is entered
                  print("Please enter a move like 32-28 or 26x37")
                  continue
            else:
               print("Too many arguments. Enter a move like m 32-28 or m 26x37")
               continue

            # A legal lmove is found. Now update position and send a message.
            lock.acquire()   # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK
            if current.game['started'] == True and \
                  current.game['myColor'] == current.color:
                  #or True:  # TEST
               # *** outgoing MOVE message ***
               timeSpend = 0   # time spend for this move (future)

               # Convert to real, mutual version ("two-color" move)
               rmove = moving.mreal_move(current.color, lmove) 
               msg = dxp.msg_move(rmove, timeSpend)
               ####print('MOVE: ', lmove)

               try:
                  mySock.send(msg)
                  dxplog.info("snd MOVE: " + msg)
               except:
                  err = sys.exc_info()[1]
                  print( "Error sending move: %s" % err )
                  continue

            # Update position and color to move
            current.pos = current.pos.domove(lmove)
            current.color = 1-current.color   # alternating: 0 and 1 (White and Black)
            current.pos.mprint(current.color)
            printSubscript()
            lock.release()   # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK

         elif comm.upper().startswith('H') or comm.startswith('?'):
            syslog.info("Command show help")
            lock.acquire()   # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK
            # Set lock to prevent printing by incoming messages while printing help
            self.printHelp()
            lock.release()   # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK

         elif comm.startswith('conn'):
            # *** connect to remote host ***
            if mySock.sock != None:
               print("Already connected")
               continue
            if current.game['started'] == True:
               print("Game marked as started. First exit to start a new game.")
               continue
            host, port = C.HOST, C.PORT  # default
            if len(comm.split()) == 2: _, host = comm.split()
            if len(comm.split()) == 3: _, host,port = comm.split()
            syslog.info("Command make connection with host %s port %s" %(host, port) )
            try :
               mySock.open()
               mySock.connect(host, int(port))  # with timeout
               print("Successfully connected to remote host %s, port %s" %(host,port) )
            except:
               #mySock.sock.close()
               mySock.sock = None
               err = sys.exc_info()[1]
               print( "Error trying to connect: %s" % err )
               continue

            if mySock.sock != None:  # connected
               if not tReceiveHandler.isListening: tReceiveHandler.start()

         elif comm.startswith('chat'):
            # *** outgoing CHAT message ***
            if len(comm.split()) == 1:
               continue
            if len(comm.split()) > 1:
               _, txt = comm.split(' ', 1)  # strip first word
               txt = txt.strip()            # trim whitespace
               syslog.info("Command send chat message: %s" %comm.strip() )
               msg = dxp.msg_chat(txt)
               try:
                  mySock.send(msg)
                  dxplog.info("snd CHAT: " + msg)
               except:
                  err = sys.exc_info()[1]
                  print( "Error sending chat message: %s" % err )
                  continue

         elif comm.startswith('gamereq'):
            # *** outgoing GAMEREQ message ***
            if current.game['started'] == True:
               print("Game already started; gamereq not allowed")
               continue
            syslog.info("Command request new game: %s " %comm.strip() )
            myColor = "W"      # default
            gameTime = "120"   # default
            numMoves = "50"    # default
            if len(comm.split()) == 2: _, myColor = comm.split()
            if len(comm.split()) == 3: _, myColor, gameTime = comm.split()
            if len(comm.split()) == 4: _, myColor, gameTime, numMoves = comm.split()

            myColor = C.WHITE if myColor.upper().startswith('W') else C.BLACK
            current.game['myColor'] = myColor    # 0 or 1
            current.game['gameTime'] = gameTime
            current.game['numMoves'] = numMoves
            msg = dxp.msg_gamereq(myColor, gameTime, numMoves, current.pos, current.color)
            try:
               mySock.send(msg)
               dxplog.info("snd GAMEREQ: " + msg)
            except:
               err = sys.exc_info()[1]
               print( "Error sending game request: %s" % err )

         elif comm.startswith('gameend'):
            # *** outgoing GAMEEND message ***
            if current.game['started'] == False:
               print("Game already finished; gameend not allowed")
               continue
            syslog.info("Command finish game: %s " %comm.strip() )
            if current.game['started'] == True and \
                  current.game['myColor'] != current.color:
               print("Message gameend not allowed; wait until your turn")
               continue
            if len(comm.split()) == 2:
                _, reason = comm.split()
            else:
                reason = "0"
            msg = dxp.msg_gameend(reason)

            try:
               mySock.send(msg)
               dxplog.info("snd GAMEEND: " + msg)
               current.game['started'] == False   # stop game
               current.game['result'] == reason
            except:
               err = sys.exc_info()[1]
               print( "Error sending gameend message: %s" % err )

         elif comm.startswith('backreq'):
            # *** outgoing BACKREQ message ***
            if current.game['started'] == False:
               print("Game not started; backreq not allowed")
               continue
            print("Not yet supported")

         elif comm.startswith('clear'):
            syslog.info("Command clear logfiles: %s" %comm.strip() )
            clearLogFiles()
            print("Log files %s and %s cleared " % (C.SYSLOG_FILE, C.DXPLOG_FILE ) )
            syslog.info("Log files %s and %s cleared " % (C.SYSLOG_FILE, C.DXPLOG_FILE ) )

         elif comm.startswith('pieceset'):
            C.PIECE_CHARSET = 1 - C.PIECE_CHARSET    # toggle pieceset
            syslog.info("Command toggle pieceset to: " + str(['Unicode', 'ASCII'][C.PIECE_CHARSET]) )
            lock.acquire()   # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK
            current.pos.mprint(current.color)
            printSubscript()
            lock.release()   # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK
            print("new pieceset: " + str(['Unicode', 'ASCII'][C.PIECE_CHARSET]))

         elif comm.startswith('test0'):
            # TEST TEST TEST
            syslog.info("Command test: %s" %comm.strip() )
            t0 = time.time()
            for i in range(1,100):
               legalMoves = current.pos.legalMoves()
            t1 = time.time()

            current.pos.mprint(current.color)

            print("Time elapsed for test: " + str(t1 - t0)  )

         elif comm.startswith('test1'):
            # *** test1 ***
            syslog.info("Command test: %s" %comm.strip() )
 
            alert.info("Alert > TEST MESSAGE")
            syslog.info("Sys > TEST MESSAGE")
            dxplog.info("Dxp > TEST MESSAGE")

            print("My Color: " + str(['white', 'black'][current.game['myColor']]) )
            print("Color to move: " + str(['white', 'black'][current.color]) )

            msg = "Hello World"
            try:
               mySock.send(msg)
               print("snd TEST: " + msg)
            except:
               err = sys.exc_info()[1]
               print( "Error %s" % err )

         elif comm.startswith('test2'):
            # TEST TEST TEST
            msg = dxp.msg_backreq(1, C.WHITE)
            mySock.send(msg)
            print("snd TEST BACKREQ: " + msg)

         #===================================================================================
         else:
            syslog.info("Command unknown: %s" %comm.strip() )
            print("Unknown command, type h for help: %s" %comm.strip() )
            ### stack.append('H')

      # end while console input

      print("ConsoleHandler stopped")
      print("Save your data and exit program to start again. ")
      return None
   # def run(self)

   def printHelp(self):
      print(' ___________________________________________________________________  ')
      print('| Use one of these commands:  ')
      print('|  ')
      print('| q:           quit  ')
      print('| h:           this help info  ')
      print('| setup:       setup starting position  ')
      print('| setup <fen>: setup position with given fen-string  ')
      print('| fen:         show fen string ')
      print('| legal:       show legal moves  ')
      print('| clear:       clear log files ')
      print('| pieceset:    toggle between ASCII and Unicode pieceset ')
      print('|  ')
      print('| m <move>:    do move (format: 32-28, 16x27, etc)  ')
      print('| m:           do move (if only one move possible)  ')
      print('|  ')
      print('| connect <host> <port>:  ')
      print('|              connect to server  ')
      print('|              default localhost and port 27531  ')
      print('| chat <msg>:  send chat message to server  ')
      print('| gamereq <myColor> <gameTime> <numMoves>:  ')
      print('|              send game request to server with myColor W or B ')
      print('|              parameters optional with defaults: ')
      print('|              myColor: W,  gameTime: 120,  numMoves: 50 ')
      print('| gameend <reason>: ')
      print('|              send game end with reason ')
      print('|              0: unknown  1: I lose  2: draw  3: I win ')
      print('| backreq <moveId> <color>:  ')
      print('|              send request to move back ')
      print('|              not yet supported ')
      print('|  ')
      print('|___________________________________________________________________  ')
      #print()
      return None
   # def printHelp(self)

# CLASS ConsoleHandler

class ReceiveHandler(threading.Thread):
   # Subslass of Thread to handle incoming messages from client.

   def __init__(self):
      threading.Thread.__init__(self)
      self.isListening = False

   def run(self):
      # Handling incoming messages from server.
      # Excutes when thread started. Overriding python threading.Thread.run()

      syslog.info("ReceiveHandler started")
      global current, mySock, lock
      self.isListening = True
      dxplog.info("%s starts listening" % C.INITIATOR)
      while True:
         try:
            message = mySock.receive()   # wait for message
         except:
            err = sys.exc_info()[1]
            print( "Error %s" % err )
            break

         lock.acquire()   # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK
         message = message[0:127]  # DXP max length
         dxpData = dxp.parse(message)
         if dxpData["type"] == "C":
            dxplog.info("rcv CHAT: " + message)
            print("\nChat message: " + dxpData["text"])
            prompt()

         elif dxpData["type"] == "A":
            dxplog.info("rcv GAMEACC: " + message)
            if dxpData["accCode"] == "0":
               current.game['started'] = True
               current.game['myColor'] = current.game['myColor']  # as requested
               current.game['engineName'] = dxpData["engineName"]
               current.game['startingTime'] = "YYY"   # TODO
               print("\nGame request accepted by " + dxpData["engineName"])
            else:
               current.game['started'] = False
               print("\nGame request NOT accepted by " + dxpData["engineName"] + " Reason: " + dxpData["accCode"])
            current.pos.mprint(current.color)
            printSubscript()
            prompt()

         elif dxpData["type"] == "E":
            dxplog.info("rcv GAMEEND: " + message)
            print("\nRequest end of game accepted. Reason: " + dxpData["reason"] + " Stop: " + dxpData["stop"])
            prompt()
            # Confirm game end by sending message back (if not sent by me)
            if current.game['started'] == True:
               current.game['started'] = False
               current.game['result'] = dxpData["reason"]
               msg = dxp.msg_gameend(dxpData["reason"])
               mySock.send(msg)
               dxplog.info("snd GAMEEND: " + msg)

         elif dxpData["type"] == "M":
            dxplog.info("rcv MOVE: " + message)
            steps = [ dxpData['from'], dxpData['to'] ]
            nsteps = map( int, steps )
            ntakes = map( int, dxpData['captures'] )
            rmove_dxp = Move(nsteps, ntakes)   # namedtuple, a real move from host
            ##color_text = str(['white', 'black'][current.color])
            ##print("Received move: " + str(rmove_dxp) + " with color " + color_text )
            move_dxp = moving.mreal_move(current.color, rmove_dxp)  # the "one-color" dxp move
            xmove = current.pos.matchStepsAndTakes(move_dxp.steps, move_dxp.takes) # the "one-color" system move

            if xmove != None:
               # Update position and color to move
               ##print("Received xmove: " + str(xmove))
               print("\nMove received: " + moving.mrender_move(current.color, xmove) )
               current.pos = current.pos.domove(xmove)
               current.color = 1-current.color   # alternating: 0 and 1 (White and Black)
               current.pos.mprint(current.color)
               printSubscript()
               prompt()
            else:
               print("Error: received move is illegal [" + message + "]")
               prompt()

         elif dxpData["type"] == "B":
            # For the time being do not confirm request from server: send message back.
            dxplog.info("rcv BACKREQ: " + message)
            accCode = "1"   # 0: BACK YES; 1: BACK NO; 2: CONTINUE
            msg = dxp.msg_backacc(accCode)
            mySock.send(msg)
            dxplog.info("snd BACKACC: " + msg)

         elif dxpData["type"] == "K":
            # Answer to my request to move back
            dxplog.info("rcv BACKACC: " + message)
            print("rcv BACKACC: " + message)   # TEST
            accCode = dxpData['accCode']
            if accCode == "0":
               # Actions to go back in history as specified in my request
               print("TODO: actions to move back")
               pass   # TODO

         else:
            dxplog.info("rcv UNKNOWN: " + message)
            print("\nrcv Unknown message: " + message)
            prompt()

         lock.release()   # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK

      # end while listening

      self.isListening = False
      dxplog.error("Listening stopped; connection broken")
      print("Connection broken; receiveHandler stopped. ")
      print("Save your data and exit program to start again. ")
      prompt()
      return None
   # def run(self)

# CLASS ReceiveHandler

if __name__ == '__main__':
   print("||==================================================================||")
   print("||   DXC100: DamExchange Client for 10x10 International Draughts    ||")
   print("||==================================================================||")

   dxp = DamExchange()     # global, singleton
   moving = Moving()       # global, singleton
   mySock = MySocket()     # global, singleton
   current = State(Position(C.BOARD_START), C.WHITE)  # global; use default parms
   lock = threading.Lock() # global
   initLogging()           # globals: syslog, dxplog, alert

   # use 2 threads to simultaneous listen to incoming messages and to console input
   tConsoleHandler = ConsoleHandler()   # Thread subclass instance
   tReceiveHandler = ReceiveHandler()   # Thread subclass instance. Start when connected.
   tConsoleHandler.start()

# endif


#*******************************************************************************************

