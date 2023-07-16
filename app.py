"""
Simple 2d world where the player can interact with the items in the world.
"""

__author__ = "Chen-An Wang"
__date__ = "18/5/2019"
__version__ = "1.1.0"
__copyright__ = "The University of Queensland, 2019"

import tkinter as tk
import tkinter.messagebox
import math
import cmath
import random
from collections import namedtuple

import pymunk

from block import Block, ResourceBlock, BREAK_TABLES, LeafBlock, TrickCandleFlameBlock
from grid import Stack, Grid, SelectableGrid, ItemGridView
from item import Item, SimpleItem, HandItem, BlockItem, MATERIAL_TOOL_TYPES, TOOL_DURABILITIES
from player import Player
from dropped_item import DroppedItem
from crafting import GridCrafter, CraftingWindow
from world import World
from core import positions_in_range
from game import GameView, WorldViewRouter
from physical_thing import BoundaryWall
from mob import Mob, Bird

BLOCK_SIZE = 2 ** 5
GRID_WIDTH = 2 ** 5
GRID_HEIGHT = 2 ** 4

# Task 3/Post-grad only:
# Class to hold game data that is passed to each thing's step function
# Normally, this class would be defined in a separate file
# so that type hinting could be used on PhysicalThing & its
# subclasses, but since it will likely need to be extended
# for these tasks, we have defined it here
GameData = namedtuple('GameData', ['world', 'player'])

ADDITIONAL_BREAK_TABLES = {

    "plank": {
        "hand": (3, True),
        "wood_axe": (1.5, True),
        "stone_axe": (.75, True),
        "iron_axe": (.5, True),
        "diamond_axe": (.4, True),
        "golden_axe": (.25, True)
    },

    "crafting_table": {
       "hand": (3, True),
       "wood_axe": (1.5, True),
       "stone_axe": (.75, True),
       "iron_axe": (.5, True),
       "diamond_axe": (.4, True),
       "golden_axe": (.25, True)
    },

    "furnace": {
        "hand": (7.5, False),
        "wood_pickaxe": (1.15, True),
        "stone_pickaxe": (0.6, True),
        "iron_pickaxe": (0.4, True),
        "diamond_pickaxe": (0.3, True),
        "golden_pickaxe": (0.2, True)
    },

    "wool": {
        "hand": (.5, True),
    },

    "honey": {
        "hand": (3, True),
        "wood_shovel": (1.5, True),
        "stone_shovel": (.75, True),
        "iron_shovel": (.5, True),
        "diamond_shovel": (.4, True),
        "golden_shovel": (.25, True)
    },

    "hive": {
        "hand": (3, False),
        "wood_axe": (1.5, False),
        "stone_axe": (.75, False),
        "iron_axe": (.5, False),
        "diamond_axe": (.4, False),
        "golden_axe": (.25, False)
    },

    "iron_ore": {
        "hand": (7.5, False),
        "wood_pickaxe": (3.5, False),
        "stone_pickaxe": (1, True),
        "iron_pickaxe": (0.5, True),
        "diamond_pickaxe": (0.3, True),
        "golden_pickaxe": (0.2, True)
    },

    "gold_ore": {
        "hand": (7.5, False),
        "wood_pickaxe": (3.5, False),
        "stone_pickaxe": (1, True),
        "iron_pickaxe": (0.5, True),
        "diamond_pickaxe": (0.3, True),
        "golden_pickaxe": (0.2, True)
    }
}

BLOCK_ITEMS = ["dirt", "wood", "stone", "wool", "honey", "hive", "plank",
               "crafting_table", "furnace", "iron_ore", "gold_ore"]

FOOD_ITEMS = [("apple", 2), ('cooked_apple', 4), ('burnt_apple', -2), ("golden_apple", 20), ("infinity_apple", 99)]

SIMPLE_ITEMS = ['stick', "charcoal", "sweater", "iron_ingot", "gold_ingot", "apple_seed"]


for key, value in ADDITIONAL_BREAK_TABLES.items():
    BREAK_TABLES.update({key: value})


def create_block(*block_id):
    """(Block) Creates a block (this function can be thought of as a block factory)

    Parameters:
        block_id (*tuple): N-length tuple to uniquely identify the block,
        often comprised of strings, but not necessarily (arguments are grouped
        into a single tuple)

    Examples:
        >>> create_block("leaf")
        LeafBlock()
        >>> create_block("stone")
        ResourceBlock('stone')
        >>> create_block("mayhem", 1)
        TrickCandleFlameBlock(1)
    """
    if len(block_id) == 1:
        block_id = block_id[0]
        if block_id == "leaf":
            return LeafBlock()
        elif block_id == 'crafting_table':
            return CraftingTableBlock(block_id, BREAK_TABLES[block_id])
        elif block_id == "hive":
            return HiveBlock(block_id, BREAK_TABLES[block_id])
        elif block_id == 'furnace':
            return FurnaceBlock(block_id, BREAK_TABLES[block_id])
        elif block_id in BREAK_TABLES:
            return ResourceBlock(block_id, BREAK_TABLES[block_id])

    elif block_id[0] == 'mayhem':
        return TrickCandleFlameBlock(block_id[1])

    raise KeyError(f"No block defined for {block_id}")


