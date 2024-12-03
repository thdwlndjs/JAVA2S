from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

@app.route("/api/recommend", methods=["POST"])
def recommend_photos():
    user_id = request.headers.get("User-ID")

    # 사용자 선호도 불러오기
    cursor.execute("SELECT tag, score FROM Preferences WHERE user_id = %s", (user_id,))
    preferences = cursor.fetchall()
    user_preferences = {tag: score for tag, score in preferences}

    # 태그 벡터화
    cursor.execute("SELECT id, tags FROM Photos")
    photos = cursor.fetchall()
    all_tags = list(set(tag for photo in photos for tag in photo[1].split(",")))
    tag_to_index = {tag: i for i, tag in enumerate(all_tags)}

    def vectorize_tags(tags, preferences):
        vector = np.zeros(len(all_tags))
        for tag in tags:
            if tag in preferences:
                vector[tag_to_index[tag]] = preferences[tag]
        return vector

    user_vector = vectorize_tags(all_tags, user_preferences)
    photo_vectors = [vectorize_tags(photo[1].split(","), user_preferences) for photo in photos]

    similarities = cosine_similarity([user_vector], photo_vectors)[0]
    recommended_photos = [
        {"id": photos[i][0], "tags": photos[i][1]} for i in np.argsort(similarities)[::-1] if similarities[i] > 0
    ]
    return jsonify(recommended_photos)
