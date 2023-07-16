"""Data structures for managing objects and collision detection in 2d space.

Each object exists in space within an axis-aligned bounding box (the smallest
possible rectangle that is aligned with the axes and completely contains the
object). Coordinates are references as ((x0, y0), (x1, y1)). For example, the
following triangle (with vertices (16, 0) -> (0, 32) -> (32, 32)) would have
the bounding box (0, 0), (32, 32):

Coordinates in (x, y)

*----->
|    +x
|
v +y


 (0, 0)          (16, 0)         (32, 0)
*---------------*---------------*
|              /| \             |
|             / |  \            |
|            /  |   \           |
|           /   |    \          |
|          /    |     \         |
|         /     |      \        |
|(0, 16) /   (16, 16)   \       |(32, 16)
*-------/-------*--------\------*
|      /        |         \     |
|     /         |          \    |
|    /          |           \   |
|   /           |            \  |
|  /            |             \ |
| /             |              \|
*---------------*---------------*
 (0, 32)         (16, 32)        (32, 32)


See:
  - https://en.wikipedia.org/wiki/Minimum_bounding_box
  - https://en.wikipedia.org/wiki/Bounding_volume
"""

import random


__author__ = "Benjamin Martin"
__date__ = "26/04/2019"
__copyright__ = "The University of Queensland, 2019"


QUADRISECTIONS = [
    #   NW  |  NE
    #  0, 0 | 1, 0
    # ------+------
    #   SW  |  SE
    #  0, 1 | 1, 1

    (0, 0),
    (1, 0),
    (1, 1),
    (0, 1),
]


class Rectangle:
    """A 2d representation of a rectangle, represented by top-left & bottom right corners.

    Coordinates are:
        top-left corner: (x0, y0)
        bottom-right corner: (x1, y1)
    """

    def __init__(self, x0, y0, x1, y1):
        """
        Parameters:
            x0 (int): The x-coordinate of the top-left corner
            y0 (int): The y-coordinate of the top-left corner
            x1 (int): The x-coordinate of the bottom-right corner
            y1 (int): The y-coordinate of the bottom-right corner
        """
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def to_tuple(self):
        """(int, int, int, int) Returns a 4-tuple of (x0, y0, x1, y1)"""
        return self.x0, self.y0, self.x1, self.y1

    def get_size(self):
        """(int, int) Returns the dimensions (width, height) of the rectangle"""
        return self.x1 - self.x0, self.y1 - self.y0

    def __repr__(self):
        # self.__class__.__name__ will get the name of the class (i.e. Rectangle or BoundingBox, etc.)
        return f"{self.__class__.__name__}({self.x0}, {self.y0}, {self.x1}, {self.y1})"

    def move(self, dx, dy):
        """(Rectangle) Returns a copy of the rectangle moved by (dx, dy)"""
        return self.__class__(self.x0 + dx, self.y0 + dy, self.x1 + dx, self.y1 + dy)

    def contains(self, other):
        """(bool) Returns True iff this rectangle contains 'other'"""
        return other.x0 >= self.x0 and other.x1 <= self.x1 \
               and other.y0 >= self.y0 and other.y1 <= self.y1

    def get_top_left(self):
        """(int, int) Returns the top-left corner"""
        return self.x0, self.y0

    def get_bottom_right(self):
        """(int, int) Returns the bottom corner"""
        return self.x1, self.y1

    def get_centre(self):
        """(int, int) Returns the centre"""
        return self.x0 + (self.x1 - self.x0) // 2, self.y0 + (self.y1 - self.y0) // 2


