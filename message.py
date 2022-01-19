import enum
import json
import jsonpickle


class MessageType(enum.Enum):
    MESSAGE = 1
    HEARTBEAT = 2
    TRANSACTION = 3
    BLOCK = 4
    QUERY_B = 5
    SEND_B = 6
    QUERY_T_B = 7
    SEND_T_B = 8


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
    def __init__(self, type: MessageType, data) -> None:
        self.type = type
        self.data = data


def encode_message(object) -> str:
    JSONstring = jsonpickle.encode(object)
    return json.dumps(JSONstring, cls=EnumEncoder)

def decode_message(data) -> any:
    # JSONstring = json.loads(data, object_hook=as_enum)
    return jsonpickle.loads(data)