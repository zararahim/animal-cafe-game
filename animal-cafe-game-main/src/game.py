# game.py - Main game window with menu, gameplay, and end screen states

import arcade
import json
import random
import os

from src.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    STATE_MENU, STATE_PLAYING, STATE_GAME_OVER,
    COLOR_BG, COLOR_TEXT, COLOR_SCORE, FONT_UI
)
from src.customer import Customer
from src.order_checker import OrderChecker
from src.ingredient_tray import IngredientTray

# this is the directory for the data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
GAME_DURATION = 180  # seconds per round
MACHINE_ONLY_INGREDIENTS = {"espresso shot", "steamed milk"}


def draw_rect(cx, cy, w, h, color):
    # Drawing the rectangles for the menu, game, and end screen
    try:
        arcade.draw_rectangle_filled(cx, cy, w, h, color)
    except AttributeError:
        arcade.draw_lbwh_rectangle_filled(cx - w / 2, cy - h / 2, w, h, color)


def draw_rect_outline(cx, cy, w, h, color, border=2):
    # Drawing the outlines of the rectangles for the menu, game, and end screen
    try:
        arcade.draw_rectangle_outline(cx, cy, w, h, color, border)
    except AttributeError:
        arcade.draw_lbwh_rectangle_outline(cx - w / 2, cy - h / 2, w, h, color, border)


