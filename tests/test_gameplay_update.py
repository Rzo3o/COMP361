from unittest.mock import Mock
from gameplay.engine import GameEngine


class DummyPlayer:
    def __init__(self, q=0, r=0, health=10, hunger=5, dead=False):
        self.q = q
        self.r = r
        self.health = health
        self.hunger = hunger
        self.dead = dead
        self.death_count = 0

    def move(self, dq, dr):
        self.q += dq
        self.r += dr


class DummyWorld:
    def __init__(self, player, passable=True):
        self.player = player
        self.passable = passable
        self.update_fog_of_war = Mock()

    def is_passable(self, q, r):
        return self.passable


def make_engine(player, passable=True):
    engine = GameEngine.__new__(GameEngine)
    engine.db = Mock()
    engine.session_id = 1
    engine.world = DummyWorld(player, passable)
    engine.inventory = []
    engine.show_inventory = False
    engine.selected_index = 0
    return engine


def test_attempt_move_success():
    player = DummyPlayer(q=0, r=0)
    engine = make_engine(player, passable=True)

    result = engine.attempt_move(1, 0)

    assert result is True
    assert player.q == 1
    assert player.r == 0
    engine.db.save_player.assert_called_once()


def test_attempt_move_blocked():
    player = DummyPlayer(q=0, r=0)
    engine = make_engine(player, passable=False)

    result = engine.attempt_move(1, 0)

    assert result is False
    assert player.q == 0
    assert player.r == 0
    engine.db.save_player.assert_not_called()


def test_attempt_move_rollback_on_save_error():
    player = DummyPlayer(q=0, r=0)
    engine = make_engine(player, passable=True)
    engine.db.save_player.side_effect = Exception("db failed")

    result = engine.attempt_move(1, 0)

    assert result is False
    assert player.q == 0
    assert player.r == 0
    assert engine.world.update_fog_of_war.call_count == 2


def test_update_reduces_hunger():
    player = DummyPlayer(health=10, hunger=5)
    engine = make_engine(player)

    result = engine.update()

    assert result == "UPDATED"
    assert player.hunger == 4
    assert player.health == 10


def test_update_starvation_damage():
    player = DummyPlayer(health=10, hunger=0)
    engine = make_engine(player)

    result = engine.update()

    assert result == "UPDATED"
    assert player.health == 9


def test_update_player_dies():
    player = DummyPlayer(health=1, hunger=0)
    engine = make_engine(player)

    result = engine.update()

    assert result == "GAME_OVER"
    assert player.dead is True
    assert player.health == 0
    assert player.death_count == 1


def test_update_returns_save_error():
    player = DummyPlayer(health=10, hunger=5)
    engine = make_engine(player)
    engine.db.save_player.side_effect = Exception("db failed")

    result = engine.update()

    assert result == "SAVE_ERROR"