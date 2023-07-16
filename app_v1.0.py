"""
Simple 2d world where the player can interact with the items in the world.
"""

import tkinter as tk
import random
import math

import pymunk

from block import Block, ResourceBlock, BREAK_TABLES, LeafBlock, TrickCandleFlameBlock
from grid import Stack, Grid, SelectableGrid, ItemGridView
from item import Item, HandItem, BlockItem, MATERIAL_TOOL_TYPES, TOOL_DURABILITIES
from player import Player
from dropped_item import DroppedItem
from physical_thing import BoundaryWall
from crafting import CraftingWindow
from instance_router import InstanceRouter
from world import World
from geometry import positions_in_range
from game import GameView

__author__ = "Chen-An Wang"
__date__ = "19/5/2019"
__copyright__ = "The University of Queensland, 2019"

BLOCK_SIZE = 2 ** 5
GRID_WIDTH = 2 ** 5
GRID_HEIGHT = 2 ** 4

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
        return False

    def get_strength(self):
        """(float)The value that will be added to player's hunger/health"""
        return self._strength

    def place(self):
        return [("effect", ("food", self._strength))]

def create_block(*block_ids):
    if len(block_ids) == 1:
        block_id = block_ids[0]
        if block_id == "leaf":
            return LeafBlock()
        elif block_id in BREAK_TABLES:
            return ResourceBlock(block_id, BREAK_TABLES[block_id])
        # ~< remove from template
        elif block_id == "crafting_table":
            return CraftingTableBlock()
        # ~>

    elif block_ids[0] == 'mayhem':
        return TrickCandleFlameBlock(block_ids[1])

    raise KeyError(f"No block defined for {block_ids}")


def create_item(*item_types):
    if len(item_types) == 2:

        if item_types[0] in MATERIAL_TOOL_TYPES and item_types[1] in TOOL_DURABILITIES:
            raise NotImplementedError("Tool creation is not yet handled")

    elif len(item_types) == 1:

        item_type = item_types[0]

        if item_type == "hands":
            return HandItem("hands")

        elif item_type == "dirt":
            return BlockItem(item_type)

        # Task 1.4 Basic Items: Create wood & stone here
        elif item_type == "wood":
            return BlockItem(item_type)

        elif item_type == "stone":
            return BlockItem(item_type)

        # Create the apple item
        elif item_type == "apple":
            return FoodItem(item_type, 2)

    raise KeyError(f"No item defined for {item_types}")

# Categories can appear in crafting recipes to match on a group of items that are categorical.
# e.g. Oak and Birch are both a type of wood
item_categories = {
    'wood': {'oak_wood', 'birch_wood'}
}

# (Item ids | category) in row * column tuple layout
crafting_recipes = {
    (('wood',),
     ('wood',)): Stack(Item('stick'), 16),
    (('dirt',),
     ('dirt',)): Stack(Item('wood'), 4),
}

BLOCK_COLOURS = {
    'diamond': 'blue',
    'dirt': '#552015',
    'stone': 'grey',
    'wood': '#723f1c',
    'leaves': 'green',
    "crafting_table": "pink",
}

ITEM_COLOURS = {
    'diamond': 'blue',
    'dirt': '#552015',
    'stone': 'grey',
    'wood': '#723f1c',
    'apple': '#ff0000',
    'leaves': 'green',
    "crafting_table": "pink",
}


class WorldViewRouter(InstanceRouter):
    """
    Magical (sub)class used to handle drawing of different physical things
    """
    # Instances of class, or its subclasses are drawn by method
    # I.e. _draw_block handles the drawing of Block & its subclasses
    # More specific subclasses take priority, so _draw_mayhem block will handle the drawing of TrickCandleFlameBlock
    _routing_table = [
        # (class, method name)
        (Block, '_draw_block'),
        (TrickCandleFlameBlock, '_draw_mayhem_block'),
        (DroppedItem, '_draw_physical_item'),
        (Player, '_draw_player'),
        (BoundaryWall, '_draw_undefined'),
        (None.__class__, '_draw_undefined')
    ]

    def _draw_block(self, instance, shape, view):
        return [view.create_rectangle(shape.bb.left, shape.bb.top, shape.bb.right, shape.bb.bottom,
                                      fill=BLOCK_COLOURS[instance.get_id()], tag='block')]

    def _draw_mayhem_block(self, instance, shape, view):
        return [view.create_rectangle(shape.bb.left, shape.bb.top, shape.bb.right, shape.bb.bottom,
                                      fill=instance.colours[instance._i], tag='block')]

    def _draw_physical_item(self, instance, shape, view):
        return [view.create_rectangle(shape.bb.left, shape.bb.top, shape.bb.right, shape.bb.bottom,
                                      fill=ITEM_COLOURS[instance.get_item().get_id()],
                                      tag='physical_item')]

    def _draw_player(self, instance, shape, view):
        return [view.create_oval(shape.bb.left, shape.bb.top, shape.bb.right, shape.bb.bottom,
                                 fill='red', tag='player')]

    def _draw_undefined(self, instance, shape, view):
        return [view.create_rectangle(shape.bb.left, shape.bb.top, shape.bb.right, shape.bb.bottom,
                                      fill='black', tag='undefined')]


