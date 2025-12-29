from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, asdict
from bson.objectid import ObjectId


@dataclass
class ChatMessage:
    """Chat message schema"""

    email: str
    file_name: str
    question: str
    answer: str
    created_at: datetime = None
    shared_with: Optional[List[str]] = None
    shared_in_group: Optional[List[str]] = None
    favorite: bool = False
    _id: Optional[ObjectId] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self):
        """Convert to dictionary for MongoDB"""
        data = asdict(self)
        data = {k: v for k, v in data.items() if v is not None}
        return data


@dataclass
class Group:
    """Group schema"""

    group_admin: str
    group_name: str
    members: List[str]
    created_at: datetime = None
    shared_qa_count: int = 0
    _id: Optional[ObjectId] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self):
        """Convert to dictionary for MongoDB"""
        data = asdict(self)
        data = {k: v for k, v in data.items() if v is not None}
        return data


@dataclass
class User:
    """User schema"""

    email: str
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class FileMetadata:
    """File metadata"""

    file_name: str
    file_type: str
    upload_time: datetime = None
    size_mb: float = 0.0

    def __post_init__(self):
        if self.upload_time is None:
            self.upload_time = datetime.now()
