import math

class HexMath:
    def __init__(self, size):
        self.size = size  # Radius of the hex
        self.width = size * 2
        self.height = math.sqrt(3) * size

    def hex_to_pixel(self, q, r):
        # Axial to Screen space conversion
        x = self.size * (3/2 * q)
        y = self.size * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
        return (x, y)

    def get_hex_corners(self, center_x, center_y):
        # Calculates the 6 points of a hexagon for drawing
        points = []
        for i in range(6):
            angle_deg = 60 * i
            angle_rad = math.pi / 180 * angle_deg
            px = center_x + self.size * math.cos(angle_rad)
            py = center_y + self.size * math.sin(angle_rad)
            points.append((px, py))
        return points