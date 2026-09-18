from .starfield import Starfield
from .matrix import MatrixRain
from .life import Life
from .fireworks import Fireworks

SCENES = {
    "starfield": Starfield,
    "matrix": MatrixRain,
    "life": Life,
    "fireworks": Fireworks,
}

__all__ = ["Starfield", "MatrixRain", "Life", "Fireworks", "SCENES"]
