import time

class Transaction():
    def __init__(self, node_id, data) -> None:
        self.node_id = node_id
        self.data = data
        self.timestamp = time.time()


