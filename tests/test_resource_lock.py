from gameplay.resource_lock import ResourceLockManager, ResourceState


def test_add_resource():
    manager = ResourceLockManager()
    manager.add_resource(100)

    assert manager.get_state(100) == ResourceState.AVAILABLE


def test_try_acquire_success():
    manager = ResourceLockManager()
    manager.add_resource(100)

    assert manager.try_acquire(100) is True
    assert manager.get_state(100) == ResourceState.PENDING


def test_try_acquire_twice_fails():
    manager = ResourceLockManager()
    manager.add_resource(100)

    assert manager.try_acquire(100) is True
    assert manager.try_acquire(100) is False
    assert manager.get_state(100) == ResourceState.PENDING


def test_consume_after_acquire():
    manager = ResourceLockManager()
    manager.add_resource(100)

    manager.try_acquire(100)
    assert manager.consume(100) is True
    assert manager.get_state(100) == ResourceState.CONSUMED


def test_release_after_acquire():
    manager = ResourceLockManager()
    manager.add_resource(100)

    manager.try_acquire(100)
    assert manager.release(100) is True
    assert manager.get_state(100) == ResourceState.AVAILABLE


def test_consume_without_pending_fails():
    manager = ResourceLockManager()
    manager.add_resource(100)

    assert manager.consume(100) is False
    assert manager.get_state(100) == ResourceState.AVAILABLE