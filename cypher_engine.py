import re
import uuid
import os
import json
from graph_storage import GraphStorage
from graph_entities import Node, Relationship

node_pattern = re.compile(r"CREATE \((\w+):(\w+) \{([^}]+)\}\)")
match_pattern_with_props = re.compile(r"MATCH \((\w+):(\w+) \{([^}]+)\}\) RETURN \w+")
match_pattern_simple = re.compile(r"MATCH \((\w+):(\w+)\) RETURN \w+")
rel_create_pattern = re.compile(
    r"CREATE \((\w+):(\w+)(?: \{([^}]+)\})?\)"  # left node (3 groups)
    r"-\[:(\w+)(?: \{([^}]+)\})?\]->"           # relationship type (1 group) + rel props (optional, 1 group)
    r"\((\w+):(\w+)(?: \{([^}]+)\})?\)"        # right node (3 groups)
)
match_relationship_pattern_directed = re.compile(r"MATCH\s+\((\w+):(\w+)\)-\[:(\w+)\]->\((\w+):(\w+)\)\s+RETURN\s+\w+,\s*\w+")
match_relationship_pattern_bidirectional = re.compile(r"MATCH\s+\((\w+):(\w+)\)<-\[:(\w+)\]-\((\w+):(\w+)\)\s+RETURN\s+\w+,\s*\w+")
match_relationship_pattern_undirected = re.compile(r"MATCH\s+\((\w+):(\w+)\)-\[:(\w+)\]-\((\w+):(\w+)\)\s+RETURN\s+\w+,\s*\w+")
match_pattern_with_where = re.compile(
    r"MATCH\s+\((\w+):(\w+)\)\s+WHERE\s+(\w+)\.(\w+)\s*([=<>!]=?)\s*(\"[^\"]+\"|\d+(?:\.\d+)?)\s+RETURN\s+\w+"
)
match_all_pattern = re.compile(r"MATCH\s*\(\w+\)\s*RETURN\s*\w+")


def load_indexes(db_path):
    idx_file = os.path.join(db_path, "indexes.json")
    if os.path.exists(idx_file):
        with open(idx_file, "r") as f:
            return json.load(f)
    return {}

def save_indexes(db_path, indexes):
    idx_file = os.path.join(db_path, "indexes.json")
    with open(idx_file, "w") as f:
        json.dump(indexes, f, indent=2)

def build_index_for_label_prop(db_path, label, prop):
    storage = GraphStorage(db_path)
    nodes = storage.load_nodes()
    index = {}
    for node in nodes:
        if label in node.labels:
            value = node.properties.get(prop)
            if value is not None:
                index.setdefault(str(value), []).append(node.id)
    return index

def create_index(db_path, label, prop):
    index_path = os.path.join(db_path, "indexes.json")
    nodes_path = os.path.join(db_path, "nodes.json")

    # Load existing indexes or start fresh
    if os.path.exists(index_path):
        with open(index_path) as f:
            indexes = json.load(f)
    else:
        indexes = {}

    # Load nodes
    if os.path.exists(nodes_path):
        with open(nodes_path) as f:
            nodes = json.load(f)
    else:
        nodes = []

    # Initialize nested index structure
    if label not in indexes:
        indexes[label] = {}
    if prop not in indexes[label]:
        indexes[label][prop] = {}

    # Populate the index with property values
    for node in nodes:
        if label in node.get("labels", []):
            props = node.get("properties", {})
            node_id = node.get("id")
            value = props.get(prop)

            if value is not None:
                value_str = str(value)
                indexes[label][prop].setdefault(value_str, []).append(node_id)

    # Write back the updated index
    with open(index_path, "w") as f:
        json.dump(indexes, f, indent=2)

    print(f"Index created for :{label} on property '{prop}'")

def find_nodes_with_index(db_path, label, prop, value):
    indexes_path = os.path.join(db_path, "indexes.json")
    if not os.path.exists(indexes_path):
        return []

    with open(indexes_path, "r") as f:
        indexes = json.load(f)

    label_indexes = indexes.get(label, {})

    # Ensure label_indexes is a dict
    if not isinstance(label_indexes, dict):
        print(f"Invalid index format for label '{label}': Expected dict but got {type(label_indexes)}")
        return []

    prop_index = label_indexes.get(prop, {})

    if not isinstance(prop_index, dict):
        print(f"Invalid property index for prop '{prop}': Expected dict but got {type(prop_index)}")
        return []

    return prop_index.get(str(value), [])


