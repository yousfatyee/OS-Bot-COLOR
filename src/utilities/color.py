from typing import List, Union

import cv2
import numpy as np


class Color:
    def __init__(self, lower: List[int], upper: List[int] = None):
        """
        Defines a color or range of colors. This class converts RGB colors to BGR to satisfy OpenCV's color format.
        Args:
            lower: The lower bound of the color range [R, G, B].
            upper: The upper bound of the color range [R, G, B]. Exclude this arg if you're defining a solid color.
        """
        self.lower = np.array(lower[::-1])
        self.upper = np.array(upper[::-1]) if upper else np.array(lower[::-1])


def isolate_colors(image: cv2.Mat, colors: Union[Color, List[Color]]) -> cv2.Mat:
    """
    Isolates ranges of colors within an image and saves a new resulting image.
    Args:
        image: The image to process.
        colors: A Color or list of Colors.
    Returns:
        The image with the isolated colors (all shown as white).
    """
    if not isinstance(colors, list):
        colors = [colors]
    # Generate masks for each color
    masks = [cv2.inRange(image, color.lower, color.upper) for color in colors]
    # Create black mask
    h, w = image.shape[:2]
    mask = np.zeros([h, w, 1], dtype=np.uint8)
    # Combine masks
    for mask_ in masks:
        mask = cv2.bitwise_or(mask, mask_)
    return mask


"""Solid colors"""
BLACK = Color([0, 0, 0])
BLUE = Color([0, 0, 255])
CYAN = Color([0, 255, 255])
GREEN = Color([0, 255, 0])
ORANGE = Color([255, 144, 64])
DARK_ORANGE = Color([255, 72, 32])
PINK = Color([255, 0, 231])
PURPLE = Color([170, 0, 255])
RED = Color([255, 0, 0])
WHITE = Color([255, 255, 255])
YELLOW = Color([255, 255, 0])
#DARK_BLUE = Color([0,15,255])
LIGHT_RED = Color([199,0,0])
GROUND_PURPLE = Color([170,0,255]) 
DARK_GREEN = Color([0,140,0]) 
DARK_RED = Color([54,0,0]) 
DARK_YELLOW = Color([149, 146, 15])
DARKER_YELLOW = Color([5, 255, 255])
DARK_BLUE = Color([20, 95, 94])
DARK_PURPLE = Color([106, 32, 110])
#DARK_GREEN = Color([18, 234, 28])
DARKER_GREEN = Color([0, 95, 0])
DARKER_GREEN_50 = Color([0, 95, 50])
DARK_ORANGE2 = Color([255, 120, 24])
#LIGHT_RED = Color([242, 125, 98])
LIGHT_PURPLE = Color([74, 133, 245])
LIGHT_BROWN = Color([166, 116, 80])
LIGHT_CYAN = Color([0, 183, 255])
TEXT_RED = Color([239, 16, 32])
DODGY_NECKLACE_RED = Color([255, 255, 1])
TEXT_GREEN = Color([6, 96, 12])
RED_50 = Color([0, 205, 225])
HIGH_PINK = Color([255, 55, 150])
SWAMP_GREEN = Color([125, 158, 0])
GROUND_PURPLE = Color([170, 0, 255])
ROCK_PINK = Color([255, 155, 150])
LIGHT_GREEN = Color([159, 250, 89])
ANTIFIRE = Color([151, 3, 42])
SERVANT_BLUE = Color([47,39,83])



"""Colors for use with semi-transparent text"""
OFF_CYAN = Color([0, 200, 200], [70, 255, 255])
OFF_GREEN = Color([0, 100, 0], [30, 255, 255])
OFF_ORANGE = Color([180, 100, 30], [255, 166, 103])
OFF_WHITE = Color([190, 190, 190], [255, 255, 255])
OFF_YELLOW = Color([190, 190, 0], [255, 255, 120])

"""Colors for use with minimap orb text"""
ORB_GREEN = Color([0, 255, 0], [255, 255, 0])
ORB_RED = Color([255, 0, 0], [255, 255, 0])