def create_item(*item_id):
    """(Item) Creates an item (this function can be thought of as a item factory)

    Parameters:
        item_id (*tuple): N-length tuple to uniquely identify the item,
        often comprised of strings, but not necessarily (arguments are grouped
        into a single tuple)

    Examples:
        >>> create_item("dirt")
        BlockItem('dirt')
        >>> create_item("hands")
        HandItem('hands')
        >>> create_item("pickaxe", "stone")  # *without* Task 2.1.2 implemented
        Traceback (most recent call last):
        ...
        NotImplementedError: "Tool creation is not yet handled"
        >>> create_item("pickaxe", "stone")  # *with* Task 2.1.2 implemented
        ToolItem('stone_pickaxe')
    """
    if len(item_id) == 2:

        if item_id[0] in MATERIAL_TOOL_TYPES and item_id[1] in TOOL_DURABILITIES:
            return ToolItem(f"{item_id[1]}_{item_id[0]}", item_id[0], TOOL_DURABILITIES[item_id[1]])

    elif len(item_id) == 1:

        item_type = item_id[0]

        if item_type == "hands":
            return HandItem("hands")

        # Task 1.4 Basic Items: Create wood & stone here
        for item in BLOCK_ITEMS:
            if item_type == item:
                return BlockItem(item)

        # Create Food Items
        for item, strength in FOOD_ITEMS:
            if item_type == item:
                return FoodItem(item, strength)

        # Create Simple Items
        for item in SIMPLE_ITEMS:
            if item_type == item:
                return SimpleItem(item)

    raise KeyError(f"No item defined for {item_id}")


# Task 1.3: Implement StatusView class here
class StatusView(tk.Frame):
    """Shows the status of the bar under the GameView"""

    def __init__(self, master):
        """Construct a basic gui to show the player status

        Parameter:
            player(DynamicThing): the player object
        """
        self._master = master
        self._player = self._master.get_player()

        # Construct GUI
        self._first_role = tk.Frame()
        self._first_role.pack(side=tk.TOP)

        # Health Format: [heart_icon] Health: 10.0
        health_icon = tk.PhotoImage(file="images/heart.gif").subsample(20, 20)
        self._health_icon = tk.Label(master=self._first_role, image=health_icon)
        self._health_icon.image = health_icon
        self._health_icon.pack(side=tk.LEFT)
        self._health_gui = tk.Label(master=self._first_role, text=f"Health:{self._player.get_health() / 2.0}")
        self._health_gui.pack(side=tk.LEFT)

        # Food Format [food_icon] Food: 10.0
        food_icon = tk.PhotoImage(file="images/food.gif").subsample(6, 6)
        self._food_icon = tk.Label(master=self._first_role, image=food_icon)
        self._food_icon.image = food_icon
        self._food_icon.pack(side=tk.LEFT)
        self._food_gui = tk.Label(master=self._first_role, text=f"Food:{self._player.get_food() / 2.0}")
        self._food_gui.pack(side=tk.LEFT)

    def set_health(self, new_health):
        """Set the health value to the input value

        Parameter:
            new_health(float): The player's health value
        """
        new_health = round(new_health) / 2.0
        self._health_gui["text"] = f"Health:{new_health}"

    def set_food(self, new_food):
        """Set the food value to the input value

        Parameter:
            new_food(float): The player's food value
        """
        new_food = round(new_food) / 2.0
        self._food_gui["text"] = f"Food:{new_food}"


# Task 2.1
class FoodItem(Item):
    """An item that restores player's health/hunger when used"""

    def __init__(self, item_id, strength):
        """Food item constructor

        Parameter:
            item_id(str): The id of the item
            strength(float): How much hunger/health is restored by consuming the item
        """
        super().__init__(item_id)
        self._strength = strength

    def can_attack(self):
        """(Bool) Return False since you don't fight with food"""
        return False

    def get_strength(self):
        """(float)The value that will be added to player's hunger/health"""
        return self._strength

    def place(self):
        """(list<str, tuple<str, int>>)Use the food when player left clicked"""
        return [("effect", ("food", self._strength))]


class ToolItem(Item):
    """Advanced items used to mine blocks"""
    def __init__(self, item_id, tool_type, durability):
        """Tool item constructor

        Parameter:
            item_id(str): The id of the item
            tool_type(str): Identifies what kind of tool it is
            durability(float): How much durability does this item have
        """
        super().__init__(item_id, 1)
        self._type = tool_type
        self._durability = self._max_durability = durability

    def get_type(self):
        """(str) Return the tool type"""
        return self._type

    def get_durability(self):
        """(float) Return the remaining durability of this tool"""
        return self._durability

    def get_max_durability(self):
        """(float) Return the maximum durability of this tool"""
        return self._max_durability

    def reduce_durability(self, damage):
        """Reduce the durability if an attack is not successful

        Parameter:
            damage(float): How much durability should be deducted
        """
        self._durability -= damage

    def can_attack(self):
        """(bool) Return true if the tool is not depleted"""
        if self.get_durability() > 0:
            return True
        else:
            return False

    def is_usable(self):
        """(bool) Return False since tools are not 'usable' """
        return False

    def place(self):
        pass

    def attack(self, successful):
        """Attacking with the tool

        Parameter:
            successful(bool): The boolean value that determines if the attack
            is successful
        """
        if not successful:
            self.reduce_durability(1)


