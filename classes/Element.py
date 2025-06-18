import pygame
import math
import random

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LOVE = (255, 141, 0)    # #FF8D00 - Orange for love
LOGIC = (1, 148, 220)   # #0194DC - Blue for logic
BALANCE = (151, 218, 167)  # #97DAA7 - Green for perfect balance
PURPLE = (128, 0, 128)

class Element:
    def __init__(self, x, y, size=30, love_logic_ratio=0.5, level=1, structure_pattern=None):
        self.x = x
        self.y = y
        self.size = size
        self.love_logic_ratio = love_logic_ratio  # 0 = pure logic, 1 = pure love
        self.level = level  # Evolution level
        self.color = self.calculate_color()
        self.dragging = False
        self.connections = []  # List of connected elements
        self.rect = pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)
        self.structure_pattern = structure_pattern  # For elements that represent previous structures
        self.shape = 0  # 0=circle, 1=square, 2=star, 3=hexagon, 4=pentagon, 5=triangle, 6=diamond, 7=cross, 8=heart, 9=crescent

        # If structure pattern is provided, try to get the shape from it
        if structure_pattern and 'shapes' in structure_pattern and structure_pattern['shapes']:
            # Use the first shape in the pattern as the default shape for this element
            self.shape = structure_pattern['shapes'][0]

        self.structure_scale_factor = 1.0  # Default scale factor for structure patterns
        self.evolve_direction = 'up'  # Default evolution direction

    def calculate_color(self):
        # Calculate color based on love/logic ratio
        # Love = #FF8D00 (orange)
        # Logic = #0194DC (blue)
        # Perfect balance (0.5) = #97DAA7 (green)

        if abs(self.love_logic_ratio - 0.5) < 0.05:
            # Close to perfect balance
            return BALANCE
        elif self.love_logic_ratio > 0.5:
            # More love than logic - blend between balance and love
            t = (self.love_logic_ratio - 0.5) * 2  # 0 to 1
            r = int(BALANCE[0] + t * (LOVE[0] - BALANCE[0]))
            g = int(BALANCE[1] + t * (LOVE[1] - BALANCE[1]))
            b = int(BALANCE[2] + t * (LOVE[2] - BALANCE[2]))
            return (r, g, b)
        else:
            # More logic than love - blend between balance and logic
            t = (0.5 - self.love_logic_ratio) * 2  # 0 to 1
            r = int(BALANCE[0] + t * (LOGIC[0] - BALANCE[0]))
            g = int(BALANCE[1] + t * (LOGIC[1] - BALANCE[1]))
            b = int(BALANCE[2] + t * (LOGIC[2] - BALANCE[2]))
            return (r, g, b)

    def draw(self, surface):
        # Update rectangle position
        self.rect = pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)

        # Draw connections first (so they appear behind elements)
        for connected_element in self.connections:
            pygame.draw.line(surface, PURPLE, (self.x, self.y),
                            (connected_element.x, connected_element.y), 3)  # Thicker connection lines

        # Draw element with fractal pattern based on level and type
        if self.structure_pattern:
            # This is a higher-level element containing a previous structure
            # First draw a background circle/shape with the element's color
            self.draw_shape(surface, self.x, self.y, self.size//2)
            # Then draw the structure pattern on top
            self.draw_structure_pattern(surface)
        else:
            # This is a regular element (level 1)
            self.draw_fractal(surface, self.x, self.y, self.size//2, self.level)

    def draw_structure_pattern(self, surface):
        # Only draw the pattern if it's valid
        if not self.structure_pattern or 'positions' not in self.structure_pattern or not self.structure_pattern['positions']:
            return

        # Get the positions from the pattern
        positions = self.structure_pattern['positions']
        if not positions:
            return

        # Calculate the bounding box of the original structure
        min_x = min(pos[0] for pos in positions)
        max_x = max(pos[0] for pos in positions)
        min_y = min(pos[1] for pos in positions)
        max_y = max(pos[1] for pos in positions)

        # Calculate the width and height of the original structure
        width = max(1, max_x - min_x)
        height = max(1, max_y - min_y)

        # Calculate the center of the original structure
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        # Calculate the scale factor to fit the structure inside this element
        # Use a larger scale factor to make the pattern more visible
        self.structure_scale_factor = min((self.size * 0.8) / width, (self.size * 0.8) / height)
        scale_factor = self.structure_scale_factor

        # Get original properties if available
        original_colors = self.structure_pattern.get('colors', [])
        original_shapes = self.structure_pattern.get('shapes', [])
        original_levels = self.structure_pattern.get('levels', [])
        original_love_logic = self.structure_pattern.get('love_logic_ratios', [])

        # Draw connections from the pattern using the element's color (for links only)
        if 'connections' in self.structure_pattern:
            for conn in self.structure_pattern['connections']:
                # Validate connection indices
                if isinstance(conn, tuple):
                    if len(conn) != 2:
                        continue
                    conn_idx = conn[0]
                    conn_targets = conn[1]
                elif isinstance(conn, list):
                    if len(conn) != 2:
                        continue
                    conn_idx = conn[0]
                    conn_targets = conn[1]
                else:
                    continue

                if conn_idx >= len(positions):
                    continue

                pos1 = positions[conn_idx]

                # Ensure conn_targets is a list
                if isinstance(conn_targets, tuple):
                    conn_targets = list(conn_targets)
                elif not isinstance(conn_targets, list):
                    continue

                for idx in conn_targets:
                    if idx >= len(positions):
                        continue

                    pos2 = positions[idx]

                    # Scale and center the positions relative to the element
                    x1 = self.x + (pos1[0] - center_x) * scale_factor
                    y1 = self.y + (pos1[1] - center_y) * scale_factor
                    x2 = self.x + (pos2[0] - center_x) * scale_factor
                    y2 = self.y + (pos2[1] - center_y) * scale_factor

                    # Draw the connection line using the element's color (current level's harmony)
                    # Use original colors if available for connections
                    conn_color = self.color
                    if conn_idx < len(original_colors) and idx < len(original_colors):
                        # Use a blend of the two node colors for the connection
                        color1 = original_colors[conn_idx]
                        color2 = original_colors[idx]
                        conn_color = (
                            (color1[0] + color2[0]) // 2,
                            (color1[1] + color2[1]) // 2,
                            (color1[2] + color2[2]) // 2
                        )

                    pygame.draw.line(surface, conn_color, (x1, y1), (x2, y2), 2)  # Slightly thinner lines

        # Draw nodes from the pattern with increased size and original properties
        for i, pos in enumerate(positions):
            # Scale and center the position relative to the element
            x = self.x + (pos[0] - center_x) * scale_factor
            y = self.y + (pos[1] - center_y) * scale_factor

            # Use original properties if available
            node_color = original_colors[i] if i < len(original_colors) else self.color
            node_shape = original_shapes[i] if i < len(original_shapes) else self.shape
            node_level = original_levels[i] if i < len(original_levels) else 1

            # Draw the node with increased size
            node_size = max(10, int(15 * scale_factor))  # Increased size for better visibility

            # For evolved elements, draw fractal patterns based on their level
            if node_level > 1:
                self.draw_node_fractal(surface, int(x), int(y), node_size, node_level, node_shape, node_color)
            else:
                # Draw the appropriate shape
                self.draw_node_shape(surface, int(x), int(y), node_size, node_shape, node_color)

    def draw_node_fractal(self, surface, x, y, size, depth, shape, color):
        """Draw a fractal pattern for a node based on its evolution level"""
        # Draw the main shape
        self.draw_node_shape(surface, x, y, size, shape, color)

        # Draw smaller shapes around it if evolved
        if depth > 1:
            num_shapes = min(depth * 2, 8)  # More shapes at higher levels
            for i in range(num_shapes):
                angle = 2 * math.pi * i / num_shapes
                new_x = x + int(size * 0.8 * math.cos(angle))
                new_y = y + int(size * 0.8 * math.sin(angle))
                new_size = size // 2

                # Recursive fractal pattern with decreasing depth
                # Use the same shape as the parent element
                self.draw_node_shape(surface, new_x, new_y, new_size, shape, color)

    def draw_node_shape(self, surface, x, y, size, shape, color):
        """Draw a specific shape for a node"""
        # Draw the shape based on the shape property
        if shape == 0:  # Circle
            pygame.draw.circle(surface, color, (x, y), size)
            pygame.draw.circle(surface, BLACK, (x, y), size, 1)

        elif shape == 1:  # Square
            rect = pygame.Rect(x - size, y - size, size * 2, size * 2)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)

        elif shape == 2:  # Star
            points = []
            for i in range(10):
                angle = math.pi/2 + 2 * math.pi * i / 10
                # Alternate between outer and inner points
                curr_size = size if i % 2 == 0 else size * 0.4
                px = x + curr_size * math.cos(angle)
                py = y + curr_size * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, BLACK, points, 1)

        elif shape == 3:  # Hexagon
            points = []
            for i in range(6):
                angle = 2 * math.pi * i / 6
                px = x + size * math.cos(angle)
                py = y + size * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, BLACK, points, 1)

        elif shape == 4:  # Pentagon
            points = []
            for i in range(5):
                angle = -math.pi/2 + 2 * math.pi * i / 5
                px = x + size * math.cos(angle)
                py = y + size * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, BLACK, points, 1)

        elif shape == 5:  # Triangle
            points = []
            for i in range(3):
                angle = -math.pi/2 + 2 * math.pi * i / 3
                px = x + size * math.cos(angle)
                py = y + size * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, BLACK, points, 1)

        elif shape == 6:  # Diamond
            points = [(x, y - size), (x + size, y), (x, y + size), (x - size, y)]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, BLACK, points, 1)

        elif shape == 7:  # Cross
            # Horizontal bar
            rect1 = pygame.Rect(x - size, y - size/3, size * 2, size * 2/3)
            # Vertical bar
            rect2 = pygame.Rect(x - size/3, y - size, size * 2/3, size * 2)
            pygame.draw.rect(surface, color, rect1)
            pygame.draw.rect(surface, color, rect2)
            pygame.draw.rect(surface, BLACK, rect1, 1)
            pygame.draw.rect(surface, BLACK, rect2, 1)

        elif shape == 8:  # Heart
            # Draw a heart shape
            heart_points = []
            for i in range(30):
                angle = i / 30 * 2 * math.pi
                px = x + size * (16 * math.sin(angle) ** 3) / 16
                py = y - size * (13 * math.cos(angle) - 5 * math.cos(2*angle) - 2 * math.cos(3*angle) - math.cos(4*angle)) / 16
                heart_points.append((px, py))
            pygame.draw.polygon(surface, color, heart_points)
            pygame.draw.polygon(surface, BLACK, heart_points, 1)

        elif shape == 9:  # Crescent
            # Draw a full circle for the base
            pygame.draw.circle(surface, color, (x, y), size)
            # Draw a slightly offset circle to create the crescent effect
            offset_x = x + size * 0.4
            offset_size = size * 0.9
            pygame.draw.circle(surface, WHITE, (int(offset_x), int(y)), int(offset_size))
            # Draw the outline
            pygame.draw.circle(surface, BLACK, (x, y), size, 1)
        else:
            # Default to circle if shape is unknown
            pygame.draw.circle(surface, color, (x, y), size)
            pygame.draw.circle(surface, BLACK, (x, y), size, 1)

    def draw_fractal(self, surface, x, y, size, depth):
        if depth <= 0:
            return

        # Draw main shape based on the shape property
        self.draw_shape(surface, x, y, size)

        # Draw smaller shapes around it if evolved
        if depth > 1:
            num_shapes = min(depth * 2, 8)  # More shapes at higher levels
            for i in range(num_shapes):
                angle = 2 * math.pi * i / num_shapes
                new_x = x + int(size * 0.8 * math.cos(angle))
                new_y = y + int(size * 0.8 * math.sin(angle))
                new_size = size // 2

                # Use the same shape as the parent element for sub-elements
                # Draw the shape directly instead of calling draw_shape to ensure shape consistency
                if self.shape == 0:  # Circle
                    pygame.draw.circle(surface, self.color, (new_x, new_y), new_size)
                    pygame.draw.circle(surface, BLACK, (new_x, new_y), new_size, 1)
                elif self.shape == 1:  # Square
                    rect = pygame.Rect(new_x - new_size, new_y - new_size, new_size * 2, new_size * 2)
                    pygame.draw.rect(surface, self.color, rect)
                    pygame.draw.rect(surface, BLACK, rect, 1)
                elif self.shape == 2:  # Star
                    points = []
                    for j in range(10):
                        angle_j = math.pi/2 + 2 * math.pi * j / 10
                        curr_size_j = new_size if j % 2 == 0 else new_size * 0.4
                        px = new_x + curr_size_j * math.cos(angle_j)
                        py = new_y + curr_size_j * math.sin(angle_j)
                        points.append((px, py))
                    pygame.draw.polygon(surface, self.color, points)
                    pygame.draw.polygon(surface, BLACK, points, 1)
                else:  # For other shapes, use the draw_shape method
                    self.draw_shape(surface, new_x, new_y, new_size)

    def draw_shape(self, surface, x, y, size):
        # Draw the shape based on the shape property
        if self.shape == 0:  # Circle
            pygame.draw.circle(surface, self.color, (x, y), size)
            pygame.draw.circle(surface, BLACK, (x, y), size, 1)

        elif self.shape == 1:  # Square
            rect = pygame.Rect(x - size, y - size, size * 2, size * 2)
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)

        elif self.shape == 2:  # Star
            points = []
            for i in range(10):
                angle = math.pi/2 + 2 * math.pi * i / 10
                # Alternate between outer and inner points
                curr_size = size if i % 2 == 0 else size * 0.4
                px = x + curr_size * math.cos(angle)
                py = y + curr_size * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, BLACK, points, 1)

        elif self.shape == 3:  # Hexagon
            points = []
            for i in range(6):
                angle = 2 * math.pi * i / 6
                px = x + size * math.cos(angle)
                py = y + size * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, BLACK, points, 1)

        elif self.shape == 4:  # Pentagon
            points = []
            for i in range(5):
                angle = -math.pi/2 + 2 * math.pi * i / 5
                px = x + size * math.cos(angle)
                py = y + size * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, BLACK, points, 1)

        elif self.shape == 5:  # Triangle
            points = []
            for i in range(3):
                angle = -math.pi/2 + 2 * math.pi * i / 3
                px = x + size * math.cos(angle)
                py = y + size * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, BLACK, points, 1)

        elif self.shape == 6:  # Diamond
            points = [(x, y - size), (x + size, y), (x, y + size), (x - size, y)]
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, BLACK, points, 1)

        elif self.shape == 7:  # Cross
            # Horizontal bar
            rect1 = pygame.Rect(x - size, y - size/3, size * 2, size * 2/3)
            # Vertical bar
            rect2 = pygame.Rect(x - size/3, y - size, size * 2/3, size * 2)
            pygame.draw.rect(surface, self.color, rect1)
            pygame.draw.rect(surface, self.color, rect2)
            pygame.draw.rect(surface, BLACK, rect1, 1)
            pygame.draw.rect(surface, BLACK, rect2, 1)

        elif self.shape == 8:  # Heart
            # Draw a heart shape
            heart_points = []
            for i in range(30):
                angle = i / 30 * 2 * math.pi
                px = x + size * (16 * math.sin(angle) ** 3) / 16
                py = y - size * (13 * math.cos(angle) - 5 * math.cos(2*angle) - 2 * math.cos(3*angle) - math.cos(4*angle)) / 16
                heart_points.append((px, py))
            pygame.draw.polygon(surface, self.color, heart_points)
            pygame.draw.polygon(surface, BLACK, heart_points, 1)

        elif self.shape == 9:  # Crescent
            # Draw a full circle for the base
            pygame.draw.circle(surface, self.color, (x, y), size)
            # Draw a slightly offset circle to create the crescent effect
            offset_x = x + size * 0.4
            offset_size = size * 0.9
            pygame.draw.circle(surface, WHITE, (int(offset_x), int(y)), int(offset_size))
            # Draw the outline
            pygame.draw.circle(surface, BLACK, (x, y), size, 1)

    def change_shape(self):
        # Cycle to the next shape
        self.shape = (self.shape + 1) % 10

        # For higher-level elements, we don't want to modify the structure pattern
        # This ensures changes only affect the selected element
        # The structure pattern represents the previous level's elements and should remain unchanged

        return self.shape

    def is_over(self, pos):
        # Check if the mouse is over this element
        return ((self.x - pos[0])**2 + (self.y - pos[1])**2) <= (self.size//2)**2

    def start_drag(self):
        self.dragging = True

    def end_drag(self):
        self.dragging = False

    def update_position(self, pos):
        if self.dragging:
            self.x, self.y = pos

    def adjust_love_logic(self, amount):
        # Adjust the love/logic ratio and update color
        self.love_logic_ratio = max(0, min(1, self.love_logic_ratio + amount))
        self.color = self.calculate_color()

        # For higher-level elements, we don't want to modify the structure pattern
        # This ensures changes only affect the selected element
        # The structure pattern represents the previous level's elements and should remain unchanged

    def evolve(self):
        # For elements in upper levels, cycle between min and max levels
        if self.structure_pattern:
            # If at max level, start decreasing
            if self.level >= 4:
                self.level -= 1
                print(f"Element decreased to level {self.level}")
            # If at min level, start increasing
            elif self.level <= 1:
                self.level += 1
                print(f"Element increased to level {self.level}")
            # Otherwise continue in current direction
            elif hasattr(self, 'evolve_direction') and self.evolve_direction == 'down':
                self.level -= 1
                print(f"Element decreased to level {self.level}")
            else:
                self.level += 1
                print(f"Element increased to level {self.level}")

            # Set direction for next evolution
            if self.level >= 4:
                self.evolve_direction = 'down'
            elif self.level <= 1:
                self.evolve_direction = 'up'

            # Update the structure pattern complexity
            if self.structure_pattern:
                self.structure_pattern = self.enhance_structure_pattern(self.structure_pattern)

            return True
        # For regular elements (level 1), just increase up to max level
        else:
            if self.level < 4:  # Maximum level cap
                self.level += 1
                print(f"Element increased to level {self.level}")
                return True
            return False

    def enhance_structure_pattern(self, pattern):
        # Add more detail to the structure pattern when evolving
        if not pattern or 'positions' not in pattern:
            return pattern

        # Add some additional points between existing ones
        new_positions = pattern['positions'].copy()
        new_connections = []

        # Copy existing connections - handle both list and tuple types
        for conn in pattern['connections']:
            if isinstance(conn, tuple):
                # If it's a tuple, convert to list format
                if len(conn) == 2:
                    new_connections.append([conn[0], list(conn[1]) if isinstance(conn[1], (list, tuple)) else []])
            elif isinstance(conn, list):
                # If it's a list, we can use copy
                new_connections.append(conn.copy())
            else:
                # Skip invalid connections
                continue

        # Add some detail points
        if len(pattern['positions']) > 1:
            for i in range(min(3, len(pattern['positions']))):
                idx1 = random.randint(0, len(pattern['positions'])-1)
                idx2 = (idx1 + 1) % len(pattern['positions'])

                pos1 = pattern['positions'][idx1]
                pos2 = pattern['positions'][idx2]

                # Create a new point between these two
                mid_x = (pos1[0] + pos2[0]) / 2 + random.uniform(-10, 10)
                mid_y = (pos1[1] + pos2[1]) / 2 + random.uniform(-10, 10)

                # Add the new point
                new_idx = len(new_positions)
                new_positions.append((mid_x, mid_y))

                # Connect it to the original points
                for existing_conn in new_connections:
                    if existing_conn[0] == idx1:
                        existing_conn[1].append(new_idx)
                    elif existing_conn[0] == idx2:
                        existing_conn[1].append(new_idx)

                # Add a new connection from this point
                new_connections.append([new_idx, [idx1, idx2]])

        return {
            'positions': new_positions,
            'connections': new_connections
        }

    def connect_to(self, other_element):
        # Connect this element to another
        if other_element not in self.connections:
            self.connections.append(other_element)
            other_element.connections.append(self)

    def create_child(self, elements):
        # Create a child element that inherits properties
        # Position the child nearby
        angle = random.uniform(0, 2 * math.pi)

        # Scale the distance based on the structure_scale_factor if this is a structure pattern element
        # Use a smaller distance to keep child elements closer to their parents
        if self.structure_pattern and hasattr(self, 'structure_scale_factor'):
            distance = self.size * 0.6  # Reduced distance factor
        else:
            distance = self.size * 0.8  # Reduced distance for regular elements too

        child_x = self.x + distance * math.cos(angle)
        child_y = self.y + distance * math.sin(angle)

        # Child inherits love/logic ratio with slight variation
        child_ratio = max(0, min(1, self.love_logic_ratio + random.uniform(-0.1, 0.1)))

        # Create the child element with the same structure pattern if this is a higher-level element
        child = Element(child_x, child_y, size=self.size,
                       love_logic_ratio=child_ratio, level=self.level,  # Inherit parent's level
                       structure_pattern=self.structure_pattern)

        # Child inherits parent's shape
        child.shape = self.shape

        # Child inherits parent's structure scale factor
        if hasattr(self, 'structure_scale_factor'):
            child.structure_scale_factor = self.structure_scale_factor

        # Connect child to parent
        self.connect_to(child)

        # Add to elements list
        elements.append(child)
        return child
