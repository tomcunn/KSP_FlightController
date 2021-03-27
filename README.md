# KSP_FlightController

Custom KSP flight controller to work with Kerbal Space Program. Lots of I/O to work with here.

# Usage

To interface to the game, a KRPC server is used. A mod has to be installed to the game to access to the KRPC server. Once the game is started, the KRPC server must be started. After started the server, a local python client connects to the game. Then the wireless controller connects to the local python client. 

# Issues

Lots

* The current network connection between the local python client, and the controller uses a TCP connection which is prone to drop out after some time.
* The current flow is only one direction, which is from the controller to the game. The game is currently not sending data back to the controller. This is possible, I just haven't done it yet.
* I would look into some gamepad emulation for future designs, because the interface is more basic, connectionless, and most likely more robust. 
