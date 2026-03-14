from gameplay.monster import Monster
from gameplay.player import Player
from gameplay.item import Item


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
    assert monster.damage == 8  # property: base_damage + weapon bonus (0)


def test_monster_take_damage():
    monster = Monster(monster_data)

    monster.take_damage(5)
    assert monster.hp == 25  # no defense, full damage
    assert monster.is_alive()

    monster.take_damage(30)
    assert monster.hp == 0
    assert not monster.is_alive()


def test_monster_attack_player():
    # Place monster adjacent to player (distance 1) so attack can land
    adj_monster = dict(monster_data)
    adj_monster["current_q"] = 2
    adj_monster["current_r"] = 2
    monster = Monster(adj_monster)
    player = Player(player_data)

    # Player has 0 base defense, so full damage applies
    monster.attack_player(player)
    assert player.hp == 20 - monster.damage
    assert not player.dead


def test_monster_attack_kill_player():
    """If monster damage is lethal, the player should die."""
    adj_monster = dict(monster_data)
    adj_monster["current_q"] = 2
    adj_monster["current_r"] = 2
    adj_monster["damage"] = 25
    monster = Monster(adj_monster)
    player = Player(player_data)

    monster.attack_player(player)
    assert player.hp == 0
    assert player.dead


def _always_passable(q, r):
    """Test helper: all tiles are passable."""
    return True


def test_monster_move_towards_player():
    # Monster at (5,7), player at (1,2) — greedy path goes r-first
    monster = Monster(monster_data)
    player = Player(player_data)

    monster.move_towards_player(player, _always_passable)
    assert monster.q == 5
    assert monster.r == 6

    monster.move_towards_player(player, _always_passable)
    assert monster.q == 5
    assert monster.r == 5


def test_monster_move_towards_player_other_side():
    # Monster at (5,7), player at (7,9)
    monster = Monster(monster_data)
    new_player_data = dict(player_data)
    new_player_data["current_q"] = 7
    new_player_data["current_r"] = 9
    player = Player(new_player_data)

    monster.move_towards_player(player, _always_passable)
    assert monster.q == 6
    assert monster.r == 7

    monster.move_towards_player(player, _always_passable)
    assert monster.q == 7
    assert monster.r == 7

    monster.move_towards_player(player, _always_passable)
    assert monster.q == 7
    assert monster.r == 8

    # Can't move closer (distance = 1)
    monster.move_towards_player(player, _always_passable)
    assert monster.q == 7
    assert monster.r == 8


# =============================================
# Equipment and loot tests
# =============================================


def test_monster_equip_weapon_increases_damage():
    monster = Monster(monster_data)
    assert monster.damage == 8  # base

    sword = Item({
        "id": 1, "name": "Goblin Blade", "item_type": "weapon",
        "slot": "weapon", "base_damage": 5,
    })
    monster.equip(sword)
    assert monster.damage == 13  # 8 + 5


def test_monster_equip_armor_increases_defense():
    monster = Monster(monster_data)
    assert monster.total_defense == 0

    helmet = Item({
        "id": 2, "name": "Rusty Helmet", "item_type": "armor",
        "slot": "head", "defense": 3,
    })
    monster.equip(helmet)
    assert monster.total_defense == 3


def test_monster_defense_reduces_incoming_damage():
    monster = Monster(monster_data)
    armor = Item({
        "id": 2, "name": "Shell Armor", "item_type": "armor",
        "slot": "chest", "defense": 4,
    })
    monster.equip(armor)

    monster.take_damage(5)
    assert monster.hp == 29  # 5 - 4 defense = 1 damage


def test_monster_drops_equipment_on_death():
    monster = Monster(monster_data)
    sword = Item({
        "id": 1, "name": "Goblin Blade", "item_type": "weapon",
        "slot": "weapon", "base_damage": 5,
    })
    helmet = Item({
        "id": 2, "name": "Rusty Helmet", "item_type": "armor",
        "slot": "head", "defense": 3,
    })
    monster.equip(sword)
    monster.equip(helmet)

    # Kill the monster
    monster.take_damage(999)
    assert monster.dead

    # on_death should have cleared equipment and returned drops
    # Verify equipment slots are now empty
    assert monster.equipment["weapon"] is None
    assert monster.equipment["head"] is None


def test_monster_unequip_reverts_stats():
    monster = Monster(monster_data)
    sword = Item({
        "id": 1, "name": "Blade", "item_type": "weapon",
        "slot": "weapon", "base_damage": 7,
    })
    monster.equip(sword)
    assert monster.damage == 15  # 8 + 7

    removed = monster.unequip("weapon")
    assert removed is sword
    assert monster.damage == 8  # back to base
