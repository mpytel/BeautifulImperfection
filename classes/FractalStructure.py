import pygame
import os
import datetime

# Colors
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LOVE = (255, 141, 0)    # #FF8D00 - Orange for love
LOGIC = (1, 148, 220)   # #0194DC - Blue for logic
BALANCE = (151, 218, 167)  # #97DAA7 - Green for perfect balance
WHITE = (255, 255, 255)

class FractalStructure:
     def __init__(self):
         self.elements = []
         self.harmony_score = 0
         self.level = 1
         self.previous_structure = None

     def add_element(self, element):
         self.elements.append(element)
         self.calculate_harmony()

     def calculate_harmony(self):
         # Calculate harmony based on balance and connections
         if not self.elements:
             self.harmony_score = 0
             return

         # Balance factor - how well distributed are love/logic ratios
         love_values = [e.love_logic_ratio for e in self.elements]
         avg_love = sum(love_values) / len(love_values)
         
         # Perfect balance at 0.5, decreases as it moves toward 0 or 1
         balance_factor = 1 - abs(0.5 - avg_love) * 2  # Now ranges from 0 to 1
         
         # Disharmony factor - increases with level and extreme love/logic values
         # Higher levels should have more potential for disharmony
         level_factor = min(1.0, self.level / 10)  # Caps at level 10
         
         # Calculate variance in love/logic ratios - more variance = more disharmony
         if len(love_values) > 1:
             variance = sum((x - avg_love) ** 2 for x in love_values) / len(love_values)
             # Scale variance to a reasonable range (0 to 1)
             variance_factor = min(1.0, variance * 10)
         else:
             variance_factor = 0
         
         # Connection factor - how well connected are elements
         # Too many or too few connections can create disharmony
         total_possible = len(self.elements) * (len(self.elements) - 1) / 2
         if total_possible == 0:
             connection_factor = 0
         else:
             total_connections = sum(len(e.connections) for e in self.elements) / 2
             connection_ratio = total_connections / total_possible
             
             # Optimal connection ratio is around 0.6 (not too sparse, not too dense)
             # Decreases as it moves toward 0 or 1
             connection_factor = 1 - abs(0.6 - connection_ratio) * 1.5
             connection_factor = max(0, min(1, connection_factor))  # Clamp between 0 and 1

         # Evolution factor - balanced evolution is better than extremes
         evolution_values = [e.level for e in self.elements]
         avg_evolution = sum(evolution_values) / len(evolution_values)
         
         # Calculate evolution variance - more variance = more disharmony
         if len(evolution_values) > 1:
             evo_variance = sum((x - avg_evolution) ** 2 for x in evolution_values) / len(evolution_values)
             # Scale variance to a reasonable range (0 to 1)
             evo_variance_factor = min(1.0, evo_variance * 0.5)
         else:
             evo_variance_factor = 0
         
         # Evolution harmony is highest when average level is around 2.5 (balanced)
         evolution_factor = 1 - abs(2.5 - avg_evolution) / 2.5
         evolution_factor = max(0, min(1, evolution_factor))  # Clamp between 0 and 1
         
         # Apply disharmony factors
         disharmony = (variance_factor * 0.3 + evo_variance_factor * 0.3 + level_factor * 0.4) * 0.5
         
         # Calculate overall harmony with disharmony reduction
         raw_harmony = (balance_factor * 0.4 + connection_factor * 0.3 + evolution_factor * 0.3)
         adjusted_harmony = raw_harmony * (1 - disharmony)
         
         # Ensure harmony is between 0 and 100%
         self.harmony_score = max(0, min(100, adjusted_harmony * 100))
         
         # Debug output
         print(f"Level: {self.level}, Harmony: {self.harmony_score:.1f}%, " +
               f"Balance: {balance_factor:.2f}, Connections: {connection_factor:.2f}, " +
               f"Evolution: {evolution_factor:.2f}, Disharmony: {disharmony:.2f}")

     def draw_harmony_meter(self, surface):
         # Draw harmony meter at the top of the screen
         meter_width = 300
         meter_height = 20
         x = surface.get_width() // 2 - meter_width // 2
         y = 20

         # Draw background
         pygame.draw.rect(surface, GRAY, (x, y, meter_width, meter_height))

         # Draw filled portion based on harmony score
         fill_width = int(meter_width * (self.harmony_score / 100))
         
         # Ensure fill_width is valid
         fill_width = max(0, min(meter_width, fill_width))
         
         # Color gradient based on harmony score
         if self.harmony_score < 33:
             # Low harmony - red to orange
             t = self.harmony_score / 33  # 0 to 1
             color = (
                 255,  # Red stays at max
                 max(0, min(255, int(t * 165))),  # Green increases
                 0     # Blue stays at 0
             )
         elif self.harmony_score < 66:
             # Medium harmony - orange to green
             t = (self.harmony_score - 33) / 33  # 0 to 1
             color = (
                 max(0, min(255, int(255 - t * 155))),  # Red decreases
                 max(0, min(255, int(165 + t * 90))),   # Green increases
                 max(0, min(255, int(t * 167)))         # Blue increases
             )
         else:
             # High harmony - green to blue/purple
             t = (self.harmony_score - 66) / 34  # 0 to 1
             color = (
                 max(0, min(255, int(100 + t * 55))),   # Red increases slightly
                 max(0, min(255, int(255 - t * 55))),   # Green decreases slightly
                 max(0, min(255, int(167 + t * 88)))    # Blue increases
             )

         # Draw filled portion if there's any harmony
         if fill_width > 0:
             pygame.draw.rect(surface, color, (x, y, fill_width, meter_height))

         # Draw border
         pygame.draw.rect(surface, BLACK, (x, y, meter_width, meter_height), 1)

         # Draw text
         font = pygame.font.SysFont('Arial', 12)
         text = font.render(f"Level {self.level} - Harmony: {self.harmony_score:.1f}%", True, BLACK)
         surface.blit(text, (x + meter_width // 2 - text.get_width() // 2, y + meter_height + 5))

     def save_structure(self):
         # Create a copy of the current structure for the next level
         self.previous_structure = {
             'elements': self.elements.copy(),
             'connections': [(self.elements.index(e),
                             [self.elements.index(c) for c in e.connections])
                            for e in self.elements],
             'shapes': [e.shape for e in self.elements],
             'love_logic_ratios': [e.love_logic_ratio for e in self.elements],
             'levels': [e.level for e in self.elements]
         }

     def save_image(self):
         # Create a directory for saved images if it doesn't exist
         if not os.path.exists('saved_fractals'):
             os.makedirs('saved_fractals')

         # Generate filename with timestamp and level
         timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
         filename = f"saved_fractals/{timestamp}_l{self.level:02d}.jpg"

         # Create a clean surface to draw only the fractal
         WIDTH, HEIGHT = 800, 600  # Assuming these are the screen dimensions
         fractal_surface = pygame.Surface((WIDTH, HEIGHT))
         fractal_surface.fill(WHITE)

         # Draw only the elements and their connections
         for element in self.elements:
             element.draw(fractal_surface)

         # Save just the fractal image
         pygame.image.save(fractal_surface, filename)
         return filename

     def advance_level(self):
         # Save the current structure for reference
         self.save_structure()

         # Clear current elements
         self.elements = []

         # Increment level
         self.level += 1

         # Reset harmony score
         self.harmony_score = 0

         return self.level
     def calculate_level_target(self):
         """Calculate the target harmony score for the current level"""
         # Base target starts at 40% for level 1 and increases more gradually
         base_target = 40 + 20 * (1 - (1 / (self.level + 0.5)))
         
         # Add some variation based on level number, but reduced
         variation = (self.level % 3) * 3  # 0, 3, or 6 percent variation
         
         # Return the target score (capped at 85%)
         return min(85, base_target + variation)

     def get_strategic_hint(self):
         """Provide a strategic hint based on current harmony factors"""
         # Get current factors
         love_values = [e.love_logic_ratio for e in self.elements]
         avg_love = sum(love_values) / len(love_values) if love_values else 0.5
         
         # Count connections
         total_possible = len(self.elements) * (len(self.elements) - 1) / 2
         total_connections = sum(len(e.connections) for e in self.elements) / 2 if self.elements else 0
         connection_ratio = total_connections / total_possible if total_possible > 0 else 0
         
         # Determine what's most needed
         if abs(avg_love - 0.5) > 0.2:
             if avg_love > 0.5:
                 return "Try adding more logic (down arrow) to some elements for better balance."
             else:
                 return "Try adding more love (up arrow) to some elements for better balance."
         elif connection_ratio < 0.3:
             return "Your structure needs more connections between elements."
         elif connection_ratio > 0.8:
             return "Your structure may have too many connections. Try a more elegant approach."
         else:
             # Check evolution levels
             evolution_values = [e.level for e in self.elements]
             avg_evolution = sum(evolution_values) / len(evolution_values) if evolution_values else 1
             if avg_evolution < 2:
                 return "Try evolving some elements (space key) to increase complexity."
             else:
                 return "Your structure is well-balanced. Consider changing some shapes (S key) for variety."

     def draw_target_indicator(self, surface, target=None):
         """Draw an indicator showing progress toward the level target"""
         # Calculate target for this level if not provided
         if target is None:
             target = self.calculate_level_target()
         
         # Draw at the top right of the screen
         WIDTH, HEIGHT = surface.get_width(), surface.get_height()
         x = WIDTH - 150
         y = 20
         width = 120
         height = 80
         
         # Draw background
         pygame.draw.rect(surface, (240, 240, 240), (x, y, width, height))
         pygame.draw.rect(surface, (0, 0, 0), (x, y, width, height), 1)
         
         # Draw title
         font = pygame.font.SysFont('Arial', 14)
         title = font.render(f"Level {self.level} Target", True, (0, 0, 0))
         surface.blit(title, (x + width//2 - title.get_width()//2, y + 5))
         
         # Draw target line - moved higher in the box
         target_y = y + 35  # Changed from y + height - 25 to y + 35
         pygame.draw.line(surface, (255, 0, 0), (x + 10, target_y), (x + width - 10, target_y), 2)
         
         # Draw target text - adjusted position
         target_text = font.render(f"{target:.1f}%", True, (255, 0, 0))
         surface.blit(target_text, (x + width - 30, target_y - 15))
         
         # Draw current harmony marker
         marker_x = x + 10 + (width - 20) * min(1, self.harmony_score / 100)
         pygame.draw.circle(surface, (0, 0, 255), (int(marker_x), target_y), 5)
         
         # Draw current harmony text - adjusted position
         current_text = font.render(f"{self.harmony_score:.1f}%", True, (0, 0, 255))
         surface.blit(current_text, (marker_x - 15, target_y + 5))
         
         # Draw status message
         status_font = pygame.font.SysFont('Arial', 12)
         if self.harmony_score >= target:
             status = "Target Achieved!"
             color = (0, 128, 0)  # Green
         else:
             progress = self.harmony_score / target * 100
             if progress >= 90:
                 status = "Almost there!"
                 color = (0, 0, 255)  # Blue
             elif progress >= 70:
                 status = "Good progress"
                 color = (128, 128, 0)  # Yellow
             elif progress >= 40:
                 status = "Keep working"
                 color = (255, 128, 0)  # Orange
             else:
                 status = "Just starting"
                 color = (255, 0, 0)  # Red
         
         status_text = status_font.render(status, True, color)
         surface.blit(status_text, (x + width//2 - status_text.get_width()//2, y + height - 15))
