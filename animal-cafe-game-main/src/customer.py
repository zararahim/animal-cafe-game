import random
import os
import arcade
from src.constants import (
    MOOD_HAPPY, MOOD_IMPATIENT, MOOD_NORMAL,
    HAPPY_TIME, IMPATIENT_TIME, NORMAL_TIME, FONT_UI
)

# drawing the rectangles for the speech bubble and the patience bar
def draw_rect(cx, cy, w, h, color):
    try:
        arcade.draw_rectangle_filled(cx, cy, w, h, color)
    except AttributeError:
        arcade.draw_lbwh_rectangle_filled(cx - w / 2, cy - h / 2, w, h, color)

# drawing the outline of the rectangles for the speech bubble and the patience bar
def draw_rect_outline(cx, cy, w, h, color, border=2):
    try:
        arcade.draw_rectangle_outline(cx, cy, w, h, color, border)
    except AttributeError:
        arcade.draw_lbwh_rectangle_outline(cx - w / 2, cy - h / 2, w, h, color, border)


class Customer:
    # This class is used to create the customers that visit the cafe
    ANIMAL_TYPES = ["cat", "otter", "bunny", "fox", "sloth"]
    MOOD_OPTIONS = [MOOD_HAPPY, MOOD_IMPATIENT, MOOD_NORMAL]
    # types of food 
    SWEET_KEYWORDS = ("cake", "cookie", "muffin", "brownie", "tart", "cupcake", "roll", "pancake", "croissant", "pop")
    TEXTURE_FILES = {
        "cat": "cat.png",
        "otter": "otter.png",
        "bunny": "bunny.png",
        "fox": "fox.png",
        "sloth": "sloth.png",
    }
    ORDER_BUBBLE_FILE = "order_bubble.png"

    # this helps w giving each mood a visible personality in the bubble
    MOOD_EMOTICONS = {
        MOOD_HAPPY: ["( ˶ˆᗜˆ˵ )"],
        MOOD_IMPATIENT: ["૮(¬ ‸ ¬\")ა", "(•̀⤙•́ )"],
        MOOD_NORMAL: ["૮(˶ㅠ︿ㅠ)ა", "(っ˕ -｡)ᶻ 𝗓 𐰁"],
    }
    _texture_cache = {}
    _sprite_cache = {}
    _bubble_texture = None
    _bubble_sprite = None

    # this is the constructor for the Customer class
    def __init__(
        self,
        x: float,
        y: float,
        recipes: dict,
        animal_preferences: dict = None,
        preferred_animal_type: str = None,
        start_x: float = None,
    ):
        self.target_x = x
        self.x = start_x if start_x is not None else x
        self.y = y
        self.recipes = recipes
        self.animal_preferences = animal_preferences or {}

        # this helps w giving each customer a unique animal type
        available_animals = list(self.animal_preferences.keys()) or self.ANIMAL_TYPES
        if preferred_animal_type in available_animals:
            self.animal_type = preferred_animal_type
        else:
            self.animal_type = random.choice(available_animals)
        self.profile = self.animal_preferences.get(self.animal_type, {})
        self.mood = self._pick_mood()

        # this helps w giving each mood a visible personality in the bubble
        self.mood_text = random.choice(self.MOOD_EMOTICONS.get(self.mood, [":|"]))
        self.order = self._pick_order()
        self.time_limit = self._get_time_limit()
        self.time_remaining = self.time_limit
        self.texture = self._load_texture_for_animal(self.animal_type)
        self.sprite = self._create_sprite_for_animal(self.animal_type)
        self.walk_speed = 190.0
        self.is_arriving = abs(self.x - self.target_x) > 1
        self.is_served = False
        self.is_leaving = False

    # Loading the textures for the animals
    @classmethod
    def _load_texture_for_animal(cls, animal_type: str):
        if animal_type in cls._texture_cache:
            return cls._texture_cache[animal_type]
        filename = cls.TEXTURE_FILES.get(animal_type)
        if not filename:
            cls._texture_cache[animal_type] = None
            return None
        image_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets",
            "images",
            filename,
        )
        try:
            texture = arcade.load_texture(image_path)
        except Exception:
            texture = None
        cls._texture_cache[animal_type] = texture
        return texture

    # Creating the sprite for the animal
    @classmethod
    def _create_sprite_for_animal(cls, animal_type: str):
        if animal_type in cls._sprite_cache:
            return cls._sprite_cache[animal_type]
        texture = cls._load_texture_for_animal(animal_type)
        if texture is None:
            cls._sprite_cache[animal_type] = None
            return None
        try:
            target_size = 92
            points = getattr(texture, "hit_box_points", []) or []
            if points:
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                visible_w = max(1.0, max(xs) - min(xs))
                visible_h = max(1.0, max(ys) - min(ys))
            else:
                visible_w = max(1.0, float(texture.width))
                visible_h = max(1.0, float(texture.height))
            scale = min(target_size / visible_w, target_size / visible_h)
            sprite = arcade.Sprite(texture, scale=scale)
        except Exception:
            sprite = None
        cls._sprite_cache[animal_type] = sprite
        return sprite

    # Loading the texture for the order bubble
    @classmethod
    def _load_order_bubble_texture(cls):
        if cls._bubble_texture is not None:
            return cls._bubble_texture
        image_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets",
            "images",
            cls.ORDER_BUBBLE_FILE,
        )
        try:
            cls._bubble_texture = arcade.load_texture(image_path)
        except Exception:
            cls._bubble_texture = None
        return cls._bubble_texture

    # Creating the sprite for the order bubble
    @classmethod
    def _get_order_bubble_sprite(cls):
        if cls._bubble_sprite is not None:
            return cls._bubble_sprite
        texture = cls._load_order_bubble_texture()
        if texture is None:
            cls._bubble_sprite = None
            return None
        try:
            target_w = 240
            points = getattr(texture, "hit_box_points", []) or []
            if points:
                xs = [p[0] for p in points]
                visible_w = max(1.0, max(xs) - min(xs))
            else:
                visible_w = max(1.0, float(texture.width))
            scale = target_w / visible_w
            cls._bubble_sprite = arcade.Sprite(texture, scale=scale)
        except Exception:
            cls._bubble_sprite = None
        return cls._bubble_sprite

    # Picking the mood for the customer
    def _pick_mood(self) -> str:
        mood_weights = self.profile.get("mood_weights", {})
        if isinstance(mood_weights, dict):
            weighted = []
            for mood in self.MOOD_OPTIONS:
                weight = int(mood_weights.get(mood, 0))
                if weight > 0:
                    weighted.extend([mood] * weight)
            if weighted:
                # did this in order to make some animals feel more impatient/chill than others
                return random.choice(weighted)
        preferred_mood = self.profile.get("preferred_mood")
        if preferred_mood in self.MOOD_OPTIONS and random.random() < 0.8:
            return preferred_mood
        return random.choice(self.MOOD_OPTIONS)

    # Picking the order for the customer
    def _pick_order(self) -> str:
        favorites = [item for item in self.profile.get("favorite_items", []) if item in self.recipes]
        disliked = set(self.profile.get("disliked_items", []))
        allowed_orders = [name for name in self.recipes.keys() if name not in disliked]
        if not allowed_orders:
            allowed_orders = list(self.recipes.keys())
        favorite_bias = float(self.profile.get("favorite_bias", 0.75))
        if favorites and random.random() < favorite_bias:
            return random.choice(favorites)
        sweet_bias = float(self.profile.get("sweet_order_bias", 0.0))
        sweet_orders = [name for name in allowed_orders if self._is_sweet_item(name)]
        if sweet_orders and random.random() < sweet_bias:
            return random.choice(sweet_orders)
        return random.choice(allowed_orders)

    # Checking if the item is sweet
    def _is_sweet_item(self, item_name: str) -> bool:
        name = item_name.lower()
        return any(word in name for word in self.SWEET_KEYWORDS)

    # Getting the time limit for the customer
    def _get_time_limit(self) -> float:
        mood_times = {
            MOOD_HAPPY: HAPPY_TIME,
            MOOD_IMPATIENT: IMPATIENT_TIME,
            MOOD_NORMAL: NORMAL_TIME,
        }
        base_time = mood_times[self.mood]
        patience_multiplier = float(self.profile.get("patience_multiplier", 1.0))
        # this helps w per-animal pacing (sloths can wait longer, foxes less)
        return max(6.0, base_time * patience_multiplier)

    def update(self, delta_time: float):
        if self.is_arriving:
            # did this in order to make customers "walk in" instead of pop in
            direction = 1 if self.target_x > self.x else -1
            self.x += direction * self.walk_speed * delta_time
            reached = (direction == 1 and self.x >= self.target_x) or (direction == -1 and self.x <= self.target_x)
            if reached:
                self.x = self.target_x
                self.is_arriving = False
            return
        if not self.is_served and not self.is_leaving:
            self.time_remaining -= delta_time
            if self.time_remaining <= 0:
                self.time_remaining = 0
                self.is_leaving = True

    def get_patience_ratio(self) -> float:
        return max(0.0, self.time_remaining / self.time_limit)

    def get_required_ingredients(self) -> list:
        return self.recipes.get(self.order, {}).get("ingredients", [])

    def draw(self):
        color_map = {
            "cat": (255, 200, 180),
            "otter": (190, 140, 100),
            "bunny": (220, 200, 255),
            "fox": (230, 130, 50),
            "sloth": (170, 140, 110),
        }
        color = color_map.get(self.animal_type, (255, 255, 255))

        drew_texture = False
        if self.sprite:
            try:
                self.sprite.center_x = self.x
                self.sprite.center_y = self.y
                arcade.draw_sprite(self.sprite, pixelated=True)
                drew_texture = True
            except Exception:
                self.sprite = None

        # Fallback if image is missing or drawing failed
        if not drew_texture:
            arcade.draw_circle_filled(self.x, self.y, 40, color)
            arcade.draw_circle_outline(self.x, self.y, 40, (80, 40, 20), 3)

        self._draw_speech_bubble()
        self._draw_patience_bar()

    def _draw_speech_bubble(self):
        bubble_w = 240
        bubble_h = 108
        bx, by = self.x + 85, self.y + 67
        bubble_sprite = self._get_order_bubble_sprite()
        drew_bubble_texture = False
        if bubble_sprite:
            try:
                bubble_sprite.center_x = bx
                bubble_sprite.center_y = by
                arcade.draw_sprite(bubble_sprite)
                drew_bubble_texture = True
            except Exception:
                drew_bubble_texture = False

        if not drew_bubble_texture:
            draw_rect(bx, by, bubble_w, 44, (255, 255, 255))
            draw_rect_outline(bx, by, bubble_w, 44, (80, 40, 20), 2)
            tail_x = bx - bubble_w / 2 + 18
            tail_y = by - 22
            try:
                arcade.draw_triangle_filled(
                    tail_x - 8, tail_y,
                    tail_x + 4, tail_y,
                    tail_x - 2, tail_y - 12,
                    (255, 255, 255),
                )
                arcade.draw_triangle_outline(
                    tail_x - 8, tail_y,
                    tail_x + 4, tail_y,
                    tail_x - 2, tail_y - 12,
                    (80, 40, 20),
                    2,
                )
            except Exception:
                draw_rect(tail_x - 2, tail_y - 6, 10, 10, (255, 255, 255))
                draw_rect_outline(tail_x - 2, tail_y - 6, 10, 10, (80, 40, 20), 2)

        text_y = by - 8
        if drew_bubble_texture:
            text_y = by + 11
        mood_text = self.mood_text
        # Keep order and emoticon in fixed, separated lanes.
        order_x = bx - 88
        mood_x = bx + 64
        order_area_w = 130
        order_char_w = 6.1
        max_chars = max(4, int(order_area_w / order_char_w))
        display_order = self.order
        if len(display_order) > max_chars:
            display_order = display_order[: max_chars - 1] + "…"

        arcade.draw_text(
            display_order,
            order_x,
            text_y,
            (80, 40, 20),
            11,
            anchor_x="left",
            anchor_y="center",
            bold=True,
            font_name=FONT_UI,
            width=order_area_w,
        )
        arcade.draw_text(
            mood_text,
            mood_x,
            text_y,
            (80, 40, 20),
            8,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )

    # Drawing the patience bar for the customer
    def _draw_patience_bar(self):
        bar_width = 80
        ratio = self.get_patience_ratio()
        filled = bar_width * ratio

        # Background
        draw_rect(self.x, self.y - 60, bar_width, 10, (200, 200, 200))

        # Filled portion
        if filled > 0:
            if ratio > 0.5:
                bar_color = (50, 200, 50)
            elif ratio > 0.25:
                bar_color = (220, 200, 0)
            else:
                bar_color = (220, 50, 50)
            draw_rect(self.x - (bar_width - filled) / 2, self.y - 60, filled, 10, bar_color)

        draw_rect_outline(self.x, self.y - 60, bar_width, 10, (100, 100, 100), 1)
