from enum import Enum


class ResourceState(Enum):
    AVAILABLE = "available"
    PENDING = "pending"
    CONSUMED = "consumed"


def inventory_resource_id(inventory_entry_id):
    return ("inventory", inventory_entry_id)


def ground_resource_id(item_id):
    return ("ground", item_id)


class ResourceLockManager:
    def __init__(self):
        self._states = {}

    def add_resource(self, resource_id):
        self._states[resource_id] = ResourceState.AVAILABLE

    def get_state(self, resource_id):
        return self._states.get(resource_id)

    def can_acquire(self, resource_id):
        return self._states.get(resource_id) == ResourceState.AVAILABLE

    def acquire(self, resource_id):
        if not self.can_acquire(resource_id):
            return False

        self._states[resource_id] = ResourceState.PENDING
        return True

    def try_acquire(self, resource_id):
        return self.acquire(resource_id)

    def consume(self, resource_id):
        if self._states.get(resource_id) != ResourceState.PENDING:
            return False

        self._states[resource_id] = ResourceState.CONSUMED
        return True

    def release(self, resource_id):
        if self._states.get(resource_id) != ResourceState.PENDING:
            return False

        self._states[resource_id] = ResourceState.AVAILABLE
        return True
    