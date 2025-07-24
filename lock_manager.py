import threading

class LockManager:
    def __init__(self):
        # Locks held: key = resource id (node or rel), value = threading.Lock()
        self.locks = {}
        self.locks_mutex = threading.Lock()  # To protect the locks dict itself

    def acquire_lock(self, resource_id):
        with self.locks_mutex:
            if resource_id not in self.locks:
                self.locks[resource_id] = threading.Lock()
            lock = self.locks[resource_id]

        lock.acquire()

    def release_lock(self, resource_id):
        with self.locks_mutex:
            if resource_id in self.locks:
                lock = self.locks[resource_id]
                lock.release()
