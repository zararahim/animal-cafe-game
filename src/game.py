import arcade
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE


class AnimalCafeGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.CREAM)
        self.current_screen = "menu"
        self.score = 0

    def setup(self):
        self.score = 0
        self.current_screen = "menu"

    def on_draw(self):
        self.clear()

        if self.current_screen == "menu":
            arcade.draw_text("Animal Cafe Game", 320, 420, arcade.color.BROWN, 32)
            arcade.draw_text("Press ENTER to Start", 360, 360, arcade.color.BLACK, 20)

        elif self.current_screen == "game":
            arcade.draw_text("Gameplay coming soon", 320, 400, arcade.color.BLACK, 24)
            arcade.draw_text(f"Score: {self.score}", 40, 650, arcade.color.BLACK, 18)

        elif self.current_screen == "end":
            arcade.draw_text("Game Over", 400, 420, arcade.color.RED, 30)
            arcade.draw_text(f"Final Score: {self.score}", 390, 360, arcade.color.BLACK, 20)
            arcade.draw_text("Press R to Restart", 380, 320, arcade.color.GRAY, 18)

    def on_key_press(self, key, modifiers):
        if self.current_screen == "menu" and key == arcade.key.ENTER:
            self.current_screen = "game"
        elif self.current_screen == "game" and key == arcade.key.ESCAPE:
            self.current_screen = "end"
        elif self.current_screen == "end" and key == arcade.key.R:
            self.setup()