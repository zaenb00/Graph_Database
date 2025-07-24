import os
import json
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_database(db_name: str, hashed_pwd: str):
    path = os.path.join("databases", db_name)
    os.makedirs(path, exist_ok=True)

    for file in ["nodes.json", "relationships.json", "properties.json", "indexes.json"]:
        with open(os.path.join(path, file), "w") as f:
            json.dump({}, f)

    with open(os.path.join(path, "password.txt"), "w") as f:
        f.write(hashed_pwd)
