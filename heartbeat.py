import threading
import time
from managers import encode

from message import Message, MessageType

# from peer import Peer2PeerNode

class Heartbeat():
    def __init__(self, node):
        self.node = node
        self.thread = None
        self.terminate_flag = threading.Event()

    def perform_heartbeat(self):
        while not self.terminate_flag.is_set():
            time.sleep(1)
            print(f"Performing heartbeat on {self.node.host}:{self.node.port}")
            connections = self.node.node_data_manager.connections
            if connections:
                message = Message(self.node.host, self.node.port,
                                  MessageType.heartbeat,
                                  data=self.node.node_data_manager.connections)
                messageJSONData = encode(message)
                self.node.send_to_nodes(messageJSONData)

            try: time.sleep(9)
            except: continue

    def start(self):
        self.thread = threading.Thread(target=self.perform_heartbeat).start()

    def stop(self):
        self.terminate_flag.set()

