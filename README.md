# DXC100: a DamExchange client for 10x10 International Draughts

This application has a command line interface to play a draughts game.
I create this application because I missed a Linux frontend for draughts engines.
Most of the frontends are only available for Windows.

You can connect to a remote draughts server and play a game against the server.
It makes use of the widely used DamExchange protocol to exchange messages. Communication over a TCP/IP socket connection.
The application knows the rules of draughts but has no intelligence to play a game.

I tested the client using the MobyDam engine on a Linux Mint platform with Python 2.7.12.
I am not sure but I am not surprised if the client works for other platforms like macOS or Windows.

Of course you can choose your own draughts engine. The platform of the server is not important.
The only condition is that your server supports the DXP protocol.

Basic usage:
- Download the DXC100 python files to a folder
- Start from a terminal: python dxc100_run.py

After the prompt ">>>" you can type instructions for use.

The application is not comparable to the advantages of a GUI.
Nevertheless, I hope the application is useful for you.
