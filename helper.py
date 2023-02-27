from enum import Enum
from abc import ABC, abstractmethod
from typing import List

class MessageType(Enum):
    unknown = 0
    EcgSamples = 1
    FileCommand = 2
    FileInfo = 3
    FileStatus = 4
    MiscInfo = 5
    SensorMode = 6
    Units = 7

class CortriumMessage(ABC):
    def __init__(self, message_type: MessageType, raw_data_bytes: bytearray()):
        self.message_type = message_type
        self.raw_data_bytes = raw_data_bytes

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.__serialize_fields__ = ["message_type", "raw_data_bytes"]

    def __getstate__(self):
        return {name: getattr(self, name) for name in self.__serialize_fields__}

    def __setstate__(self, state):
        for name, value in state.items():
            setattr(self, name, value)

    def pack_data_to_bytes(self):
        raise NotImplementedError("Not supported for message type: " + str(self.message_type))

    @classmethod
    def from_bytes(cls, bytes_: bytes):
        raise NotImplementedError("Not supported for message type: " + str(cls.message_type))

    def __str__(self):
        return f"{self.__class__.__name__}({self.message_type}, {self.raw_data_bytes})"