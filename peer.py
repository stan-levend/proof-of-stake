import hashlib
import json
import socket
import threading
import time

from p2pnetwork.node import Node
from p2pnetwork.nodeconnection import NodeConnection
from blockchain import Transaction

from heartbeat import Heartbeat
from managers import NodeDataManager
from message import Message, MessageType, decode_message, encode_message
from node_interface import NodeInputInterface

HOST = "127.0.0.1"

T_THRESHOLD = 3

# class MyOwnNodeConnection (NodeConnection):
#     # Python class constructor
#      def __init__(self, main_node, sock, id, host, port):
#         super(MyOwnNodeConnection, self).__init__(main_node, sock, id, host, port)


class Peer2PeerNode (Node):
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        id = f"{host}:{port}"
        self.nodes_outbound_mapper = {}
        super(Peer2PeerNode, self).__init__(host, port, id, callback, max_connections)
        print("Peer2PeerNode: Started")
        self.node_data_manager = NodeDataManager(HOST, port)
        self.connect_neighbors()

        self.heartbeat = Heartbeat(self)
        self.heartbeat.start()

        self.input = NodeInputInterface(self)
        self.input.start()

    @property
    def name(self):
        return f"{self.host}:{self.port}"

    def __str__(self):
        return f'{self.host}:{self.port}'

    @property
    def all_peers_in_network(self):
        connections = self.node_data_manager.connections
        return [self.name] + connections

    def outbound_node_connected(self, node):
        print("outbound_node_connected (" + self.id + "): " + node.id)
        print(self.nodes_outbound)
        connections = self.node_data_manager.connections
        if f"{node.host}:{node.port}" not in connections:
            connections.append(f"{node.host}:{node.port}")
            self.node_data_manager.connections = connections

    def node_message(self, node, data):
        print("node_message (" + self.id + ") from " + node.id + node.host + str(node.port) + ": " + str(data))
        message = decode_message(data)

        if message.type == MessageType.heartbeat:
            # print(message.data)
            connections = self.node_data_manager.connections
            inactive_connections = []
            message_sender = f"{message.host}:{message.port}"
            if message_sender not in connections:
                connections.append(message_sender)
                # self.connect_with_node(message.host, int(message.port))
            for c in message.data:
                if c != self.name and c not in connections:
                    connections.append(c)
                    host, port = c.split(":")
                    result = self.connect_with_node(host, int(port))
                    if result is False:
                        inactive_connections.append(c)
                    # merge lists but also connect to the nodes
            if inactive_connections:
                for c in inactive_connections:
                    connections.remove(c)
            self.node_data_manager.connections = connections

        if message.type == MessageType.transaction:
            print(message.data)

    def inbound_node_disconnected(self, node):
        print("inbound_node_disconnected: (" + self.id + "): " + node.id)

    def outbound_node_disconnected(self, node):
        print("outbound_node_disconnected: (" + self.id + "): " + node.id)

    def node_disconnect_with_outbound_node(self, node):
        print("node wants to disconnect with oher outbound node: (" + self.id + "): " + node.id)

    def node_request_to_stop(self):
        print("node is requested to stop (" + self.id + "): ")

    #  def create_new_connection(self, connection, id, host, port):
    #     return MyOwnNodeConnection(self, connection, id, host, port)

    def connect_neighbors(self):
        connections = self.node_data_manager.connections
        inactive_connections = []
        for c in connections:
            host, port = c.split(":")
            result = self.connect_with_node(host, int(port))
            if result is False:
                inactive_connections.append(c)

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
        # new_transaction = Transaction(self.id, data)

        transactions = self.node_data_manager.transactions
        transactions.append(new_transaction)
        self.node_data_manager.transactions = transactions

        if len(transactions) == T_THRESHOLD:
            blockchain = self.node_data_manager.blockchain
            new_block = {
                "index": blockchain[-1].index + 1,
                "timestamp": time.time(),
                "data": transactions,
                "prev_block_hash": blockchain[-1].hash
            }
            new_block_string = json.dumps(new_block)
            new_block["hash"] = hashlib.sha256(new_block_string.encode('utf-8')).hexdigest()

        thread = threading.Thread(target=self.send_to_nodes, args=(new_transaction))
        thread.start()
        thread.join()

        if len(transactions) == T_THRESHOLD:
            pass
        else:
            #save to file and send to all nodes
            transactions_string = json.dumps(transactions)
            hash = hashlib.sha256(transactions_string.encode())
            pass

        # self.send_to_nodes(new_transaction)


    def send_to_nodes(self, data, exclude=[]):
        for n in self.nodes_outbound:
            self.send_to_node(n, data)

        # time.sleep(0.5)
        connections = self.node_data_manager.connections
        nodes_outbound_map = [f"{n.host}:{n.port}" for n in self.nodes_outbound]
        inactive_connections = [n for n in connections if n not in nodes_outbound_map]

        if inactive_connections:
            for c in inactive_connections:
                connections.remove(c)
            self.node_data_manager.connections = connections


        # inactive_connections = []
        # connections = self.node_data_manager.connections
        # for c in connections:
        #     if c in self.nodes_outbound_mapper:
        #         result = self.send_to_node(self.nodes_outbound_mapper[c], data)
        #         if result is False:
        #             inactive_connections.append(c)
        #             del self.nodes_outbound_mapper[c]
        #     else: inactive_connections.append(c)

        # for c in inactive_connections:
        #     connections.remove(c)

        # if inactive_connections:
        #     self.node_data_manager.connections = connections

        # inactive_connections = []
        # for n in self.nodes_outbound:
        #     result = self.send_to_node(n, data)
        #     if result is False:
        #         inactive_connections.append(f"{n.host}:{n.port}")

        # connections = [f"{n.host}:{n.port}" for n in self.nodes_outbound]
        # neighbors = self.node_data_manager.connections
        # inactive_connections.extend([n for n in neighbors if n not in connections])

        # for c in inactive_connections:
        #     neighbors.remove(c)

        # if inactive_connections:
        #     self.node_data_manager.connections = neighbors


    def send_to_node(self, n, data):
        #prepisat na mojich neighbors, namapovat na nodeconnections
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

            thread_client = self.create_new_connection(sock, connected_node_id, host, port)
            thread_client.start()

            self.nodes_outbound.append(thread_client)
            # self.nodes_outbound_mapper[f"{thread_client.host}:{thread_client.port}"] = thread_client
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
                    thread_client = self.create_new_connection(connection, connected_node_id, client_host, int(client_port))
                    thread_client.start()

                    # self.nodes_inbound.append(thread_client)
                    self.nodes_outbound.append(thread_client)
                    # self.nodes_outbound_mapper[f"{thread_client.host}:{thread_client.port}"] = thread_client
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


if __name__ == "__main__":
    # PORT = random.randint(1024, 49151)
    try: PORT = int(input(f"{HOST}, Input port: "))
    except: raise TypeError("Invalid type: Input integer from interval (1024 - 49151)")
    if PORT not in range(1024, 49151+1): raise ValueError("Invalid port: Choose from interval (1024 - 49151)")
    node = Peer2PeerNode(HOST, PORT)
    time.sleep(0.3)
    node.start()