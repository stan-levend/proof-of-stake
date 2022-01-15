import hashlib
import json
import threading


class NodeDataManager():
    def __init__(self, hostname, port) -> None:
        self.hostname = hostname
        self.port = port

        self._connections_lock = threading.Lock()
        self._connections = self.__load_connections()

        self._transactions_lock = threading.Lock()
        self._transactions = self.__load_transactions()

        self._blockchain_lock = threading.Lock()
        self.__load_block()
        # self._blockchain = self.__load_blockchain()


    def __load_connections(self) -> list:
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


    def __load_transactions(self) -> list:
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
    def transactions(self, list_of_t) -> None:
        with self._transactions_lock:
            with open(f"transactions/{self.hostname}:{self.port}.json", "w+") as json_file:
                json.dump(list_of_t, json_file)


    def __load_block(self):
        with self._blockchain_lock:

            try:
                with open(f"blockchain/{self.hostname}:{self.port}.json", "r+") as json_file:
                    return json.load(json_file)
            except:
                with open(f"blockchain/{self.hostname}:{self.port}.json", "w+") as json_file:
                    genesis_block = {
                        "index" : 0,
                        "timestamp" : 0,
                        "data" : None,
                        "prev_hash" : 0,
                    }
                    genesis_block_string = json.dumps(genesis_block)
                    genesis_block["hash"] = hashlib.sha256(genesis_block_string.encode('utf-8')).hexdigest()
                    json.dump(genesis_block, json_file)
                    return [genesis_block]

    @property
    def blockchain(self):
        with self._blockchain_lock:
            return self._blockchain

    @blockchain.setter
    def blockchain(self, blocks) -> None:
        with self._blockchain_lock:
            with open(f"blockchain/{self.hostname}:{self.port}.json", "w+") as json_file:
                json.dump(blocks, json_file)