from flask import Flask, render_template, request, jsonify
import mysql.connector
import os

app = Flask(__name__)

# =========================
# DATABASE CONNECTION
# =========================

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("MYSQLHOST"),
        port=int(os.environ.get("MYSQLPORT")),
        user=os.environ.get("MYSQLUSER"),
        password=os.environ.get("MYSQLPASSWORD"),
        database=os.environ.get("MYSQLDATABASE")
    )


# =========================
# PAGE ROUTES
# =========================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/add_skill_request_page")
def skill_request_page():
    return render_template("add_skill_request.html")


@app.route("/add_collab_page")
def collab_page():
    return render_template("add_collab.html")


@app.route("/match_page")
def match_page():
    return render_template("match.html")


@app.route("/wallet_page")
def wallet_page():
    return render_template("wallet.html")


@app.route("/certifications_page")
def cert_page():
    return render_template("certifications.html")

@app.route("/bid_page")
def bid_page():
    return render_template("bid.html")

@app.route("/session_page")
def session_page():
    return render_template("session.html")

@app.route("/rating_page")
def rating_page():
    return render_template("rating.html")

@app.route("/schedule_session", methods=["POST"])
def schedule_session():

    db = get_db()
    cursor = db.cursor()

    data = request.form

    sql = """
    INSERT INTO Session
    (collab_id, session_date, duration_hours, session_status)
    VALUES (%s,%s,%s,'Scheduled')
    """

    cursor.execute(sql, (
        data["collab_id"],
        data["date"],
        data["duration"]
    ))

    db.commit()

    cursor.close()
    db.close()

    return "Session scheduled!"

@app.route("/rate_teacher", methods=["POST"])
def rate_teacher():

    db = get_db()
    cursor = db.cursor()

    data = request.form

    sql = """
    INSERT INTO Skill_Rating
    (session_id, reviewer_id, rating, review)
    VALUES (%s,%s,%s,%s)
    """

    cursor.execute(sql, (
        data["session_id"],
        data["reviewer_id"],
        data["rating"],
        data["review"]
    ))

    db.commit()

    cursor.close()
    db.close()

    return "Rating submitted!"

@app.route("/update_progress", methods=["POST"])
def update_progress():

    db = get_db()
    cursor = db.cursor()

    data = request.form

    sql = """
    INSERT INTO Skill_Progress
    (student_id, skill_id, progress_percent, last_updated)
    VALUES (%s,%s,%s,CURDATE())
    """

    cursor.execute(sql, (
        data["student_id"],
        data["skill_id"],
        data["progress"]
    ))

    db.commit()

    cursor.close()
    db.close()

    return "Progress updated!"

@app.route("/place_bid", methods=["POST"])
def place_bid():

    db = get_db()
    cursor = db.cursor()

    data = request.form

    sql = """
    INSERT INTO Skill_Bid
    (request_id, teacher_id, proposed_points, message)
    VALUES (%s,%s,%s,%s)
    """

    cursor.execute(sql, (
        data["request_id"],
        data["teacher_id"],
        data["points"],
        data["message"]
    ))

    db.commit()

    cursor.close()
    db.close()

    return "Bid submitted!"


# =========================
# ADD SKILL REQUEST
# =========================

@app.route("/add_skill_request", methods=["POST"])
def add_skill_request():

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        data = request.form

        sql = """
        INSERT INTO Skill_Request
        (student_id, skill_id, desired_level, urgency_level, preferred_mode)
        VALUES (%s,%s,%s,%s,%s)
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

        cursor.close()
        db.close()

        return "Skill Request Added Successfully!"

    except Exception as e:
        return str(e)


# =========================
# ADD COLLABORATION REQUEST
# =========================

@app.route("/add_collab", methods=["POST"])
def add_collab():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        data = request.form

        sender = data["sender_id"]
        receiver = data["receiver_id"]
        offer_id = data["offer_id"]
        request_id = data["request_id"]

        # Insert collaboration request
        sql = """
        INSERT INTO Collaboration_Request
        (sender_id, receiver_id, offer_id, request_id, request_date)
        VALUES (%s,%s,%s,%s,CURDATE())
        """

        cursor.execute(sql, (sender, receiver, offer_id, request_id))


        # Get cost of the skill (points/hr)
        cost_query = """
        SELECT hourly_points_value
        FROM Skill_Offer
        WHERE offer_id = %s
        """

        cursor.execute(cost_query, (offer_id,))
        result = cursor.fetchone()

        if result:
            cost = result["hourly_points_value"]
        else:
            return "Invalid offer ID"


        # Deduct points from learner
        deduct_query = """
        UPDATE Wallet
        SET points_balance = points_balance - %s
        WHERE student_id = %s
        """

        cursor.execute(deduct_query, (cost, sender))


        # Add points to teacher
        add_query = """
        UPDATE Wallet
        SET points_balance = points_balance + %s
        WHERE student_id = %s
        """

        cursor.execute(add_query, (cost, receiver))


        db.commit()

        cursor.close()
        db.close()

        return "Collaboration Request Sent and Wallet Updated!"

    except Exception as e:
        return str(e)


# =========================
# MATCHING ENGINE
# =========================

@app.route("/match/<int:student_id>")
def match_skills(student_id):

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

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

        cursor.close()
        db.close()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})


# =========================
# WALLET
# =========================

@app.route("/wallet/<int:student_id>")
def wallet(student_id):

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        sql = "SELECT points_balance FROM Wallet WHERE student_id = %s"

        cursor.execute(sql, (student_id,))
        result = cursor.fetchone()

        cursor.close()
        db.close()

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
        db = get_db()
        cursor = db.cursor(dictionary=True)

        sql = """
        SELECT s.skill_name, c.issue_date, c.certification_level
        FROM Skill_Certification c
        JOIN Skill s ON c.skill_id = s.skill_id
        WHERE c.student_id = %s
        """

        cursor.execute(sql, (student_id,))
        result = cursor.fetchall()

        cursor.close()
        db.close()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})


# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))