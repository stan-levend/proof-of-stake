import json
import threading

import jsonpickle

from message import EnumEncoder, as_enum


class NodeDataManager():
    def __init__(self, hostname, port) -> None:
        self.hostname = hostname
        self.port = port
        self._connections_lock = threading.Lock()
        self._transactions_lock = threading.Lock()
        self._blockchain_lock = threading.Lock()
        self._connections = self.__get_connections()
        self._transactions = self.__get_transactions()
        self._blockchain = self.__get_blockchain()

    def __get_connections(self) -> list:
        # with self._connections_lock:
            try:
                with open(f"connections/{self.hostname}:{self.port}", "r+") as file:
                    lines = file.readlines()
                    return [line.strip() for line in lines]
            except:
                with open(f"connections/{self.hostname}:{self.port}", "w+") as file:
                    return []

    @property
    def connections(self):
        with self._connections_lock:
            return self._connections

    @connections.setter
    def connections(self, connections) -> None:
        with self._connections_lock:
            with open(f"connections/{self.hostname}:{self.port}", "w+") as file:
                for c in connections:
                    file.write(c + "\n")
                self.__get_connections()


    def __get_transactions(self) -> list:
        with self._transactions_lock:
            try:
                with open(f"transactions/{self.hostname}:{self.port}.json", "r+") as json_file:
                    return json.load(json_file)
            except:
                with open(f"transactions/{self.hostname}:{self.port}.json", "w+") as json_file:
                    return []

    @property
    def transactions(self):
        with self._transactions_lock:
            return self._transactions

    @transactions.setter
    def transactions(self, transactions) -> None:
        with self._transactions_lock:
            with open(f"transactions/{self.hostname}:{self.port}.json", "w+") as json_file:
                json.dump(transactions, json_file)


    def __get_blockchain(self) -> list:
        with self._blockchain_lock:
            try:
                with open(f"blockchain/{self.hostname}:{self.port}.json", "r+") as json_file:
                    return json.load(json_file)
            except:
                with open(f"blockchain/{self.hostname}:{self.port}.json", "w+") as json_file:
                    return []

    @property
    def blockchain(self):
        with self._blockchain_lock:
            return self._blockchain

    @blockchain.setter
    def blockchain(self, blocks) -> None:
        with self._blockchain_lock:
            with open(f"blockchain/{self.hostname}:{self.port}.json", "w+") as json_file:
                json.dump(blocks, json_file)


def encode(object) -> str:
    JSONstring = jsonpickle.encode(object)
    return json.dumps(JSONstring, cls=EnumEncoder)

def decode(data) -> any:
    # JSONstring = json.loads(data, object_hook=as_enum)
    return jsonpickle.loads(data)