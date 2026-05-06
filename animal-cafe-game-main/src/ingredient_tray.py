# ingredient_tray.py - Manages clickable ingredients the player can select
# Owner: Zara
import arcade
import math
from src.constants import FONT_UI


def draw_rect(cx, cy, w, h, color):
    try:
        arcade.draw_rectangle_filled(cx, cy, w, h, color)
    except AttributeError:
        arcade.draw_lbwh_rectangle_filled(cx - w / 2, cy - h / 2, w, h, color)


def draw_rect_outline(cx, cy, w, h, color, border=2):
    try:
        arcade.draw_rectangle_outline(cx, cy, w, h, color, border)
    except AttributeError:
        arcade.draw_lbwh_rectangle_outline(cx - w / 2, cy - h / 2, w, h, color, border)


class Ingredient:
    # A clickable ingredient on the tray.

    def __init__(self, name: str, x: float, y: float, width=110, height=44):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.selected = False

    def is_clicked(self, click_x: float, click_y: float) -> bool:
        return (abs(click_x - self.x) <= self.width / 2 and
                abs(click_y - self.y) <= self.height / 2)

    def toggle(self):
        self.selected = not self.selected

    def draw(self):
        color = (255, 240, 150) if self.selected else (245, 225, 180)
        border = (200, 100, 0) if self.selected else (120, 70, 30)
        draw_rect(self.x, self.y, self.width, self.height, color)
        draw_rect_outline(self.x, self.y, self.width, self.height, border, 3 if self.selected else 1)
        arcade.draw_text(self.name, self.x, self.y - 8, (80, 40, 20), 11,
                         anchor_x="center", width=self.width - 4, align="center", font_name=FONT_UI)


class IngredientTray:
    # Displays all available ingredients at the bottom of the screen.

    def __init__(self, all_ingredients: list, start_x=90, top_row_y=96, spacing=125):
        self.ingredients = []
        self.machine_selected = set()
        # Arrange ingredient buttons in a compact grid.
        max_columns = 6
        row_gap = 52
        for i, name in enumerate(all_ingredients):
            col = i % max_columns
            row = i // max_columns
            x = start_x + col * spacing
            y = top_row_y - row * row_gap
            self.ingredients.append(Ingredient(name, x, y))

        self.submit_x = 880
        self.submit_y = 70
        self.submit_w = 110
        self.submit_h = 55

        # Simple drink station controls.
        self.espresso_x = 780
        self.espresso_y = 212
        self.milk_x = 848
        self.milk_y = 212
        self.machine_radius = 22
        self.hover_machine = None

    def _machine_button_clicked(self, x: float, y: float, bx: float, by: float) -> bool:
        return math.hypot(x - bx, y - by) <= self.machine_radius

    def on_click(self, x: float, y: float):
        # Regular ingredient buttons.
        for ing in self.ingredients:
            if ing.is_clicked(x, y):
                ing.toggle()
                return "ingredient"
        # this helps w making drinks feel interactive (machine actions like a mini station)
        if self._machine_button_clicked(x, y, self.espresso_x, self.espresso_y):
            self._toggle_machine_ingredient("espresso shot")
            return "machine:espresso shot"
        if self._machine_button_clicked(x, y, self.milk_x, self.milk_y):
            self._toggle_machine_ingredient("steamed milk")
            return "machine:steamed milk"
        if (abs(x - self.submit_x) <= self.submit_w / 2 and
                abs(y - self.submit_y) <= self.submit_h / 2):
            return "submit"
        return None

    def _toggle_machine_ingredient(self, ingredient_name: str):
        # Clicking again removes the machine ingredient (toggle behavior).
        if ingredient_name in self.machine_selected:
            self.machine_selected.remove(ingredient_name)
        else:
            self.machine_selected.add(ingredient_name)

    def update_hover(self, x: float, y: float):
        # Track hover state so we can show context labels near machine buttons.
        if self._machine_button_clicked(x, y, self.espresso_x, self.espresso_y):
            self.hover_machine = "coffee"
        elif self._machine_button_clicked(x, y, self.milk_x, self.milk_y):
            self.hover_machine = "milk"
        else:
            self.hover_machine = None

    def get_selected(self) -> list:
        selected = [ing.name for ing in self.ingredients if ing.selected]
        # did this in order to combine normal ingredients + machine ingredients in one order
        return selected + sorted(self.machine_selected)

    def clear_selection(self):
        # Clear both tray selections and drink machine selections after serve/reset.
        for ing in self.ingredients:
            ing.selected = False
        self.machine_selected.clear()

    def draw(self):
        # Bottom counter panel behind ingredients.
        draw_rect(500, 80, 1000, 140, (200, 150, 100))
        try:
            arcade.draw_line(0, 145, 1000, 145, (80, 40, 20), 3)
        except Exception:
            pass
        for ing in self.ingredients:
            ing.draw()

        # Drink station buttons
        espresso_on = "espresso shot" in self.machine_selected
        milk_on = "steamed milk" in self.machine_selected

        espresso_color = (160, 110, 75) if espresso_on else (134, 89, 57)
        milk_color = (240, 245, 250) if milk_on else (228, 235, 243)
        arcade.draw_circle_filled(self.espresso_x, self.espresso_y, self.machine_radius, espresso_color)
        arcade.draw_circle_outline(self.espresso_x, self.espresso_y, self.machine_radius, (65, 40, 25), 3)
        arcade.draw_circle_filled(self.milk_x, self.milk_y, self.machine_radius, milk_color)
        arcade.draw_circle_outline(self.milk_x, self.milk_y, self.machine_radius, (95, 110, 130), 3)
        arcade.draw_text("C", self.espresso_x, self.espresso_y - 8, (255, 255, 255), 17,
                         anchor_x="center", font_name=FONT_UI, bold=True)
        arcade.draw_text("M", self.milk_x, self.milk_y - 8, (80, 90, 110), 17,
                         anchor_x="center", font_name=FONT_UI, bold=True)

        if self.hover_machine == "coffee":
            draw_rect(self.espresso_x - 96, self.espresso_y + 2, 170, 26, (55, 45, 38))
            draw_rect_outline(self.espresso_x - 96, self.espresso_y + 2, 170, 26, (130, 102, 78), 2)
            arcade.draw_text("Brew Coffee", self.espresso_x - 96, self.espresso_y - 6,
                             (255, 245, 235), 10, anchor_x="center", font_name=FONT_UI, bold=True)
        elif self.hover_machine == "milk":
            draw_rect(self.milk_x - 86, self.milk_y + 2, 150, 26, (205, 214, 228))
            draw_rect_outline(self.milk_x - 86, self.milk_y + 2, 150, 26, (120, 135, 160), 2)
            arcade.draw_text("Pour Milk", self.milk_x - 86, self.milk_y - 6,
                             (45, 55, 75), 10, anchor_x="center", font_name=FONT_UI, bold=True)

        draw_rect(self.submit_x, self.submit_y, self.submit_w, self.submit_h, (40, 160, 40))
        arcade.draw_text("Serve!", self.submit_x, self.submit_y - 8,
                         (255, 255, 255), 14, anchor_x="center", bold=True, font_name=FONT_UI)
