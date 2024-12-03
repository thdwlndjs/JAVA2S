from google.cloud import vision
import os
import re
import mysql.connector

def vision_api(file_path):
    # 인증 파일 경로 설정 (환경 변수로 설정하는 것이 좋음)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/Administrator/Downloads/elite-academy-394705-26c336aaa8d4.json"

    # 클라이언트 생성
    client = vision.ImageAnnotatorClient()

    # 이미지 파일 열기
    with open(file_path, "rb") as image_file:
        content = image_file.read()

    # 이미지 객체 생성
    image = vision.Image(content=content)

    # 텍스트 감지 요청
    response = client.text_detection(image=image)

    # 제목을 저장할 리스트
    titles = []
    tags = []

    # 감지된 텍스트가 없을 경우 처리
    if not response.text_annotations:
        print("No text found.")
    else:
        detected_text = response.text_annotations[0].description

        # 1. 첫 번째 텍스트(공백까지)를 추출
        first_word = detected_text.split()[0]

        # 2. 해시태그를 추출하여 제목에 포함
        hashtags = set(re.findall(r'#[\w]+', detected_text))  # 해시태그 중복 제거
        if hashtags:
            print("Detected Hashtags (Titles):")
            for hashtag in hashtags:
                titles.append(hashtag)  # 해시태그를 제목 리스트에 추가
                tags.append(hashtag)    # 해시태그를 tags 리스트에 추가
                print(hashtag)

        # 3. 해시태그가 없으면 첫 번째 단어만 제목으로 사용
        if not hashtags:
            titles.append(first_word)  # 첫 번째 단어를 제목 리스트에 추가
            tags.append(first_word)    # 첫 번째 단어를 tags 리스트에 추가
            print("Title based on first word: ", first_word)

    # 리스트에 저장된 제목 출력
    print("\nFinal Titles List:")
    print(titles)

    # 데이터베이스 연결 (MySQL)
    db_connection = mysql.connector.connect(
        host="localhost",
        user="your_username",      # MySQL 사용자 이름
        password="your_password",  # MySQL 비밀번호
        database="your_database"   # MySQL 데이터베이스 이름
    )

    cursor = db_connection.cursor()

    # 콘텐츠 테이블 생성
    create_contents_table = """
    CREATE TABLE IF NOT EXISTS contents (
        id INT AUTO_INCREMENT PRIMARY KEY,   -- 콘텐츠 고유 ID
        place_name VARCHAR(255) NOT NULL,     -- 장소명
        file_name VARCHAR(255) NOT NULL,      -- 파일명
        tags TEXT,                            -- 태그 (여러 개의 태그 저장 가능)
        UNIQUE(place_name, file_name)         -- 장소명과 파일명에 대한 중복 방지
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """

    # 테이블 생성 쿼리 실행
    cursor.execute(create_contents_table)

    # 1. photo_tag 테이블에서 파일명 가져오기
    cursor.execute("SELECT file_name FROM photo_tag WHERE file_name = %s", (file_path.split("/")[-1],))
    result = cursor.fetchone()

    if result:
        file_name = result[0]
    else:
        file_name = file_path.split("/")[-1]

    # 2. 파일명 길이가 짧을 경우 장소명에 맞춰서 중복으로 삽입
    place_name = ", ".join(titles)  # 제목 리스트를 쉼표로 구분하여 장소명으로 사용

    if len(file_name) < len(place_name):
        print(f"File name '{file_name}' is shorter than place name '{place_name}'. Duplicating the entry.")
        file_name = place_name  # 파일명을 장소명에 맞게 중복 삽입

    # 3. 태그는 쉼표로 구분하여 하나의 문자열로 저장
    tags_string = ", ".join(tags)

    # 4. 데이터 삽입
    insert_query = """
    INSERT INTO contents (place_name, file_name, tags)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE tags = VALUES(tags);
    """
    cursor.execute(insert_query, (place_name, file_name, tags_string))

    # 변경사항 커밋
    db_connection.commit()

    # 연결 종료
    cursor.close()
    db_connection.close()

    # 오류 처리
    if response.error.message:
        raise Exception(f'{response.error.message}\nFor more info on error messages, check: https://cloud.google.com/apis/design/errors')

# 함수 호출 예시
vision_api("C:/Users/Administrator/readmeifucan/358151973_576270338050817_348653891790442800_n.jpg")
