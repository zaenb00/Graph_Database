# graph_entities.py

class Node:
    def __init__(self, id, labels=None, properties=None):
        self.id = id
        self.labels = labels or []
        self.properties = properties or {}

    def to_dict(self):
        return {
            "id": self.id,
            "labels": self.labels,
            "properties": self.properties
        }

    @staticmethod
    def from_dict(data):
        return Node(data["id"], data.get("labels", []), data.get("properties", {}))


class Relationship:
    def __init__(self, id, start_node, end_node, rel_type, properties=None):
        self.id = id
        self.start_node = start_node
        self.end_node = end_node
        self.rel_type = rel_type
        self.properties = properties or {}

    def to_dict(self):
        return {
            "id": self.id,
            "start_node": self.start_node,
            "end_node": self.end_node,
            "type": self.rel_type,
            "properties": self.properties
        }

    @staticmethod
    def from_dict(data):
        return Relationship(
            data["id"],
            data["start_node"],
            data["end_node"],
            data["type"],
            data.get("properties", {})
        )
