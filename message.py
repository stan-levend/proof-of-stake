import enum
import json


class MessageType(enum.Enum):
    message = 1
    heartbeat = 2
    transaction = 3
    block = 4


PUBLIC_ENUMS = {
    'MesageType': MessageType,
    # ...
}

class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) in PUBLIC_ENUMS.values():
            return {"__enum__": str(obj)}
        return json.JSONEncoder.default(self, obj)

def as_enum(d):
    if "__enum__" in d:
        name, member = d["__enum__"].split(".")
        return getattr(PUBLIC_ENUMS[name], member)
    else:
        return d


class Message():
    def __init__(self, host, port, type: MessageType, data: list) -> None:
        self.host = host
        self.port = port
        self.type = type
        self.data = data