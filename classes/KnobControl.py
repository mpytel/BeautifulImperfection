import pygame
import math
import json
import os

class KnobControl:
    def __init__(self, x, y, min_val, max_val, initial_val, label="", size=80):
        self.x = x
        self.y = y
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.size = size
        self.active = False
        self.is_hovered = False
        self.font = pygame.font.SysFont('Arial', 12)
        self.angle = self.value_to_angle(self.value)
        self.knob_frames = []
        self.load_knob_frames()
        # Track the previous mouse position for drag calculations
        self.prev_mouse_x = 0
        self.prev_mouse_y = 0
        # Track if this is the first update in a drag sequence
        self.drag_started = False

    def load_knob_frames(self):
        """Load knob frames from spritesheet or individual files"""
        try:
            # Try to load individual frame files first
            base_path = os.path.join('assets', 'Images', 'wt_knob')
            for i in range(1, 11):
                frame_path = os.path.join(base_path, f"knob{i:02d}.jpg")
                if os.path.exists(frame_path):
                    frame = pygame.image.load(frame_path)
                    # Scale the frame to the desired size
                    frame = pygame.transform.scale(frame, (self.size, self.size))
                    self.knob_frames.append(frame)
                else:
                    print(f"Warning: Could not find knob frame {frame_path}")

            if not self.knob_frames:
                # If individual frames weren't found, try loading from spritesheet
                json_path = os.path.join(base_path, "spritesheet.json.txt")
                spritesheet_path = os.path.join(base_path, "spritesheet.png")

                if os.path.exists(json_path) and os.path.exists(spritesheet_path):
                    with open(json_path, 'r') as f:
                        sheet_data = json.load(f)

                    spritesheet = pygame.image.load(spritesheet_path)

                    # Load each frame from the spritesheet
                    for i in range(1, 11):
                        frame_name = f"knob{i:02d}.jpg"
                        if frame_name in sheet_data['frames']:
                            frame_data = sheet_data['frames'][frame_name]['frame']
                            frame = spritesheet.subsurface((
                                frame_data['x'],
                                frame_data['y'],
                                frame_data['w'],
                                frame_data['h']
                            ))
                            # Scale the frame to the desired size
                            frame = pygame.transform.scale(frame, (self.size, self.size))
                            self.knob_frames.append(frame)
                        else:
                            print(f"Warning: Frame {frame_name} not found in spritesheet data")
                else:
                    print("Warning: Could not find spritesheet or its JSON data")

            # If we still don't have frames, create a fallback
            if not self.knob_frames:
                self.create_fallback_frames()

        except Exception as e:
            print(f"Error loading knob frames: {e}")
            self.create_fallback_frames()

    def create_fallback_frames(self):
        """Create simple fallback frames if loading fails"""
        self.knob_frames = []
        for i in range(10):
            # Create a simple knob image
            frame = pygame.Surface((self.size, self.size), pygame.SRCALPHA)

            # Draw knob body
            pygame.draw.circle(frame, (200, 200, 200), (self.size//2, self.size//2), self.size//2)
            pygame.draw.circle(frame, (100, 100, 100), (self.size//2, self.size//2), self.size//2, 2)

            # Draw indicator line at the appropriate angle
            # angle_rad = math.radians(i * 30)  # 0 to 270 degrees across 10 frames
            # line_length = self.size * 0.4
            # end_x = self.size//2 + line_length * math.cos(angle_rad)
            # end_y = self.size//2 + line_length * math.sin(angle_rad)
            # pygame.draw.line(frame, (50, 50, 50), (self.size//2, self.size//2), (end_x, end_y), 3)

            self.knob_frames.append(frame)

    def value_to_angle(self, value):
        """Convert a value to an angle (0-270 degrees)"""
        # Map value from min_val-max_val to 0-270 degrees
        ratio = (value - self.min_val) / (self.max_val - self.min_val)
        return ratio * 270  # 270 degrees is the full range of the knob

    def angle_to_value(self, angle):
        """Convert an angle (0-270 degrees) to a value"""
        # Clamp angle to 0-270 range
        angle = max(0, min(270, angle))
        # Map angle from 0-270 to min_val-max_val
        ratio = angle / 270
        return self.min_val + ratio * (self.max_val - self.min_val)

    def get_frame_index(self):
        """Get the appropriate frame index based on current value"""
        # Map value to frame index (0-9)
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        index = int(ratio * 9)  # 9 because we have 10 frames (0-9)
        return max(0, min(9, index))  # Clamp to 0-9 range

    def get_drag_feedback(self):
        """Get visual feedback parameters based on drag state"""
        # This can be used to create visual effects when the knob is turned
        # Returns a tuple of (color, size, opacity) for visual effects
        if not self.active:
            return ((255, 255, 255), 0, 0)  # No effect when not dragging

        # Calculate how far the knob has been turned as a percentage
        turn_percent = (self.value - self.min_val) / (self.max_val - self.min_val)

        # Color shifts from blue to green to red as the knob is turned
        if turn_percent < 0.5:
            # Blue to green (0% to 50%)
            r = int(turn_percent * 2 * 255)
            g = int(turn_percent * 2 * 255)
            b = int(255 - turn_percent * 2 * 255)
        else:
            # Green to red (50% to 100%)
            r = int(255)
            g = int(255 - (turn_percent - 0.5) * 2 * 255)
            b = 0

        # Size increases slightly as the knob is turned
        size = int(self.size * (0.9 + turn_percent * 0.2))

        # Opacity pulses slightly when active
        opacity = 120 + int(abs(math.sin(pygame.time.get_ticks() / 200)) * 50)

        return ((r, g, b), size, opacity)

    def __init__(self, x, y, min_val, max_val, initial_val, label="", size=80):
        self.x = x
        self.y = y
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.size = size
        self.active = False
        self.is_hovered = False
        self.font = pygame.font.SysFont('Arial', 12)
        self.angle = self.value_to_angle(self.value)
        self.knob_frames = []
        self.load_knob_frames()
        # Track the previous mouse position for drag calculations
        self.prev_mouse_x = 0
        self.prev_mouse_y = 0
        # Track if this is the first update in a drag sequence
        self.drag_started = False

    def update(self, mouse_pos, mouse_pressed):
        """Update knob state based on mouse interaction"""
        x, y = mouse_pos

        # Calculate the center of the knob
        center_x = self.x + self.size//2
        center_y = self.y + self.size//2

        # Check if mouse is over knob
        dx = x - center_x
        dy = y - center_y
        distance = math.sqrt(dx*dx + dy*dy)
        self.is_hovered = distance <= self.size//2

        # Store previous value for threshold detection
        prev_value = self.value
        value_changed = False

        # Update active state
        if mouse_pressed and self.is_hovered:
            self.active = True
            # If this is the start of a drag, record the initial position
            if not self.drag_started:
                self.prev_mouse_x = x
                self.prev_mouse_y = y
                self.drag_started = True
                # Calculate initial angle directly from mouse position
                initial_angle = math.degrees(math.atan2(y - center_y, x - center_x))
                # Convert to 0-270 range for the knob
                # We want 0 at top (-90°) and 270 at 3/4 clockwise (180°)
                self.angle = (initial_angle + 90) % 360
                if self.angle > 270:
                    self.angle = 270
                # Update value based on angle
                self.value = self.angle_to_value(self.angle)
                value_changed = True
        elif not mouse_pressed:
            self.active = False
            self.drag_started = False

        # Update value if active and not the first click
        if self.active and not value_changed:
            # Direct angle calculation from current mouse position
            current_angle = math.degrees(math.atan2(y - center_y, x - center_x))

            # Convert to 0-270 range for the knob (0 at top, 270 at 3/4 clockwise)
            adjusted_angle = (current_angle + 90) % 360
            if adjusted_angle > 270:
                adjusted_angle = 270

            # Update value based on the new angle
            self.value = self.angle_to_value(adjusted_angle)
            self.angle = adjusted_angle

            # Store current mouse position for next update
            self.prev_mouse_x = x
            self.prev_mouse_y = y

            # Check if we crossed a threshold
            self.check_threshold_crossed(prev_value, self.value)

            return True  # Value changed

        return value_changed  # Return whether value changed

    def check_threshold_crossed(self, old_value, new_value):
        """Check if the knob value crossed a significant threshold"""
        # Define thresholds for difficulty levels
        thresholds = [2, 4, 8]  # No Target/Easy, Easy/Normal, Normal/Hard

        # Check if we crossed any threshold
        for threshold in thresholds:
            if (old_value <= threshold < new_value) or (old_value >= threshold > new_value):
                # We crossed a threshold - provide feedback
                # This is where you could play a sound or add a visual effect
                # For now, we'll just print to the console
                print(f"Crossed difficulty threshold: {threshold}")

                # Return the threshold that was crossed
                return threshold

        return None

    def draw(self, surface):
        """Draw the knob control"""
        # Draw the appropriate knob frame
        frame_index = self.get_frame_index()
        if 0 <= frame_index < len(self.knob_frames):
            surface.blit(self.knob_frames[frame_index], (self.x, self.y))

        # Get visual feedback parameters
        feedback_color, feedback_size, feedback_opacity = self.get_drag_feedback()

        # Calculate center of knob
        center_x = self.x + self.size//2
        center_y = self.y + self.size//2

        # Draw a highlight effect when the knob is being dragged
        if self.active:
            # Draw a glow effect
            glow = pygame.Surface((self.size + 20, self.size + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow, feedback_color + (feedback_opacity,),
                              (glow.get_width()//2, glow.get_height()//2),
                              self.size//2 + 5)
            surface.blit(glow, (self.x - 10, self.y - 10))

        # Always draw the indicator line to show current position
        # indicator_length = self.size * 0.4
        # indicator_angle = math.radians(self.angle - 90)  # Adjust angle to match our coordinate system
        # indicator_end_x = center_x + indicator_length * math.cos(indicator_angle)
        # indicator_end_y = center_y + indicator_length * math.sin(indicator_angle)

        # Draw a thicker line when active
        # line_width = 3 if self.active else 2
        # line_color = (255, 0, 0) if self.active else (0, 0, 0)
        # pygame.draw.line(surface, line_color, (center_x, center_y),
        #                 (indicator_end_x, indicator_end_y), line_width)

        # Draw a small circle at the end of the indicator line
        # pygame.draw.circle(surface, line_color, (int(indicator_end_x), int(indicator_end_y)),
        #                   line_width + 1)

        # Draw label
        if self.label:
            label_text = self.font.render(self.label, True, (0, 0, 0))
            surface.blit(label_text, (self.x + self.size//2 - label_text.get_width()//2, self.y - 20))

        # Draw value
        value_text = self.font.render(f"{int(self.value)}", True, (0, 0, 0))
        surface.blit(value_text, (self.x + self.size//2 - value_text.get_width()//2, self.y + self.size + 5))

        # Draw difficulty labels
        if self.min_val == 1 and self.max_val == 10:  # Only for difficulty knob
            # No target
            if self.value <= 2:
                diff_text = self.font.render("No Target", True, (100, 100, 100))
            # Easy
            elif self.value <= 4:
                diff_text = self.font.render("Easy", True, (0, 150, 0))
            # Normal
            elif self.value <= 8:
                diff_text = self.font.render("Normal", True, (0, 0, 150))
            # Hard
            else:
                diff_text = self.font.render("Hard", True, (150, 0, 0))

            surface.blit(diff_text, (self.x + self.size + 10, self.y + self.size//2 - diff_text.get_height()//2))
