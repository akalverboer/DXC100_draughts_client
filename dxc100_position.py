#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
|============================================================================
| DXC100: Position class
| (c) Arthur Kalverboer 2018
|============================================================================
"""

import re, sys
import dxc100_config as C
from dxc100_moves import Move, gen_moves

class Position:
    # A position of a draughts 10x10 game
    # Position stored as a list of 52 char; first and last index unused ('0') rotation-symmetry
    # Coding:
    # - lowercase: black
    # - uppercase: white
    # - P: white piece; K: white king
    # - p: black piece; k: black king
    # - dot is empty field
    # The setup is a "one-color" setup. Always white to move.
    # Parameter setup has two appearances: list of char or string of char.
    # The string can differ in that it has also spaces to visualize the board.
    # NB. In Python both list and string has the same methods.
    #

    def __init__(self, setup):
        if len(setup) == 52:
           # No spaces in setup
           self.setup = list(setup)  # make a list clone
        else:
           # Spaces added to setup (string, maybe list)
           str_setup = "".join(setup)  # convert to string regardless of type list or string
           str_setup = str_setup.replace(" ","")   # remove all spaces
           self.setup = list(str_setup)  # convert to list

    def key(self):
        pos_key = ''.join(self.setup)    # array to string
        return pos_key

    def rotate(self):
        rotSetup = [ x.swapcase() for x in self.setup[::-1] ]  # clone!
        return Position(rotSetup)

    def clone(self):
        return Position(self.setup)

    def legalMoves(self):
        return gen_moves(self)

    def domove(self, move):
        # Move is named tuple with list of steps and list of takes
        # The move is a "one-color" move; white always playing
        # Returns new rotated position object after moving.
        # Remember: move is always done with white
        if move is None: return self.rotate()     # turn to other player

        setup = list(self.setup)    # clone setup

        # Actual move
        i, j = move.steps[0], move.steps[-1]    # first, last (NB. sometimes i==j !)
        p =  setup[i]

        # Move piece and promote to white king
        promotion_line = range(1,6)
        setup[i] = '.'
        if j in promotion_line and (p != 'K'):
           setup[j] = 'K'
        else:
           setup[j] = p

        # Capture
        for k in move.takes:
           setup[k] = '.'

        # We rotate the returned position, so it's ready for the next player
        posnew = Position(setup).rotate()

        return posnew
    # def doMove()

    def toFEN(self, colorToMove):
       # Parameter colorToMove: 0 white, 1 black

       # Get setup mutual version
       if colorToMove == C.WHITE: mSetup = self.setup
       else:                      mSetup = self.rotate().setup

       sideToMove = str( ['W', 'B'][colorToMove] )   

       whitePieces = ""
       first = True
       for num in range(1,51):
          pieceCode = mSetup[num];
          if pieceCode == 'P' and first == False: whitePieces += ","
          if pieceCode == 'K' and first == False: whitePieces += ","
          if pieceCode == 'P': whitePieces += str(num); first = False
          if pieceCode == 'K': whitePieces += 'K' + str(num); first = False

       blackPieces = ""
       first = True
       for num in range(1,51):
          pieceCode = mSetup[num];
          if pieceCode == 'p' and first == False: blackPieces += ","
          if pieceCode == 'k' and first == False: blackPieces += ","
          if pieceCode == 'p': blackPieces += str(num); first = False
          if pieceCode == 'k': blackPieces += 'K' + str(num); first = False

       fenPosition = sideToMove + ":W" + whitePieces + ":B" + blackPieces + ".";
       return fenPosition
    # def toFEN()

    def mprint(self, color):
       # Print position ("two-color" version; mutual)
       if color == C.WHITE: self.xprint()
       else: self.rotate().xprint()
       return None
    # def mprint()

    def xprint(self):
       # Print position in a human readable format.
       # unicodes:  ⛀    ⛁    ⛂    ⛃
       # setup of board is array 0..52; fill 'p', 'P', 'k', 'K', '.'
       numSpaces = 0
       uni_piececode = {'p':'⛂', 'k':'⛃', 'P':'⛀', 'K':'⛁', '.':'·', ' ':' '}  # utf-8
       chr_piececode = {'p':'b', 'k':'B', 'P':'w', 'K':'W', '.':'·', ' ':' '}   # asci
       if C.PIECE_CHARSET == 0:
          piececode = uni_piececode
       else:
          piececode = chr_piececode
       nrows = 10

       sys.stdout.write("\n")
       for i in range(1, nrows+1):
          row_len = 5
          start = (i-1) * (nrows//2) + 1
          row = self.setup[start: start + (nrows//2)]
          numSpaces = 0 if numSpaces == 2 else 2   # alternate
          spaces = ' ' * numSpaces                   # spaces before row of pieces
          numbering = ' %2d - %2d ' %( start, start + nrows//2 - 1)
          pieces = '   '.join(piececode.get(p, p) for p in row)
          #print(numbering + '   ' + spaces + pieces)
          sys.stdout.write(numbering + '   ' + spaces + pieces + "\n")
       sys.stdout.write("\n")
       sys.stdout.flush()
       return None
    # def print_pos()

    def matchSteps(self, steps):
       # Match list of steps with a (not always unique) legal move.
       # If all steps of a move/capture are given, the match will be unique.
       # Parameter pos: position and steps "one-color" version (white always plays)
       # If no match found, returns None
       nsteps = map( int, steps )
       lmoves = self.legalMoves()
       if len(nsteps) == 2:
          for move in lmoves:
             if move.steps[0] == nsteps[0] and move.steps[-1] == nsteps[-1]:
                return move
       else:
          for move in lmoves:
             if set(move.steps) == set(nsteps):
                return move
       return None
     # def matchSteps()

    def matchStepsAndTakes(self, steps, takes):
       # Match given parameters to get a unique legal move (DXP version).
       # Parameter steps is a list of 2 items: from-field an to-field.
       # Parameter takes is a list of all fields of taken pieces.
       # Parameter pos: a "one-color" position (white always plays)
       # If no match found, returns None
       nsteps = map( int, steps )
       ntakes = map( int, takes )
       lmoves = self.legalMoves()
       for move in lmoves:
          steps_OK = (move.steps[0] == nsteps[0] and move.steps[-1] == nsteps[-1])
          takes_OK = (set(move.takes) == set(ntakes))
          if steps_OK and takes_OK:
             return move
       return None
    # def matchStepsAndTakes()


# *** END class Position ***


def parseFEN(iFen):
   """ Parses a string in Forsyth-Edwards Notation into a Position """
   fen = iFen                  # working copy
   fen = fen.replace(" ", "")  # remove all spaces
   fen = re.sub(r'\..*$', '', fen)   # cut off info (.xxx) at the end
   if fen == '': fen = 'W:B:W'       # empty FEN Position
   if fen == 'W::': fen = 'W:B:W'
   if fen == 'B::': fen = 'B:B:W'
   fen = re.sub(r'.::$', 'W:W:B', fen)
   parts = fen.split(':')

   rlist = list('0'*51)                            # init temp return list
   sideToMove = 'B' if parts[0][0] == 'B' else 'W'
   rlist[0] = sideToMove

   for i in range(1,3):   # process the two sides
      side = parts[i]     # working copy
      color = side[0]
      side = side[1:]     # strip color char
      if len(side) == 0: continue    # nothing to do: next side
      numSquares = side.split(',')   # list of numbers or range of numbers with/without king flag
      for num in numSquares:
         isKing = True if num[0] == 'K' else False
         num = num[1:] if isKing else num       # strip 'K'
         isRange = True if len(num.split('-')) == 2 else False
         if isRange:
            r = num.split('-')
            for j in range( int(r[0]), int(r[1]) + 1 ):
               rlist[j] = color.upper() if isKing else color.lower()
         else:
            rlist[int(num)] = color.upper() if isKing else color.lower()

   # prepare output
   pcode = {'w': 'P', 'W': 'K', 'b': 'p', 'B': 'k', '0': '.'}
   board = ['0'] + [pcode[elem] for elem in rlist[1:]] + ['0']
   pos = Position(board)
   return pos if sideToMove == 'W' else pos.rotate()
# def parseFEN()

#*******************************************************************************************
def main():
   print('nothing to do')
   return 0

if __name__ == '__main__':
    main()


