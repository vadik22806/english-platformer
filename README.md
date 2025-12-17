# English Platformer 🎮📚

Educational platformer game for learning English with Python and Arcade library.

![Game Preview](assets/images/background.png)

## 🎯 Description
A 5-level platformer game where players collect letters to form English words while learning their translations. Features bonus system and physics-based gameplay.

## ✨ Features
- 5 progressively challenging levels
- Learn 15 English words with translations
- Bonus system (speed boost, jump boost, shield)
- Arcade library physics engine
- Fall damage and spike hazards (in advanced levels)
- Git version control for progress tracking

## 🚀 Installation

```bash
# Clone repository
git clone https://github.com/vadik22806/english-platformer.git
cd english-platformer

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

## 🎮 Controls
- **← → / A D** - Move left/right
- **↑ / W / Space** - Jump
- **1, 2, 3** - Purchase bonuses:
  - 1 - Speed boost (5 coins)
  - 2 - Jump boost (10 coins)
  - 3 - Shield (15 coins)

## 📁 Project Structure
```
english-platformer/
├── main.py              # Main game logic (1727 lines)
├── requirements.txt     # Python dependencies
├── .gitignore          # Ignored files
├── assets/             # Game resources
│   └── images/         # Game graphics
│       ├── player.png  # Player sprite
│       └── background.png # Background image
└── vocab.csv          # Vocabulary for learning
```

## 📋 Requirements
- Python 3.8+
- Arcade library: `pip install arcade`

## 🎯 Game Objective
Collect all letters for each English word, learn their translations, and complete all 5 levels.

## 💻 Development
This project uses Git for version control. All changes are tracked through commits.

## 📄 License
Educational project for learning Python and Git.