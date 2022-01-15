import time

class Transaction():
    def __init__(self, node_id, data) -> None:
        self.node_id = node_id
        self.data = data
        self.timestamp = time.time()


class Block():
    def __init__(self, index, timestamp, data, prev_block_hash, hash) -> None:
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.prev_block_hash = prev_block_hash
        self.hash = hash