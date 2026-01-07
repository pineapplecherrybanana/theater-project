from flask import Flask, redirect, render_template, request, url_for
from dotenv import load_dotenv
import os
import git
import hmac
import hashlib
from db import db_read, db_write
from auth import login_manager, authenticate, register_user
from flask_login import login_user, logout_user, login_required, current_user
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Load .env variables
load_dotenv()
W_SECRET = os.getenv("W_SECRET")

# Init flask app
app = Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = "supersecret"

# Init auth
login_manager.init_app(app)
login_manager.login_view = "login"

# DON'T CHANGE
def is_valid_signature(x_hub_signature, data, private_key):
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)

# DON'T CHANGE
@app.post('/update_server')
def webhook():
    x_hub_signature = request.headers.get('X-Hub-Signature')
    if is_valid_signature(x_hub_signature, request.data, W_SECRET):
        repo = git.Repo('./mysite')
        origin = repo.remotes.origin
        origin.pull()
        return 'Updated PythonAnywhere successfully', 200
    return 'Unathorized', 401

# Auth routes
@app.get("/users")
@login_required
def users():
    return "Hallo from users"

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        user = authenticate(
            request.form["username"],
            request.form["password"]
        )

        if user:
            login_user(user)
            return redirect(url_for("index"))

        error = "Email-Adresse oder Passwort ist falsch."

    return render_template(
        "auth.html",
        title="In dein Konto einloggen",
        action=url_for("login"),
        button_label="Einloggen",
        error=error,
        footer_text="Noch kein Konto?",
        footer_link_url=url_for("register"),
        footer_link_label="Registrieren"
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        ok = register_user(username, password)
        if ok:
            return redirect(url_for("login"))

        error = "Email-Adresse existiert bereits."

    return render_template(
        "auth.html",
        title="Neues Konto erstellen",
        action=url_for("register"),
        button_label="Registrieren",
        error=error,
        footer_text="Du hast bereits ein Konto?",
        footer_link_url=url_for("login"),
        footer_link_label="Einloggen"
    )

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))



# App routes
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # GET
    if request.method == "GET":
        todos = db_read("SELECT id, content, due FROM todos WHERE user_id=%s ORDER BY due", (current_user.id,))
        return render_template("main_page.html", todos=todos)

    # POST
    content = request.form["contents"]
    due = request.form["due_at"]
    db_write("INSERT INTO todos (user_id, content, due) VALUES (%s, %s, %s)", (current_user.id, content, due, ))
    return redirect(url_for("index"))

@app.post("/complete")
@login_required
def complete():
    todo_id = request.form.get("id")
    db_write("DELETE FROM todos WHERE user_id=%s AND id=%s", (current_user.id, todo_id,))
    return redirect(url_for("index"))


@app.route("/kostueme", methods=["GET", "POST"])
@login_required
def costumes():
    # GET
    if request.method == "GET":
        costumes = db_read("SELECT id, costume_name, costume_size FROM costumes WHERE user_id=%s ORDER BY costume_name", (current_user.id,))
        return render_template("costumes.html", costumes=costumes)
    # POST
    costume_name = request.form["costume_name"]
    costume_size = request.form["costume_size"]
    db_write("INSERT INTO costumes (user_id, costume_name, costume_size) VALUES (%s, %s, %s)", (current_user.id, costume_name, costume_size, ))
    return redirect(url_for("costumes"))

    c=db_read("SELECT COUNT(*) FROM roles WHERE role_name=%s", (current_user.id,))
    if c >= 1:
        
        for i in range (0, c):
            db_write("INSERT INTO costumes (role_id) VALUES (%s)", (role_id, ))

@app.route("/rollen", methods=["GET", "POST"])
@login_required
def roles():
    # GET
    if request.method == "GET":
        roles = db_read("SELECT id, role_name FROM roles WHERE user_id=%s ORDER BY role_name", (current_user.id,))
        return render_template("roles.html", roles=roles)
    # POST
    role_name = request.form["role_name"]
    db_write("INSERT INTO roles (user_id, role_name) VALUES (%s, %s)", (current_user.id, role_name, ))
    return redirect(url_for("roles"))

@app.route("/schauspielende", methods=["GET", "POST"])
@login_required
def actors():
    # GET
    if request.method == "GET":
        actors = db_read("SELECT id, actor_fname, actor_lname, actor_email ,actor_size FROM actors WHERE user_id=%s ORDER BY actor_fname", (current_user.id,))
        return render_template("actors.html", actors=actors)
    # POST
    actor_fname = request.form["actor_fname"]
    actor_lname = request.form["actor_lname"]
    actor_email = request.form["actor_email"]
    actor_size = request.form["actor_size"]
    db_write("INSERT INTO actors (user_id, actor_fname, actor_lname, actor_email, actor_size) VALUES (%s, %s, %s, %s, %s)", (current_user.id, actor_fname, actor_lname, actor_email, actor_size, ))
    return redirect(url_for("actors"))

@app.route("/szenen", methods=["GET", "POST"])
@login_required
def scenes():
    # GET
    if request.method == "GET":
        scenes = db_read("SELECT id, scene_name FROM scenes WHERE user_id=%s ORDER BY scene_name", (current_user.id,))
        return render_template("scenes.html", scenes=scenes)
    # POST
    scene_name = request.form["scene_name"]
    role1 = request.form["role_name1"]
    role2 = request.form["role_name2"]
    role3 = request.form["role_name3"]
    roleslist = [role1, role2, role3]
    db_write("INSERT INTO scenes (user_id, scene_name) VALUES (%s, %s)", (current_user.id, scene_name, ))
    for i in range (0,3):
        db_write("INSERT INTO roles (user_id, role_name) VALUES (%s, %s)", (current_user.id, roleslist[i] ))
    return redirect(url_for("scenes"))


@app.route("/ueberblick_rollen", methods=["GET", "POST"])
@login_required
def overview_roles():
    # GET
    if request.method == "GET":
        costumes = db_read("SELECT id, costume_name, costume_size FROM costumes ORDER BY costume_name")
        return render_template("overview_roles.html", costumes=costumes)
        
#@app.route("/ueberblick_kostueme", methods=["GET", "POST"])
#@login_required
#def costumes():
    # GET
#   if request.method == "GET":
#       costumes = db_read("SELECT id, costume_name, costume_size FROM costumes ORDER BY costume_name")
#       return render_template("costumes.html", costumes=costumes)

#Hier weitere Pfade einfügen!

if __name__ == "__main__":
    app.run()
