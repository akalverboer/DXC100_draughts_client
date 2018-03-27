#!/usr/bin/env python

"""
|============================================================================
| DXC100: CONSTANTS and config settings
| (c) Arthur Kalverboer 2018
|============================================================================
"""

WHITE, BLACK = 0, 1   # CONSTANT

VERSION = "2018.04.1"
INITIATOR = "DXC100 Client " + "(" + VERSION + ")"   # DamExchange protocol
APPNAME = {'short':'DXC100', 'long':'DamExchange Client', 'github': 'dxc100_draughts_client'}
SYSLOG_FILE = 'mysys.log'
DXPLOG_FILE = 'mydxp.log'

HOST = '127.0.0.1' # default host address of the server
PORT = 27531       # default port DXP protocol
PIECE_CHARSET = 0  # 0: utf-8 (unicodes);  1: ASCII (Windows console does not accept Unicode-only characters)

# The external respresentation of our board is a 100 character string.
BOARD_EMPTY = ('0'
    '   .   .   .   .   . '    #  01 - 05
    ' .   .   .   .   .   '    #  06 - 10
    '   .   .   .   .   . '    #  11 - 15
    ' .   .   .   .   .   '    #  16 - 20
    '   .   .   .   .   . '    #  21 - 25
    ' .   .   .   .   .   '    #  26 - 30
    '   .   .   .   .   . '    #  31 - 35
    ' .   .   .   .   .   '    #  36 - 40
    '   .   .   .   .   . '    #  41 - 45
    ' .   .   .   .   .   '    #  46 - 50
'0')

BOARD_START = ('0'
    '   p   p   p   p   p '    #  01 - 05
    ' p   p   p   p   p   '    #  06 - 10
    '   p   p   p   p   p '    #  11 - 15
    ' p   p   p   p   p   '    #  16 - 20
    '   .   .   .   .   . '    #  21 - 25
    ' .   .   .   .   .   '    #  26 - 30
    '   P   P   P   P   P '    #  31 - 35
    ' P   P   P   P   P   '    #  36 - 40
    '   P   P   P   P   P '    #  41 - 45
    ' P   P   P   P   P   '    #  46 - 50
'0')

BOARD_TEST_01 = ('0'
    '   .   K   .   .   . '    #  01 - 05
    ' .   .   .   .   .   '    #  06 - 10
    '   p   .   k   .   . '    #  11 - 15
    ' .   .   .   .   p   '    #  16 - 20
    '   .   .   .   .   p '    #  21 - 25
    ' .   .   .   .   .   '    #  26 - 30
    '   .   p   .   .   . '    #  31 - 35
    ' .   .   .   .   .   '    #  36 - 40
    '   .   .   .   p   . '    #  41 - 45
    ' .   .   .   .   .   '    #  46 - 50
'0')

BOARD_TEST_02 = ('0'
    '   .   .   .   .   . '    #  01 - 05
    ' .   .   .   .   .   '    #  06 - 10
    '   .   .   .   .   . '    #  11 - 15
    ' .   .   .   .   .   '    #  16 - 20
    '   p   p   .   .   . '    #  21 - 25
    ' P   .   .   .   .   '    #  26 - 30
    '   p   p   p   p   . '    #  31 - 35
    ' .   .   .   .   .   '    #  36 - 40
    '   .   .   .   .   . '    #  41 - 45
    ' .   .   .   .   .   '    #  46 - 50
'0')

BOARD_PROBLEM_01 = ('0'
    '   .   .   .   .   p '    #  01 - 05  P.Lauwen, DP, 4/1977
    ' .   .   p   .   .   '    #  06 - 10
    '   .   .   .   .   P '    #  11 - 15
    ' .   .   .   P   .   '    #  16 - 20
    '   .   .   .   P   . '    #  21 - 25
    ' .   .   .   P   p   '    #  26 - 30
    '   .   P   .   .   p '    #  31 - 35
    ' .   p   .   .   p   '    #  36 - 40
    '   P   p   .   .   p '    #  41 - 45
    ' .   .   .   P   P   '    #  46 - 50
'0')

# FEN examples
FEN_INITIAL = "W:B1-20:W31-50"
FEN_DXP100_1 = "W:W15,19,24,29,32,41,49,50:B5,8,30,35,37,40,42,45."  # P.Lauwen, DP, 4/1977
FEN_DXP100_2 = "W:W17,28,32,33,38,41,43:B10,18-20,23,24,37."
FEN_DXP100_3 = "W:WK3,25,34,45:B38,K47."
FEN_DXP100_4 = "W:W18,23,31,33,34,39,47:B8,11,20,24,25,26,32."       # M.Dalman
FEN_DXP100_5 = "B:B7,11,13,17,20,22,24,30,41:W26,28,29,31,32,33,38,40,48."  # after 30-35 white wins

# Solution 1x1 after 20 moves!! Mad100 finds solution. Set nodes 300000.
FEN_DXP100_6 = "W:W16,21,25,32,37,38,41,42,45,46,49,50:B8,9,12,17,18,19,26,29,30,33,34,35,36."


#===================================================================================

