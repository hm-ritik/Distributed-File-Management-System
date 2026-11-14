
from abc import ABC, abstractmethod


class StorageBase(ABC):

    @abstractmethod
    def upload(self,key: str,data: bytes,content_type: str ) -> None:
        pass

    @abstractmethod
    def download(self, key: str) -> bytes:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass
