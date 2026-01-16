from flask import Flask, redirect, render_template, request, url_for, flash
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
    db_write("INSERT INTO costumes (user_id, costume_name, costume_size) VALUES (%s, %s, %s)", (current_user.id, costume_name, costume_size))

    c=db_read("SELECT COUNT(*) AS count FROM roles WHERE role_name=%s", (costume_name,))
    c = c[0]['count'] # extract the integer
    if c >= 1:
        db_write(
            """UPDATE costumes
            SET role_id = (SELECT id FROM roles WHERE role_name = %s AND user_id = %s)
            WHERE costume_name = %s 
            AND role_id IS NULL""",
            (costume_name, current_user.id, costume_name,)
        )
    return redirect(url_for("costumes"))

@app.route("/rollen", methods=["GET", "POST"])
@login_required
def roles():
    # GET
    if request.method == "GET":
        roles = db_read("SELECT id, role_name FROM roles WHERE user_id=%s ORDER BY role_name", (current_user.id,))
        return render_template("roles.html", roles=roles)
    # POST
    role_name = request.form["role_name"]
    existing = db_read("SELECT id FROM roles WHERE role_name=%s AND user_id=%s", (role_name, current_user.id))
    if existing:
        flash(f"Die Rolle '{role_name}' existiert bereits!")
    else:
        db_write("INSERT INTO roles (user_id, role_name) VALUES (%s, %s)", (current_user.id, role_name, ))
    return redirect(url_for("roles"))

@app.route("/schauspielende", methods=["GET", "POST"])
@login_required
def actors():
    # GET
    if request.method == "GET":
        actors = db_read("SELECT a.id, a.actor_fname, a.actor_lname, a.actor_email , a.actor_size, r.role_name FROM actors a LEFT JOIN roles r ON a.role_id = r.id WHERE a.user_id=%s AND r.user_id=%s ORDER BY actor_fname", (current_user.id, current_user.id))
        roles = db_read("SELECT id, role_name FROM roles WHERE user_id=%s ORDER BY role_name", (current_user.id, ))
        return render_template("actors.html", actors=actors, roles=roles)
    # POST
    actor_fname = request.form["actor_fname"]
    actor_lname = request.form["actor_lname"]
    actor_email = request.form["actor_email"]
    actor_size = request.form["actor_size"]
    role_id = request.form["role_id"]

    role_id = request.form.get("role_id")
    if not role_id or role_id == "":
        role_id = None

    db_write("INSERT INTO actors (user_id, actor_fname, actor_lname, actor_email, actor_size, role_id) VALUES (%s, %s, %s, %s, %s, %s)", (current_user.id, actor_fname, actor_lname, actor_email, actor_size, role_id))
    return redirect(url_for("actors"))



@app.route("/szenen", methods=["GET", "POST"])
@login_required
def scenes():
    # GET
    if request.method == "GET":
        query = """
            SELECT s.id, s.scene_name, GROUP_CONCAT(r.role_name SEPARATOR ', ') as roles_list
            FROM scenes s
            LEFT JOIN plays p ON s.id = p.scenes_id
            LEFT JOIN roles r ON p.roles_id = r.id
            WHERE s.user_id = %s
            GROUP BY s.id
            ORDER BY s.scene_name
        """
        scenes = db_read(query, (current_user.id,))
        roles = db_read("SELECT id, role_name FROM roles WHERE user_id=%s ORDER BY role_name", (current_user.id,))

        return render_template("scenes.html", scenes=scenes, roles=roles)
    # POST
    scene_name = request.form["scene_name"]
    selected_role_ids = request.form.getlist("role_ids")

    scene_id = db_write("INSERT INTO scenes (user_id, scene_name) VALUES (%s, %s)", (current_user.id, scene_name, ))

    result = db_read("SELECT id FROM scenes WHERE user_id=%s AND scene_name=%s ORDER BY id DESC LIMIT 1", (current_user.id, scene_name))

    if result:
        actual_scene_id = result[0]['id']
        for role_id in selected_role_ids:
            db_write("INSERT INTO plays (scenes_id, roles_id, user_id) VALUES (%s, %s, %s)", (actual_scene_id, role_id, current_user.id))
    
    return redirect(url_for("scenes"))


@app.route("/ueberblick_rollen", methods=["GET"])
@login_required
def overview_roles():
    # GET
    if request.method == "GET":
        roles = db_read("SELECT DISTINCT roles.role_name, actors.actor_fname, actors.actor_lname, costumes.costume_name, costumes.costume_size FROM roles LEFT JOIN actors ON roles.id = actors.role_id LEFT JOIN costumes ON roles.id = costumes.role_id AND actors.actor_size = costumes.costume_size WHERE roles.user_id=%s ORDER BY role_name", (current_user.id, ))
        return render_template("overview_roles.html", roles=roles)
        
@app.route("/ueberblick_szenen", methods=["GET"])
@login_required
def overview_theatre():
    # GET
   if request.method == "GET":
        scenes = db_read("""
            SELECT 
                scenes.id, 
                scenes.scene_name,
                GROUP_CONCAT(DISTINCT CONCAT(roles.role_name, ' (', IFNULL(actors.actor_fname, 'ROLLE NOCH NICHT BESETZT!'), ' ', IFNULL(actors.actor_lname, ''), ')') SEPARATOR ', ') AS role_actor_pairs
            FROM scenes 
            LEFT JOIN plays ON scenes.id = plays.scenes_id 
            LEFT JOIN roles ON plays.roles_id = roles.id 
            LEFT JOIN actors ON roles.id = actors.role_id 
            WHERE scenes.user_id=%s 
            GROUP BY scenes.id, scenes.scene_name
            ORDER BY scene_name
        """, (current_user.id, ))
        return render_template("overview_theatre.html", scenes=scenes)
#Hier weitere Pfade einfügen!

if __name__ == "__main__":
    app.run()
