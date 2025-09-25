class Material:
    COLOR_MAP = {
        "white": (1.0, 1.0, 1.0),
        "black": (0.0, 0.0, 0.0),
        "red": (1.0, 0.0, 0.0),
        "green": (0.0, 1.0, 0.0),
        "blue": (0.0, 0.0, 1.0),
        "yellow": (1.0, 1.0, 0.0),
        "gray": (0.5, 0.5, 0.5),
        # Add more as needed
    }

    def __init__(self, kind="Steel", color="white"):
        self.kind = kind
        # self.color = color
        if isinstance(color, tuple) and len(color) == 3 and all(isinstance(c, (int, float)) for c in color):
            # Already RGB
            self.color = color
        else:
            self.color = self.COLOR_MAP.get(color.lower(), (1.0, 1.0, 1.0))  # default to white

    def attach(self, owner_object):
        return "material"