class BoundingBox(Rectangle):
    """A 2d bounding box"""

    def intersects(self, other):
        # treat range as [x0, x1], [y0, y1]
        return not (other.x0 >= self.x1 or other.x1 <= self.x0
                    or other.y0 >= self.y1 or other.y1 <= self.y0)

    def overlaps(self, other):
        # treat range as (x0, x1), (y0, y1)
        return not (other.x0 > self.x1 or other.x1 < self.x0
                    or other.y0 > self.y1 or other.y1 < self.y0)

    def quadrisect(self):
        """Divides box into four quadrants, one split on each axis"""

        corners = [
            self.get_top_left(),
            self.get_centre(),
            self.get_bottom_right()
        ]

        quadrants = []

        for dx, dy in QUADRISECTIONS:
            box = BoundingBox(corners[dx][0],
                              corners[dy][1],
                              corners[dx + 1][0],
                              corners[dy + 1][1])
            quadrants.append(box)

        return quadrants

    def __lt__(self, other):
        return (self.x0, self.y0, self.x1, self.y1) < (other.x0, other.y0, other.x1, other.y1)

    def __add__(self, other):
        return BoundingBox(min(self.x0, other.x0), min(self.y0, other.y0), max(self.x1, other.x1), max(self.y1, other.y1))


class AbstractSpace:
    """An abstract representation of 2d space that manages elements'
       positions and supports querying for elements that intersect
       (i.e. collide/overlap with) a bounding box.
    """

    def get_bounding_box(self):
        """(BoundingBox) Returns the bounding box for the entirety of space."""
        raise NotImplementedError("AbstractSpace subclass must implement a get_bounding_box method")

    def get_intersecting(self, bounding_box: BoundingBox):
        """(*, BoundingBox) Yields pairs of (element, bounding box) for all elements whose
        bounding boxes intersect a given bounding box.

        Parameters:
            bounding_box (BoundingBox): Bounding box to check for intersections.
        """
        raise NotImplementedError("AbstractSpace subclass must implement a get_intersecting method")

    def get_all(self):
        """(*, BoundingBox) Yields pairs of (element, bounding box) for all elements

        Parameters:
            bounding_box (BoundingBox): Bounding box to check for intersections.
        """
        raise NotImplementedError("AbstractSpace subclass must implement a get_all method")

    def __len__(self):
        """(int) Returns the number of elements stored in space."""
        raise NotImplementedError("AbstractSpace subclass must implement a __len__ method")

    def insert(self, element, bounding_box: BoundingBox):
        """Insert element into space.

        Parameters:
            element (*): Element to insert.
            bounding_box (BoundingBox): Element's bounding box.
        """
        raise NotImplementedError("AbstractSpace subclass must implement an insert method")

    def remove(self, element, bounding_box: BoundingBox):
        """Removes element from space.

        Parameters:
            element (*): Element to remove.
            bounding_box (BoundingBox): Element's bounding box.

        Raises:
            May raise an error if element does not exist at bounding_box.
        """
        raise NotImplementedError("AbstractSpace subclass must implement a remove method")

    def move(self, element, from_box: BoundingBox, to_box: BoundingBox):
        """Move element in space.

        Parameters:
            element (*): Element to move.
            from_box (BoundingBox): Element's current bounding box.
            to_box (BoundingBox): Element's new bounding box.
        """
        raise NotImplementedError("AbstractSpace subclass must implement a move method")


class QuadrantError(Exception):
    pass


