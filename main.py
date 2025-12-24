import arcade
import os
import random
import time
import sys

# --------------------------------
# Конфигурация
# --------------------------------
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 700
SCREEN_TITLE = "English Platformer — Урок 13 (Обучение английскому)"

# Игрок
PLAYER_SCALE = 1.0
PLAYER_MOVE_SPEED = 15
PLAYER_JUMP_SPEED = 25
GRAVITY = 0.9

WORLD_BOUNDARY = 35000

# Генерация платформ
PLATFORM_MIN_GAP = 100
PLATFORM_MAX_GAP = 260
PLATFORM_MIN_Y = 120
PLATFORM_MAX_Y = 480
PLATFORM_MIN_WIDTH = 60
PLATFORM_MAX_WIDTH = 250
SPAWN_BUFFER = 600

# Переход между уровнями
LEVEL_1_END = 5000
LEVEL_2_START = 5050
LEVEL_2_END = 13000
LEVEL_3_START = 13050
LEVEL_3_END = 20000
LEVEL_4_START = 20050
LEVEL_4_END = 28000
LEVEL_5_START = 28050
LEVEL_5_END = 35000

# Механика смерти от падения
FALL_DEATH_THRESHOLD = int(SCREEN_HEIGHT * 0.7)  # 80% высоты экрана

# Шипы
SPIKES_PROBABILITY = 0.4
SPIKES_MIN_COUNT = 3
SPIKES_MAX_COUNT = 6
SPIKE_WIDTH = 40
SPIKE_HEIGHT = 40

# Пути к ассетам
BASE_DIR = os.path.dirname(
    sys.executable if getattr(sys, "frozen", False)
    else os.path.abspath(__file__)
)

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
PLAYER_IMAGE_PATH = os.path.join(IMAGES_DIR, "player.png")
BACKGROUND_IMAGE_PATH = os.path.join(IMAGES_DIR, "background.png")

class Platform(arcade.Sprite):
    """Класс платформы для оптимизации"""

    def __init__(self, x, y, width, height, color):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.width = width
        self.height = height
        self.color = color


class Coin(arcade.Sprite):
    """Класс монетки"""

    def __init__(self, x, y):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.collected = False


class Letter(arcade.Sprite):
    """Класс буквы"""

    def __init__(self, x, y, letter, word):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.letter = letter
        self.word = word
        self.collected = False


class Spike(arcade.Sprite):
    """Класс шипа"""

    def __init__(self, x, y):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.width = SPIKE_WIDTH
        self.height = SPIKE_HEIGHT


