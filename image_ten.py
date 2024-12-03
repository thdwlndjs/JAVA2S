import os
import numpy as np
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import mysql.connector
from concurrent.futures import ThreadPoolExecutor
import cv2


class PhotoProcessor:
    def __init__(self, db_config):
        self.model = MobileNetV2(weights="imagenet")  # MobileNetV2 모델 로드
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.db = mysql.connector.connect(**db_config)
        self.cursor = self.db.cursor()
        self.custom_tags = {
            "산": ["mountain", "peak", "ridge"],
            "바다": ["ocean", "sea", "coastline"],
            "도시": ["city", "metropolis", "urban"],
            "카페": ["coffee_shop", "cafe"],
            "공원": ["park", "garden"],
            "식당": ["restaurant", "diner"],
            "건물": ["building", "architecture"],
            "호텔": ["hotel", "resort"],
            "야경": ["skyline", "night_view"],
            "길": ["road", "pathway", "street"],
            "고기": ["meat", "steak", "grill"],
            "해산물": ["seafood", "fish"],
            "디저트": ["dessert", "cake", "pastry"],
            "음료": ["drink", "beverage", "coffee"],
            "따뜻함": ["warmth", "cozy"],
            "모던함": ["modern", "minimalist"],
            "차가움": ["cold", "icy"],
            "조용함": ["quiet", "peaceful"],
            "활기참": ["vibrant", "lively"],
            "로맨틱": ["romantic", "intimate"],
            "어두움": ["dark", "gloomy"],
            "밝음": ["bright", "cheerful"],
        }

    def has_faces(self, img_path):
        """얼굴 검출"""
        img = cv2.imread(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        return len(faces) > 0

    def analyze_image(self, img_path):
        """이미지 분석 및 태그 생성"""
        img = image.load_img(img_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)

        preds = self.model.predict(img_array)
        decoded = decode_predictions(preds, top=10)  # 상위 10개의 예측
        return self.match_custom_tags(decoded)

    def match_custom_tags(self, decoded_preds):
        """예측 결과를 사용자 정의 태그로 매핑"""
        assigned_tags = []
        for pred in decoded_preds[0]:
            for tag, keywords in self.custom_tags.items():
                if pred[1] in keywords:
                    assigned_tags.append(tag)
        return list(set(assigned_tags))  # 중복 제거

    def save_to_db(self, img_path, tags):
        """태그를 데이터베이스에 저장"""
        sql = "INSERT INTO Photos (image_path, tags) VALUES (%s, %s)"
        self.cursor.execute(sql, (img_path, ",".join(tags)))
        self.db.commit()

    def process_photo(self, img_path):
        """사진 처리 및 저장"""
        if self.has_faces(img_path):
            print(f"얼굴 감지됨: {img_path}, 건너뜀.")
            return

        tags = self.analyze_image(img_path)
        self.save_to_db(img_path, tags)
        print(f"분석 완료: {img_path}, 태그: {tags}")

    def process_photos_in_folder(self, folder_path):
        """폴더 내 모든 사진 처리"""
        photos = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith((".jpg", ".png"))]
        with ThreadPoolExecutor(max_workers=4) as executor:  # 병렬 처리
            executor.map(self.process_photo, photos)


if __name__ == "__main__":
    # 데이터베이스 설정
    db_config = {
        "host": "localhost",
        "user": "your_user",
        "password": "your_password",
        "database": "your_database"
    }

    folder_path = "/path/to/photos"  # 사진이 있는 폴더 경로
    processor = PhotoProcessor(db_config)
    processor.process_photos_in_folder(folder_path)
    print("모든 사진 처리 완료!")
