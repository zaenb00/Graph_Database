import os
import json
from graph_entities import Node, Relationship

class GraphStorage:
    def __init__(self, db_path):
        self.db_path = db_path
        self.nodes_file = os.path.join(db_path, "nodes.json")
        self.rels_file = os.path.join(db_path, "relationships.json")

    def load_nodes(self):
        if not os.path.exists(self.nodes_file):
            return []
        with open(self.nodes_file) as f:
            data = json.load(f)
        return [Node.from_dict(d) for d in data]

    def save_nodes(self, nodes):
        with open(self.nodes_file, 'w') as f:
            json.dump([n.to_dict() for n in nodes], f, indent=2)

    def load_relationships(self):
        if not os.path.exists(self.rels_file):
            return []
        with open(self.rels_file) as f:
            data = json.load(f)
        return [Relationship.from_dict(d) for d in data]

    def save_relationships(self, rels):
        with open(self.rels_file, 'w') as f:
            json.dump([r.to_dict() for r in rels], f, indent=2)