# Task 2.3
class CraftingTableBlock(ResourceBlock):
    """The crafting table block that is used for advanced crafting"""

    def __init__(self, block_id, break_table):
        """Construct the crafting table

        Parameter:
            block_id(str): The id of the block
            break_table(list): The list of object that can break this block
        """
        super().__init__(block_id, break_table)

    def can_use(self):
        """(bool)Return True since crafting table is a usable block"""
        return True

    def use(self):
        """Opens the crafting menu when used"""
        return ["crafting", "crafting_table"]

    def get_drops(self, luck, correct_item_used):
        """Only drops a single crafting table when mined"""
        return [('item', ('crafting_table',))]

    def __repr__(self):
        return f"CraftingTableBlock()"


# Task 3.1: mobs
class Sheep(Mob):
    """A grass eating creature that produces wool"""

    def __init__(self, mob_id, size):
        """Sheep Constructor
        Parameter:
            mob_id(str): The id of the mob
            size(tuple<int, int>): A tuple that contains the width and height of the mob
        """
        super().__init__(mob_id, size)
        self.set_shape(pymunk.Circle)

    def step(self, time_delta, game_data):
        """Move on the ground randomly each step"""
        # game_data.player
        # game_data.world.get
        if self._steps % 40 == 0:
            # Decide a random direction to head towards
            dx, dy = random.randint(-1, 1), 30
            x, y = self.get_velocity()
            velocity = x + dx * 150, y + dy

            self.set_velocity(velocity)

        super().step(time_delta, game_data)

    def use(self):
        """You can't use a sheep"""
        pass


class Bee(Mob):
    """A hostile flying mob that likes honey"""

    def __init__(self, mob_id, size):
        """Bee Constructor

        Parameter:
            mob_id(str): The id of the mob
            size(tuple<int, int>): A tuple that contains the width and height of the mob
            player(Player): Store the player object for future use
        """

        super().__init__(mob_id, size)
        self.set_shape(pymunk.Circle)

    def attack_player(self, game_data):
        """Attacks the player if the player is near it"""
        player = game_data.player
        player_x, player_y = player.get_position()
        x, y = self.get_position()
        player_distance = math.sqrt((player_x - x) ** 2 + (player_y - y) ** 2)

        if player_distance <= BLOCK_SIZE:
            player.change_health(-0.5)

    def get_honey_block(self, game_data):
        """Search for nearby honey block

        Parameter:
            game_data(Game_Data): The Class that contains the World and Player class
        """
        x, y = self.get_position()
        nearby_blocks = game_data.world.get_blocks_nearby(x, y, 200)
        for block in nearby_blocks:
            if block.get_id() == "honey":
                return block.get_position()
        return None

    def step(self, time_delta, game_data):
        """Move on the ground randomly each step"""
        if self._steps % 15 == 0:

            # Move towards target
            bee_x, bee_y = self.get_position()
            honey_block_position = self.get_honey_block(game_data)

            if honey_block_position is not None:
                target_x, target_y = honey_block_position
            else:
                target_x, target_y = game_data.player.get_position()

            # Get direction to move towards to
            radian_angle = math.atan2((target_y - bee_y), (target_x - bee_x))
            z = cmath.rect(self._tempo, radian_angle)

            dx, dy = z.real + random.randint(-16, 16), z.imag + random.randint(-16, 16)
            x, y = self.get_velocity()
            velocity = x + dx * 1.5, y + dy * 1.5 - 150

            self.set_velocity(velocity)

            # Attack player when it's near player
            self.attack_player(game_data)

        super().step(time_delta, game_data)

    def use(self):
        """You can't use a bee"""
        pass


class HiveBlock(ResourceBlock):
    """The honey block that spawns bees when mined"""

    def __init__(self, block_id, break_table):
        """Construct the hive block

        Parameter:
            block_id(str): The id of the block
            break_table(list): The list of object that can break this block
        """
        super().__init__(block_id, break_table)

    def can_use(self):
        """(bool)Return False since HoneyBlock is a resource block"""
        return False

    def use(self):
        """HoneyBlock can't be used"""
        pass

    def get_drops(self, luck, correct_item_used):
        """Drops honey block when mined"""
        return [('bee', ('honey',))]

    def __repr__(self):
        return f"HiveBlock()"


# Task 3.2
class FurnaceBlock(ResourceBlock):
    """The furnace table block that is used for smelting"""

    def __init__(self, block_id, break_table):
        """Construct the furnace block

        Parameter:
            block_id(str): The id of the block
            break_table(list): The list of object that can break this block
        """
        super().__init__(block_id, break_table)

    def can_use(self):
        """(bool)Return True since furnace is a usable block"""
        return True

    def use(self):
        """Opens the crafting menu when used"""
        return ["crafting", "smelting"]

    def get_drops(self, luck, correct_item_used):
        """Only drops a single furnace table when mined"""
        return [('item', ('furnace',))]

    def __repr__(self):
        return f"FurnaceBlock()"


