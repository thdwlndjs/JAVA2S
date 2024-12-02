import mariadb

# 데이터베이스 이름 설정
DATABASE_NAME = 'mydatabase'

# MariaDB에 연결하는 함수
def create_connection(database=None):
    try:
        connection = mariadb.connect(
            host="localhost",        # MariaDB 서버 주소
            user="root",             # MariaDB 사용자 이름
            password="1234",         # MariaDB 비밀번호
            database=database       # 사용할 데이터베이스 이름 (없으면 None)
        )
        print("MariaDB에 성공적으로 연결되었습니다.")
        return connection
    except mariadb.Error as e:
        print(f"MariaDB 연결 오류: {e}")
        return None

# 데이터베이스 생성 함수 (이름을 인자로 받음)
def create_database(db_name):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # 데이터베이스가 존재하지 않으면 생성
            create_db_query = f"""
            CREATE DATABASE IF NOT EXISTS {db_name}
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci;
            """
            cursor.execute(create_db_query)
            print(f"'{db_name}' 데이터베이스가 성공적으로 생성되었습니다.")
        except mariadb.Error as e:
            print(f"데이터베이스 생성 오류: {e}")
        finally:
            cursor.close()
            connection.close()

# 테이블 생성 함수 (테이블 이름을 인자로 받음)
def create_tables(db_name):
    connection = create_connection(db_name)
    if connection:
        try:
            cursor = connection.cursor()
            use_db_query = f"USE {db_name};"
            cursor.execute(use_db_query)

            # Users 테이블 생성 쿼리
            create_users_table = """
            CREATE TABLE IF NOT EXISTS Users (
                id INT AUTO_INCREMENT PRIMARY KEY,    -- 사용자 고유 ID
                username VARCHAR(255) NOT NULL,        -- 사용자 이름
                email VARCHAR(255) NOT NULL,           -- 사용자 이메일
                password_hash VARCHAR(255) NOT NULL,   -- 비밀번호 해시 값
                UNIQUE(email)                         -- 이메일 중복 방지
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """
            cursor.execute(create_users_table)
            
            # contents 테이블 생성 쿼리
            create_users_table = """
            CREATE TABLE IF NOT EXISTS contents (
                id INT AUTO_INCREMENT PRIMARY KEY,   -- 콘텐츠 고유 ID
                place_name VARCHAR(255) NOT NULL,     -- 장소명
                file_name VARCHAR(255) NOT NULL,      -- 파일명
                tags TEXT,                            -- 태그 (여러 개의 태그 저장 가능)
                UNIQUE(place_name, file_name)         -- 장소명과 파일명에 대한 중복 방지
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """
            cursor.execute(create_users_table)

            # Tags 테이블 생성 쿼리
            create_tags_table = """
            CREATE TABLE IF NOT EXISTS Tags (
                id INT AUTO_INCREMENT PRIMARY KEY,     -- 태그 고유 ID
                name VARCHAR(50) NOT NULL,              -- 태그 이름 (예: '산', '바다' 등)
                UNIQUE(name)                            -- 태그 이름 중복 방지
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """
            cursor.execute(create_tags_table)

            # User_Tag_Relationship 테이블 생성 쿼리
            create_user_tag_relationship_table = """
            CREATE TABLE IF NOT EXISTS User_Tag_Relationship (
                user_id INT,                            -- 사용자 ID (Users 테이블 참조)
                tag_id INT,                             -- 태그 ID (Tags 테이블 참조)
                weight FLOAT DEFAULT 0,                 -- 태그에 대한 선호도 (기본값 0)
                PRIMARY KEY (user_id, tag_id),         -- user_id와 tag_id 조합이 유니크하도록 설정
                FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,   -- Users 테이블의 id 참조
                FOREIGN KEY (tag_id) REFERENCES Tags(id) ON DELETE CASCADE     -- Tags 테이블의 id 참조
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """
            cursor.execute(create_user_tag_relationship_table)

            print(f"테이블들이 성공적으로 생성되었습니다.")
        except mariadb.Error as e:
            print(f"테이블 생성 오류: {e}")
        finally:
            cursor.close()
            connection.close()

# 사용자 정보 삽입 함수
def insert_user(db_name, username, email, password_hash):
    connection = create_connection(db_name)
    if connection:
        try:
            cursor = connection.cursor()
            insert_user_query = """
            INSERT INTO Users (username, email, password_hash)
            VALUES (?, ?, ?);
            """
            cursor.execute(insert_user_query, (username, email, password_hash))
            connection.commit()
            print(f"사용자 '{username}'가 성공적으로 추가되었습니다.")
        except mariadb.Error as e:
            print(f"사용자 삽입 오류: {e}")
        finally:
            cursor.close()
            connection.close()

# 태그 정보 삽입 함수
def insert_tag(db_name, tag_name):
    connection = create_connection(db_name)
    if connection:
        try:
            cursor = connection.cursor()
            insert_tag_query = """
            INSERT INTO Tags (name)
            VALUES (?);
            """
            cursor.execute(insert_tag_query, (tag_name,))
            connection.commit()
            print(f"태그 '{tag_name}'가 성공적으로 추가되었습니다.")
        except mariadb.Error as e:
            print(f"태그 삽입 오류: {e}")
        finally:
            cursor.close()
            connection.close()

# User_Tag_Relationship 정보 삽입 함수
def insert_user_tag_relationship(db_name, user_id, tag_id, weight):
    connection = create_connection(db_name)
    if connection:
        try:
            cursor = connection.cursor()
            insert_relationship_query = """
            INSERT INTO User_Tag_Relationship (user_id, tag_id, weight)
            VALUES (?, ?, ?);
            """
            cursor.execute(insert_relationship_query, (user_id, tag_id, weight))
            connection.commit()
            print(f"사용자 '{user_id}'와 태그 '{tag_id}' 간의 관계가 성공적으로 추가되었습니다.")
        except mariadb.Error as e:
            print(f"User_Tag_Relationship 삽입 오류: {e}")
        finally:
            cursor.close()
            connection.close()

# 데이터베이스 생성
create_database(DATABASE_NAME)

# 테이블 생성
create_tables(DATABASE_NAME)

# 사용자 정보 삽입 예제
insert_user(DATABASE_NAME, 'john_doe', 'john.doe@example.com', 'hashed_password')

# 태그 정보 삽입 예제
insert_tag(DATABASE_NAME, '산')
insert_tag(DATABASE_NAME, '바다')

# User_Tag_Relationship 삽입 예제 (사용자 'john_doe'와 '산' 태그에 대한 선호도 5)
insert_user_tag_relationship(DATABASE_NAME, 1, 1, 5.0)
