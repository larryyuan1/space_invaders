import pygame
import sys

from constants    import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from save_manager import SaveManager
from screens      import (
    MainMenuScreen, ShipSelectScreen, GameScreen,
    ResultScreen, LeaderboardScreen, UpgradeScreen,
)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock  = pygame.time.Clock()
        self.save   = SaveManager()

        # Daily login checked once at startup; reward shown on first menu visit only
        self._daily_reward = self.save.check_daily_login()
        self.current = MainMenuScreen(self.save, self._daily_reward)

    def run(self):
        while True:
            dt = self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                result = self.current.handle_event(event)
                if result:
                    self._go(*result)

            update_result = self.current.update(dt)
            if update_result:
                self._go(*update_result)

            self.current.draw(self.screen)
            pygame.display.flip()

    def _go(self, state, data):
        if state == "main_menu":
            # Only show daily notification once per session
            reward = self._daily_reward
            self._daily_reward = 0
            self.current = MainMenuScreen(self.save, reward)

        elif state == "ship_select":
            self.current = ShipSelectScreen(self.save)

        elif state == "game":
            self.current = GameScreen(data, self.save)

        elif state == "result":
            self.current = ResultScreen(data, self.save)

        elif state == "leaderboard":
            self.current = LeaderboardScreen(self.save)

        elif state == "upgrade":
            self.current = UpgradeScreen(self.save)


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