def load_simple_world(world):
    block_weights = [
        (100, 'dirt'),
        (30, 'stone'),
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

    world.add_block_to_grid(TrickCandleFlameBlock(0), 14, 8)


class StatusView(tk.Frame):

    def __init__(self, player):
        """Construct a basic gui to show the player status

        Parameter:
            player(DynamicThing): the player object
        """
        self._player = player

        # Construct GUI
        self._first_role = tk.Frame()
        self._first_role.pack(side=tk.TOP)

        self._health_gui = tk.Label(master=self._first_role, text=f"Health:{self._player.get_health() / 2.0}")
        self._health_gui.pack(side=tk.LEFT)
        self._food_gui = tk.Label(master=self._first_role, text=f"Food:{self._player.get_food() / 2.0}")
        self._food_gui.pack(side=tk.LEFT)

    def set_health(self, new_health):
        self._health_gui["text"] = f"Health:{self._player.get_health()}"

    def set_food(self, new_food):
        self._food_gui["text"] = f"Food:{self._player.get_food()}"

    def update(self):
        """Update the StatusView according to the new player status"""
        # Round Player Values to the nearest 0.5
        new_health = round(self._player.get_health()) / 2.0
        new_hunger = round(self._player.get_food()) / 2.0

        self._health_gui["text"] = f"Health:{new_health}"
        self._food_gui["text"] = f"Food:{new_hunger}"


class Ninedraft:
    def __init__(self, master):

        self._master = master
        self._master.title("Ninedraft")
        self._world = World((GRID_WIDTH, GRID_HEIGHT), BLOCK_SIZE)

        load_simple_world(self._world)

        self._player = Player()
        self._world.add_player(self._player, 250, 150)

        self._world.add_collision_handler("player", "item", on_begin=self._handle_player_collide_item)

        self._hot_bar = SelectableGrid(rows=1, columns=10)
        self._hot_bar.select((0, 0))

        starting_hotbar = [
            Stack(create_item("dirt"), 20),
            Stack(create_item("apple"), 4)
        ]

        for i, item in enumerate(starting_hotbar):
            self._hot_bar[0, i] = item

        self._hands = create_item('hands')

        starting_inventory = [
            ((1, 5), Stack(Item('oak_wood'), 1)),
            ((0, 2), Stack(Item('birch_wood'), 1)),
        ]
        self._inventory = Grid(rows=3, columns=10)
        for position, stack in starting_inventory:
            self._inventory[position] = stack

        self._crafting_window = None
        self._master.bind("e",
                          lambda e: self.run_effect(('crafting', 'basic')))

        self._view = GameView(master, self._world.get_pixel_size(), WorldViewRouter())
        self._view.pack()

        # Task 1.2 Mouse Controls: Bind mouse events here
        # Bind mouse event
        self._master.bind('<Button-1>', self._left_click)
        self._master.bind('<Button-3>', self._right_click)
        self._master.bind('<Motion>', self._mouse_move)

        # Task 1.3: Create instance of StatusView here
        self._status = StatusView(self._player)

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
        self._file_menu.add_command(label="New Game", command=self._master.quit)
        self._file_menu.add_command(label="Quit", command=self._master.quit)

        # Add File menu to the main menu bar
        self._menu.add_cascade(label="File", menu=self._file_menu)
        self._master.config(menu=self._menu)

        self._target_in_range = False
        self._target_position = 0, 0

        self.redraw()

        self.step()

    def redraw(self):
        # TODO: cache items internally to improve efficiency
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
        self._status.update()

        # hot bar
        self._hot_bar_view.render(self._hot_bar.items(), self._hot_bar.get_selected())

    def step(self):
        # TODO: pass effects...
        self._world.step()
        self.check_target()
        self.redraw()

        # Task 1.6 File Menu & Dialogs: Handle the player's death if necessary
        self._master.after(15, self.step)

    def _move(self, dx, dy):
        velocity = self._player.get_velocity()
        self._player.set_velocity((velocity.x + dx * 80, velocity.y + dy * 80))

    def _jump(self):
        velocity = self._player.get_velocity()
        # Task 1.4 Keyboard Controls: Update the player's velocity here
        jump_force = -300
        if abs(velocity.x) < 25:
            self._player.set_velocity((velocity.x, jump_force))
            print("jump 1")
        else:
            self._player.set_velocity((velocity.x * 0.25, jump_force))
            print("jump 2")

    def mine_block(self, block, x, y):
        luck = random.random()

        active_item, effective_item = self.get_holding()

        was_item_suitable, was_attack_successful = block.mine(effective_item, active_item, luck)

        effective_item.attack(was_attack_successful)

        if block.is_mined():
            # Task 1.2 Mouse Controls: Reduce the player's food/health appropriately
            #          You may select what you believe is an appropriate amount by
            #          which to reduce the food or health.
            if self._player.get_food() > 0:
                self._player.change_food(-0.2)
            else:
                self._player.change_health(-1)

            self._world.remove_block(block)
            # Task 1.2 Mouse Controls: Get what the block drops.
            drops = block.get_drops(luck, was_attack_successful)

            if not drops:
                return
            x0, y0 = block.get_position()

            for i, (drop_category, drop_types) in enumerate(drops):
                print(f'Dropped {drop_category}, {drop_types}')

                if drop_category == "item":
                    physical = DroppedItem(create_item(*drop_types))

                    # TODO: this is so bleh
                    x = x0 - BLOCK_SIZE // 2 + 5 + (i % 3) * 11 + random.randint(0, 2)
                    y = y0 - BLOCK_SIZE // 2 + 5 + ((i // 3) % 3) * 11 + random.randint(0, 2)

                    self._world.add_item(physical, x, y)
                elif drop_category == "block":
                    self._world.add_block(create_block(*drop_types), x, y)
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

    def _left_click(self, event):
        # Invariant: (event.x, event.y) == self._target_position
        #  => Due to mouse move setting target position to cursor
        x, y = self._target_position

        if self._target_in_range:
            block = self._world.get_block(x, y)
            if block:
                self.mine_block(block, x, y)

    def _trigger_crafting(self, craft_type):
        print(f"Crafting with {craft_type}")

    def run_effect(self, effect):
        if len(effect) == 2:
            if effect[0] == "crafting":
                craft_type = effect[1]

                if craft_type == "basic":
                    print("Can't craft much on a 2x2 grid :/")

                elif craft_type == "crafting_table":
                    print("Let's get our kraft® on! King of the brands")

                self._trigger_crafting(craft_type)
                return
            elif effect[0] in ("food", "health"):
                stat, strength = effect
                print(f"Gaining {strength} {stat}!")
                if self._player.get_food() == self._player.get_max_food():
                    getattr(self._player, f"change_{stat}")(strength)
                else:
                    stat = "health"
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
            item = self._hot_bar.get_selected_value().get_item()

            if not item:
                return

            drops = item.place()

            if not drops:
                return

            # TODO: handle multiple drops
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

    def _handle_player_collide_item(self, player: Player, item: DroppedItem, data,
                                    arbiter: pymunk.Arbiter):
        """Callback to handle collision between the player and a (dropped) item. If the player has sufficient space in
        their to pick up the item, the item will be removed from the game world.

        Parameters:
            player (Player): The player that was involved in the collision
            item (DroppedItem): The (dropped) item that the player collided with
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

        if self._inventory.add_item(item.get_item()):
            print(f"Picked up a {item!r}")
            self._world.remove_item(item)

        return False


# Task 1.1 App class: Add a main function to instantiate the GUI here
if __name__ == "__main__":
    root = tk.Tk()
    app = Ninedraft(root)
    root.mainloop()