class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)

        # Списки спрайтов
        self.player_list = None
        self.wall_list = None
        self.platform_visual_list = None
        self.coins_list = None
        self.letters_list = None
        self.spikes_list = None
        self.background_list = None

        # Игрок и физика
        self.player_sprite = None
        self.physics_engine = None

        # Камера
        self.camera_x = 0

        # Генерация мира
        self.max_spawn_x = SCREEN_WIDTH

        # Статистика
        self.score = 0
        self.coins_collected = 0
        self.collected_letters = []
        self.completed_words = []

        # Бонусы
        self.shield_count = 0  # Количество щитов
        self.has_shield_active = False  # Активен ли щит в данный момент
        self.speed_boost_active = False  # Активно ли ускорение
        self.jump_boost_active = False  # Активно ли усиление прыжка
        self.speed_boost_end_time = 0  # Время окончания ускорения
        self.jump_boost_end_time = 0  # Время окончания усиления прыжка

        # Цены бонусов
        self.BONUS_PRICES = {
            "speed": 2,  # ускорение
            "jump": 3,  # усиление прыжка
            "shield": 5  # щит
        }

        # Бонусные эффекты
        self.SPEED_BOOST_MULTIPLIER = 1.5  # Ускорение на 50%
        self.JUMP_BOOST_MULTIPLIER = 1.4  # Усиление прыжка на 40%
        self.BONUS_DURATION = 15  # Длительность бонусов в секундах

        # Текущий уровень
        self.current_level = 1

        # Механика смерти от падения
        self.fall_start_height = None  # Высота начала непрерывного падения
        self.was_on_ground = True  # Был ли игрок на земле в предыдущем кадре
        self.show_death_message = False
        self.death_message_timer = 0
        self.death_type = "fall"
        self.shield_save_message = False  # Сообщение о спасении щитом
        self.shield_save_timer = 0
        self.bonus_purchase_message = ""  # Сообщение о покупке бонуса
        self.bonus_message_timer = 0

        # Загрузка
        self.is_loading = True
        self.loading_progress = 0
        self.platforms_generated = 0
        self.total_platforms_to_generate = 50  # Сколько платформ сгенерировать заранее

        # Слова для изучения
        self.words_to_collect = {
            "cat": {"letters": ["c", "a", "t"], "translation": "кот", "collected": False, "progress": {}},
            "dog": {"letters": ["d", "o", "g"], "translation": "собака", "collected": False, "progress": {}},
            "mother": {"letters": ["m", "o", "t", "h", "e", "r"], "translation": "мама", "collected": False,
                       "progress": {}},
            "father": {"letters": ["f", "a", "t", "h", "e", "r"], "translation": "папа", "collected": False,
                       "progress": {}},
            "brother": {"letters": ["b", "r", "o", "t", "h", "e", "r"], "translation": "брат", "collected": False,
                        "progress": {}},
            "food": {"letters": ["f", "o", "o", "d"], "translation": "еда", "collected": False, "progress": {}},
            "pizza": {"letters": ["p", "i", "z", "z", "a"], "translation": "пицца", "collected": False, "progress": {}},
            "bread": {"letters": ["b", "r", "e", "a", "d"], "translation": "хлеб", "collected": False, "progress": {}},
            "math": {"letters": ["m", "a", "t", "h"], "translation": "математика", "collected": False, "progress": {}},
            "physics": {"letters": ["p", "h", "y", "s", "i", "c", "s"], "translation": "физика", "collected": False,
                        "progress": {}},
            "chemistry": {"letters": ["c", "h", "e", "m", "i", "s", "t", "r", "y"], "translation": "химия",
                          "collected": False, "progress": {}},
            "sofa": {"letters": ["s", "o", "f", "a"], "translation": "диван", "collected": False, "progress": {}},
            "table": {"letters": ["t", "a", "b", "l", "e"], "translation": "стол", "collected": False, "progress": {}},
            "chair": {"letters": ["c", "h", "a", "i", "r"], "translation": "стул", "collected": False, "progress": {}}
        }

        # Очереди букв
        self.letter_queue_level1 = [
            ("cat", "c"), ("cat", "a"), ("cat", "t"),
            ("dog", "d"), ("dog", "o"), ("dog", "g"),
        ]
        self.letter_queue_level2 = [
            ("mother", "m"), ("mother", "o"), ("mother", "t"), ("mother", "h"), ("mother", "e"), ("mother", "r"),
            ("father", "f"), ("father", "a"), ("father", "t"), ("father", "h"), ("father", "e"), ("father", "r"),
            ("brother", "b"), ("brother", "r"), ("brother", "o"), ("brother", "t"), ("brother", "h"), ("brother", "e"),
            ("brother", "r"),
        ]
        self.letter_queue_level3 = [
            ("food", "f"), ("food", "o"), ("food", "o"), ("food", "d"),
            ("pizza", "p"), ("pizza", "i"), ("pizza", "z"), ("pizza", "z"), ("pizza", "a"),
            ("bread", "b"), ("bread", "r"), ("bread", "e"), ("bread", "a"), ("bread", "d"),
        ]
        self.letter_queue_level4 = [
            ("math", "m"), ("math", "a"), ("math", "t"), ("math", "h"),
            ("physics", "p"), ("physics", "h"), ("physics", "y"), ("physics", "s"), ("physics", "i"), ("physics", "c"),
            ("physics", "s"),
            ("chemistry", "c"), ("chemistry", "h"), ("chemistry", "e"), ("chemistry", "m"), ("chemistry", "i"),
            ("chemistry", "s"), ("chemistry", "t"), ("chemistry", "r"), ("chemistry", "y"),
        ]
        self.letter_queue_level5 = [
            ("sofa", "s"), ("sofa", "o"), ("sofa", "f"), ("sofa", "a"),
            ("table", "t"), ("table", "a"), ("table", "b"), ("table", "l"), ("table", "e"),
            ("chair", "c"), ("chair", "h"), ("chair", "a"), ("chair", "i"), ("chair", "r"),
        ]

        arcade.set_background_color(arcade.color.SKY_BLUE)

    def setup(self):
        """Инициализация игры"""
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.platform_visual_list = arcade.SpriteList()
        self.coins_list = arcade.SpriteList()
        self.letters_list = arcade.SpriteList()
        self.spikes_list = arcade.SpriteList()
        self.background_list = arcade.SpriteList()

        # Сбрасываем статистику
        self.score = 0
        self.coins_collected = 0
        self.collected_letters = []
        self.completed_words = []
        self.camera_x = 0
        self.max_spawn_x = SCREEN_WIDTH
        self.current_level = 1

        # Сбрасываем бонусы
        self.shield_count = 0
        self.has_shield_active = False
        self.speed_boost_active = False
        self.jump_boost_active = False
        self.speed_boost_end_time = 0
        self.jump_boost_end_time = 0

        # Сбрасываем механику падения
        self.fall_start_height = None
        self.was_on_ground = True
        self.show_death_message = False
        self.death_message_timer = 0
        self.shield_save_message = False
        self.shield_save_timer = 0
        self.death_type = "fall"
        self.bonus_purchase_message = ""
        self.bonus_message_timer = 0

        # ЗАГРУЗКА ДЛЯ КАЖДОГО УРОВНЯ
        self.is_loading = True
        self.loading_progress = 0
        self.platforms_generated = 0

        # РЕАЛЬНОЕ количество платформ для каждого уровня
        if self.current_level == 1:
            self.total_platforms_to_generate = 40  # Уровень 1: 5000px / 150px = ~33 + запас
        elif self.current_level == 2:
            self.total_platforms_to_generate = 60  # Уровень 2: 7950px / 150px = ~53 + запас
        elif self.current_level == 3:
            self.total_platforms_to_generate = 50  # Уровень 3: 6950px / 150px = ~46 + запас
        elif self.current_level == 4:
            self.total_platforms_to_generate = 50  # Уровень 4: 7950px / 150px = ~53 + запас
        elif self.current_level == 5:
            self.total_platforms_to_generate = 50  # Уровень 5: 6950px / 150px = ~46 + запас

        # Сбрасываем состояние слов
        for word in self.words_to_collect:
            self.words_to_collect[word]["collected"] = False
            self.words_to_collect[word]["progress"] = {}
            for letter in self.words_to_collect[word]["letters"]:
                self.words_to_collect[word]["progress"][letter] = 0

        # Сбрасываем очереди букв
        self.letter_queue_level1 = [
            ("cat", "c"), ("cat", "a"), ("cat", "t"),
            ("dog", "d"), ("dog", "o"), ("dog", "g"),
        ]
        self.letter_queue_level2 = [
            ("mother", "m"), ("mother", "o"), ("mother", "t"), ("mother", "h"), ("mother", "e"), ("mother", "r"),
            ("father", "f"), ("father", "a"), ("father", "t"), ("father", "h"), ("father", "e"), ("father", "r"),
            ("brother", "b"), ("brother", "r"), ("brother", "o"), ("brother", "t"), ("brother", "h"), ("brother", "e"),
            ("brother", "r"),
        ]
        self.letter_queue_level3 = [
            ("food", "f"), ("food", "o"), ("food", "o"), ("food", "d"),
            ("pizza", "p"), ("pizza", "i"), ("pizza", "z"), ("pizza", "z"), ("pizza", "a"),
            ("bread", "b"), ("bread", "r"), ("bread", "e"), ("bread", "a"), ("bread", "d"),
        ]
        self.letter_queue_level4 = [
            ("math", "m"), ("math", "a"), ("math", "t"), ("math", "h"),
            ("physics", "p"), ("physics", "h"), ("physics", "y"), ("physics", "s"), ("physics", "i"), ("physics", "c"),
            ("physics", "s"),
            ("chemistry", "c"), ("chemistry", "h"), ("chemistry", "e"), ("chemistry", "m"), ("chemistry", "i"),
            ("chemistry", "s"), ("chemistry", "t"), ("chemistry", "r"), ("chemistry", "y"),
        ]
        self.letter_queue_level5 = [
            ("sofa", "s"), ("sofa", "o"), ("sofa", "f"), ("sofa", "a"),
            ("table", "t"), ("table", "a"), ("table", "b"), ("table", "l"), ("table", "e"),
            ("chair", "c"), ("chair", "h"), ("chair", "a"), ("chair", "i"), ("chair", "r"),
        ]

        # Загрузка фона
        if os.path.exists(BACKGROUND_IMAGE_PATH):
            try:
                self.background_texture = arcade.load_texture(BACKGROUND_IMAGE_PATH)
                self.background_sprite = arcade.Sprite()
                self.background_sprite.texture = self.background_texture
                self.background_sprite.center_x = SCREEN_WIDTH // 2
                self.background_sprite.center_y = SCREEN_HEIGHT // 2
                self.background_sprite.width = SCREEN_WIDTH
                self.background_sprite.height = SCREEN_HEIGHT
                self.background_list.append(self.background_sprite)
            except Exception as e:
                self.background_list = None
        else:
            self.background_list = None

        # Создаем игрока
        if os.path.exists(PLAYER_IMAGE_PATH):
            try:
                self.player_sprite = arcade.Sprite(PLAYER_IMAGE_PATH, scale=0.125)
            except Exception as e:
                self.player_sprite = arcade.Sprite(
                    ":resources:images/animated_characters/female_person/femalePerson_idle.png",
                    scale=PLAYER_SCALE,
                )
        else:
            self.player_sprite = arcade.Sprite(
                ":resources:images/animated_characters/female_person/femalePerson_idle.png",
                scale=PLAYER_SCALE,
            )

        # Стартовая позиция игрока
        self.player_sprite.center_x = 128
        self.player_sprite.center_y = 200
        self.player_list.append(self.player_sprite)

        # Создаем начальные платформы и объекты
        self.create_initial_platforms()

        # Физика
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=self.wall_list
        )

    def create_initial_platforms(self):
        """Создает только минимальные стартовые платформы"""
        if self.current_level == 1:
            # Пол первого уровня
            floor_end = LEVEL_1_END - 500
            floor_center_x = floor_end // 2

            # Физическая платформа
            physics_sprite = arcade.SpriteSolidColor(floor_end, 40, arcade.color.TRANSPARENT_BLACK)
            physics_sprite.center_x = floor_center_x
            physics_sprite.center_y = 20
            self.wall_list.append(physics_sprite)

            # Визуальная платформа
            platform_visual = Platform(floor_center_x, 20, floor_end, 40, arcade.color.DARK_SLATE_GRAY)
            self.platform_visual_list.append(platform_visual)

            # Стартовая платформа для игрока
            start_x = 200
            start_y = 180
            start_width = 160

            physics_sprite = arcade.SpriteSolidColor(start_width, 20, arcade.color.TRANSPARENT_BLACK)
            physics_sprite.center_x = start_x
            physics_sprite.center_y = start_y
            self.wall_list.append(physics_sprite)

            platform_visual = Platform(start_x, start_y, start_width, 20, arcade.color.DARK_GREEN)
            self.platform_visual_list.append(platform_visual)

            self.max_spawn_x = start_x + start_width // 2

        elif self.current_level == 2:
            # Пол второго уровня
            floor_width = LEVEL_2_END - LEVEL_2_START
            floor_center_x = LEVEL_2_START + floor_width // 2

            # Пол
            physics_sprite = arcade.SpriteSolidColor(floor_width, 40, arcade.color.TRANSPARENT_BLACK)
            physics_sprite.center_x = floor_center_x
            physics_sprite.center_y = 20
            self.wall_list.append(physics_sprite)

            platform_visual = Platform(floor_center_x, 20, floor_width, 40, arcade.color.DARK_SLATE_GRAY)
            self.platform_visual_list.append(platform_visual)

            # Первая платформа
            first_x = LEVEL_2_START + 200
            first_y = 300
            first_width = 160

            physics_sprite = arcade.SpriteSolidColor(first_width, 20, arcade.color.TRANSPARENT_BLACK)
            physics_sprite.center_x = first_x
            physics_sprite.center_y = first_y
            self.wall_list.append(physics_sprite)

            platform_visual = Platform(first_x, first_y, first_width, 20, arcade.color.DARK_GREEN)
            self.platform_visual_list.append(platform_visual)

            self.max_spawn_x = first_x + first_width // 2

        elif self.current_level == 3:
            # Пол третьего уровня
            floor_width = LEVEL_3_END - LEVEL_3_START
            floor_center_x = LEVEL_3_START + floor_width // 2

            # Пол
            physics_sprite = arcade.SpriteSolidColor(floor_width, 40, arcade.color.TRANSPARENT_BLACK)
            physics_sprite.center_x = floor_center_x
            physics_sprite.center_y = 20
            self.wall_list.append(physics_sprite)

            platform_visual = Platform(floor_center_x, 20, floor_width, 40, arcade.color.DARK_SLATE_GRAY)
            self.platform_visual_list.append(platform_visual)

            # Первая платформа
            first_x = LEVEL_3_START + 200
            first_y = 400
            first_width = 160

            physics_sprite = arcade.SpriteSolidColor(first_width, 20, arcade.color.TRANSPARENT_BLACK)
            physics_sprite.center_x = first_x
            physics_sprite.center_y = first_y
            self.wall_list.append(physics_sprite)

            platform_visual = Platform(first_x, first_y, first_width, 20, arcade.color.DARK_GREEN)
            self.platform_visual_list.append(platform_visual)

            self.max_spawn_x = first_x + first_width // 2

        elif self.current_level == 4:
            # Пол четвертого уровня
            floor_width = LEVEL_4_END - LEVEL_4_START
            floor_center_x = LEVEL_4_START + floor_width // 2

            # Пол
            physics_sprite = arcade.SpriteSolidColor(floor_width, 40, arcade.color.TRANSPARENT_BLACK)
            physics_sprite.center_x = floor_center_x
            physics_sprite.center_y = 20
            self.wall_list.append(physics_sprite)

            platform_visual = Platform(floor_center_x, 20, floor_width, 40, arcade.color.DARK_SLATE_GRAY)
            self.platform_visual_list.append(platform_visual)

            # Первая платформа
            first_x = LEVEL_4_START + 200
            first_y = 400
            first_width = 160

            physics_sprite = arcade.SpriteSolidColor(first_width, 20, arcade.color.TRANSPARENT_BLACK)
            physics_sprite.center_x = first_x
            physics_sprite.center_y = first_y
            self.wall_list.append(physics_sprite)

            platform_visual = Platform(first_x, first_y, first_width, 20, arcade.color.DARK_GREEN)
            self.platform_visual_list.append(platform_visual)

            self.max_spawn_x = first_x + first_width // 2

        else:  # Уровень 5
            # Пол пятого уровня
            floor_width = WORLD_BOUNDARY - LEVEL_5_START
            floor_center_x = LEVEL_5_START + floor_width // 2

            # Пол
            physics_sprite = arcade.SpriteSolidColor(floor_width, 40, arcade.color.TRANSPARENT_BLACK)
            physics_sprite.center_x = floor_center_x
            physics_sprite.center_y = 20
            self.wall_list.append(physics_sprite)

            platform_visual = Platform(floor_center_x, 20, floor_width, 40, arcade.color.DARK_SLATE_GRAY)
            self.platform_visual_list.append(platform_visual)

            # Первая платформа
            first_x = LEVEL_5_START + 200
            first_y = 400
            first_width = 160

            physics_sprite = arcade.SpriteSolidColor(first_width, 20, arcade.color.TRANSPARENT_BLACK)
            physics_sprite.center_x = first_x
            physics_sprite.center_y = first_y
            self.wall_list.append(physics_sprite)

            platform_visual = Platform(first_x, first_y, first_width, 20, arcade.color.DARK_GREEN)
            self.platform_visual_list.append(platform_visual)

            self.max_spawn_x = first_x + first_width // 2

    def spawn_spikes_on_floor(self, start_x, count=None):
        """Создает шипы с проверкой границ"""
        if self.current_level not in [4, 5]:
            return

        if count is None:
            count = random.randint(SPIKES_MIN_COUNT, SPIKES_MAX_COUNT)

        total_width = count * SPIKE_WIDTH

        # Определяем границы уровня
        if self.current_level == 4:
            level_end = LEVEL_4_END
        else:  # level 5
            level_end = WORLD_BOUNDARY

        # Проверяем, не выходят ли шипы за границу
        if start_x + total_width > level_end - 100:  # Отступ 100px
            return  # Не создаем

        start_x = start_x + total_width // 2

        for i in range(count):
            spike_x = start_x + (i - count // 2) * SPIKE_WIDTH

            # Проверка каждого шипа
            if spike_x > level_end - 50:  # Отступ 50px
                continue

            spike = Spike(spike_x, 20 + SPIKE_HEIGHT)
            self.spikes_list.append(spike)

    def spawn_platform(self, start_x):
        """Генерирует новую платформу"""
        MAX_ATTEMPTS = 5
        MIN_HORIZONTAL_CLEARANCE = 8
        MIN_VERTICAL_SEPARATION = 40

        for attempt in range(MAX_ATTEMPTS):
            # Параметры зависят от уровня
            if self.current_level == 2:
                gap = random.randint(150, 320)
                width = random.randint(60, 200)
                y = random.randint(180, 550)
            elif self.current_level == 3 or self.current_level == 4 or self.current_level == 5:
                gap = random.randint(120, 280)
                width = random.randint(80, 220)
                y = random.randint(300, 600)
            else:
                gap = random.randint(PLATFORM_MIN_GAP, PLATFORM_MAX_GAP)
                width = random.randint(PLATFORM_MIN_WIDTH, PLATFORM_MAX_WIDTH)
                y = random.randint(PLATFORM_MIN_Y, PLATFORM_MAX_Y)

            platform_left = start_x + gap
            platform_right = platform_left + width
            platform_x = platform_left + width // 2

            # Ограничиваем генерацию
            if self.current_level == 1 and platform_right > LEVEL_1_END - 500:
                continue
            elif self.current_level == 2 and platform_right > LEVEL_2_END:
                continue
            elif self.current_level == 3 and platform_right > LEVEL_3_END:
                continue
            elif self.current_level == 4 and platform_right > LEVEL_4_END:
                continue
            elif platform_right > WORLD_BOUNDARY:
                continue

            # Проверяем пересечения
            intersects = False
            for wall in self.wall_list:
                wall_left = wall.center_x - wall.width // 2
                wall_right = wall.center_x + wall.width // 2
                wall_y = wall.center_y

                horizontal_overlap = not (
                        platform_right + MIN_HORIZONTAL_CLEARANCE < wall_left or
                        platform_left - MIN_HORIZONTAL_CLEARANCE > wall_right
                )
                vertical_close = abs(y - wall_y) < MIN_VERTICAL_SEPARATION

                if horizontal_overlap and vertical_close:
                    intersects = True
                    break

            if intersects:
                continue

            color = random.choice([
                arcade.color.DARK_GREEN, arcade.color.OLIVE,
                arcade.color.DARK_ORANGE, arcade.color.DARK_CERULEAN,
                arcade.color.DARK_RED, arcade.color.DARK_VIOLET
            ])

            # Создаем физическую платформу
            physics_sprite = arcade.SpriteSolidColor(width, 20, arcade.color.TRANSPARENT_BLACK)
            physics_sprite.center_x = platform_x
            physics_sprite.center_y = y
            self.wall_list.append(physics_sprite)

            # Создаем визуальную платформу
            platform_visual = Platform(platform_x, y, width, 20, color)
            self.platform_visual_list.append(platform_visual)

            right_edge = platform_x + width // 2
            if right_edge > self.max_spawn_x:
                self.max_spawn_x = right_edge

            # Добавляем шипы на четвертом и пятом уровнях
            if self.current_level in [4, 5] and random.random() < SPIKES_PROBABILITY:
                self.spawn_spikes_on_floor(platform_x + width // 2 + 100)

            return {"x": platform_x, "y": y, "width": width}

        return None

    def _spawn_world_elements(self):
        """Генерация элементов мира - сначала буквы, потом монетки"""
        new_platform = self.spawn_platform(self.max_spawn_x)
        if new_platform:
            platform_width = new_platform["width"]
            platform_x = new_platform["x"]
            platform_y = new_platform["y"]

            # Проверяем есть ли еще буквы в очереди для текущего уровня
            has_letters = (
                    (self.current_level == 1 and self.letter_queue_level1) or
                    (self.current_level == 2 and self.letter_queue_level2) or
                    (self.current_level == 3 and self.letter_queue_level3) or
                    (self.current_level == 4 and self.letter_queue_level4) or
                    (self.current_level == 5 and self.letter_queue_level5)
            )

            if has_letters:
                # БУКВА - 100% если есть в очереди
                letter_offset = random.uniform(-platform_width * 0.4, -platform_width * 0.1)

                if self.current_level == 1 and self.letter_queue_level1:
                    word, letter_char = self.letter_queue_level1.pop(0)
                    letter = Letter(platform_x + letter_offset, platform_y + 30, letter_char, word)
                    self.letters_list.append(letter)
                elif self.current_level == 2 and self.letter_queue_level2:
                    word, letter_char = self.letter_queue_level2.pop(0)
                    letter = Letter(platform_x + letter_offset, platform_y + 30, letter_char, word)
                    self.letters_list.append(letter)
                elif self.current_level == 3 and self.letter_queue_level3:
                    word, letter_char = self.letter_queue_level3.pop(0)
                    letter = Letter(platform_x + letter_offset, platform_y + 30, letter_char, word)
                    self.letters_list.append(letter)
                elif self.current_level == 4 and self.letter_queue_level4:
                    word, letter_char = self.letter_queue_level4.pop(0)
                    letter = Letter(platform_x + letter_offset, platform_y + 30, letter_char, word)
                    self.letters_list.append(letter)
                elif self.current_level == 5 and self.letter_queue_level5:
                    word, letter_char = self.letter_queue_level5.pop(0)
                    letter = Letter(platform_x + letter_offset, platform_y + 30, letter_char, word)
                    self.letters_list.append(letter)
            else:
                # МОНЕТКА - только если буквы закончились
                coin_offset = random.uniform(-platform_width * 0.4, platform_width * 0.4)
                coin = Coin(platform_x + coin_offset, platform_y + 30)
                self.coins_list.append(coin)

    def _check_letter_collisions(self):
        """Проверка букв - ОПТИМИЗИРОВАННАЯ"""
        # Кэшируем координаты игрока
        px = self.player_sprite.center_x
        py = self.player_sprite.center_y
        p_half_width = self.player_sprite.width // 2
        p_half_height = self.player_sprite.height // 2

        # Проверяем только буквы рядом
        check_left = px - 120
        check_right = px + 120
        check_top = py + 120
        check_bottom = py - 120

        for letter in self.letters_list:
            if letter.collected:
                continue

            letter_x = letter.center_x
            letter_y = letter.center_y

            # Быстрая фильтрация
            if (letter_x < check_left or letter_x > check_right or
                    letter_y < check_bottom or letter_y > check_top):
                continue

            # Простая проверка расстояния
            dx = letter_x - px
            dy = letter_y - py
            if dx * dx + dy * dy < 1600:  # 40px радиус
                # Нельзя собрать снизу
                player_top = py + p_half_height
                letter_bottom = letter_y - 20
                if player_top > letter_bottom:
                    letter.collected = True
                    self.collected_letters.append(letter.letter)
                    self._process_letter_collection(letter)
                    self.score += 20
                    self.check_word_completion()

    def _check_coin_collisions(self):
        """Проверка монет - ОПТИМИЗИРОВАННАЯ"""
        # Кэшируем координаты игрока
        px = self.player_sprite.center_x
        py = self.player_sprite.center_y
        p_half_width = self.player_sprite.width // 2
        p_half_height = self.player_sprite.height // 2

        # Проверяем только монеты рядом
        check_left = px - 120
        check_right = px + 120
        check_top = py + 120
        check_bottom = py - 120

        for coin in self.coins_list:
            if coin.collected:
                continue

            coin_x = coin.center_x
            coin_y = coin.center_y

            # Быстрая фильтрация
            if (coin_x < check_left or coin_x > check_right or
                    coin_y < check_bottom or coin_y > check_top):
                continue

            # Простая проверка расстояния
            dx = coin_x - px
            dy = coin_y - py
            if dx * dx + dy * dy < 1600:  # 40px радиус
                # Нельзя собрать снизу
                player_top = py + p_half_height
                coin_bottom = coin_y - 20
                if player_top > coin_bottom:
                    coin.collected = True
                    self.coins_collected += 1
                    self.score += 10

    def _process_letter_collection(self, letter):
        """Обработка собранной буквы"""
        if letter.word and letter.word in self.words_to_collect:
            data = self.words_to_collect[letter.word]
            if not data["collected"]:
                needed_count = data["letters"].count(letter.letter)
                current_count = data["progress"].get(letter.letter, 0)
                if current_count < needed_count:
                    data["progress"][letter.letter] = current_count + 1

    def _draw_hud(self):
        """Отрисовка HUD"""
        arcade.draw_text(
            f"Уровень: {self.current_level}",
            10, SCREEN_HEIGHT - 30, arcade.color.BLACK, 20
        )
        arcade.draw_text(
            "← → : Двигаться    ↑/Пробел : Прыжок",
            10, SCREEN_HEIGHT - 60, arcade.color.WHITE, 14
        )
        arcade.draw_text(f"Монеты: {self.coins_collected}", 10, SCREEN_HEIGHT - 84, arcade.color.WHITE, 14)
        arcade.draw_text(f"Собрано букв: {len(self.collected_letters)}", 10, SCREEN_HEIGHT - 108, arcade.color.WHITE,
                         14)

        # Отрисовка информации о бонусах в правом верхнем углу
        bonus_x = SCREEN_WIDTH - 380
        bonus_y = SCREEN_HEIGHT - 40

        # Заголовок бонусов
        arcade.draw_text(
            "ПОКУПКА БОНУСОВ:",
            bonus_x, bonus_y,
            arcade.color.GOLD, 18
        )

        # Ускорение (клавиша 1)
        arcade.draw_text(
            "Клавиша 1 - Ускорение (2 монет)",
            bonus_x, bonus_y - 40,
            arcade.color.GREEN, 14
        )

        # Усиление прыжка (клавиша 2)
        arcade.draw_text(
            "Клавиша 2 - Усиление прыжка (3 монет)",
            bonus_x, bonus_y - 70,
            arcade.color.GREEN, 14
        )

        # Щит (клавиша 3)
        arcade.draw_text(
            "Клавиша 3 - Щит (5 монет)",
            bonus_x, bonus_y - 100,
            arcade.color.GREEN, 14
        )

        # Количество щитов
        arcade.draw_text(
            f"Щитов: {self.shield_count}",
            bonus_x, bonus_y - 130,
            arcade.color.LIGHT_BLUE, 16
        )

        # Активные бонусы
        current_time = time.time()
        active_bonuses_y = bonus_y - 190

        if self.speed_boost_active:
            time_left = max(0, int(self.speed_boost_end_time - current_time))
            arcade.draw_text(
                f"Ускорение: {time_left}с",
                bonus_x, active_bonuses_y,
                arcade.color.GREEN, 14
            )
            active_bonuses_y -= 25

        if self.jump_boost_active:
            time_left = max(0, int(self.jump_boost_end_time - current_time))
            arcade.draw_text(
                f"Прыжок усилен: {time_left}с",
                bonus_x, active_bonuses_y,
                arcade.color.GREEN, 14
            )
            active_bonuses_y -= 25

        # Сообщение о покупке бонуса
        if self.bonus_message_timer > 0:
            arcade.draw_text(
                self.bonus_purchase_message,
                SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                arcade.color.GREEN, 24,
                align="center", anchor_x="center", anchor_y="center"
            )

        y_offset = SCREEN_HEIGHT - 140
        for i, (word, translation) in enumerate(self.completed_words):
            arcade.draw_text(
                f"{word} - {translation}",
                10, y_offset - i * 30,
                arcade.color.BLACK, 16
            )

        if self.show_death_message:
            message = "СМЕРТЬ ОТ ШИПОВ!" if self.death_type == "spikes" else "СМЕРТЬ ОТ ПАДЕНИЯ!"
            arcade.draw_text(
                message,
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                arcade.color.RED, 36,
                align="center", anchor_x="center", anchor_y="center"
            )

    def _draw_loading_screen(self):
        """Отрисовка экрана загрузки"""
        # Фон
        arcade.draw_lrbt_rectangle_filled(
            0, SCREEN_WIDTH, 0, SCREEN_HEIGHT,
            arcade.color.WHITE
        )

        # Текст
        arcade.draw_text(
            "ПОЖАЛУЙСТА ПОДОЖДИТЕ, СОЗДАЕМ И НАСТРАИВАЕМ МИР...",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80,
            arcade.color.BLACK, 28,
            align="center", anchor_x="center", anchor_y="center"
        )

        # Рамка прогресс-бара
        bar_width = 600
        bar_height = 40
        bar_x = SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = SCREEN_HEIGHT // 2 - 20

        # Фон прогресс-бара
        arcade.draw_lrbt_rectangle_filled(
            bar_x, bar_x + bar_width,
            bar_y, bar_y + bar_height,
            arcade.color.DARK_GRAY
        )

        # Заполнение прогресс-бара
        fill_width = (bar_width * self.loading_progress) / 100
        if fill_width > 0:
            arcade.draw_lrbt_rectangle_filled(
                bar_x, bar_x + fill_width,
                       bar_y + 3, bar_y + bar_height - 3,
                arcade.color.GREEN
            )

        # Процент
        arcade.draw_text(
            f"{int(self.loading_progress)}%",
            SCREEN_WIDTH // 2, bar_y - 40,
            arcade.color.WHITE, 24,
            align="center", anchor_x="center", anchor_y="center"
        )

        # Статус
        status_text = f"Сгенерировано платформ: {self.platforms_generated}/{self.total_platforms_to_generate}"
        arcade.draw_text(
            status_text,
            SCREEN_WIDTH // 2, bar_y - 80,
            arcade.color.LIGHT_GRAY, 18,
            align="center", anchor_x="center", anchor_y="center"
        )

    def check_spikes_collision(self):
        """Проверка шипов - ОПТИМИЗИРОВАННАЯ"""
        if self.current_level not in [4, 5]:
            return

        # Кэшируем координаты игрока
        px = self.player_sprite.center_x
        py = self.player_sprite.center_y
        p_width = self.player_sprite.width

        # Проверяем только шипы рядом
        check_left = px - 150
        check_right = px + 150

        for spike in self.spikes_list:
            # Быстрая фильтрация по X
            spike_x = spike.center_x
            if spike_x < check_left or spike_x > check_right:
                continue

            # Простая круговая проверка (быстрее прямоугольников)
            dx = spike_x - px
            dy = spike.center_y - py
            distance_squared = dx * dx + dy * dy

            # 60px радиус
            if distance_squared < 3600:
                if self.shield_count > 0:
                    self.shield_count -= 1
                    self.shield_save_message = True
                    self.shield_save_timer = 60
                    self.bonus_purchase_message = f"Щит спас от смерти от шипов!"
                    self.bonus_message_timer = 60

                    # Отскок и остановка
                    self.player_sprite.change_x = 0
                    self.player_sprite.change_y = 25
                    return

                # Смерть
                self.show_death_message = True
                self.death_message_timer = 60
                self.death_type = "spikes"
                if self.current_level == 4:
                    self.restart_level_4()
                elif self.current_level == 5:
                    self.restart_level_5()
                return

    def check_level_transition(self):
        """Проверяет переход на следующий уровень"""
        if (self.current_level == 1 and
                self.player_sprite.center_x >= LEVEL_1_END - 500 and
                self.player_sprite.center_y < -10):
            self.transition_to_level_2()
        elif (self.current_level == 2 and
              self.player_sprite.center_x >= LEVEL_2_END - 100 and
              self.player_sprite.center_y < -50):
            self.transition_to_level_3()
        elif (self.current_level == 3 and
              self.player_sprite.center_x >= LEVEL_3_END - 100 and
              self.player_sprite.center_y < -50):
            self.transition_to_level_4()
        elif (self.current_level == 4 and
              self.player_sprite.center_x >= LEVEL_4_END - 100 and
              self.player_sprite.center_y < -50):
            self.transition_to_level_5()

    def transition_to_level_2(self):
        """Переход на второй уровень"""
        self.current_level = 2

        # Очищаем объекты
        self.wall_list.clear()
        self.platform_visual_list.clear()
        self.coins_list.clear()
        self.letters_list.clear()
        self.spikes_list.clear()
        self.collected_letters = []

        # Очищаем собранные слова первого уровня
        self.completed_words = [(word, trans) for word, trans in self.completed_words
                                if word not in ["cat", "dog"]]

        self.max_spawn_x = LEVEL_2_START

        # ЗАПУСКАЕМ ЗАГРУЗКУ ДЛЯ ВТОРОГО УРОВНЯ
        self.is_loading = True
        self.loading_progress = 0
        self.platforms_generated = 0
        self.total_platforms_to_generate = 60

        # Перемещаем игрока
        self.player_sprite.center_x = LEVEL_2_START + 100
        self.player_sprite.center_y = 300
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0
        self.fall_start_height = None  # Сбрасываем высоту падения
        self.was_on_ground = True

        # Создаем начальные платформы
        self.create_initial_platforms()

        # Обновляем физический движок
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=self.wall_list
        )

    def transition_to_level_3(self):
        """Переход на третий уровень"""
        self.current_level = 3

        # Очищаем объекты
        self.wall_list.clear()
        self.platform_visual_list.clear()
        self.coins_list.clear()
        self.letters_list.clear()
        self.spikes_list.clear()
        self.collected_letters = []

        # Очищаем собранные слова второго уровня
        self.completed_words = [(word, trans) for word, trans in self.completed_words
                                if word not in ["mother", "father", "brother"]]

        self.max_spawn_x = LEVEL_3_START

        # ЗАПУСКАЕМ ЗАГРУЗКУ ДЛЯ ТРЕТЬЕГО УРОВНЯ
        self.is_loading = True
        self.loading_progress = 0
        self.platforms_generated = 0
        self.total_platforms_to_generate = 50

        # Перемещаем игрока
        self.player_sprite.center_x = LEVEL_3_START + 100
        self.player_sprite.center_y = 400
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0
        self.fall_start_height = None  # Сбрасываем высоту падения
        self.was_on_ground = True

        # Создаем начальные платформы
        self.create_initial_platforms()

        # Обновляем физический движок
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=self.wall_list
        )

    def transition_to_level_4(self):
        """Переход на четвертый уровень"""
        self.current_level = 4

        # Очищаем объекты
        self.wall_list.clear()
        self.platform_visual_list.clear()
        self.coins_list.clear()
        self.letters_list.clear()
        self.spikes_list.clear()
        self.collected_letters = []

        # Очищаем собранные слова третьего уровня
        self.completed_words = [(word, trans) for word, trans in self.completed_words
                                if word not in ["food", "pizza", "bread"]]

        self.max_spawn_x = LEVEL_4_START

        # ЗАПУСКАЕМ ЗАГРУЗКУ ДЛЯ ЧЕТВЕРТОГО УРОВНЯ
        self.is_loading = True
        self.loading_progress = 0
        self.platforms_generated = 0
        self.total_platforms_to_generate = 50

        # Перемещаем игрока
        self.player_sprite.center_x = LEVEL_4_START + 100
        self.player_sprite.center_y = 400
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0
        self.fall_start_height = None  # Сбрасываем высоту падения
        self.was_on_ground = True

        # Создаем начальные платформы
        self.create_initial_platforms()

        # Обновляем физический движок
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=self.wall_list
        )

    def transition_to_level_5(self):
        """Переход на пятый уровень"""
        self.current_level = 5

        # Очищаем объекты
        self.wall_list.clear()
        self.platform_visual_list.clear()
        self.coins_list.clear()
        self.letters_list.clear()
        self.spikes_list.clear()
        self.collected_letters = []

        # Очищаем собранные слова четвертого уровня
        self.completed_words = [(word, trans) for word, trans in self.completed_words
                                if word not in ["math", "physics", "chemistry"]]

        self.max_spawn_x = LEVEL_5_START

        # ЗАПУСКАЕМ ЗАГРУЗКУ ДЛЯ ПЯТОГО УРОВНЯ
        self.is_loading = True
        self.loading_progress = 0
        self.platforms_generated = 0
        self.total_platforms_to_generate = 50

        # Перемещаем игрока
        self.player_sprite.center_x = LEVEL_5_START + 100
        self.player_sprite.center_y = 400
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0
        self.fall_start_height = None  # Сбрасываем высоту падения
        self.was_on_ground = True

        # Создаем начальные платформы
        self.create_initial_platforms()

        # Обновляем физический движок
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=self.wall_list
        )

    def check_fall_damage(self):
        """Смерть от падения - ИСПРАВЛЕННАЯ версия"""
        if self.current_level not in [3, 4, 5]:
            return

        # Проверяем, стоит ли игрок на чем-либо (пол ИЛИ платформа)
        is_on_something = False

        # Простая проверка: если вертикальная скорость почти 0 и игрок не падает
        if abs(self.player_sprite.change_y) < 0.1:  # Почти не движется по Y
            # Дополнительная проверка: игрок находится близко к какой-то поверхности снизу
            player_bottom = self.player_sprite.center_y - self.player_sprite.height // 2

            # Быстрая проверка расстояния до ближайшей поверхности
            # Ищем платформы/пол под игроком
            for wall in self.wall_list:
                wall_top = wall.center_y + wall.height // 2

                # Если игрок находится над платформой и близко к ней
                if (player_bottom <= wall_top + 5 and  # В пределах 5px
                        player_bottom >= wall_top - 15 and  # Не слишком далеко
                        abs(self.player_sprite.center_x - wall.center_x) < wall.width // 2 + 20):
                    is_on_something = True
                    break

            # Также проверяем пол (Y ≤ 60)
            if player_bottom <= 60:
                is_on_something = True

        if is_on_something:
            # Стоит на чем-то (платформа ИЛИ пол) - проверяем высоту падения
            if self.fall_start_height is not None:
                fall_distance = self.fall_start_height - self.player_sprite.center_y

                # Смерть ТОЛЬКО если падение на ПОЛ и высота > порога
                player_bottom = self.player_sprite.center_y - self.player_sprite.height // 2
                landed_on_floor = player_bottom <= 60  # Приземлился именно на пол

                if landed_on_floor and fall_distance > FALL_DEATH_THRESHOLD:
                    if self.shield_count > 0:
                        self.shield_count -= 1
                        self.shield_save_message = True
                        self.shield_save_timer = 60
                        self.bonus_purchase_message = "Щит спас от падения!"
                        self.bonus_message_timer = 60
                    else:
                        self.show_death_message = True
                        self.death_message_timer = 60
                        self.death_type = "fall"

                        if self.current_level == 3:
                            self.restart_level_3()
                        elif self.current_level == 4:
                            self.restart_level_4()
                        elif self.current_level == 5:
                            self.restart_level_5()

            # Сбрасываем высоту при приземлении на ЛЮБУЮ поверхность
            self.fall_start_height = None

        else:
            # В воздухе
            if self.fall_start_height is None:
                self.fall_start_height = self.player_sprite.center_y
            elif self.player_sprite.center_y > self.fall_start_height:
                self.fall_start_height = self.player_sprite.center_y

    def restart_level_3(self):
        """Рестарт третьего уровня"""
        # Восстанавливаем очередь букв
        self.letter_queue_level3 = [
            ("food", "f"), ("food", "o"), ("food", "o"), ("food", "d"),
            ("pizza", "p"), ("pizza", "i"), ("pizza", "z"), ("pizza", "z"), ("pizza", "a"),
            ("bread", "b"), ("bread", "r"), ("bread", "e"), ("bread", "a"), ("bread", "d"),
        ]

        # Сбрасываем прогресс слов
        for word in ["food", "pizza", "bread"]:
            if word in self.words_to_collect:
                self.words_to_collect[word]["collected"] = False
                self.words_to_collect[word]["progress"] = {}
                for letter in self.words_to_collect[word]["letters"]:
                    self.words_to_collect[word]["progress"][letter] = 0

        # Удаляем слова из completed_words
        self.completed_words = [(word, trans) for word, trans in self.completed_words
                                if word not in ["food", "pizza", "bread"]]

        # Очищаем объекты
        self.wall_list.clear()
        self.platform_visual_list.clear()
        self.coins_list.clear()
        self.letters_list.clear()
        self.spikes_list.clear()
        self.collected_letters = []

        self.max_spawn_x = LEVEL_3_START

        # ⛔️ НЕ ВКЛЮЧАЕМ ЗАГРУЗКУ - мгновенный рестарт
        self.is_loading = False

        # Перемещаем игрока
        self.player_sprite.center_x = LEVEL_3_START + 100
        self.player_sprite.center_y = 400
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0
        self.fall_start_height = None  # Сбрасываем высоту падения
        self.was_on_ground = True

        # Создаем начальные платформы
        self.create_initial_platforms()

        # 🔥 ДОБАВИТЬ: ГЕНЕРАЦИЯ ПЛАТФОРМ ПРИ РЕСТАРТЕ
        platforms_to_generate = 50  # Столько же сколько при загрузке 3 уровня
        for _ in range(platforms_to_generate):
            self._spawn_world_elements()

        # Обновляем физический движок
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=self.wall_list
        )

    def restart_level_4(self):
        """Рестарт четвертого уровня"""

        # Восстанавливаем очередь букв
        self.letter_queue_level4 = [
            ("math", "m"), ("math", "a"), ("math", "t"), ("math", "h"),
            ("physics", "p"), ("physics", "h"), ("physics", "y"), ("physics", "s"), ("physics", "i"), ("physics", "c"),
            ("physics", "s"),
            ("chemistry", "c"), ("chemistry", "h"), ("chemistry", "e"), ("chemistry", "m"), ("chemistry", "i"),
            ("chemistry", "s"), ("chemistry", "t"), ("chemistry", "r"), ("chemistry", "y"),
        ]

        # Сбрасываем прогресс слов
        for word in ["math", "physics", "chemistry"]:
            if word in self.words_to_collect:
                self.words_to_collect[word]["collected"] = False
                self.words_to_collect[word]["progress"] = {}
                for letter in self.words_to_collect[word]["letters"]:
                    self.words_to_collect[word]["progress"][letter] = 0

        # Удаляем слова из completed_words
        self.completed_words = [(word, trans) for word, trans in self.completed_words
                                if word not in ["math", "physics", "chemistry"]]

        # Очищаем объекты
        self.wall_list.clear()
        self.platform_visual_list.clear()
        self.coins_list.clear()
        self.letters_list.clear()
        self.spikes_list.clear()
        self.collected_letters = []

        self.max_spawn_x = LEVEL_4_START

        # ⛔️ НЕ ВКЛЮЧАЕМ ЗАГРУЗКУ - мгновенный рестарт
        self.is_loading = False

        # Перемещаем игрока
        self.player_sprite.center_x = LEVEL_4_START + 100
        self.player_sprite.center_y = 400
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0
        self.fall_start_height = None  # Сбрасываем высоту падения
        self.was_on_ground = True

        # Создаем начальные платформы
        self.create_initial_platforms()

        # 🔥 ДОБАВИТЬ: ГЕНЕРАЦИЯ ПЛАТФОРМ ПРИ РЕСТАРТЕ
        platforms_to_generate = 50  # Столько же сколько при загрузке 4 уровня
        for _ in range(platforms_to_generate):
            self._spawn_world_elements()

        # Обновляем физический движок
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=self.wall_list
        )

    def restart_level_5(self):
        """Рестарт пятого уровня"""

        # Восстанавливаем очередь букв
        self.letter_queue_level5 = [
            ("sofa", "s"), ("sofa", "o"), ("sofa", "f"), ("sofa", "a"),
            ("table", "t"), ("table", "a"), ("table", "b"), ("table", "l"), ("table", "e"),
            ("chair", "c"), ("chair", "h"), ("chair", "a"), ("chair", "i"), ("chair", "r"),
        ]

        # Сбрасываем прогресс слов
        for word in ["sofa", "table", "chair"]:
            if word in self.words_to_collect:
                self.words_to_collect[word]["collected"] = False
                self.words_to_collect[word]["progress"] = {}
                for letter in self.words_to_collect[word]["letters"]:
                    self.words_to_collect[word]["progress"][letter] = 0

        # Удаляем слова из completed_words
        self.completed_words = [(word, trans) for word, trans in self.completed_words
                                if word not in ["sofa", "table", "chair"]]

        # Очищаем объекты
        self.wall_list.clear()
        self.platform_visual_list.clear()
        self.coins_list.clear()
        self.letters_list.clear()
        self.spikes_list.clear()
        self.collected_letters = []

        self.max_spawn_x = LEVEL_5_START

        # ⛔️ НЕ ВКЛЮЧАЕМ ЗАГРУЗКУ - мгновенный рестарт
        self.is_loading = False

        # Перемещаем игрока
        self.player_sprite.center_x = LEVEL_5_START + 100
        self.player_sprite.center_y = 400
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0
        self.fall_start_height = None  # Сбрасываем высоту падения
        self.was_on_ground = True

        # Создаем начальные платформы
        self.create_initial_platforms()

        # 🔥 ДОБАВИТЬ: ГЕНЕРАЦИЯ ПЛАТФОРМ ПРИ РЕСТАРТЕ
        platforms_to_generate = 50  # Столько же сколько при загрузке 5 уровня
        for _ in range(platforms_to_generate):
            self._spawn_world_elements()

        # Обновляем физический движок
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=self.wall_list
        )

    def check_word_completion(self):
        """Проверяет, собраны ли все буквы для какого-либо слова"""
        for word, data in self.words_to_collect.items():
            if data["collected"]:
                continue

            if self.current_level == 1 and word not in ["cat", "dog"]:
                continue
            if self.current_level == 2 and word not in ["mother", "father", "brother"]:
                continue
            if self.current_level == 3 and word not in ["food", "pizza", "bread"]:
                continue
            if self.current_level == 4 and word not in ["math", "physics", "chemistry"]:
                continue
            if self.current_level == 5 and word not in ["sofa", "table", "chair"]:
                continue

            all_letters_collected = True
            for letter in data["letters"]:
                needed_count = data["letters"].count(letter)
                collected_count = data["progress"].get(letter, 0)
                if collected_count < needed_count:
                    all_letters_collected = False
                    break

            if all_letters_collected:
                data["collected"] = True
                if not any(w == word for w, t in self.completed_words):
                    self.completed_words.append((word, data["translation"]))

    def on_draw(self):
        """Отрисовка игры - СУПЕР ОПТИМИЗИРОВАННАЯ"""
        self.clear()

        if self.is_loading:
            self._draw_loading_screen()
            return

        # 1. ФОН
        if self.background_list:
            self.background_list.draw()

        # 2. ВИДИМАЯ ОБЛАСТЬ
        cam_left = self.camera_x
        cam_right = self.camera_x + SCREEN_WIDTH

        # 3. ПЛАТФОРМЫ - только видимые
        for platform in self.platform_visual_list:
            plat_left = platform.center_x - platform.width // 2
            plat_right = platform.center_x + platform.width // 2

            if plat_right >= cam_left and plat_left <= cam_right:
                draw_left = plat_left - self.camera_x
                draw_right = plat_right - self.camera_x
                bottom = platform.center_y - platform.height // 2
                top = platform.center_y + platform.height // 2
                arcade.draw_lrbt_rectangle_filled(draw_left, draw_right, bottom, top, platform.color)

        # 4. ШИПЫ
        if self.current_level in [4, 5]:
            for spike in self.spikes_list:
                if cam_left <= spike.center_x <= cam_right:
                    x = spike.center_x - self.camera_x
                    y = spike.center_y
                    # 🔥 Исправлено: draw_polygon вместо draw_triangle
                    points = [
                        (x, y + SPIKE_HEIGHT // 2),
                        (x - SPIKE_WIDTH // 2, y - SPIKE_HEIGHT // 2),
                        (x + SPIKE_WIDTH // 2, y - SPIKE_HEIGHT // 2)
                    ]
                    arcade.draw_polygon_filled(points, arcade.color.BLACK)
                    arcade.draw_polygon_outline(points, arcade.color.DARK_RED, 2)

        # 5. МОНЕТКИ
        for coin in self.coins_list:
            if not coin.collected and cam_left <= coin.center_x <= cam_right:
                x = coin.center_x - self.camera_x
                arcade.draw_circle_filled(x, coin.center_y, 15, arcade.color.GOLD)

        # 6. БУКВЫ - 🔥 ИСПРАВЛЕНО: полная отрисовка как раньше
        for letter in self.letters_list:
            if not letter.collected and cam_left <= letter.center_x <= cam_right:
                x = letter.center_x - self.camera_x
                y = letter.center_y

                # 1. Синий круг (фон буквы)
                arcade.draw_circle_filled(x, y, 20, arcade.color.LIGHT_BLUE)

                # 2. Темно-синяя обводка
                arcade.draw_circle_outline(x, y, 20, arcade.color.DARK_BLUE, 2)

                # 3. Сама буква черная по центру
                arcade.draw_text(
                    letter.letter.upper(),
                    x, y,
                    arcade.color.BLACK, 18,
                    align="center", anchor_x="center", anchor_y="center"
                )

        # 7. ИГРОК
        # 🔥 Исправлено: правильно работаем с камерой
        for player in self.player_list:
            player.center_x -= self.camera_x
        self.player_list.draw()
        for player in self.player_list:
            player.center_x += self.camera_x

        # 8. HUD
        self._draw_hud()

    def on_update(self, delta_time):
        """Обновление игры - ОПТИМИЗИРОВАННОЕ"""
        if self.is_loading:
            # Загрузка
            platforms_per_frame = 1
            for _ in range(platforms_per_frame):
                if self.platforms_generated < self.total_platforms_to_generate:
                    self._spawn_world_elements()
                    self.platforms_generated += 1

            self.loading_progress = (self.platforms_generated / self.total_platforms_to_generate) * 100

            if self.platforms_generated >= self.total_platforms_to_generate:
                self.is_loading = False
            return

        # Только основные проверки
        self.check_level_transition()

        # Условные проверки для нужных уровней
        if self.current_level in [3, 4, 5]:
            self.check_fall_damage()

        if self.current_level in [4, 5]:
            self.check_spikes_collision()

        # Камера - мягкое следование
        target_x = self.player_sprite.center_x - SCREEN_WIDTH / 2
        if target_x < 0:
            target_x = 0

        if self.current_level == 1:
            max_camera = LEVEL_1_END - SCREEN_WIDTH
        elif self.current_level == 2:
            max_camera = WORLD_BOUNDARY - SCREEN_WIDTH
        else:
            max_camera = WORLD_BOUNDARY - SCREEN_WIDTH

        if target_x > max_camera:
            target_x = max_camera

        self.camera_x += (target_x - self.camera_x) * 0.15

        # Таймеры
        if self.show_death_message:
            self.death_message_timer -= 1
            if self.death_message_timer <= 0:
                self.show_death_message = False

        if self.shield_save_message:
            self.shield_save_timer -= 1
            if self.shield_save_timer <= 0:
                self.shield_save_message = False

        if self.bonus_message_timer > 0:
            self.bonus_message_timer -= 1

        # Проверка времени бонусов
        if self.speed_boost_active or self.jump_boost_active:
            current_time = time.time()
            if self.speed_boost_active and current_time > self.speed_boost_end_time:
                self.speed_boost_active = False
            if self.jump_boost_active and current_time > self.jump_boost_end_time:
                self.jump_boost_active = False

        # Ограничения движения
        if self.current_level == 1:
            if self.player_sprite.center_x < 0:
                self.player_sprite.center_x = 0
                self.player_sprite.change_x = 0
        elif self.current_level == 2:
            if self.player_sprite.center_x < LEVEL_2_START:
                self.player_sprite.center_x = LEVEL_2_START
                self.player_sprite.change_x = 0
        elif self.current_level == 3:
            if self.player_sprite.center_x < LEVEL_3_START:
                self.player_sprite.center_x = LEVEL_3_START
                self.player_sprite.change_x = 0
        else:
            if self.current_level == 4:
                if self.player_sprite.center_x < LEVEL_4_START:
                    self.player_sprite.center_x = LEVEL_4_START
                    self.player_sprite.change_x = 0
            elif self.current_level == 5:
                if self.player_sprite.center_x < LEVEL_5_START:
                    self.player_sprite.center_x = LEVEL_5_START
                    self.player_sprite.change_x = 0

            if self.player_sprite.center_x > WORLD_BOUNDARY:
                self.player_sprite.center_x = WORLD_BOUNDARY
                self.player_sprite.change_x = 0

        # Физика
        self.physics_engine.update()

        # Коллизии - только если движется
        if abs(self.player_sprite.change_x) > 0.1 or abs(self.player_sprite.change_y) > 0.1:
            self._check_coin_collisions()
            self._check_letter_collisions()

    def buy_bonus(self, bonus_type):
        """Покупка бонуса"""
        price = self.BONUS_PRICES[bonus_type]

        if self.coins_collected >= price:
            self.coins_collected -= price
            current_time = time.time()

            if bonus_type == "shield":
                self.shield_count += 1
                self.bonus_purchase_message = f"Куплен щит! Всего щитов: {self.shield_count}"
            elif bonus_type == "speed":
                self.speed_boost_active = True
                self.speed_boost_end_time = current_time + self.BONUS_DURATION
                self.bonus_purchase_message = f"Куплено ускорение на {self.BONUS_DURATION} секунд!"
            elif bonus_type == "jump":
                self.jump_boost_active = True
                self.jump_boost_end_time = current_time + self.BONUS_DURATION
                self.bonus_purchase_message = f"Куплено усиление прыжка на {self.BONUS_DURATION} секунд!"

            self.bonus_message_timer = 60  # Показать сообщение 2 секунды (60 кадров)
        else:
            self.bonus_purchase_message = f"Недостаточно монет!"
            self.bonus_message_timer = 60

    def on_key_press(self, key, modifiers):
        """Обработка нажатия клавиш"""
        if self.is_loading:
            return  # Игнорируем ввод во время загрузки

        current_move_speed = PLAYER_MOVE_SPEED
        current_jump_speed = PLAYER_JUMP_SPEED

        # Применяем бонусы скорости и прыжка
        if self.speed_boost_active:
            current_move_speed = int(PLAYER_MOVE_SPEED * self.SPEED_BOOST_MULTIPLIER)

        if self.jump_boost_active:
            current_jump_speed = int(PLAYER_JUMP_SPEED * self.JUMP_BOOST_MULTIPLIER)

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = -current_move_speed
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = current_move_speed
        elif key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = current_jump_speed

        # Покупка бонусов по клавишам
        elif key == arcade.key.KEY_1 or key == arcade.key.NUM_1:
            self.buy_bonus("speed")
        elif key == arcade.key.KEY_2 or key == arcade.key.NUM_2:
            self.buy_bonus("jump")
        elif key == arcade.key.KEY_3 or key == arcade.key.NUM_3:
            self.buy_bonus("shield")

    def on_key_release(self, key, modifiers):
        """Обработка отпускания клавиш"""
        if self.is_loading:
            return  # Игнорируем ввод во время загрузки

        if (key == arcade.key.LEFT or key == arcade.key.A) and self.player_sprite.change_x < 0:
            self.player_sprite.change_x = 0
        elif (key == arcade.key.RIGHT or key == arcade.key.D) and self.player_sprite.change_x > 0:
            self.player_sprite.change_x = 0


# --------------------------------
# Запуск игры
# --------------------------------
def main():
    window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()