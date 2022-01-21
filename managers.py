import hashlib
import json
import threading
import time

class NodeDataManager():
    def __init__(self, host, port) -> None:
        self.host = host
        self.port = port

        self._connections_lock = threading.Lock()
        self._transactions_lock = threading.Lock()
        self._blockchain_lock = threading.Lock()

        self._connections = []
        self._transactions = []
        self.__load_transactions()
        self._blockchain = []
        self.__load_blocks()

    def __load_connections(self):
        try:
            with open(f"connections/{self.host}:{self.port}", "r+") as file:
                lines = file.readlines()
                self._connections = [line.strip() for line in lines]
        except:
            with open(f"connections/{self.host}:{self.port}", "w+") as file:
                pass

    @property
    def connections(self):
        with self._connections_lock:
            self.__load_connections()
            return self._connections

    @connections.setter
    def connections(self, connections) -> None:
        with self._connections_lock:
            with open(f"connections/{self.host}:{self.port}", "w+") as file:
                for c in connections:
                    file.write(c + "\n")

    def __load_transactions(self):
        try:
            with open(f"transactions/{self.host}:{self.port}.json", "r+") as json_file:
                self._transactions = json.load(json_file)
        except:
            with open(f"transactions/{self.host}:{self.port}.json", "w+") as json_file:
                json_file.write('[]')

    @property
    def transactions(self):
        with self._transactions_lock:
            self.__load_transactions()
            # return sorted(self._transactions, key=lambda t:t['timestamp']) if self._transactions else self._transactions #TODO
            return self._transactions


    @transactions.setter
    def transactions(self, list_of_t) -> None:
        with self._transactions_lock:
            with open(f"transactions/{self.host}:{self.port}.json", "w+") as json_file:
                json.dump(list_of_t, json_file)

    def transactions_append(self, element):
        with self._transactions_lock:
            transactions = self.transactions
            transactions.append(element)
            with open(f"transactions/{self.host}:{self.port}.json", "w+") as json_file:
                json.dump(transactions, json_file)


    def __load_blocks(self):
        try:
            with open(f"blockchain/{self.host}:{self.port}.json", "r+") as json_file:
                self._blockchain = json.load(json_file)
        except:
            with open(f"blockchain/{self.host}:{self.port}.json", "w+") as json_file:
                genesis_block = {
                    "index" : 0,
                    "timestamp" : 0,
                    "data" : None,
                    "prev_block_hash" : 0,
                }
                genesis_block_string = json.dumps(genesis_block)
                genesis_block["hash"] = hashlib.sha256(genesis_block_string.encode('utf-8')).hexdigest()
                json.dump([genesis_block], json_file)
                self._blockchain = [genesis_block]

    @property
    def blockchain(self):
        with self._blockchain_lock:
            self.__load_blocks()
            time.sleep(0.01)
            return self._blockchain

    @blockchain.setter
    def blockchain(self, blockchain) -> None:
        with self._blockchain_lock:
            with open(f"blockchain/{self.host}:{self.port}.json", "w+") as json_file:
                json.dump(blockchain, json_file)


    def blockchain_append(self, element) -> None:
        with self._blockchain_lock:
            blockchain = self._blockchain
            blockchain.append(element)
            with open(f"blockchain/{self.host}:{self.port}.json", "w+") as json_file:
                json.dump(blockchain, json_file)