BLOCK_COLOURS = {
    'diamond': 'blue',
    'dirt': '#552015',
    'stone': 'grey',
    'wood': '#723f1c',
    'leaves': 'green',
    'crafting_table': 'pink',
    'furnace': 'black',
    'plank': '#e7bfa2',
    'wool': '#ffffff',
    'honey': '#ffe07c',
    'hive': "#b78d86",
    "iron_ore": "#493e3f",
    "gold_ore": "#ffe319"
}

ITEM_COLOURS = {
    'diamond': 'blue',
    'dirt': '#552015',
    'stone': 'grey',
    'wood': '#723f1c',
    'plank': '#e7bfa2',
    'apple': '#ff0000',
    'leaves': 'green',
    'crafting_table': 'pink',
    'furnace': 'black',
    'cooked_apple': 'red4',
    'wool': '#ffffff',
    'honey': '#ffe07c',
    'hive': "#b78d86",
    "iron_ore": "#493e3f",
    "gold_ore": "#ffe319"
}

# 2x2 Crafting Recipes
CRAFTING_RECIPES_2x2 = [
    (
        (
            (None, 'plank'),
            (None, 'plank')
        ),
        Stack(create_item('stick'), 4)
    ),
    (
        (
            (None, None),
            (None, 'wood')
        ),
        Stack(create_item('plank'), 4)
    ),
    (
        (
            ('plank', 'plank'),
            ('plank', 'plank')
        ),
        Stack(create_item('crafting_table'), 1)
    ),
    (
        (
            ('honey', 'honey'),
            ('honey', 'honey')
        ),
        Stack(create_item('hive'), 1)
    ),
    (
        (
            (None, None),
            (None, 'apple')
        ),
        Stack(create_item('apple_seed'), 4)
    ),

]

# 3x3 Crafting Recipes
CRAFTING_RECIPES_3x3 = {
    (
        (
            (None, None, None),
            (None, 'plank', None),
            (None, 'plank', None)
        ),
        Stack(create_item('stick'), 4)
    ),
    (
        (
            ('plank', 'plank', 'plank'),
            (None, 'stick', None),
            (None, 'stick', None)
        ),
        Stack(create_item('pickaxe', 'wood'), 1)
    ),
    (
        (
            ('plank', 'plank', None),
            ('plank', 'stick', None),
            (None, 'stick', None)
        ),
        Stack(create_item('axe', 'wood'), 1)
    ),
    (
        (
            (None, 'plank', None),
            (None, 'stick', None),
            (None, 'stick', None)
        ),
        Stack(create_item('shovel', 'wood'), 1)
    ),
(
        (
            (None, 'plank', None),
            (None, 'plank', None),
            (None, 'stick', None)
        ),
        Stack(create_item('sword', 'wood'), 1)
    ),
    (
        (
            (None, 'plank', None),
            (None, 'plank', None),
            (None, 'stick', None)
        ),
        Stack(create_item('sword', 'wood'), 1)
    ),
    (
        (
            ('stone', 'stone', 'stone'),
            (None, 'stick', None),
            (None, 'stick', None)
        ),
        Stack(create_item('pickaxe', 'stone'), 1)
    ),
    (
        (
            ('stone', 'stone', None),
            ('stone', 'stick', None),
            (None, 'stick', None)
        ),
        Stack(create_item('axe', 'stone'), 1)
    ),
    (
        (
            (None, 'stone', None),
            (None, 'stick', None),
            (None, 'stick', None)
        ),
        Stack(create_item('shovel', 'stone'), 1)
    ),
    (
        (
            (None, 'stone', None),
            (None, 'stone', None),
            (None, 'stick', None)
        ),
        Stack(create_item('sword', 'stone'), 1)
    ),
    (
        (
            ('stone', 'stone', 'stone'),
            ('stone', None, 'stone'),
            ('stone', 'stone', 'stone')
        ),
        Stack(create_item('furnace'), 1)
    ),
    (
        (
            ('iron_ingot', 'iron_ingot', 'iron_ingot'),
            (None, 'stick', None),
            (None, 'stick', None)
        ),
        Stack(create_item('pickaxe', 'iron'), 1)
    ),
    (
        (
            ('iron_ingot', 'iron_ingot', None),
            ('iron_ingot', 'stick', None),
            (None, 'stick', None)
        ),
        Stack(create_item('axe', 'iron'), 1)
    ),
    (
        (
            (None, 'iron_ingot', None),
            (None, 'stick', None),
            (None, 'stick', None)
        ),
        Stack(create_item('shovel', 'iron'), 1)
    ),
    (
        (
            (None, 'iron_ingot', None),
            (None, 'iron_ingot', None),
            (None, 'stick', None)
        ),
        Stack(create_item('sword', 'iron'), 1)
    ),
    (
        (
            ('stone', 'stone', 'stone'),
            ('stone', None, 'stone'),
            ('stone', 'stone', 'stone')
        ),
        Stack(create_item('furnace'), 1)
    ),
    (
        (
            ('wool', None, 'wool'),
            ('wool', 'wool', 'wool'),
            ('wool', 'wool', 'wool')
        ),
        Stack(create_item('sweater'), 1)
    ),
    (
        (
            ('gold_ingot', 'gold_ingot', 'gold_ingot'),
            ('gold_ingot', 'apple', 'gold_ingot'),
            ('gold_ingot', 'gold_ingot', 'gold_ingot')
        ),
        Stack(create_item('golden_apple'), 1)
    )
}