class QuadTree(AbstractSpace):
    """A sophisticated representation of 2d space that manages elements'
       positions and support efficient querying for elements that intersect (
       i.e. collide/overlap with) a bounding box, based upon a quad tree that
       recursively subdivides space into quadrants to ensure that no leaf
       quadrant holds more than a certain number of items.
    """

    def __init__(self, bounding_box: BoundingBox, capacity=15):
        self._elements = []
        self._bounding_box = bounding_box
        self._capacity = capacity

        self._quadrants = None

    def __len__(self):
        if self._quadrants:
            return len(self._elements) + sum(len(q) for q in self._quadrants)
        else:
            return len(self._elements)

    def get_bounding_box(self):
        return self._bounding_box

    def get_intersecting(self, bounding_box: BoundingBox):
        for element, element_bounding_box in self._elements:
            if bounding_box.intersects(element_bounding_box):
                yield (element, element_bounding_box)

        if self._quadrants:
            for quadrant in self._quadrants:
                if quadrant.get_bounding_box().intersects(bounding_box):
                    yield from quadrant.get_intersecting(bounding_box)

    def get_all(self):
        yield from self._elements

        if self._quadrants:
            for quadrant in self._quadrants:
                yield from quadrant.get_all()

    def insert(self, element, bounding_box: BoundingBox):

        # needs to be subdivided?
        if not self._quadrants and len(self._elements) == self._capacity:
            self._subdivide()

        if self._quadrants:
            # add to appropriate quadrant (or elements if spans multiple)
            quadrants = list(self._select_quadrant(bounding_box))

            if len(quadrants) == 0:
                boxes = [q.get_bounding_box() for q in self._quadrants]
                raise QuadrantError(f"Bounding box {bounding_box} spans none of {boxes}")

            if len(quadrants) == 1:
                i = quadrants[0]
                self._quadrants[i].insert(element, bounding_box)
            else:
                self._elements.append((element, bounding_box))

        else:
            self._elements.append((element, bounding_box))

    def remove(self, element, bounding_box):

        if self._quadrants:
            quadrants = list(self._select_quadrant(bounding_box))

            if len(quadrants) == 0:
                boxes = [q.get_bounding_box() for q in self._quadrants]
                raise QuadrantError(f"Bounding box {bounding_box} spans none of {boxes}")
        else:
            quadrants = []

        if len(quadrants) == 1:
            i = quadrants[0]
            self._quadrants[i].remove(element, bounding_box)
        else:
            self._elements.remove((element, bounding_box))

    def move(self, element, from_box, to_box):
        self.remove(element, from_box)
        self.insert(element, to_box)

    def _select_quadrant(self, bounding_box):
        if not self._quadrants:
            raise QuadrantError("QuadTree has not yet been subdivided")

        for i, quadrant in enumerate(self._quadrants):
            if quadrant.get_bounding_box().intersects(bounding_box):
                yield i

    def _subdivide(self):
        # create quadrants
        self._quadrants = [
            QuadTree(quadrant_box, capacity=self._capacity) for quadrant_box in self._bounding_box.quadrisect()
        ]

        # insert elements into appropriate quadrants
        elements = []

        for element, bounding_box in self._elements:
            quadrants = list(self._select_quadrant(bounding_box))

            if len(quadrants) == 1:
                i = quadrants[0]
                self._quadrants[i].insert(element, bounding_box)
            else:
                elements.append((element, bounding_box))

        self._elements = elements


class NaiveSpace(AbstractSpace):
    """A naive implementation of 2d space that manages elements' positions
       and supports inefficient querying for elements that intersect
       (i.e. collide/overlap with) a bounding box, using a simple list
       and linear probing.
    """

    def __init__(self, bounding_box: BoundingBox, capacity=15):
        self._elements = []
        self._bounding_box = bounding_box
        self._capacity = capacity

    def __len__(self):
        return len(self._elements)

    def get_bounding_box(self):
        return self._bounding_box

    def get_intersecting(self, bounding_box: BoundingBox):
        for element, element_bounding_box in self._elements:
            if bounding_box.intersects(element_bounding_box):
                yield element, element_bounding_box

    def get_all(self):
        yield from self._elements

    def insert(self, element, bounding_box: BoundingBox):
        self._elements.append((element, bounding_box))

    def remove(self, element, bounding_box: BoundingBox):
        index = None
        for i, (the_element, the_box) in enumerate(self._elements):
            if the_element is element:
                index = i
                break

        del self._elements[index]

    def move(self, element, from_box: BoundingBox, to_box: BoundingBox):
        self.remove(element, from_box)
        self.insert(element, to_box)


# Crude, inexhaustive testing code for BoundingBox & AbstractSpace subclasses

def bounding_box_test():
    b1 = BoundingBox(0, 0, 200, 200)
    b2 = BoundingBox(200, 200, 400, 400)

    assert not b1.intersects(b2)
    assert not b2.intersects(b1)


def generate_range_within(minimum, maximum, min_width=1, max_width=0):
    start = random.randint(minimum, maximum - min_width - 1)
    end = random.randint(start, maximum - min_width)

    if end >= start:
        end += min_width

    if start > end:
        start, end = end, start

    return start, end


