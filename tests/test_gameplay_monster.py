from gameplay.monster import Monster
from gameplay.player import Player


monster_data = {
    "current_q": 5,
    "current_r": 7,
    "texture_file": "monster.png",
    "id": "goblin-1",
    "name": "Goblin",
    "health": 30,
    "damage": 8,
}

player_data = {
    "current_q": 1,
    "current_r": 2,
    "texture_file": "player.png",
    "health": 20,
    "max_health": 150,
    "hunger": 50,
    "max_hunger": 150,
    "experience": 200,
}


def test_monster_initialization_full_data():
    monster = Monster(monster_data)

    assert monster.q == 5
    assert monster.r == 7
    assert monster.texture == "monster.png"
    assert monster.id == "goblin-1"
    assert monster.name == "Goblin"
    assert monster.hp == 30
    assert monster.damage == 8


def test_monster_take_damage():
    monster = Monster(monster_data)

    monster.take_damage(5)
    assert monster.hp == 25
    assert monster.is_alive()

    monster.take_damage(30)
    assert monster.hp == 0  # HP should not go below 0
    assert not monster.is_alive()


def test_monster_attack_player():
    monster = Monster(monster_data)
    player = Player(player_data)

    monster.attack_player(player)
    assert player.hp == 20 - monster.damage
    assert not player.dead


def test_monster_attack_kill_player():
    """If monster damage is lethal, the player should die."""
    new_monster_data = dict(monster_data)
    new_monster_data["damage"] = 25
    monster = Monster(new_monster_data)
    player = Player(player_data)

    monster.attack_player(player)
    assert player.hp == 0
    assert player.dead


def test_monster_move_towards_player():
    new_monster_data = dict(monster_data)
    new_monster_data["current_q"] = 5
    new_monster_data["current_r"] = 3
    monster = Monster(monster_data)
    player = Player(player_data)

    monster.move_towards_player(player)
    assert monster.q == 4
    assert monster.r == 2

    # only move in q direction since r is already aligned
    monster.move_towards_player(player)
    assert monster.q == 3
    assert monster.r == 2

    monster.move_towards_player(player)
    assert monster.q == 2
    assert monster.r == 2

    # Can't move closer
    monster.move_towards_player(player)
    assert monster.q == 2
    assert monster.r == 2


def test_monster_move_towards_player_other_side():
    monster = Monster(monster_data)
    new_player_data = dict(player_data)
    new_player_data["current_q"] = 7
    new_player_data["current_r"] = 9
    player = Player(new_player_data)

    # Monster is at (5, 7), player is at (7, 8) -> move by (1, 1)
    monster.move_towards_player(player)
    assert monster.q == 6
    assert monster.r == 8

    # move in q first, then r can't move since it's already aligned
    monster.move_towards_player(player)
    assert monster.q == 7
    assert monster.r == 8

    # Can't move closer
    monster.move_towards_player(player)
    assert monster.q == 7
    assert monster.r == 8
