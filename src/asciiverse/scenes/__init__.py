from .starfield import Starfield
from .matrix import MatrixRain
from .life import Life
from .fireworks import Fireworks
from .fireworks_color import FireworksColor
from .matrix_color import MatrixColor

SCENES = {
    "starfield": Starfield,
    "matrix": MatrixRain,
    "life": Life,
    "fireworks": Fireworks,
    "fireworks-color": FireworksColor,
    "matrix-green": MatrixColor,
}

__all__ = [
    "Starfield",
    "MatrixRain",
    "Life",
    "Fireworks",
    "FireworksColor",
    "MatrixColor",
    "SCENES",
]