# Furnace Recipes
FURNACE_RECIPES ={
    (
        (
            ('wood',),
            ('plank',),
        ),
        Stack(create_item('charcoal'), 4)
    ),
    (
        (
            ('iron_ore',),
            ('plank',),
        ),
        Stack(create_item('iron_ingot'), 1)
    ),
    (
        (
            ('gold_ore',),
            ('plank',),
        ),
        Stack(create_item('gold_ingot'), 1)
    ),
    (
        (
            ('apple',),
            ('plank',),
        ),
        Stack(create_item('cooked_apple'), 1)
    ),
    (
        (
            ('cooked_apple',),
            ('plank',),
        ),
        Stack(create_item('burnt_apple'), 1)
    ),
    (
        (
            ('golden_apple',),
            ('charcoal',),
        ),
        Stack(create_item('infinity_apple'), 1)
    )
}


def load_simple_world(world):
    """Loads blocks into a world

    Parameters:
        world (World): The game world to load with blocks
    """
    block_weights = [
        (100, 'dirt'),
        (30, 'stone'),
        (3, 'iron_ore'),
        (2, 'gold_ore')
    ]

    cells = {}

    ground = []

    width, height = world.get_grid_size()

    for x in range(width):
        for y in range(height):
            if x < 22:
                if y <= 8:
                    continue
            else:
                if x + y < 30:
                    continue

            ground.append((x, y))

    weights, blocks = zip(*block_weights)
    kinds = random.choices(blocks, weights=weights, k=len(ground))

    for cell, block_id in zip(ground, kinds):
        cells[cell] = create_block(block_id)

    trunks = [(3, 8), (3, 7), (3, 6), (3, 5)]

    for trunk in trunks:
        cells[trunk] = create_block('wood')

    leaves = [(4, 3), (3, 3), (2, 3), (4, 2), (3, 2), (2, 2), (4, 4), (3, 4), (2, 4)]

    for leaf in leaves:
        cells[leaf] = create_block('leaf')

    for cell, block in cells.items():
        # cell -> box
        i, j = cell

        world.add_block_to_grid(block, i, j)

    world.add_block_to_grid(create_block("mayhem", 0), 14, 8)

    world.add_mob(Bird("friendly_bird", (12, 12)), 400, 100)
    world.add_mob(Sheep("sheep", (30, 30)), 200, 200)
    world.add_mob(Bee("bee", (15, 15)), 400, 100)


class CustomPlayer(Player):
    """Functions the same as Player, with extra methods for convenience"""

    def get_max_food(self):
        """(float) Return the maximum food value the player has"""
        return self._max_food


class CustomWorld(World):
    """Functions the same as world, but with extra methods for convenience"""

    def get_blocks_nearby(self, x: float, y: float, max_distance: float) -> [Mob]:
        """(list<Mob>) Returns all blocks within 'max_distance' from the point ('x', 'y')"""
        queries = self._space.point_query((x, y), max_distance,
                                          pymunk.ShapeFilter(mask=self._thing_categories["block"]))

        return [q.shape.object for q in queries]


class CustomWorldViewRouter(WorldViewRouter):
    """Functions the same as WorldViewRouter, with more drawing methods for convenience"""

    _routing_table = [
        # (class, method name)
        (Block, '_draw_block'),
        (TrickCandleFlameBlock, '_draw_mayhem_block'),
        (DroppedItem, '_draw_physical_item'),
        (Player, '_draw_player'),
        (Bird, '_draw_bird'),
        (Sheep, '_draw_sheep'),
        (Bee, '_draw_bee'),
        (BoundaryWall, '_draw_undefined'),
        (None.__class__, '_draw_undefined')
    ]

    def _draw_sheep(self, instance, shape, view):
        """Draws the sheep mob in world view"""
        bb = shape.bb

        return [
            view.create_oval((bb.left, bb.top, bb.right, bb.bottom),
                                fill='#ffffff', tags=('mob', 'sheep'))]

    def _draw_bee(self, instance, shape, view):
        """Draws the bee mob in world view"""
        bb = shape.bb

        centre_x = (bb.left + bb.right) // 2
        centre_y = (bb.top + bb.bottom) // 2

        return [
            view.create_polygon((centre_x, bb.top), (bb.right, centre_y), (centre_x, bb.bottom), (bb.left, centre_y),
                                fill='#ffe07c', tags=('mob', 'bee'))]


