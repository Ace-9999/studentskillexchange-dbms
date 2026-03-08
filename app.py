from flask import Flask, render_template, request, jsonify
import mysql.connector
import os

app = Flask(__name__)

# =========================
# DATABASE CONNECTION
# =========================

import os

db = mysql.connector.connect(
    host=os.environ.get("DB_HOST"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    database=os.environ.get("DB_NAME")
)

cursor = db.cursor(dictionary=True)


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# ADD SKILL REQUEST
# =========================

@app.route("/add_skill_request", methods=["POST"])
def add_skill_request():
    try:
        data = request.form

        sql = """
            INSERT INTO Skill_Request
            (student_id, skill_id, desired_level, urgency_level, preferred_mode)
            VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            data["student_id"],
            data["skill_id"],
            data["desired_level"],
            data["urgency_level"],
            data["preferred_mode"]
        )

        cursor.execute(sql, values)
        db.commit()

        return "Skill Request Added Successfully!"

    except Exception as e:
        return f"Error: {str(e)}"


# =========================
# ADD COLLABORATION REQUEST
# =========================

@app.route("/add_collab", methods=["POST"])
def add_collab():
    try:
        data = request.form

        sql = """
            INSERT INTO Collaboration_Request
            (sender_id, receiver_id, offer_id, request_id, request_date)
            VALUES (%s, %s, %s, %s, CURDATE())
        """

        values = (
            data["sender_id"],
            data["receiver_id"],
            data["offer_id"],
            data["request_id"]
        )

        cursor.execute(sql, values)
        db.commit()

        return "Collaboration Request Sent Successfully!"

    except Exception as e:
        return f"Error: {str(e)}"


# =========================
# MATCHING ENGINE
# =========================

@app.route("/match/<int:student_id>")
def match_skills(student_id):
    try:
        sql = """
            SELECT
                so.offer_id,
                s2.student_id,
                s2.name,
                sk.skill_name,
                so.proficiency_level,
                so.hourly_points_value
            FROM Skill_Request sr
            JOIN Skill_Offer so
                ON sr.skill_id = so.skill_id
            JOIN Student s2
                ON so.student_id = s2.student_id
            JOIN Skill sk
                ON sk.skill_id = sr.skill_id
            WHERE sr.student_id = %s
            AND so.student_id != sr.student_id
        """

        cursor.execute(sql, (student_id,))
        result = cursor.fetchall()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})


# =========================
# WALLET
# =========================

@app.route("/wallet/<int:student_id>")
def wallet(student_id):
    try:
        sql = "SELECT points_balance FROM Wallet WHERE student_id = %s"
        cursor.execute(sql, (student_id,))
        result = cursor.fetchone()

        if result:
            return jsonify(result)
        else:
            return jsonify({"points_balance": 0})

    except Exception as e:
        return jsonify({"error": str(e)})


# =========================
# CERTIFICATIONS
# =========================

@app.route("/certifications/<int:student_id>")
def certifications(student_id):
    try:
        sql = """
            SELECT s.skill_name, c.issue_date, c.certification_level
            FROM Skill_Certification c
            JOIN Skill s ON c.skill_id = s.skill_id
            WHERE c.student_id = %s
        """

        cursor.execute(sql, (student_id,))
        result = cursor.fetchall()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})


# =========================
# RUN SERVER
# =========================



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))