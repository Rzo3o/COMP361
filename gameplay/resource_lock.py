from enum import Enum


class ResourceState(Enum):
    AVAILABLE = "available"
    PENDING = "pending"
    CONSUMED = "consumed"


class ResourceLockManager:
    def __init__(self):
        self._states = {}

    def add_resource(self, resource_id):
        self._states[resource_id] = ResourceState.AVAILABLE

    def get_state(self, resource_id):
        return self._states.get(resource_id)

    def try_acquire(self, resource_id):
        state = self._states.get(resource_id)

        if state is None:
            return False

        if state != ResourceState.AVAILABLE:
            return False

        self._states[resource_id] = ResourceState.PENDING
        return True

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