class Ninedraft:
    """High-level app class for Ninedraft, a 2d sandbox game"""

    def __init__(self, master):
        """Constructor

        Parameters:
            master (tk.Tk): tkinter root widget
        """
        self._master = master
        self._master.title("Ninedraft")
        self._world = CustomWorld((GRID_WIDTH, GRID_HEIGHT), BLOCK_SIZE)

        load_simple_world(self._world)

        self._player = CustomPlayer()
        self._world.add_player(self._player, 250, 150)

        self._world.add_collision_handler("player", "item", on_begin=self._handle_player_collide_item)

        self._hot_bar = SelectableGrid(rows=1, columns=10)
        self._hot_bar.select((0, 0))

        starting_hotbar = [
            Stack(create_item("dirt"), 20),
            Stack(create_item("apple"), 20),
            Stack(create_item("honey"), 4)
        ]

        for i, item in enumerate(starting_hotbar):
            self._hot_bar[0, i] = item

        self._hands = create_item('hands')

        starting_inventory = [
            ((1, 5), Stack(Item('dirt'), 10)),
            ((0, 2), Stack(Item('wood'), 10)),
        ]
        self._inventory = Grid(rows=3, columns=10)
        for position, stack in starting_inventory:
            self._inventory[position] = stack

        self._crafting_window = None
        self._master.bind("e",
                          lambda e: self.run_effect(('crafting', 'basic')))

        self._view = GameView(self._master, self._world.get_pixel_size(), CustomWorldViewRouter(BLOCK_COLOURS, ITEM_COLOURS))
        self._view.pack()

        # Task 1.2 Mouse Controls: Bind mouse events here
        self._master.bind('<Button-1>', self._left_click)
        self._master.bind('<Button-3>', self._right_click)
        self._view.bind('<Motion>', self._mouse_move)
        self._view.bind('<Leave>', self._mouse_leave)

        # Task 1.3: Create instance of StatusView here
        self._status = StatusView(self)

        self._hot_bar_view = ItemGridView(master, self._hot_bar.get_size())
        self._hot_bar_view.pack(side=tk.TOP, fill=tk.X)

        # Task 1.5 Keyboard Controls: Bind to space bar for jumping here
        self._master.bind("<space>", lambda e: self._jump())

        self._master.bind("a", lambda e: self._move(-1, 0))
        self._master.bind("<Left>", lambda e: self._move(-1, 0))
        self._master.bind("d", lambda e: self._move(1, 0))
        self._master.bind("<Right>", lambda e: self._move(1, 0))
        self._master.bind("s", lambda e: self._move(0, 1))
        self._master.bind("<Down>", lambda e: self._move(0, 1))

        # Task 1.5 Keyboard Controls: Bind numbers to hotbar activation here
        self._master.bind("1", lambda e: self._hot_bar.toggle_selection((0, 0)))
        self._master.bind("2", lambda e: self._hot_bar.toggle_selection((0, 1)))
        self._master.bind("3", lambda e: self._hot_bar.toggle_selection((0, 2)))
        self._master.bind("4", lambda e: self._hot_bar.toggle_selection((0, 3)))
        self._master.bind("5", lambda e: self._hot_bar.toggle_selection((0, 4)))
        self._master.bind("6", lambda e: self._hot_bar.toggle_selection((0, 5)))
        self._master.bind("7", lambda e: self._hot_bar.toggle_selection((0, 6)))
        self._master.bind("8", lambda e: self._hot_bar.toggle_selection((0, 7)))
        self._master.bind("9", lambda e: self._hot_bar.toggle_selection((0, 8)))
        self._master.bind("0", lambda e: self._hot_bar.toggle_selection((0, 9)))

        # Task 1.6 File Menu & Dialogs: Add file menu here
        self._menu = tk.Menu(self._master)
        # Construct a cascade menu for file
        self._file_menu = tk.Menu(self._menu, tearoff=0)
        self._file_menu.add_command(label="New Game", command=self.setup)
        self._file_menu.add_command(label="Quit", command=self.create_question_box)

        # Add File menu to the main menu bar
        self._menu.add_cascade(label="File", menu=self._file_menu)
        self._master.config(menu=self._menu)

        # If the player quits using the x button
        self._master.protocol("WM_DELETE_WINDOW", self.create_question_box)

        self._target_in_range = False
        self._target_position = 0, 0

        self.redraw()

        self.step()

    def get_player(self):
        """Returns the player object, mainly for Status View"""
        return self._player

    def setup(self):
        self._world = CustomWorld((GRID_WIDTH, GRID_HEIGHT), BLOCK_SIZE)

        load_simple_world(self._world)

        self._player = CustomPlayer()
        self._world.add_player(self._player, 250, 150)

        self._world.add_collision_handler("player", "item", on_begin=self._handle_player_collide_item)

        self._hot_bar = SelectableGrid(rows=1, columns=10)
        self._hot_bar.select((0, 0))

        starting_hotbar = [
            Stack(create_item("dirt"), 20),
            Stack(create_item("apple"), 20),
            Stack(create_item("honey"), 4),
        ]

        for i, item in enumerate(starting_hotbar):
            self._hot_bar[0, i] = item

        self._hands = create_item('hands')

        starting_inventory = [
            ((1, 5), Stack(Item('dirt'), 10)),
            ((0, 2), Stack(Item('wood'), 10)),
        ]
        self._inventory = Grid(rows=3, columns=10)
        for position, stack in starting_inventory:
            self._inventory[position] = stack

        self._crafting_window = None

    def create_question_box(self):
        """Creates a question box to ask if the player is leaving"""
        question_box = tk.messagebox.askyesno("Quit Game", "Are you sure you want to quit the game?")
        if question_box:
            self._master.quit()

    def redraw(self):
        self._view.delete(tk.ALL)

        # physical things
        self._view.draw_physical(self._world.get_all_things())

        # target
        target_x, target_y = self._target_position
        target = self._world.get_block(target_x, target_y)
        cursor_position = self._world.grid_to_xy_centre(*self._world.xy_to_grid(target_x, target_y))

        # Task 1.2 Mouse Controls: Show/hide target here
        if self._target_in_range:
            self._view.show_target(self._player.get_position(), cursor_position)
        else:
            self._view.hide_target()

        # Task 1.3 StatusView: Update StatusView values here
        self._status.set_food(self._player.get_food())
        self._status.set_health(self._player.get_health())

        # hot bar
        self._hot_bar_view.render(self._hot_bar.items(), self._hot_bar.get_selected())

    def step(self):
        data = GameData(self._world, self._player)
        self._world.step(data)
        # self.check_target()
        self.redraw()

        # Task 1.6 File Menu & Dialogs: Handle the player's death if necessary
        if self._player.get_health() <= 0:
            restartbox = tk.messagebox.askyesno("You died", "Do you wish to restart the game?")
            if restartbox:
                self.setup()
            else:
                self._master.quit()

        self._master.after(15, self.step)

    def _move(self, dx, dy):
        self.check_target()
        velocity = self._player.get_velocity()
        self._player.set_velocity((velocity.x + dx * 80, velocity.y + dy * 80))

    def _jump(self):
        self.check_target()
        velocity = self._player.get_velocity()
        # Task 1.2: Update the player's velocity here
        self._player.set_velocity((velocity.x * 0.5, -300))

    def mine_block(self, block, x, y):
        luck = random.random()

        active_item, effective_item = self.get_holding()

        was_item_suitable, was_attack_successful = block.mine(effective_item, active_item, luck)

        effective_item.attack(was_attack_successful)

        if block.is_mined():
            # Task 1.2 Mouse Controls: Reduce the player's food/health appropriately
            if self._player.get_food() > 0:
                self._player.change_food(-0.5)
            else:
                self._player.change_health(-1)

            # Task 1.2 Mouse Controls: Remove the block from the world & get its drops
            drops = block.get_drops(luck, was_item_suitable)
            self._world.remove_block(block)

            if not drops:
                return

            x0, y0 = block.get_position()

            for i, (drop_category, drop_types) in enumerate(drops):
                print(f'Dropped {drop_category}, {drop_types}')

                if drop_category == "item":
                    physical = DroppedItem(create_item(*drop_types))

                    # this is so bleh
                    x = x0 - BLOCK_SIZE // 2 + 5 + (i % 3) * 11 + random.randint(0, 2)
                    y = y0 - BLOCK_SIZE // 2 + 5 + ((i // 3) % 3) * 11 + random.randint(0, 2)

                    self._world.add_item(physical, x, y)
                elif drop_category == "block":
                    self._world.add_block(create_block(*drop_types), x, y)

                elif drop_category == "bee":
                    for i in range(5):
                        self._world.add_mob(Bee("bee", (15, 15)), x + random.randint(-40, 40) , y + random.randint(-40, 40))
                else:
                    raise KeyError(f"Unknown drop category {drop_category}")

    def get_holding(self):
        active_stack = self._hot_bar.get_selected_value()
        active_item = active_stack.get_item() if active_stack else self._hands

        effective_item = active_item if active_item.can_attack() else self._hands

        return active_item, effective_item

    def check_target(self):
        # select target block, if possible
        active_item, effective_item = self.get_holding()

        pixel_range = active_item.get_attack_range() * self._world.get_cell_expanse()

        self._target_in_range = positions_in_range(self._player.get_position(),
                                                   self._target_position,
                                                   pixel_range)

    def _mouse_move(self, event):
        self._target_position = event.x, event.y
        self.check_target()

    def _mouse_leave(self, event):
        """Set the target position to nothing when the mouse leave the gameview"""
        self._target_in_range = False

    def _left_click(self, event):
        # Invariant: (event.x, event.y) == self._target_position
        #  => Due to mouse move setting target position to cursor
        x, y = self._target_position

        if self._target_in_range:
            block = self._world.get_block(x, y)
            if block:
                self.mine_block(block, x, y)
                return

            # Get mobs in attack range
            mobs = self._world.get_mobs(x, y, BLOCK_SIZE/2)
            print(mobs)

            # attack mob
            for mob in mobs:
                self.attack_mob(mob)

    def attack_mob(self, mob):
        """Apply damage or effect when a mob is attacked

        Parameter:
            mob(Mob): The mob that is attacked
        """
        # Sheep drop wool when attacked
        if mob.get_id() == "sheep":
            x, y = mob.get_position()
            wool = DroppedItem(create_item('wool'))
            self._world.add_item(wool, x, y - 20)

        # Bees lose health when attacked
        if mob.get_id() == "bee":
            self._world.remove_mob(mob)

    def _trigger_crafting(self, craft_type):
        print(f"Crafting with {craft_type}")
        if craft_type == "basic":
            crafter = GridCrafter(CRAFTING_RECIPES_2x2, rows=2, columns=2)
        elif craft_type == "crafting_table":
            crafter = GridCrafter(CRAFTING_RECIPES_3x3, rows=3, columns=3)
        elif craft_type == "smelting":
            crafter = GridCrafter(FURNACE_RECIPES, rows=2, columns=1)

        if self._crafting_window is None:
            if craft_type == "smelting":
                self._crafting_window = CraftingWindow(self._master, "furnace", self._hot_bar, self._inventory, crafter)
            else:
                self._crafting_window = CraftingWindow(self._master, "craft", self._hot_bar, self._inventory, crafter)
            self._crafting_window.bind("e", self._close_crafter_view)
        else:
            self._close_crafter_view()

    def _close_crafter_view(self, event=None):
        """Close the crafter view when e is pressed in the inventory"""
        self._crafting_window.destroy()
        self._crafting_window = None

    def run_effect(self, effect):
        if len(effect) == 2:
            if effect[0] == "crafting":
                craft_type = effect[1]

                if craft_type == "basic":
                    print("Can't craft much on a 2x2 grid :/")

                elif craft_type == "crafting_table":
                    print("Let's get our kraft® on! King of the brands")

                elif craft_type == "smelting":
                    print("What are you cookin' boi?")

                self._trigger_crafting(craft_type)
                return

            elif effect[0] in ("food", "health"):
                stat, strength = effect
                if self._player.get_food() == self._player.get_max_food():
                    stat = "health"
                print(f"Gaining {strength} {stat}!")
                getattr(self._player, f"change_{stat}")(strength)
                return

        raise KeyError(f"No effect defined for {effect}")

    def _right_click(self, event):
        print("Right click")

        x, y = self._target_position
        target = self._world.get_thing(x, y)

        if target:
            # use this thing
            print(f'using {target}')
            effect = target.use()
            print(f'used {target} and got {effect}')

            if effect:
                self.run_effect(effect)

        else:
            # place active item
            selected = self._hot_bar.get_selected()

            if not selected:
                return

            stack = self._hot_bar[selected]
            drops = stack.get_item().place()

            stack.subtract(1)
            if stack.get_quantity() == 0:
                # remove from hotbar
                self._hot_bar[selected] = None

            if not drops:
                return

            # handling multiple drops would be somewhat finicky, so prevent it
            if len(drops) > 1:
                raise NotImplementedError("Cannot handle dropping more than 1 thing")

            drop_category, drop_types = drops[0]

            x, y = event.x, event.y

            if drop_category == "block":
                existing_block = self._world.get_block(x, y)

                if not existing_block:
                    self._world.add_block(create_block(drop_types[0]), x, y)
                else:
                    raise NotImplementedError(
                        "Automatically placing a block nearby if the target cell is full is not yet implemented")

            elif drop_category == "effect":
                self.run_effect(drop_types)

            else:
                raise KeyError(f"Unknown drop category {drop_category}")

    def _activate_item(self, index):
        print(f"Activating {index}")

        self._hot_bar.toggle_selection((0, index))

    def _handle_player_collide_item(self, player: Player, dropped_item: DroppedItem, data,
                                    arbiter: pymunk.Arbiter):
        """Callback to handle collision between the player and a (dropped) item. If the player has sufficient space in
        their to pick up the item, the item will be removed from the game world.

        Parameters:
            player (Player): The player that was involved in the collision
            dropped_item (DroppedItem): The (dropped) item that the player collided with
            data (dict): data that was added with this collision handler (see data parameter in
                         World.add_collision_handler)
            arbiter (pymunk.Arbiter): Data about a collision
                                      (see http://www.pymunk.org/en/latest/pymunk.html#pymunk.Arbiter)
                                      NOTE: you probably won't need this
        Return:
             bool: False (always ignore this type of collision)
                   (more generally, collision callbacks return True iff the collision should be considered valid; i.e.
                   returning False makes the world ignore the collision)
        """

        item = dropped_item.get_item()

        if self._hot_bar.add_item(item):
            print(f"Added 1 {item!r} to the hotbar")
        elif self._inventory.add_item(item):
            print(f"Added 1 {item!r} to the inventory")
        else:
            print(f"Found 1 {item!r}, but both hotbar & inventory are full")
            return True

        self._world.remove_item(dropped_item)
        return False


# Task 1.1 App class: Add a main function to instantiate the GUI here
def main():
    root = tk.Tk()
    app = Ninedraft(root)
    root.mainloop()

if __name__ == "__main__":
    main()

