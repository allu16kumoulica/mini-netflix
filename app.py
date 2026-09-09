from flask import Flask, render_template, redirect, url_for, request, session
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "mini-netflix-learning-secret"
)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


# =====================================
# WELCOME PAGE
# =====================================

@app.route("/")
def home():

    # Already logged in
    if "user_id" in session:
        return redirect(url_for("browse"))

    # Not logged in
    return render_template("welcome.html")


# =====================================
# SIGN UP
# =====================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    message = None

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        try:

            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            if auth_response.user:

                auth_user_id = str(auth_response.user.id)

                # Check whether profile already exists
                existing = (
                    supabase
                    .table("users")
                    .select("*")
                    .eq("auth_user_id", auth_user_id)
                    .execute()
                )

                if not existing.data:

                    supabase.table("users").insert({
                        "name": name,
                        "email": email,
                        "auth_user_id": auth_user_id
                    }).execute()

                return redirect(url_for("login"))

            message = "Could not create account."

        except Exception as e:

            message = str(e)

    return render_template(
        "signup.html",
        message=message
    )


# =====================================
# LOGIN
# =====================================

@app.route("/login", methods=["GET", "POST"])
def login():

    message = None

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        try:

            auth_response = (
                supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
            )

            if auth_response.user and auth_response.session:

                auth_user_id = str(auth_response.user.id)

                user_response = (
                    supabase
                    .table("users")
                    .select("*")
                    .eq("auth_user_id", auth_user_id)
                    .execute()
                )

                if user_response.data:

                    user = user_response.data[0]

                    session["user_id"] = user["user_id"]
                    session["auth_user_id"] = auth_user_id
                    session["email"] = email
                    session["name"] = user["name"]

                    return redirect(url_for("browse"))

                else:

                    message = "User profile was not found."

            else:

                message = "Login failed."

        except Exception as e:

            message = str(e)

    return render_template(
        "login.html",
        message=message
    )


# =====================================
# LOGOUT
# =====================================

@app.route("/logout")
def logout():

    try:
        supabase.auth.sign_out()
    except:
        pass

    session.clear()

    return redirect(url_for("home"))


# =====================================
# MOVIE BROWSE PAGE
# =====================================

@app.route("/browse")
def browse():

    if "user_id" not in session:
        return redirect(url_for("login"))

    response = (
        supabase
        .table("movies")
        .select("*")
        .execute()
    )

    movies = response.data

    return render_template(
        "index.html",
        movies=movies
    )


# =====================================
# ADD MOVIE TO MY LIST
# =====================================

@app.route("/add/<int:movie_id>", methods=["POST"])
def add_to_list(movie_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:

        existing = (
            supabase
            .table("my_list")
            .select("*")
            .eq("user_id", session["user_id"])
            .eq("movie_id", movie_id)
            .execute()
        )

        if not existing.data:

            supabase.table("my_list").insert({
                "user_id": session["user_id"],
                "movie_id": movie_id
            }).execute()

    except Exception as e:

        return f"Error adding movie: {e}"

    return redirect(url_for("browse"))


# =====================================
# MY LIST PAGE
# =====================================

@app.route("/my-list")
def my_list():

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:

        response = (
            supabase
            .table("my_list")
            .select(
                "movie_id, movies(movie_id,title,genre,year,video_url)"
            )
            .eq("user_id", session["user_id"])
            .execute()
        )

        return render_template(
            "my_list.html",
            items=response.data
        )

    except Exception as e:

        return f"Error loading My List: {e}"


# =====================================
# REMOVE FROM MY LIST
# =====================================

@app.route("/remove/<int:movie_id>", methods=["POST"])
def remove_from_list(movie_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:

        (
            supabase
            .table("my_list")
            .delete()
            .eq("user_id", session["user_id"])
            .eq("movie_id", movie_id)
            .execute()
        )

    except Exception as e:

        return f"Error removing movie: {e}"

    return redirect(url_for("my_list"))


# =====================================
# WATCH MOVIE
# =====================================

@app.route("/watch/<int:movie_id>")
def watch_movie(movie_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:

        response = (
            supabase
            .table("movies")
            .select("*")
            .eq("movie_id", movie_id)
            .single()
            .execute()
        )

        movie = response.data

        # Save watch history
        supabase.table("watch_history").insert({
            "user_id": session["user_id"],
            "movie_id": movie_id
        }).execute()

        return render_template(
            "watch.html",
            movie=movie
        )

    except Exception as e:

        return f"Error loading movie: {e}"



# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    try:
        supabase.auth.sign_out()
    except:
        pass

    session.clear()

    return redirect(url_for("home"))


# =========================
# ADD TO MY LIST
# =========================

@app.route("/add/<int:movie_id>", methods=["POST"])
def add_to_list(movie_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:

        existing = (
            supabase
            .table("my_list")
            .select("*")
            .eq("user_id", session["user_id"])
            .eq("movie_id", movie_id)
            .execute()
        )

        if not existing.data:

            supabase.table("my_list").insert({
                "user_id": session["user_id"],
                "movie_id": movie_id
            }).execute()

    except Exception as e:
        return f"Error: {e}"

    return redirect(url_for("home"))


# =========================
# MY LIST PAGE
# =========================

@app.route("/my-list")
def my_list():

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:

        response = (
            supabase
            .table("my_list")
            .select(
                "movie_id, movies(title, genre, year, video_url)"
            )
            .eq("user_id", session["user_id"])
            .execute()
        )

        return render_template(
            "my_list.html",
            items=response.data
        )

    except Exception as e:
        return f"Error: {e}"


# =========================
# REMOVE FROM MY LIST
# =========================

@app.route("/remove/<int:movie_id>", methods=["POST"])
def remove_from_list(movie_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:

        (
            supabase
            .table("my_list")
            .delete()
            .eq("user_id", session["user_id"])
            .eq("movie_id", movie_id)
            .execute()
        )

    except Exception as e:
        return f"Error: {e}"

    return redirect(url_for("my_list"))


# =========================
# WATCH MOVIE
# =========================

@app.route("/watch/<int:movie_id>")
def watch_movie(movie_id):

    try:

        movie_response = (
            supabase
            .table("movies")
            .select("*")
            .eq("movie_id", movie_id)
            .single()
            .execute()
        )

        movie = movie_response.data

        # Only save watch history if user is logged in
        if "user_id" in session:

            supabase.table("watch_history").insert({
                "user_id": session["user_id"],
                "movie_id": movie_id
            }).execute()

        return render_template(
            "watch.html",
            movie=movie
        )

    except Exception as e:
        return f"Error: {e}"


# =========================
# RUN FLASK
# =========================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )