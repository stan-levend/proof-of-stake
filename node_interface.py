import json
import threading
import time

HOSTNAME = "127.0.0.1"


class NodeInputInterface():
    def __init__(self, node):
        self.node = node
        self.thread = None
        self.terminate_flag = threading.Event()

    def scan_input(self):
        while not self.terminate_flag.is_set():
            try: cli_input = input().split()
            except:
                print("""Invalid input - press "h" for Help""")
                continue
            if not cli_input:
                print("""Invalid input - press "h" for Help""")
                continue

            if cli_input[0] == "c":
                print("connect")

                try: PORT = int(cli_input[1])
                except Exception:
                    print("Invalid port: Choose from interval (1024 - 49151)")
                    continue
                # threading.Thread(target=self.connect_with_node, args=(HOSTNAME, PORT))
                self.node.connect_with_node(HOSTNAME, PORT)

            elif cli_input[0] == "gt":
                print("generate transaction")

                if len(cli_input) > 2:
                    cli_input.pop(0)
                    data = ' '.join(cli_input)
                else:
                    try: data = cli_input[1]
                    except Exception:
                        print("Invalid value for generating transaction.")
                        continue
                self.node.generate_transaction(data)

            elif cli_input[0] == "t":
                print("transaction")
                t = self.node.node_data_manager.transactions
                print(json.dumps(t, indent=4))

            elif cli_input[0] == "p":
                print(self.node.nodes_outbound)
                print(*self.node.all_peers_in_network, sep=", ")

            # "d"  - Disconnect from the network and reset all neighbors of the node (not implemented)
            # elif cli_input[0] == "d":
            #     self.node.disconnect_with_node()

            elif cli_input[0] == "q":
                self.stop()

            elif cli_input[0] == "h":
                print("""
                    "c <port>" - Connect to a node
                    "q"  - Exit
                    "b"  - List blockchain of the node
                    "t"  - List transactions of the node
                    "gt <data>" - Generate new transaction with given data
                    "m"  - Send message
                    "p"  - List peers in the P2P network
                """)
            else:
                print("""Invalid input - press "h" for Help""")

        self.node.stop()
        self.node.heartbeat.stop()
        self.stop()

    def start(self):
        self.thread = threading.Thread(target=self.scan_input).start()

    def stop(self):
        self.terminate_flag.set()
