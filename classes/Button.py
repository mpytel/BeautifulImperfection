import pygame

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)  # BLACK border

        font = pygame.font.SysFont('Arial', 12)
        text_surf = font.render(self.text, True, (0, 0, 0))  # BLACK text
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, mouse_click):
        return self.rect.collidepoint(mouse_pos) and mouse_click
