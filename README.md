# PythonChat
Python-based chat server and client

This is a very simple chat server and client (still a work in progress). The server just waits for incoming connections and
farms out messages to the clients.

The client is a simple window for displaying what people type from the different connected clients. It gives a simple textbox
for entering a new message.

I am still working on the robustness of shutting down cleanly and making sure that I detect disconnects well.
