import os
import shutil
import numpy as np
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import mariadb
from concurrent.futures import ThreadPoolExecutor
import cv2
import pandas as pd


class PhotoProcessor:
    def __init__(self, db_config, base_output_folder, excel_path):
        self.model = MobileNetV2(weights="imagenet")  # MobileNetV2 모델 로드
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.base_output_folder = base_output_folder
        self.excel_path = excel_path

        # DB 연결
        try:
            self.db = mariadb.connect(**db_config)
            self.cursor = self.db.cursor()
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            raise

        self.tag_mapping = self.create_tag_mapping()
        self.excel_data = []  # Excel에 저장할 데이터를 담는 리스트
    def create_tag_mapping(self):
        """태그 매핑"""
        return {
        # 장소/객체 기반
        "산": ["mountain", "peak", "ridge", "summit", "hill", "trail", "rocky", "alpine", "elevation", "cliff",
               "slope", "gorge", "plateau", "ridgeback", "valley", "escarpment", "foothill", "crag", "bluff", "range",
               "spur", "ledge", "abutment", "butte", "knob", "mesa", "promontory", "tor", "peaklet", "knoll", "massif",
               "headland", "upland", "moraine", "drumlin", "pinnacle", "cairn", "summit_cross", "vista", "outcrop", 
               "alps", "pyrenees", "andes", "himalayas", "rock", "shale", "boulder", "escarpment_cliff", "precipice"],
        "바다": ["ocean", "sea", "coastline", "beach", "shore", "tidal", "reef", "wave", "surf", "maritime", "marine",
                "seaside", "breeze", "current", "tidal_wave", "pelagic", "coral", "lagoon", "harbor", "bay", "gulf", 
                "strait", "fjord", "archipelago", "island", "cove", "peninsula", "sandbar", "tidepool", "jetty", 
                "breakwater", "pier", "dock", "shipwreck", "whale", "dolphin", "cruise", "fishing", "seashell", 
                "snorkeling", "scuba_diving", "surfing", "kayaking", "windsurfing", "sailing", "yacht", "vessel", 
                "marine_reserve", "underwater", "coastal_erosion"],
        "도시": ["city", "metropolis", "urban", "skyscraper", "downtown", "suburb", "district", "neighborhood", 
                 "block", "plaza", "square", "avenue", "boulevard", "lane", "bypass", "crossroad", "intersection", 
                 "overpass", "underpass", "bridge", "highway", "train_station", "bus_stop", "metro", "tram", 
                 "skyline", "industrial", "residential", "park", "mall", "market", "bazaar", "boutique", 
                 "restaurant", "cafe", "theater", "museum", "gallery", "library", "stadium", "arena", "gym", 
                 "skatepark", "amusement_park", "zoo", "aquarium", "planetarium", "hospital", "clinic", "school", 
                 "university"],
        "카페": ["coffee_shop", "cafe", "latte", "espresso", "cappuccino", "macchiato", "mocha", "flat_white", "brew", 
                 "tea", "matcha", "green_tea", "black_tea", "chai", "herbal_tea", "pastry", "muffin", "scone", "croissant",
                 "bagel", "cake", "cheesecake", "brownie", "cookie", "tart", "waffle", "sandwich", "quiche", "salad", 
                 "baguette", "panini", "juice", "smoothie", "lemonade", "iced_coffee", "iced_tea", "latte_art", 
                 "barista", "cozy", "rustic", "industrial", "modern", "minimalist", "vintage", "hipster", "aroma", 
                 "bean", "grinder", "roast", "cup", "brewery", "coffee_beans"],
        "공원": ["park", "garden", "playground", "fountain", "bench", "tree", "flower", "grass", "bush", "lake", 
                 "pond", "bridge", "walking_path", "trail", "pavilion", "statue", "gazebo", "swing", "sandbox", 
                 "picnic_area", "sports_field", "bike_path", "dog_park", "duck_pond", "waterfall", "shade", 
                 "wildlife", "butterfly", "bird", "jogging", "relaxation", "camping", "barbecue", "arbor", 
                 "sunset", "sunrise", "scenic", "bamboo", "koi_pond", "pagoda", "orchard", "blossom", 
                 "greenhouse", "shrubbery", "bonsai", "lotus", "meditation", "hiking", "recreation"],
        "식당": ["restaurant", "bistro", "diner", "fine_dining", "casual_dining", "family_style", "buffet", 
                 "fast_food", "pub", "tavern", "steakhouse", "pizzeria", "seafood_restaurant", "sushi_bar", 
                 "noodle_shop", "taco_truck", "kitchen", "barbecue", "grill", "cuisine", "menu", "table", 
                 "reservation", "chef", "server", "waiter", "meal", "dish", "appetizer", "main_course", 
                 "dessert", "beverage", "wine", "beer", "cocktail", "chef_special", "platter", "takeout", 
                 "delivery", "outdoor_dining", "view", "ambience", "romantic", "cozy", "modern", "rustic", 
                 "open_kitchen", "banquet", "foodie", "flavors", "aroma"],
        "건물": ["architecture", "building", "skyscraper", "bridge", "castle", "temple", "monument", "tower",
                 "museum", "fortress", "villa", "lighthouse", "chapel", "windmill", "barn", "greenhouse", 
                 "factory", "mill", "stadium", "gallery", "university", "school", "hospital", "church", 
                 "airport", "train_station", "subway", "library", "theater", "opera", "amphitheater", 
                 "cottage", "bungalow", "mansion", "palace", "mausoleum", "coliseum", "cathedral", "dome", 
                 "aqueduct", "obelisk", "pagoda", "ziggurat", "shrine", "sanctuary", "synagogue", "mosque", 
                 "tent", "kiosk", "gazebo", "pavilion", "observatory"],
        "야경": ["night_view", "skyline", "moonlight", "starry", "city_lights", "lantern", "streetlamp", "neon", 
                 "silhouette", "shadow", "reflection", "fireworks", "aurora", "twilight", "evening", "foggy", 
                 "misty", "shimmer", "glow", "halo", "beam", "dark", "dusk", "dawn", "flicker", "flare", 
                 "flash", "ray", "sparkle", "spotlight", "dim", "eclipse", "starlight", "candle", "lanterns", 
                 "firefly", "constellation", "comet", "meteor", "moonglow", "streetlight", "urban_light", 
                 "colorful", "chandelier", "lamp", "fairylight", "electric"],
        "길": ["road", "pathway", "street", "trail", "lane", "alley", "boulevard", "avenue", "highway", 
               "intersection", "crossroad", "overpass", "underpass", "bridge", "walkway", "footpath", 
               "bicycle_path", "driveway", "expressway", "tunnel", "cobblestone", "sidewalk", "boardwalk", 
               "path", "track", "route", "curve", "junction", "turn", "traffic_light", "roundabout", 
               "pedestrian", "zebra_crossing", "crosswalk", "stairway", "cliffside", "forest_path", 
               "desert_road", "coastal_drive", "dirt_track", "scenic_route", "parkway", "tollway", 
               "roadtrip", "curve", "turn", "shortcut", "long_way", "main_road"],
        "고기 요리": [
                "steak", "grill", "bbq", "beef", "pork", "lamb", "chicken", "duck", "turkey", "sausage",
             "bacon", "ribs", "ham", "kebab", "meatball", "filet", "roast", "burger", "minced_meat",
             "ribeye", "sirloin", "brisket", "veal", "spare_ribs", "meat_loaf", "shank", "prime_rib",
             "skewers", "shish_kebab", "jerky", "pastrami", "charcuterie", "cold_cuts", "grilled_steak",
             "roast_beef", "chateaubriand", "medallion", "tomahawk", "meat_platter", "barbecue",
             "beef_curry", "stroganoff", "meat_stew", "steak_tartare", "smoked_meat", "tenderloin",
              "chops", "cutlet"
                ],
        "해산물 요리": [
            "seafood", "fish", "shrimp", "crab", "lobster", "oyster", "clam", "mussel", "scallop",
            "octopus", "squid", "salmon", "tuna", "trout", "mackerel", "cod", "anchovy", "sardine",
            "roe", "caviar", "eel", "grilled_fish", "baked_fish", "steamed_fish", "smoked_fish",
            "pickled_fish", "ceviche", "paella", "bouillabaisse", "clam_chowder", "seaweed",
            "tempura", "sushi", "sashimi", "fish_tacos", "seafood_pasta", "crab_legs", "king_crab",
            "blue_crab", "lobster_bisque", "fish_stew", "seafood_platter", "fried_fish", "fish_curry",
            "seafood_risotto", "shellfish", "grilled_shrimp", "cuttlefish", "seafood_soup", "fish_fillet"
        ],
        "디저트": [
            "cake", "pastry", "brownie", "cookie", "macaron", "cupcake", "muffin", "cheesecake",
            "tart", "pie", "pudding", "mousse", "trifle", "ice_cream", "sorbet", "gelato",
            "sundae", "popsicle", "chocolate", "fudge", "truffle", "candy", "caramel", "nougat",
            "toffee", "baklava", "doughnut", "eclair", "waffle", "pancake", "crepe", "strudel",
            "danish", "brulee", "tiramisu", "parfait", "gingerbread", "shortbread", "fruit_tart",
            "sponge_cake", "souffle", "mille_feuille", "churros", "custard", "jelly", "sweet_pie",
            "lemon_tart", "pavlova", "fruit_salad", "ice_cream_cake"
        ],
        "음료": [
            "coffee", "latte", "espresso", "mocha", "americano", "macchiato", "tea", "green_tea",
            "black_tea", "chai", "matcha", "herbal_tea", "smoothie", "juice", "milkshake",
            "lemonade", "soda", "cola", "sparkling_water", "cocktail", "mocktail", "wine", "beer",
            "whiskey", "vodka", "rum", "tequila", "gin", "champagne", "martini", "margarita",
            "mojito", "sangria", "hot_chocolate", "iced_tea", "iced_coffee", "pina_colada",
            "energy_drink", "sports_drink", "milk", "almond_milk", "coconut_water", "bubble_tea",
            "frappuccino", "apple_juice", "orange_juice", "cranberry_juice", "kombucha"
        ],
        "채소 요리": [
            "salad", "vegetable_stir_fry", "grilled_vegetable", "roasted_vegetable", "veggie_wrap",
            "ratatouille", "crudites", "veggie_platter", "coleslaw", "kimchi", "pickled_vegetable",
            "cucumber", "tomato", "carrot", "broccoli", "cauliflower", "spinach", "lettuce", "kale",
            "beet", "zucchini", "squash", "eggplant", "mushroom", "corn", "peas", "okra", "pepper",
            "bell_pepper", "green_bean", "asparagus", "brussels_sprout", "cabbage", "leek",
            "celery", "parsnip", "turnip", "radish", "artichoke", "chard", "arugula", "collard",
            "chickpea", "lentil", "onion", "garlic", "sweet_potato", "potato"
        ],
        "면 요리": [
            "spaghetti", "ramen", "udon", "soba", "pho", "pasta", "fettuccine", "penne", "macaroni",
            "tagliatelle", "lasagna", "bolognese", "carbonara", "alfredo", "primavera", "arrabbiata",
            "pad_thai", "lo_mein", "yakisoba", "kalguksu", "jajangmyeon", "jjamppong", "bun", 
            "rice_noodle", "glass_noodle", "stir_fry_noodle", "seafood_noodle", "beef_noodle",
            "chicken_noodle", "vegetable_noodle", "vermicelli", "curry_noodle", "dan_dan_noodle",
            "cold_noodle", "instant_noodle", "hotpot_noodle", "shabu_noodle", "meat_noodle",
            "pesto_pasta", "sushi_noodle", "tomato_pasta", "cheese_pasta", "creamy_pasta",
            "seafood_pasta", "meatball_pasta", "egg_noodle"
        ],
        "국물 요리": [
            "soup", "broth", "stew", "ramen", "pho", "jjigae", "hotpot", "gazpacho", "borscht", 
            "chowder", "bisque", "goulash", "gumbo", "consomme", "seaweed_soup", "chicken_soup",
            "beef_soup", "pork_soup", "fish_soup", "vegetable_soup", "lentil_soup", "noodle_soup",
            "clam_chowder", "lobster_bisque", "miso_soup", "kimchi_jjigae", "doenjang_jjigae",
            "bean_paste_soup", "tofu_soup", "egg_drop_soup", "clear_soup", "onion_soup",
            "pumpkin_soup", "tomato_soup", "split_pea_soup", "minestrone", "sinigang", "laksa",
            "thukpa", "shabu_shabu", "kalguksu", "dumpling_soup", "seafood_stew", "beef_stew",
            "pork_bone_soup", "ox_tail_soup", "sundae_guk"
        ],
        "빵류": [
            "bread", "baguette", "rye_bread", "sourdough", "whole_wheat", "white_bread", "ciabatta",
            "brioche", "flatbread", "naan", "pita", "chapati", "tortilla", "bun", "roll", "muffin",
            "croissant", "danish", "pastry", "bagel", "pretzel", "toast", "garlic_bread", "sandwich",
            "burger_bun", "hotdog_bun", "ciabatta_roll", "pumpernickel", "cornbread", "banana_bread",
            "zucchini_bread", "pumpkin_bread", "cinnamon_roll", "shortbread", "gingerbread", 
            "focaccia", "matzo", "chapati_bread", "flat_roll", "ciabatta_loaf", "sweet_roll",
            "crouton", "brioche_loaf", "donut", "tart_bread", "pizza_base"
        ],
                "샐러드": [
            "caesar_salad", "green_salad", "fruit_salad", "pasta_salad", "potato_salad", "coleslaw", 
            "greek_salad", "caprese_salad", "cobb_salad", "waldorf_salad", "chicken_salad", 
            "tuna_salad", "egg_salad", "quinoa_salad", "lentil_salad", "rice_salad", "bean_salad", 
            "avocado_salad", "kale_salad", "spinach_salad", "arugula_salad", "mixed_greens", 
            "crouton_salad", "beet_salad", "carrot_salad", "cucumber_salad", "tomato_salad", 
            "seaweed_salad", "asian_salad", "thai_salad", "indian_salad", "chickpea_salad", 
            "noodle_salad", "shrimp_salad", "crab_salad", "lobster_salad", "salmon_salad", 
            "roasted_vegetable_salad", "warm_salad", "cold_salad", "vegetable_salad", 
            "bacon_salad", "cheese_salad", "parmesan_salad", "dressing_salad", "vinaigrette", 
            "balsamic_salad", "sour_cream_salad", "yogurt_salad", "honey_mustard_salad"
        ],
        "따뜻함": [
            "cozy", "warmth", "hearth", "fireplace", "blanket", "comfort", "glow", "homely", "snug", 
            "intimate", "family", "peaceful", "soft_lighting", "amber_light", "rustic", "wood", 
            "sunlit", "autumn", "hygge", "handmade", "earth_tones", "wool", "knit", "natural", 
            "welcoming", "embrace", "tea", "candle", "friendly", "organic", "natural_light", 
            "plants", "calming", "gentle", "love", "reassurance", "security", "nostalgic", "sentimental",
            "firelight", "golden", "tenderness", "kindness", "simplicity", "serenity", "belonging",
            "tradition", "hearthside", "cherish", "familiar"
        ],
        "모던함": [
            "modern", "minimalist", "sleek", "clean", "contemporary", "industrial", "polished", 
            "geometric", "chrome", "glass", "urban", "neutral_colors", "monochrome", "black_and_white",
            "simplicity", "open_space", "functional", "high_tech", "smart", "futuristic", "linear",
            "sharp_edges", "metal", "abstract", "innovative", "cutting_edge", "artistic", 
            "trendsetting", "streamlined", "scandinavian", "elegant", "refined", "uncluttered", 
            "precise", "professional", "neat", "organized", "stylish", "techy", "innovation", 
            "industrial_lighting", "digital", "graphic", "artistic_lines", "sharp_contrast", 
            "state_of_the_art", "urban_chic", "avant_garde", "functional_aesthetic"
        ],
        "차가움": [
            "cold", "icy", "frosty", "blue_tones", "silver", "steel", "frozen", "winter", "crisp", 
            "arctic", "chilly", "cool", "aloof", "reserved", "snowy", "sleek", "glacial", "serene", 
            "polished", "remote", "distant", "white", "glass", "mist", "fog", "dewy", "metallic", 
            "frost", "ice", "neutral", "industrial", "minimalist", "sterile", "clean_lines", "sharp", 
            "modern", "blue", "aquatic", "refreshing", "ethereal", "wintry", "celestial", 
            "sky_tones", "calm", "precision", "unemotional", "space", "high_tech", "unfeeling", 
            "isolated", "moonlight", "frosted_glass"
        ],
        "조용함": [
            "quiet", "peaceful", "tranquil", "serene", "hushed", "calm", "relaxing", "meditative", 
            "still", "undisturbed", "silent", "repose", "soothing", "placid", "low_light", "soft", 
            "intimate", "gentle", "natural", "reclusive", "solitude", "harmonious", "balance", 
            "nature", "low_noise", "whispering", "calm_water", "zen", "minimal", "orderly", 
            "uncluttered", "smooth", "flowing", "subtle", "graceful", "muted_colors", "understated", 
            "timeless", "soothing_music", "escape", "sanctuary", "retreat", "contemplative", 
            "spiritual", "light", "calm_sea", "still_mountain", "dawn", "early_morning", "twilight"
        ],
        "활기참": [
            "vibrant", "energetic", "lively", "colorful", "bright", "cheerful", "dynamic", "bold", 
            "exciting", "playful", "radiant", "sparkling", "glowing", "jovial", "animated", 
            "flamboyant", "electric", "neon", "powerful", "spirited", "zesty", "bubbly", "joyful", 
            "dazzling", "glamorous", "sassy", "loud", "engaging", "charismatic", "hustling", 
            "bustling", "streetlife", "fiery", "party", "festival", "carnival", "parade", "exuberant", 
            "adventurous", "zany", "exotic", "brash", "pulsating", "shimmering", "effervescent", 
            "boisterous", "extravagant", "vivacious", "sunlit", "radiance"
        ],
        "로맨틱": [
            "romantic", "intimate", "loving", "passionate", "sentimental", "tender", "candlelit", 
            "cozy", "warm", "rosy", "enchanted", "dreamy", "ethereal", "heartfelt", "amorous", 
            "sweet", "gentle", "affectionate", "charming", "whimsical", "sparkling", "idyllic", 
            "roses", "flowers", "wedding", "proposal", "honeymoon", "sunset", "moonlight", "starlit", 
            "soothing", "glow", "serene", "melancholic", "soft_lighting", "harmony", "rustic", 
            "handwritten", "love_note", "timeless", "classic", "poetic", "artistic", "delicate", 
            "lovely", "graceful", "tranquil", "sunlit_balcony", "rain_kissed", "cherished"
        ],
        "어두움": [
            "dark", "gloomy", "shadowy", "mysterious", "moody", "somber", "eerie", "melancholy", 
            "misty", "dusky", "stormy", "foreboding", "gritty", "dramatic", "intense", "bold", 
            "smoky", "hidden", "subdued", "chiaroscuro", "night", "nocturnal", "moonlit", 
            "twilight", "foggy", "haunting", "black", "charcoal", "ebony", "sable", "onyx", "graphite", 
            "navy", "midnight_blue", "stormcloud", "rustic", "urban", "industrial", "underground", 
            "grunge", "abstract", "isolated", "brooding", "wild", "shadowplay", "dimly_lit", 
            "mystical", "enigmatic", "hidden_perspectives"
        ],
                "밝음": [
            "bright", "cheerful", "vivid", "colorful", "sunny", "radiant", "glowing", "illuminated", 
            "golden", "happy", "sparkling", "shimmering", "dazzling", "brilliant", "vibrant", 
            "playful", "energetic", "electric", "effervescent", "bubbly", "joyful", "optimistic", 
            "uplifting", "sunlit", "luminous", "crystal_clear", "clarity", "open", "airy", 
            "expansive", "lighthearted", "bouncy", "warm", "saturated", "pure", "radiance", 
            "highlighted", "chromatic", "dynamic", "vivid_hues", "polished", "shiny", "glinting", 
            "gleaming", "mirrored", "sparkling_water", "sunrise", "daybreak", "bright_skies", 
            "rainbow", "golden_hour", "illumination", "color_pop"
        ]
    }

    def has_faces(self, img_path):
        """얼굴 검출"""
        try:
            img = cv2.imread(img_path)
            if img is None or img.shape[0] == 0 or img.shape[1] == 0:
                print(f"이미지 크기가 유효하지 않습니다: {img_path}")
                return False

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            return len(faces) > 0
        except Exception as e:
            print(f"얼굴 검출 중 오류 발생: {e}")
            return False


    def analyze_image(self, img_path):
        """이미지 분석 및 태그 생성"""
        try:
            img = image.load_img(img_path, target_size=(224, 224))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)

            preds = self.model.predict(img_array)
            decoded = decode_predictions(preds, top=10)  # 상위 10개의 예측
            print(f"예측 결과: {decoded}")

            # 정확도 높은 상위 3개의 태그 선택, NaN 값 필터링
            tags = [pred[1] for pred in decoded[0] if not np.isnan(pred[2])][:3]
            return self.map_tags_to_categories(tags)
        except Exception as e:
            print(f"이미지 분석 중 오류 발생: {e}")
            return []



    def map_tags_to_categories(self, tags):
        """예측된 태그를 카테고리와 매핑"""
        mapped_categories = []
        for tag in tags:
            for category, keywords in self.tag_mapping.items():
                if tag in keywords:
                    mapped_categories.append(category)
                    break
        return list(set(mapped_categories))  # 중복 제거

    def save_to_excel(self, img_path, tags):
        """파일 이름과 태그를 Excel 파일에 저장"""
        file_name = os.path.basename(img_path)
        if not any(data["File Name"] == file_name for data in self.excel_data):
            self.excel_data.append({"File Name": file_name, "Tags": ", ".join(tags)})

    def save_to_db(self, img_path, tags):
        """태그를 데이터베이스에 저장"""
        try:
            # 이미지 파일 이름 추출
            file_name = os.path.basename(img_path)

            # Photos 테이블에 데이터 삽입
            self.cursor.execute("INSERT INTO contents (file_name, tags) VALUES (?, ?)", 
                                (file_name, ",".join(tags)))
            self.db.commit()
            print(f"'{file_name}'의 태그가 데이터베이스에 저장되었습니다.")
        except mariadb.Error as e:
            print(f"데이터베이스 저장 중 오류 발생: {e}")


    def create_folder_and_move_image(self, img_path, tags):
        """태그 기반 폴더 생성 및 이미지 이동"""
        for tag in tags:
            output_folder = os.path.join(self.base_output_folder, tag)
            os.makedirs(output_folder, exist_ok=True)
            shutil.move(img_path, os.path.join(output_folder, os.path.basename(img_path)))
        print(f"'{img_path}' 파일이 태그 폴더로 이동되었습니다: {tags}")

    def process_photo(self, img_path):
        """사진 처리 및 저장"""
        if self.has_faces(img_path):
            print(f"얼굴 감지됨: {img_path}, 건너뜀.")
            self.save_to_excel(img_path, ["건너뜀"])
            return

        print(f"이미지 분석 시작: {img_path}")
        tags = self.analyze_image(img_path)
        if tags:
            print(f"태그 생성됨: {tags}")
        else:
            print(f"태그 없음: {img_path}")

        self.save_to_excel(img_path, tags)
        self.save_to_db(img_path, tags)
        self.create_folder_and_move_image(img_path, tags)  # 폴더로 이동
        print(f"분석 완료: {img_path}, 태그: {tags}")

    def process_photos_in_folder(self, folder_path):
        """폴더 내 모든 사진 처리"""
        photos = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith((".jpg", ".png"))]
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(self.process_photo, photos)

        # 모든 작업이 완료되면 Excel 파일 저장
        df = pd.DataFrame(self.excel_data, columns=["File Name", "Tags"])
        try:
            os.makedirs(os.path.dirname(self.excel_path), exist_ok=True)
            df.to_excel(self.excel_path, index=False, engine="openpyxl")
            print(f"Excel 파일 저장 완료: {self.excel_path}")
        except Exception as e:
            print(f"Error saving Excel file: {e}")


if __name__ == "__main__":
    # **사용자가 직접 설정해야 할 부분**
    db_config = {
            host="localhost",        # MariaDB 서버 주소
            user="root",             # MariaDB 사용자 이름
            password="1234",         # MariaDB 비밀번호
            database=database 
    }

    folder_path = "/Users/jeongjigang/Desktop/ImageAll/서촌핫플"  # 처리할 이미지 폴더
    base_output_folder = "/Users/jeongjigang/Desktop/ImageDef"  # 결과를 저장할 폴더
    excel_path = "/Users/jeongjigang/Desktop/ImageDef/photos_analysis.xlsx"  # 결과를 저장할 Excel 파일 경로

    processor = PhotoProcessor(db_config, base_output_folder, excel_path)
    processor.process_photos_in_folder(folder_path)
    print("모든 사진 처리 완료!")