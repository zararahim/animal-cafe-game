# 🐾 Animal Cafe Game
**CS122 Project | Rose Coders**
Sana Al Hamimidi & Zara Rahim

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the game
python main.py
```

## How to Play
1. Animal customers enter the cafe and display their orders in speech bubbles
2. Each customer has a **mood** (😊 Happy / 😐 Normal / 😤 Impatient) that affects their patience timer
3. Click ingredients from the tray at the bottom to assemble the order
4. Press **Serve!** to submit — faster and more accurate = more points!
5. Serve as many customers as you can before the 2-minute timer runs out

## Scoring
| Result  | Points         |
|---------|----------------|
| Perfect | 100 + speed bonus |
| Close   | 60             |
| Wrong   | -20            |
| Customer leaves | -20   |

## Project Structure
```
animal_cafe_game/
├── main.py                  # Entry point
├── requirements.txt
├── data/
│   ├── recipes.json         # All bakery recipes & ingredients
│   └── animal_preferences.json  # Animal personalities & favorites
├── assets/
│   ├── images/              # Add sprite images here
│   └── sounds/              # Add sound effects here
└── src/
    ├── constants.py         # Game-wide settings & constants
    ├── game.py              # Main window, states, game loop (Sana & Zara)
    ├── customer.py          # Customer class, moods, timers (Zara)
    ├── order_checker.py     # Order validation & scoring (Sana)
    └── ingredient_tray.py   # Clickable ingredient UI (Zara)
```

## Task Tracker
| Task | Owner | Due |
|------|-------|-----|
| Finalize game concept | Sana & Zara | Mar 6 |
| UI mockups & character design | Zara | Mar 9 |
| Arcade window + basic game features | Sana | Mar 13 |
| Customer system & moods | Zara | Mar 16 |
| Recipes & ingredient selection | Zara | Mar 23 |
| Order checking, scoring, timer | Sana | Apr 6 |
| Debugging & UI improvements | Sana & Zara | Apr 20 |
| Final refinements + docs | Sana & Zara | May 6 |

## Adding Sprites
Replace the placeholder shapes in `customer.py` by loading images in the `draw()` method:
```python
texture = arcade.load_texture("assets/images/cat.png")
arcade.draw_texture_rectangle(self.x, self.y, 80, 80, texture)
```