class AnimalCafeGame(arcade.Window):
    # this is the constructor for the AnimalCafeGame class

    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        arcade.set_background_color(COLOR_BG)

        self.state = STATE_MENU
        self.recipes: dict = {}
        self.animal_preferences: dict = {}
        self.all_ingredients: list = []

        self.customers: list = []
        self.order_checker = None
        self.tray = None

        self.game_time_remaining = GAME_DURATION
        self.feedback_message = ""
        self.feedback_timer = 0.0
        self.spawn_timer = 0.0
        self.spawn_interval = 8.0
        self.show_recipe_book = False
        self.recipe_btn_x = 920
        self.recipe_btn_y = 620
        self.recipe_btn_w = 120
        self.recipe_btn_h = 42
        self.end_btn_x = 920
        self.end_btn_y = 572
        self.end_btn_w = 120
        self.end_btn_h = 38
        self.last_spawned_animal = None
        self.decor_textures = {}
        self.decor_sprites = {}

    def setup(self):
        # One-time game boot sequence: load JSON then initialize runtime state.
        self._load_data()
        self._reset_game()

    def _load_data(self):
        # Read recipe + personality config from data files.
        recipes_path = os.path.join(DATA_DIR, "recipes.json")
        preferences_path = os.path.join(DATA_DIR, "animal_preferences.json")
        try:
            with open(recipes_path) as f:
                self.recipes = json.load(f)
        except FileNotFoundError:
            self.recipes = {
                "Cupcake":   {"ingredients": ["flour", "sugar", "butter", "egg"]},
                "Cookie":    {"ingredients": ["flour", "sugar", "butter"]},
                "Muffin":    {"ingredients": ["flour", "sugar", "egg", "milk"]},
                "Croissant": {"ingredients": ["flour", "butter", "milk"]},
                "Cake Pop":  {"ingredients": ["flour", "sugar", "butter", "egg", "sprinkles"]},
            }
        try:
            with open(preferences_path) as f:
                self.animal_preferences = json.load(f)
        except FileNotFoundError:
            self.animal_preferences = {}
        # Build a tray list from recipe ingredients, excluding machine-only drink items.
        seen = set()
        for recipe in self.recipes.values():
            for ing in recipe["ingredients"]:
                if ing not in MACHINE_ONLY_INGREDIENTS:
                    seen.add(ing)
        self.all_ingredients = sorted(list(seen))

    def _reset_game(self):
        # Reset all per-round values so replay starts clean.
        self.customers = []
        self.order_checker = OrderChecker()
        self.tray = IngredientTray(self.all_ingredients)
        self.game_time_remaining = GAME_DURATION
        self.feedback_message = ""
        self.feedback_timer = 0.0
        self.spawn_timer = 0.0
        self.show_recipe_book = False
        self.last_spawned_animal = None
        self._spawn_customer()

    def _spawn_customer(self):
        if len(self.customers) >= 3:
            return
        x_positions = [200, 450, 700]
        # Reserve lanes by destination so arriving customers don't overlap later.
        occupied = {int(c.target_x) for c in self.customers}
        available = [x for x in x_positions if x not in occupied]
        if not available:
            return
        x = random.choice(available)
        animal_pool = list(self.animal_preferences.keys()) or Customer.ANIMAL_TYPES
        # did this in order to avoid getting the exact same animal back-to-back
        if len(animal_pool) > 1 and self.last_spawned_animal in animal_pool:
            animal_pool = [a for a in animal_pool if a != self.last_spawned_animal]
        chosen_animal = random.choice(animal_pool)
        # this helps w making the cafe feel alive (customers walk in from sides)
        start_x = -90 if random.random() < 0.5 else SCREEN_WIDTH + 90
        self.customers.append(
            Customer(
                x,
                420,
                self.recipes,
                self.animal_preferences,
                preferred_animal_type=chosen_animal,
                start_x=start_x,
            )
        )
        self.last_spawned_animal = chosen_animal

    def on_update(self, delta_time: float):
        if self.state != STATE_PLAYING:
            return
        # Global round timer.
        self.game_time_remaining -= delta_time
        if self.game_time_remaining <= 0:
            self.game_time_remaining = 0
            self.state = STATE_GAME_OVER
            return
        # Update each customer and apply miss penalty when one leaves.
        for customer in self.customers[:]:
            customer.update(delta_time)
            if customer.is_leaving:
                self.order_checker.customer_left_without_serving()
                self.customers.remove(customer)
        # Spawn loop keeps up to 3 active lanes.
        self.spawn_timer += delta_time
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0.0
            self._spawn_customer()
        # Feedback message auto-clears after a short duration.
        if self.feedback_timer > 0:
            self.feedback_timer -= delta_time
            if self.feedback_timer <= 0:
                self.feedback_message = ""

    def on_draw(self):
        self.clear()
        if self.state == STATE_MENU:
            self._draw_menu()
        elif self.state == STATE_PLAYING:
            self._draw_game()
        elif self.state == STATE_GAME_OVER:
            self._draw_game_over()

    def _draw_menu(self):
        draw_rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT, (255, 220, 180))
        arcade.draw_text("Animal Cafe", SCREEN_WIDTH // 2, 500, COLOR_TEXT, 52, anchor_x="center", bold=True, font_name=FONT_UI)
        arcade.draw_text("Serve adorable animal customers before their patience runs out!",
                         SCREEN_WIDTH // 2, 400, COLOR_TEXT, 18, anchor_x="center", font_name=FONT_UI)
        arcade.draw_text("Click ingredients -> Press SERVE -> Score points!",
                         SCREEN_WIDTH // 2, 355, COLOR_TEXT, 16, anchor_x="center", font_name=FONT_UI)
        draw_rect(SCREEN_WIDTH // 2, 260, 200, 60, (180, 100, 60))
        arcade.draw_text("PLAY", SCREEN_WIDTH // 2, 245, arcade.color.WHITE, 28, anchor_x="center", bold=True, font_name=FONT_UI)

    def _draw_game(self):
        draw_rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG)
        self._draw_kitchen()
        draw_rect(SCREEN_WIDTH // 2, 300, SCREEN_WIDTH, 20, (180, 120, 80))
        for customer in self.customers:
            customer.draw()
        self.tray.draw()
        self._draw_recipe_button()
        self._draw_end_game_button()
        if self.show_recipe_book:
            self._draw_recipe_book()
        arcade.draw_text(f"Score: {self.order_checker.total_score}",
                         20, SCREEN_HEIGHT - 40, COLOR_SCORE, 22, bold=True, font_name=FONT_UI)
        mins = int(self.game_time_remaining) // 60
        secs = int(self.game_time_remaining) % 60
        arcade.draw_text(f"Time: {mins}:{secs:02d}",
                         SCREEN_WIDTH - 18, SCREEN_HEIGHT - 40, COLOR_TEXT, 22,
                         bold=True, font_name=FONT_UI, anchor_x="right")
        if self.feedback_message:
            feedback_y = SCREEN_HEIGHT // 2 - 40
            draw_rect(SCREEN_WIDTH // 2, feedback_y + 10, 460, 52, (255, 248, 230))
            draw_rect_outline(SCREEN_WIDTH // 2, feedback_y + 10, 460, 52, (120, 80, 50), 2)
            arcade.draw_text(
                self.feedback_message,
                SCREEN_WIDTH // 2,
                feedback_y,
                arcade.color.DARK_GREEN,
                22,
                anchor_x="center",
                bold=True,
                font_name=FONT_UI,
            )

    def _draw_kitchen(self):
  
        # Customer lane wall and bottom kitchen floor.
        draw_rect(SCREEN_WIDTH // 2, 510, SCREEN_WIDTH, 380, (247, 228, 201))
        draw_rect(SCREEN_WIDTH // 2, 220, SCREEN_WIDTH, 160, (230, 186, 140))

        # String lights near the top for cozy cafe vibes.
        draw_rect(SCREEN_WIDTH // 2, 646, SCREEN_WIDTH - 80, 3, (120, 90, 70))
        for bulb_x in range(90, 930, 70):
            draw_rect(bulb_x, 636, 10, 16, (255, 232, 150))
            draw_rect_outline(bulb_x, 636, 10, 16, (180, 135, 85), 1)

        # Two simple windows behind customers.
        for cx in (310, 690):
            draw_rect(cx, 520, 300, 150, (95, 180, 210))
            draw_rect_outline(cx, 520, 300, 150, (140, 95, 65), 3)
            draw_rect(cx, 520, 6, 144, (210, 230, 235))
            draw_rect(cx, 520, 294, 6, (210, 230, 235))

        # Wall menu/chalkboard in the center.
        draw_rect(SCREEN_WIDTH // 2, 600, 210, 70, (72, 64, 56))
        draw_rect_outline(SCREEN_WIDTH // 2, 600, 210, 70, (130, 90, 60), 3)
        arcade.draw_text("Today's Bakes", SCREEN_WIDTH // 2, 612, (245, 235, 210), 11,
                         anchor_x="center", font_name=FONT_UI, bold=True)
        arcade.draw_text("Cupcake | Berry Bread", SCREEN_WIDTH // 2, 594, (230, 225, 205), 9,
                         anchor_x="center", font_name=FONT_UI)
        arcade.draw_text("Fish Cake | Latte | Coffee", SCREEN_WIDTH // 2, 580, (230, 225, 205), 9,
                         anchor_x="center", font_name=FONT_UI)

        # Kitchen station strip between bar and ingredient tray.
        draw_rect(SCREEN_WIDTH // 2, 205, SCREEN_WIDTH, 92, (170, 108, 68))
        draw_rect_outline(SCREEN_WIDTH // 2, 205, SCREEN_WIDTH, 92, (110, 70, 45), 2)
        for seam_x in (250, 500, 750):
            draw_rect(seam_x, 205, 6, 88, (132, 83, 55))

        # Cake display case.
        draw_rect(450, 184, 390, 78, (205, 190, 175))
        draw_rect_outline(450, 184, 390, 78, (110, 80, 58), 2)
        draw_rect(450, 197, 366, 44, (220, 245, 255))
        draw_rect_outline(450, 197, 366, 44, (150, 185, 205), 2)
        draw_rect(450, 170, 382, 4, (160, 120, 90))
        self._draw_decor_image("cupcake_item.png", 320, 180, 58)
        self._draw_decor_image("berry_tart_item.png", 580, 180, 58)

        # Coffee station on the far right with full machine visible.
        self._draw_decor_image("coffee_machine.png", 905, 183, 125)
        self._draw_decor_image("coffee_cup.png", 842, 168, 42)

        # Small counter plants for extra decor.
        for pot_x in (58, 944):
            draw_rect(pot_x, 332, 34, 18, (170, 95, 74))
            draw_rect_outline(pot_x, 332, 34, 18, (110, 65, 48), 2)
            for leaf_x, leaf_y in ((pot_x - 10, 348), (pot_x, 354), (pot_x + 10, 348)):
                draw_rect(leaf_x, leaf_y, 10, 16, (90, 150, 92))

    def _get_decor_texture(self, filename: str):
        if filename in self.decor_textures:
            return self.decor_textures[filename]
        image_path = os.path.join(DATA_DIR, "..", "assets", "images", filename)
        try:
            texture = arcade.load_texture(image_path)
        except Exception:
            texture = None
        self.decor_textures[filename] = texture
        return texture

    def _draw_decor_image(self, filename: str, center_x: float, center_y: float, target_width: float):
        texture = self._get_decor_texture(filename)
        if texture is None:
            return
        sprite_key = f"{filename}:{target_width}"
        sprite = self.decor_sprites.get(sprite_key)
        if sprite is None:
            points = getattr(texture, "hit_box_points", []) or []
            if points:
                xs = [p[0] for p in points]
                visible_w = max(1.0, max(xs) - min(xs))
            else:
                visible_w = max(1.0, float(texture.width))
            scale = target_width / visible_w
            sprite = arcade.Sprite(texture, scale=scale)
            self.decor_sprites[sprite_key] = sprite
        sprite.center_x = center_x
        sprite.center_y = center_y
        arcade.draw_sprite(sprite, pixelated=True)

    def _draw_recipe_button(self):
        draw_rect(self.recipe_btn_x, self.recipe_btn_y, self.recipe_btn_w, self.recipe_btn_h, (90, 110, 180))
        draw_rect_outline(self.recipe_btn_x, self.recipe_btn_y, self.recipe_btn_w, self.recipe_btn_h, (40, 50, 100), 2)
        label = "Recipes" if not self.show_recipe_book else "Hide"
        arcade.draw_text(label, self.recipe_btn_x, self.recipe_btn_y - 8,
                         arcade.color.WHITE, 14, anchor_x="center", bold=True, font_name=FONT_UI)

    def _draw_end_game_button(self):
        # Button lets player end the round early.
        draw_rect(self.end_btn_x, self.end_btn_y, self.end_btn_w, self.end_btn_h, (185, 84, 72))
        draw_rect_outline(self.end_btn_x, self.end_btn_y, self.end_btn_w, self.end_btn_h, (115, 45, 38), 2)
        arcade.draw_text(
            "End Game",
            self.end_btn_x,
            self.end_btn_y - 7,
            arcade.color.WHITE,
            13,
            anchor_x="center",
            bold=True,
            font_name=FONT_UI,
        )

    def _recipe_lines(self, name: str, ingredients: list, max_chars: int = 40) -> list:
        parts = [str(p) for p in ingredients]
        prefix = f"{name}: "
        line1 = prefix
        idx = 0
        while idx < len(parts):
            sep = "" if line1.endswith(": ") else ", "
            candidate = line1 + sep + parts[idx]
            if len(candidate) <= max_chars or line1 == prefix:
                line1 = candidate
                idx += 1
            else:
                break

        if idx >= len(parts):
            return [line1]

        remaining = ", ".join(parts[idx:])
        # did this in order to keep long recipe text from getting cut off in the panel
        line2 = "   " + remaining
        if len(line2) > max_chars:
            line2 = line2[: max_chars - 1] + "…"
        return [line1, line2]

    def _draw_recipe_book(self):
        panel_w = 360
        panel_h = 260
        margin = 22
        panel_x = SCREEN_WIDTH - panel_w / 2 - margin
        panel_y = SCREEN_HEIGHT - panel_h / 2 - 65
        draw_rect(panel_x, panel_y, panel_w, panel_h, (255, 245, 225))
        draw_rect_outline(panel_x, panel_y, panel_w, panel_h, (120, 80, 50), 3)
        arcade.draw_text("Recipe Book", panel_x, panel_y + 104, COLOR_TEXT, 20,
                         anchor_x="center", bold=True, font_name=FONT_UI)

        text_x = panel_x - 160
        y = panel_y + 76
        row_step = 16
        min_y = panel_y - panel_h / 2 + 12
        recipes = self.recipes.items()
        for name, data in recipes:
            lines = self._recipe_lines(name, data.get("ingredients", []))
            for line in lines:
                if y < min_y:
                    return
                arcade.draw_text(line, text_x, y, COLOR_TEXT, 10, font_name=FONT_UI)
                y -= row_step
            y -= 2

    def _draw_game_over(self):
        draw_rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT, (255, 210, 170))
        summary = self.order_checker.get_summary()
        arcade.draw_text("Game Over!", SCREEN_WIDTH // 2, 530, COLOR_TEXT, 50, anchor_x="center", bold=True, font_name=FONT_UI)
        arcade.draw_text(f"Final Score: {summary['score']}", SCREEN_WIDTH // 2, 440, COLOR_SCORE, 34, anchor_x="center", font_name=FONT_UI)
        arcade.draw_text(f"Orders Completed: {summary['completed']}", SCREEN_WIDTH // 2, 385, COLOR_TEXT, 22, anchor_x="center", font_name=FONT_UI)
        arcade.draw_text(f"Orders Missed: {summary['missed']}", SCREEN_WIDTH // 2, 345, COLOR_TEXT, 22, anchor_x="center", font_name=FONT_UI)
        arcade.draw_text(f"Accuracy: {summary['accuracy']}%", SCREEN_WIDTH // 2, 305, COLOR_TEXT, 22, anchor_x="center", font_name=FONT_UI)
        draw_rect(SCREEN_WIDTH // 2, 220, 220, 60, (180, 100, 60))
        arcade.draw_text("PLAY AGAIN", SCREEN_WIDTH // 2, 205, arcade.color.WHITE, 22, anchor_x="center", bold=True, font_name=FONT_UI)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.state == STATE_MENU:
            # Start button in menu.
            if abs(x - SCREEN_WIDTH // 2) <= 100 and abs(y - 260) <= 30:
                self._reset_game()
                self.state = STATE_PLAYING
        elif self.state == STATE_PLAYING:
            # Recipe toggle button in top-right.
            if (abs(x - self.recipe_btn_x) <= self.recipe_btn_w / 2 and
                    abs(y - self.recipe_btn_y) <= self.recipe_btn_h / 2):
                self.show_recipe_book = not self.show_recipe_book
                return
            # End button jumps straight to game-over screen.
            if (abs(x - self.end_btn_x) <= self.end_btn_w / 2 and
                    abs(y - self.end_btn_y) <= self.end_btn_h / 2):
                self.state = STATE_GAME_OVER
                return
            # Tray handles ingredient toggles, machine clicks, and submit click.
            action = self.tray.on_click(x, y)
            if action and action.startswith("machine:"):
                machine_item = action.split(":", 1)[1]
                self.feedback_message = f"{machine_item.title()} ready!"
                self.feedback_timer = 1.0
                return
            if action == "submit":
                self._handle_submit()
        elif self.state == STATE_GAME_OVER:
            # Play-again button on end screen.
            if abs(x - SCREEN_WIDTH // 2) <= 110 and abs(y - 220) <= 30:
                self._reset_game()
                self.state = STATE_PLAYING

    def on_key_press(self, symbol, modifiers):
        if self.state == STATE_MENU:
            if symbol in (arcade.key.ENTER, arcade.key.SPACE):
                self._reset_game()
                self.state = STATE_PLAYING
            return

        if self.state == STATE_PLAYING:
            if symbol == arcade.key.R:
                self.show_recipe_book = not self.show_recipe_book
            elif symbol in (arcade.key.SPACE, arcade.key.ENTER):
                self._handle_submit()
            elif symbol == arcade.key.C:
                self.tray.clear_selection()
            return

        if self.state == STATE_GAME_OVER:
            if symbol in (arcade.key.ENTER, arcade.key.SPACE):
                self._reset_game()
                self.state = STATE_PLAYING

    def on_mouse_motion(self, x, y, dx, dy):
        if self.state == STATE_PLAYING and self.tray is not None:
            self.tray.update_hover(x, y)

    def _handle_submit(self):
        if not self.customers:
            self.feedback_message = "No customers yet!"
            self.feedback_timer = 2.0
            return
        player_ingredients = self.tray.get_selected()
        if not player_ingredients:
            self.feedback_message = "Select some ingredients first!"
            self.feedback_timer = 2.0
            return

        # Let players serve any customer by choosing the strongest ingredient match.
        selected_set = set(player_ingredients)
        result_rank = {"perfect": 2, "good": 1, "miss": 0}

        def customer_match_score(c: Customer):
            # Preview score without mutating totals, then rank best target customer.
            preview = self.order_checker.preview_check_order(
                c.get_required_ingredients(),
                player_ingredients,
                c.get_patience_ratio(),
            )
            required_set = set(c.get_required_ingredients())
            overlap = len(required_set.intersection(selected_set))
            # Prefer better outcome first, then points, then ingredient overlap.
            return (
                result_rank.get(preview["result"], 0),
                preview["points"],
                overlap,
                c.get_patience_ratio(),
            )

        # Choose the customer with the strongest evaluated match.
        customer = max(self.customers, key=customer_match_score)

        result = self.order_checker.check_order(
            customer.get_required_ingredients(),
            player_ingredients,
            customer.get_patience_ratio(),
        )
        # Apply result to UI/game state and prep next order.
        self.feedback_message = result["message"]
        self.feedback_timer = 2.5
        customer.is_served = True
        self.customers.remove(customer)
        self.tray.clear_selection()
        self._spawn_customer()
