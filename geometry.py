"""
Geometric operations
"""

__author__ = "Benjamin Martin and Paul Haley"
__date__ = "07/05/2019"
__copyright__ = "The University of Queensland, 2019"

def euclidean_square_distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    return (x2 - x1) ** 2 + (y2 - y1) ** 2

def positions_in_range(position1, position2, max_distance):
    return euclidean_square_distance(position1, position2) <= max_distance ** 2