import hashlib
import json
import socket
import threading
import time

from p2pnetwork.node import Node

from heartbeat import Heartbeat
from managers import NodeDataManager
from message import Message, MessageType, decode_message, encode_message
from node_interface import NodeInputInterface

HOST = "127.0.0.1"
T_THRESHOLD = 3


class Peer2PeerNode (Node):
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        id = f"{host}:{port}"
        super(Peer2PeerNode, self).__init__(host, port, id, callback, max_connections)
        print(f"Node {self.name} started")

        self.node_data_manager = NodeDataManager(HOST, port)
        self.connect_neighbors()

        self.heartbeat = Heartbeat(self)
        self.heartbeat.start()

        self.input = NodeInputInterface(self)
        self.input.start()

        self.coordinator = None

    @property
    def name(self):
        return f"{self.host}:{self.port}"

    @property
    def all_peers_in_network(self):
        connections = self.node_data_manager.connections
        return [self.name] + connections

    def outbound_node_connected(self, node):
        # print("outbound_node_connected (" + self.id + "): " + node.id)
        # print(self.nodes_outbound)
        connections = self.node_data_manager.connections
        if f"{node.host}:{node.port}" not in connections:
            connections.append(f"{node.host}:{node.port}")
            self.node_data_manager.connections = connections

    def node_message(self, node, data):
        message = decode_message(data)

        if message.type == MessageType.HEARTBEAT:
            # print(f"node_message received ({self.id}) from {node.host}:{node.port}: data - {str(message.data)}")
            connections = self.node_data_manager.connections
            inactive_connections = []
            message_sender = f"{node.host}:{node.port}"
            if message_sender not in connections:
                connections.append(message_sender)
            for c in message.data:
                if c != self.name and c not in connections:
                    connections.append(c)
                    host, port = c.split(":")
                    result = self.connect_with_node(host, int(port))
                    if result is False:
                        inactive_connections.append(c)
            if inactive_connections:
                for c in inactive_connections:
                    connections.remove(c)
            self.node_data_manager.connections = connections

            ports = [c.split(':')[1] for c in connections]
            ports.append(self.port)
            ports = list(map(int, ports))
            self.coordinator = f"{self.host}:{max(ports)}"

        elif message.type == MessageType.TRANSACTION:
            print(f"node_message received ({self.id}) from {node.host, node.port}: TRANSACTION")
            self.node_data_manager.transactions_append(message.data)

            time.sleep(0.03)
            self.perform_block_creator_logic()

        elif message.type == MessageType.BLOCK:
            print(f"node_message received ({self.id}) from {node.host}:{node.port}: BLOCK")
            is_valid = self.validate_block(message.data)
            if is_valid:
                self.node_data_manager.blockchain_append(message.data)
            else:
                message = Message(MessageType.QUERY_B, None)

                self.send_to_nodes(encode_message(message)) #TODO do ktorych nodes?

        elif message.type == MessageType.QUERY_B:
            data = self.node_data_manager.blockchain
            message = Message(MessageType.SEND_B, data)
            self.send_to_node(node, encode_message(message))

        elif message.type == MessageType.SEND_B:
            print(f"node_message received ({self.id}) from {node.host}:{node.port}: QUERY FOR BLOCKCHAIN AND TRANSACTIONS")
            self.node_data_manager.blockchain = message.data.get("blockchain", [])

        elif message.type == MessageType.QUERY_T_B:
            print(f"node_message received ({self.id}) from {node.host}:{node.port}: QUERY FOR BLOCKCHAIN AND TRANSACTIONS")
            data = {
                "transactions": self.node_data_manager.transactions,
                "blockchain": self.node_data_manager.blockchain
            }
            # time.sleep(0.3)
            message = Message(MessageType.SEND_T_B, data)
            self.send_to_node(node, encode_message(message))

        elif message.type == MessageType.SEND_T_B:
            print(f"node_message received ({self.id}) from {node.port}:{node.host}: SEND BLOCKCHAIN AND TRANSACTIONS")
            self.node_data_manager.transactions = message.data.get("transactions", [])
            self.node_data_manager.blockchain = message.data.get("blockchain", [])

    def connect_neighbors(self):
        connections = self.node_data_manager.connections
        inactive_connections = []
        for c in connections:
            host, port = c.split(":")
            success = self.connect_with_node(host, int(port))
            if success is False:
                inactive_connections.append(c)
            else:
                self.query_blockchain(host, int(port)) #TODO not sure but probably right

        for c in inactive_connections:
            connections.remove(c)

        if inactive_connections:
            self.node_data_manager.connections = connections

    def generate_transaction(self, data):
        new_transaction = {
            "node_id": self.id,
            "data": data,
            "timestamp": time.time()
        }

        self.node_data_manager.transactions_append(new_transaction)

        transaction_message = Message(MessageType.TRANSACTION, new_transaction)
        self.send_to_nodes(encode_message(transaction_message))

        time.sleep(0.3)
        self.perform_block_creator_logic()


    def perform_block_creator_logic(self):
        transactions = self.node_data_manager.transactions
        sorted_transactions = sorted(transactions, key=lambda t:t['timestamp'])
        if len(sorted_transactions) == T_THRESHOLD:
            # min_timestamp_transaction = min(transactions, key=lambda t:t["timestamp"])
            available_transaction_nodes = [t for t in sorted_transactions if t.get("node_id") in self.node_data_manager.connections]
            if available_transaction_nodes:
                for t in sorted_transactions:
                    if t.get("node_id") == self.id:
                        new_block = self.generate_new_block()
                        block_message = Message(MessageType.BLOCK, new_block)
                        self.send_to_nodes(encode_message(block_message))
                        self.node_data_manager.blockchain_append(new_block)
                        break
                    elif t.get("node_id") in self.node_data_manager.connections: #TODO
                        break
            elif self.coordinator == self.name:
                new_block = self.generate_new_block()
                block_message = Message(MessageType.BLOCK, new_block)
                self.send_to_nodes(encode_message(block_message))
                self.node_data_manager.blockchain_append(new_block)

            self.node_data_manager.transactions = []


    def generate_new_block(self):
        blockchain = self.node_data_manager.blockchain
        transactions = self.node_data_manager.transactions

        new_block = {
            "index": blockchain[-1].get("index") + 1,
            "timestamp": time.time(),
            "data": transactions,
            "prev_block_hash": blockchain[-1].get("hash")
        }
        new_block_string = json.dumps(new_block)
        new_block["hash"] = hashlib.sha256(new_block_string.encode('utf-8')).hexdigest()
        return new_block

    def validate_block(self, block):
        blockchain = self.node_data_manager.blockchain
        #Validity of the index
        try:
            if blockchain[-1].get("index") + 1 != block.get("index") :
                return False
            #Validity of hash value of the current block with previous hash value of the next block
            if blockchain[-1].get("hash") != block.get("prev_block_hash"):
                return False
            for b1, b2 in zip(blockchain, blockchain[1:]):
                if b1.get("hash") != b2.get("prev_block_hash"):
                    return False
            #Validity of hash value of the new block
            new_block_hash = block.pop("hash")
            new_block_string = json.dumps(block)
            if new_block_hash != hashlib.sha256(new_block_string.encode('utf-8')).hexdigest():
                return False
            block["hash"] = new_block_hash
        except: return False
        return True

    def query_blockchain(self, host, port):
        node = next((n for n in self.nodes_outbound if n.host == host and n.port == port), None)
        if node:
            message = Message(MessageType.QUERY_T_B, data=None)
            self.send_to_node(node, encode_message(message))


    def send_to_nodes(self, data, exclude=[]):
        for n in self.nodes_outbound:
            self.send_to_node(n, data)

        connections = self.node_data_manager.connections
        nodes_outbound_map = [f"{n.host}:{n.port}" for n in self.nodes_outbound]
        inactive_connections = [n for n in connections if n not in nodes_outbound_map]

        if inactive_connections:
            for c in inactive_connections:
                connections.remove(c)
            self.node_data_manager.connections = connections


    def send_to_node(self, n, data):
        if n in self.nodes_outbound:
            try:
                n.send(data)
            except:
                n.stop()
                self.nodes_outbound.remove(n)
                return False
        else:
            print("Node send_to_node: Could not send the data, node is not found!")
            return False


    def connect_with_node(self, host, port, reconnect=False):
        if host == self.host and port == self.port:
            print("connect_with_node: Cannot connect with yourself!!")
            return False

        for node in self.nodes_outbound:
            if node.host == host and node.port == port:
                print("connect_with_node: Already connected with this node (" + node.id + ").")
                return True

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("connecting to %s port %s" % (host, port))
            sock.connect((host, port))

            # Basic information exchange (not secure) of the id's of the nodes!
            sock.send(self.id.encode('utf-8')) # Send my id to the connected node!
            connected_node_id = sock.recv(4096).decode('utf-8') # When a node is connected, it sends it id!

            # Fix bug: Cannot connect with nodes that are already connected with us!
            for node in self.nodes_inbound:
                if node.host == host and node.id == connected_node_id:
                    print("connect_with_node: This node (" + node.id + ") is already connected with us.")
                    return True

            ports = [n.port for n in self.nodes_outbound]
            if port not in ports:
                thread_client = self.create_new_connection(sock, connected_node_id, host, port)
                thread_client.start()

                self.nodes_outbound.append(thread_client)
                self.outbound_node_connected(thread_client)


        except Exception as e:
            print("TcpServer.connect_with_node: Could not connect with node. (" + str(e) + ")")
            return False


    def run(self):
        while not self.terminate_flag.is_set():  # Check whether the thread needs to be closed
            try:
                connection, client_address = self.sock.accept()

                self.debug_print("Total inbound connections:" + str(len(self.nodes_inbound)))
                # When the maximum connections is reached, it disconnects the connection
                if self.max_connections == 0 or len(self.nodes_inbound) < self.max_connections:

                    # Basic information exchange (not secure) of the id's of the nodes!
                    connected_node_id = connection.recv(4096).decode('utf-8') # When a node is connected, it sends it id!
                    connection.send(self.id.encode('utf-8')) # Send my id to the connected node!

                    client_host, client_port = connected_node_id.split(":")

                    ports = [n.port for n in self.nodes_outbound]
                    if client_port not in ports:
                        thread_client = self.create_new_connection(connection, connected_node_id, client_host, int(client_port))
                        thread_client.start()

                        self.nodes_outbound.append(thread_client)
                        # self.outbound_node_connected(thread_client)

                else:
                    connection.close()

            except socket.timeout:
                pass

            except Exception as e:
                raise e

            self.reconnect_nodes()

            time.sleep(0.01)

        print("Node stopping...")
        for t in self.nodes_inbound:
            t.stop()

        for t in self.nodes_outbound:
            t.stop()

        time.sleep(1)

        for t in self.nodes_inbound:
            t.join()

        for t in self.nodes_outbound:
            t.join()

        self.sock.settimeout(None)
        self.sock.close()
        print("Node stopped")

    def inbound_node_disconnected(self, node):
        # print("inbound_node_disconnected: (" + self.id + "): " + node.id)
        pass

    def outbound_node_disconnected(self, node):
        # print("outbound_node_disconnected: (" + self.id + "): " + node.id)
        pass

    def node_disconnect_with_outbound_node(self, node):
        # print("node wants to disconnect with oher outbound node: (" + self.id + "): " + node.id)
        pass

    def node_request_to_stop(self):
        # print("node is requested to stop (" + self.id + "): ")
        pass


if __name__ == "__main__":
    # PORT = random.randint(1024, 49151)
    try: PORT = int(input(f"{HOST}, Input port: "))
    except: raise TypeError("Invalid type: Input integer from interval (1024 - 49151)")
    if PORT not in range(1024, 49151+1): raise ValueError("Invalid port: Choose from interval (1024 - 49151)")
    node = Peer2PeerNode(HOST, PORT)
    time.sleep(0.3)
    node.start()