import pygame
from constants import DARK_GRAY, GRAY, WHITE, BLUE, CYAN


class Button:
    def __init__(self, cx, cy, w, h, text,
                 color=BLUE, hover_color=CYAN,
                 text_color=WHITE, font_size=22):
        self.rect        = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
        self.text        = text
        self.color       = color
        self.hover_color = hover_color
        self.text_color  = text_color
        self.font        = pygame.font.SysFont("monospace", font_size, bold=True)
        self.hovered     = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surf):
        col = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surf, col, self.rect, border_radius=8)
        pygame.draw.rect(surf, WHITE, self.rect, 2, border_radius=8)
        lbl = self.font.render(self.text, True, self.text_color)
        surf.blit(lbl, lbl.get_rect(center=self.rect.center))


class TextInput:
    def __init__(self, cx, cy, w, h, placeholder="", max_len=12):
        self.rect        = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
        self.text        = ""
        self.placeholder = placeholder
        self.max_len     = max_len
        self.active      = False
        self.font        = pygame.font.SysFont("monospace", 22)
        self._tick       = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return "submit"
            elif len(self.text) < self.max_len:
                ch = event.unicode
                if ch.isalnum() or ch in ("_", "-", " "):
                    self.text += ch
        return None

    def draw(self, surf):
        self._tick += 1
        border = CYAN if self.active else GRAY
        pygame.draw.rect(surf, DARK_GRAY, self.rect, border_radius=6)
        pygame.draw.rect(surf, border,    self.rect, 2, border_radius=6)

        display = self.text if self.text else self.placeholder
        col     = WHITE if self.text else GRAY
        if self.active and self._tick % 60 < 30:
            display += "|"
        lbl = self.font.render(display, True, col)
        surf.blit(lbl, lbl.get_rect(center=self.rect.center))