def parse_properties(prop_str):
    props = {}
    for item in prop_str.split(','):
        key, value = item.split(':', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")  # Remove both " and '
        # Try to convert to int, float, or leave as string
        if value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
        else:
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass  # leave as string
        props[key] = value
    return props


def handle_create(query, db_path):
    storage = GraphStorage(db_path)
    nodes = storage.load_nodes()

    matches = node_pattern.findall(query)
    new_nodes = []

    for var, label, prop_str in matches:
        props = parse_properties(prop_str)
        existing_node = find_node(nodes, label, props)
        if existing_node:
            continue
        node_id = str(uuid.uuid4())
        new_node = Node(id=node_id, labels=[label], properties=props)
        nodes.append(new_node)
        new_nodes.append(new_node)

    storage.save_nodes(nodes)

    return {
        "message": "Node(s) created",
        "nodes": [n.to_dict() for n in new_nodes],
        "relationships": []
    }


def handle_match(query, db_path):
    storage = GraphStorage(db_path)
    nodes = storage.load_nodes()
    rels = storage.load_relationships()
    matched_nodes = []
    matched_rels = []

    # MATCH with WHERE clause
    match = match_pattern_with_where.match(query)
    if match:
        var, label, where_var, prop, operator, value = match.groups()
        if var != where_var:
            return {"error": "Variable mismatch in WHERE clause"}

        for node in nodes:
            if label in node.labels:
                node_val = node.properties.get(prop)
                if node_val is None:
                    continue

                # Try to compare as float if possible
                try:
                    node_val = float(node_val)
                    value = float(value)
                except ValueError:
                    node_val = str(node_val)
                    value = str(value)

                # Safe evaluation
                try:
                    if operator == '=':
                        cond = node_val == value
                    elif operator == '!=':
                        cond = node_val != value
                    elif operator == '>':
                        cond = node_val > value
                    elif operator == '<':
                        cond = node_val < value
                    elif operator == '>=':
                        cond = node_val >= value
                    elif operator == '<=':
                        cond = node_val <= value
                    else:
                        return {"error": "Unsupported operator in WHERE clause"}
                except:
                    cond = False

                if cond:
                    matched_nodes.append(node)

        return {
            "message": f"{len(matched_nodes)} nodes matched with WHERE",
            "nodes": [n.to_dict() for n in matched_nodes],
            "relationships": []
        }
    
    # Directed relationship pattern
    match = match_relationship_pattern_directed.match(query)
    if match:
        var1, label1, rel_type, var2, label2 = match.groups()
        node_dict = {node.id: node for node in nodes}

        for rel in rels:
            if rel.rel_type != rel_type:
                continue
            start_node = node_dict.get(rel.start_node)
            end_node = node_dict.get(rel.end_node)
            if start_node and end_node:
                if label1 in start_node.labels and label2 in end_node.labels:
                    matched_nodes.extend([start_node, end_node])
                    matched_rels.append(rel)

        return {
            "message": f"{len(matched_rels)} directed relationship(s) matched",
            "nodes": [n.to_dict() for n in {n.id: n for n in matched_nodes}.values()],
            "relationships": [r.to_dict() for r in matched_rels]
        }

    # Bidirectional relationship pattern
    match = match_relationship_pattern_bidirectional.match(query)
    if match:
        var1, label1, rel_type, var2, label2 = match.groups()
        node_dict = {node.id: node for node in nodes}

        for rel in rels:
            if rel.rel_type != rel_type:
                continue
            start_node = node_dict.get(rel.start_node)
            end_node = node_dict.get(rel.end_node)
            if start_node and end_node:
                if label2 in start_node.labels and label1 in end_node.labels:
                    matched_nodes.extend([start_node, end_node])
                    matched_rels.append(rel)

        return {
            "message": f"{len(matched_rels)} bidirectional relationship(s) matched",
            "nodes": [n.to_dict() for n in {n.id: n for n in matched_nodes}.values()],
            "relationships": [r.to_dict() for r in matched_rels]
        }

    # Undirected relationship pattern
    match = match_relationship_pattern_undirected.match(query)
    if match:
        var1, label1, rel_type, var2, label2 = match.groups()
        node_dict = {node.id: node for node in nodes}

        for rel in rels:
            if rel.rel_type != rel_type:
                continue
            start_node = node_dict.get(rel.start_node)
            end_node = node_dict.get(rel.end_node)
            if start_node and end_node:
                # Check both directions
                cond1 = label1 in start_node.labels and label2 in end_node.labels
                cond2 = label2 in start_node.labels and label1 in end_node.labels
                if cond1 or cond2:
                    matched_nodes.extend([start_node, end_node])
                    matched_rels.append(rel)

        return {
            "message": f"{len(matched_rels)} undirected relationship(s) matched",
            "nodes": [n.to_dict() for n in {n.id: n for n in matched_nodes}.values()],
            "relationships": [r.to_dict() for r in matched_rels]
        }

    # MATCH with properties
    match = match_pattern_with_props.match(query)
    if match:
        var, label, prop_str = match.groups()
        props = parse_properties(prop_str)

        # Check if single property (for index usage)
        if len(props) == 1:
            prop_key, prop_val = next(iter(props.items()))
            # Try to find node IDs using index
            node_ids = find_nodes_with_index(db_path, label, prop_key, prop_val)

            if node_ids:
                # Load all nodes once and filter by IDs
                nodes = storage.load_nodes()
                matched_nodes = [node for node in nodes if node.id in node_ids]
            else:
                # Index not found or no matches, fallback to scan all nodes
                matched_nodes = [node for node in nodes if label in node.labels and all(str(node.properties.get(k)) == str(v) for k, v in props.items())]
        else:
            # Multiple props, fallback to scan all nodes (no composite indexes yet)
            matched_nodes = [node for node in nodes if label in node.labels and all(str(node.properties.get(k)) == str(v) for k, v in props.items())]

        return {
            "message": f"{len(matched_nodes)} nodes matched with properties",
            "nodes": [n.to_dict() for n in matched_nodes],
            "relationships": []
        }
    
    elif match_all_pattern.match(query):
        return {
            "message": f"{len(nodes)} nodes and {len(rels)} relationships returned",
            "nodes": [n.to_dict() for n in nodes],
            "relationships": [r.to_dict() for r in rels]
        }


    # MATCH without properties
    else:
        match = match_pattern_simple.match(query)
        if match:
            var, label = match.groups()
            for node in nodes:
                if label in node.labels:
                    matched_nodes.append(node)
        else:
            return {"error": "Invalid MATCH syntax"}

    return {
        "message": f"{len(matched_nodes)} nodes matched",
        "nodes": [n.to_dict() for n in matched_nodes],
        "relationships": []
    }

    
def find_node(nodes, label, props):
    for node in nodes:
        if label in node.labels and all(str(node.properties.get(k)) == str(v) for k,v in props.items()):
            return node
    return None

def handle_create_with_relationship(query, db_path):
    match = rel_create_pattern.match(query)
    if not match:
        return {"error": "Invalid CREATE with relationship syntax"}

    (
        var1, label1, props1,
        rel_type, rel_props,
        var2, label2, props2
    ) = match.groups()

    props1 = parse_properties(props1) if props1 else {}
    props2 = parse_properties(props2) if props2 else {}
    rel_props = parse_properties(rel_props) if rel_props else {}

    storage = GraphStorage(db_path)
    nodes = storage.load_nodes()
    rels = storage.load_relationships()

    # Find or create left node
    node1 = find_node(nodes, label1, props1)
    if not node1:
        node1 = Node(id=str(uuid.uuid4()), labels=[label1], properties=props1)
        nodes.append(node1)

    # Find or create right node
    node2 = find_node(nodes, label2, props2)
    if not node2:
        node2 = Node(id=str(uuid.uuid4()), labels=[label2], properties=props2)
        nodes.append(node2)

    # Create relationship
    relationship = Relationship(
        id=str(uuid.uuid4()),
        start_node=node1.id,
        end_node=node2.id,
        rel_type=rel_type,
        properties=rel_props
    )
    rels.append(relationship)

    storage.save_nodes(nodes)
    storage.save_relationships(rels)

    return {
        "message": "Nodes and relationship created",
        "nodes": [node1.to_dict(), node2.to_dict()],
        "relationships": [relationship.to_dict()]
    }

def execute_query(query, db_path, use_index=True):
    query = query.strip()
    if query.startswith("CREATE"):
        if rel_create_pattern.match(query):
            return handle_create_with_relationship(query, db_path)
        return handle_create(query, db_path)
    if query.strip().upper().startswith("CREATE INDEX"):
        return create_index(query, db_path)
    elif query.startswith("MATCH"):
        return handle_match(query, db_path)
    return {"error": "Unsupported query type"}

