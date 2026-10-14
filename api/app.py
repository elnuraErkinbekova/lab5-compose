from flask import Flask, jsonify, request
import psycopg2
import redis
import json
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

DB_CONFIG = {
    "host": app.config["DB_HOST"],
    "port": app.config["DB_PORT"],
    "database": app.config["DB_NAME"],
    "user": app.config["DB_USER"],
    "password": app.config["DB_PASSWORD"]
}

redis_client = redis.Redis(
    host=app.config["REDIS_HOST"],
    port=app.config["REDIS_PORT"],
    decode_responses=True
)

def init_db():
    """Создание таблицы пользователей, если она еще не существует"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization error: {e}")

with app.app_context():
    init_db()

@app.route("/")
def home():
    return jsonify({
        "app": "Lab5 API",
        "status": "running"
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/db-test")
def db_test():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        return jsonify({"status": "success", "database": version})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/cache-test")
def cache_test():
    try:
        redis_client.set("test_key", "test_value", ex=60)
        value = redis_client.get("test_key")
        return jsonify({"status": "success", "redis": "connected", "test_value": value})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    name = data.get("name")
    email = data.get("email")

    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id, name, email;",
            (name, email)
        )
        user_id, user_name, user_email = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        user_data = {"id": user_id, "name": user_name, "email": user_email}
        return jsonify(user_data), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/users", methods=["GET"])
def get_users():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT id, name, email FROM users;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        users = [{"id": row[0], "name": row[1], "email": row[2]} for row in rows]
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user_by_id(user_id):
    cache_key = f"user:{user_id}"

    cached_user = redis_client.get(cache_key)
    if cached_user:
        return jsonify({
            "source": "cache",
            "data": json.loads(cached_user)
        })

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT id, name, email FROM users WHERE id = %s;", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return jsonify({"error": "User not found"}), 404

        user_data = {"id": row[0], "name": row[1], "email": row[2]}

        redis_client.set(cache_key, json.dumps(user_data), ex=60)

        return jsonify({
            "source": "database",
            "data": user_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)