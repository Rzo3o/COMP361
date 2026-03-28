from gameplay.player import Player
from gameplay.item import Item

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
    # texture is now loaded from animations, not texture_file
    assert player.hp == 20
    assert player.max_hp == 150
    assert player.hunger == 50
    assert player.max_hunger == 150
    assert player.xp == 200


def test_player_take_damage():
    player = Player(test_data)
    # base_defense is 100, so damage must exceed it to deal more than 1
    player.take_damage(110)  # max(1, 110-100) = 10
    assert player.hp == 10
    assert not player.dead

    player.take_damage(115)  # max(1, 115-100) = 15
    assert player.hp == 0
    assert player.dead


def test_player_move_hunger():
    player = Player(test_data)
    player.move(2, 3)
    assert player.hunger == 49  # drains 1 per move


def test_player_move_damage_by_hunger():
    player = Player(test_data)
    player.hunger = 1

    # First move: hunger drops to 0, starvation damage fires
    # base_defense=100 reduces take_damage(5) to min 1
    player.move(1, 0)
    assert player.hunger == 0
    assert player.hp == 19  # 20 - max(1, 5-100) = 20 - 1

    # Reset animation lock so next move can proceed
    player.is_moving = False

    # Second move: still at 0, another 1 starvation damage
    player.move(1, 2)
    assert player.hp == 18

    player.is_moving = False

    # Third move
    player.move(1, 0)
    assert player.hp == 17


# =============================================
# Equipment system tests
# =============================================


def test_player_equip_weapon_increases_damage():
    player = Player({"current_q": 0, "current_r": 0, "health": 100, "max_health": 100})
    assert player.total_damage == 10  # base damage

    sword = Item({
        "id": 1, "name": "Sword", "item_type": "weapon",
        "slot": "weapon", "base_damage": 10,
    })
    player.equip(sword)
    assert player.total_damage == 20  # 10 base + 10 weapon
    assert player.equipment["weapon"] is sword


def test_player_unequip_weapon_reverts_damage():
    player = Player({"current_q": 0, "current_r": 0, "health": 100, "max_health": 100})
    sword = Item({
        "id": 1, "name": "Sword", "item_type": "weapon",
        "slot": "weapon", "base_damage": 10,
    })
    player.equip(sword)
    assert player.total_damage == 20  # 10 base + 10 weapon

    removed = player.unequip("weapon")
    assert removed is sword
    assert player.total_damage == 10  # back to base
    assert player.equipment["weapon"] is None


def test_player_equip_armor_increases_defense():
    player = Player({"current_q": 0, "current_r": 0, "health": 100, "max_health": 100})
    assert player.total_defense == 100  # base defense

    helmet = Item({
        "id": 2, "name": "Iron Helmet", "item_type": "armor",
        "slot": "head", "defense": 3,
    })
    chestplate = Item({
        "id": 3, "name": "Iron Chestplate", "item_type": "armor",
        "slot": "chest", "defense": 8,
    })
    player.equip(helmet)
    player.equip(chestplate)
    assert player.total_defense == 111  # 100 base + 3 + 8


def test_player_defense_reduces_damage():
    player = Player({"current_q": 0, "current_r": 0, "health": 100, "max_health": 100})
    chestplate = Item({
        "id": 3, "name": "Iron Chestplate", "item_type": "armor",
        "slot": "chest", "defense": 8,
    })
    player.equip(chestplate)
    # total_defense = 100 base + 8 armor = 108

    reduced = player.take_damage(118)  # max(1, 118-108) = 10
    assert reduced == 10
    assert player.hp == 90


def test_player_defense_minimum_1_damage():
    player = Player({"current_q": 0, "current_r": 0, "health": 100, "max_health": 100})
    chestplate = Item({
        "id": 3, "name": "Iron Chestplate", "item_type": "armor",
        "slot": "chest", "defense": 50,
    })
    player.equip(chestplate)

    reduced = player.take_damage(5)
    assert reduced == 1  # minimum 1
    assert player.hp == 99


def test_player_equip_replaces_old_item():
    player = Player({"current_q": 0, "current_r": 0, "health": 100, "max_health": 100})
    sword1 = Item({
        "id": 1, "name": "Wood Sword", "item_type": "weapon",
        "slot": "weapon", "base_damage": 3,
    })
    sword2 = Item({
        "id": 2, "name": "Iron Sword", "item_type": "weapon",
        "slot": "weapon", "base_damage": 10,
    })
    player.equip(sword1)
    assert player.total_damage == 13  # 10 base + 3

    old = player.equip(sword2)
    assert old is sword1
    assert player.total_damage == 20  # 10 base + 10


def test_player_broken_weapon_gives_no_bonus():
    player = Player({"current_q": 0, "current_r": 0, "health": 100, "max_health": 100})
    sword = Item({
        "id": 1, "name": "Worn Sword", "item_type": "weapon",
        "slot": "weapon", "base_damage": 10, "durability": 1, "max_durability": 50,
    })
    player.equip(sword)
    assert player.total_damage == 20  # 10 base + 10 weapon

    sword.degrade(1)  # durability -> 0
    assert sword.is_broken()
    assert player.total_damage == 10  # broken weapon gives no bonus, back to base


def test_non_equippable_item_returns_none():
    player = Player({"current_q": 0, "current_r": 0, "health": 100, "max_health": 100})
    bread = Item({"id": 1, "name": "Bread", "item_type": "food"})
    result = player.equip(bread)
    assert result is None
    assert all(v is None for v in player.equipment.values())
