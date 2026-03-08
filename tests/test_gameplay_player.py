from gameplay.player import Player

test_data = {
    "current_q": 1,
    "current_r": 2,
    "texture_file": "player.png",
    "health": 20,
    "max_health": 150,
    "hunger": 50,
    "max_hunger": 150,
    "experience": 200,
}


def test_player_initialization():
    player = Player(test_data)
    assert player.q == 1
    assert player.r == 2
    assert player.texture == "player.png"
    assert player.hp == 20
    assert player.max_hp == 150
    assert player.hunger == 50
    assert player.max_hunger == 150
    assert player.xp == 200


def test_player_take_damage():
    player = Player(test_data)
    player.take_damage(10)
    assert player.hp == 10
    assert not player.dead

    player.take_damage(15)
    assert player.hp == 0
    assert player.dead


def test_player_move_hunger():
    player = Player(test_data)
    player.move(2, 3)
    assert player.hunger == 45


def test_player_move_damage_by_hunger():
    player = Player(test_data)
    player.hunger = 1

    # No damage should be taken on the first move since hunger will drop to 0
    player.move(1, 0)
    assert player.hunger == 0
    assert player.hp == 20

    # Take 15 damage since 3 moves are made
    player.move(1, 2)
    assert player.hp == 5

    # take 5 damage since 1 move is made, player should now be dead
    player.move(1, 0)
    assert player.hp == 0
    assert player.dead