def generate_things_within(n, box, min_size=(1, 1)):
    for i in range(n):
        min_x, min_y = min_size

        x0, x1 = generate_range_within(box.x0, box.x1 - 1, min_width=min_x)
        y0, y1 = generate_range_within(box.y0, box.y1 - 1, min_width=min_y)

        yield BoundingBox(x0, y0, x1, y1)


def generate_small_things_within(n, box):
    for i in range(n):
        size = random.randint(20, 60)

        x0 = random.randint(box.x0, box.x1 - size - 1)
        x1 = x0 + size

        y0 = random.randint(box.y0, box.y1 - size - 1)
        y1 = y0 + size

        yield BoundingBox(x0, y0, x1, y1)


def test_trees():
    import time

    WIDTH = 2 ** 13
    HEIGHT = 2 ** 13
    SIZE = 2 ** 5

    region_box = BoundingBox(0, 0, WIDTH, HEIGHT)

    # boxes = list(generate_small_things_within(100000, region_box))

    boxes = [BoundingBox(i * 32, j * 32, (i + 1) * 32, (j + 1) * 32) for i in range(WIDTH // SIZE) for j in
             range(HEIGHT // SIZE)]

    things = [(object(), box) for box in boxes]
    intersections = generate_things_within(10, region_box, min_size=(256, 256))

    intersections = [
        BoundingBox(i, i, i + 70, i + 70) for i in [random.randint(0, 2048 - 20)]
        # ] + [
        #     region_box
    ]

    trees = []

    load_times = []

    for tree in [NaiveSpace(region_box), QuadTree(region_box)]:
        print(tree.__class__.__name__)
        print("#" * 40)

        start = time.time()
        for i, (thing, box) in enumerate(things):
            tree.insert(thing, box)

            if i % 10000 == 0:
                print(i, f"{time.time() - start:.2f}s")
        end = time.time()

        print(f"   Inserted {len(things)} elements into tree in {end - start:.2f}s")
        load_times.append(end - start)
        trees.append(tree)

    print(load_times[0] / load_times[1], load_times[0], load_times[1])
    print()

    for intersection in intersections:
        tree_intersections = []
        runtimes = []

        for tree in trees:
            start = time.time()
            intersecting_elements = list(tree.get_intersecting(intersection))
            end = time.time()

            intersecting_elements = sorted(intersecting_elements, key=lambda x: x[1])
            print(f"    {tree.__class__.__name__}")
            print(f"    ({len(intersecting_elements)})")  # j": {intersecting_elements}")

            runtimes.append(end - start)

            tree_intersections.append(intersecting_elements)

        print(runtimes[0] / runtimes[1], runtimes[0], runtimes[1])

        difference = sorted(set(tree_intersections[0]).symmetric_difference(set(tree_intersections[1])),
                            key=lambda x: x[1])
        # print(f"Difference: {difference}")

        assert len(difference) == 0
    print()

    alltimes = []

    for tree in trees:
        start = time.time()
        list(tree.get_all())
        end = time.time()

        print(f"    {tree.__class__.__name__}")

        alltimes.append(end - start)

    print(alltimes[0] / alltimes[1], alltimes[0], alltimes[1])

    print()

    for name, index in [('first', 0), ('middle', len(things) // 2), ('last', len(things) - 1)]:

        element, box = things[index]

        print(f"Removing {name} (things[{index}]) from tree")

        remove_times = []
        for tree in trees:
            print(f"    {tree.__class__.__name__}")
            print(f"       Length Before: {len(tree)}")
            start = time.time()
            tree.remove(element, box)
            end = time.time()
            print(f"       Length After: {len(tree)}")
            print(f"       Took {end - start:.2f}s")
            remove_times.append(end - start)

        print(remove_times[0] / remove_times[1], remove_times[0], remove_times[1])
        print()

    print('done')


def main():
    random.seed(150)

    test_trees()


if __name__ == "__main__":
    main()
