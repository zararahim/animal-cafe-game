import arcade
from src.game import AnimalCafeGame
from src.constants import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE

def main():
    game = AnimalCafeGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game.setup()
    arcade.run()

if __name__ == "__main__":
    main()
