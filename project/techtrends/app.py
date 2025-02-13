import sqlite3
import logging
from flask import (
    Flask,
    json,
    render_template,
    request,
    url_for,
    redirect,
    flash,
)

logger = logging.getLogger('techtrends_logger')

# Function to get a database connection.
def get_db_connection():
    """This function connects to database with the name database.db."""
    app.config["TOTAL_DB_CONNECTIONS"] += 1
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    connection.close()
    return post


# Define the Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = "your secret key"
app.config["TOTAL_DB_CONNECTIONS"] = 0

# Define the main route of the web application
@app.route("/")
def index():
    connection = get_db_connection()
    posts = connection.execute("SELECT * FROM posts").fetchall()
    connection.close()
    return render_template("index.html", posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route("/<int:post_id>")
def post(post_id):
    post = get_post(post_id)
    if post is None:
        logger.info("Article not found.")
        return render_template("404.html"), 404
    else:
        logger.info(f'"Article {post[2]}" retrieved!')
        return render_template("post.html", post=post)


# Define the About Us page
@app.route("/about")
def about():
    logger.info(f'"About Us" retrieved!')
    return render_template("about.html")


# Define the post creation functionality
@app.route("/create", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        if not title:
            flash("Title is required!")
        else:
            connection = get_db_connection()
            connection.execute(
                "INSERT INTO posts (title, content) VALUES (?, ?)", (title, content)
            )
            connection.commit()
            connection.close()
            logger.info(f'"{title}" article has been created!')
            return redirect(url_for("index"))

    return render_template("create.html")


@app.route("/healthz")
def healthz():
    try:
        connection = get_db_connection()
        connection.execute("SELECT * FROM posts LIMIT 1;")
    except Exception as e:
        logger.error(e)
        response = app.response_class(
            response=json.dumps({"result": "ERROR - unhealthy"}),
            status=500,
            mimetype="application/json",
        )
        return response

    response = app.response_class(
        response=json.dumps({"result": "OK - healthy"}),
        status=200,
        mimetype="application/json",
    )
    return response


@app.route("/metrics")
def metrics():
    connection = get_db_connection()
    posts = connection.execute("SELECT COUNT(id) FROM posts").fetchone()
    response = app.response_class(
        response=json.dumps(
            {
                "db_connection_count": app.config["TOTAL_DB_CONNECTIONS"],
                "post_count": posts[0],
            }
        ),
        status=200,
        mimetype="application/json",
    )
    return response


# start the application on port 3111
if __name__ == "__main__":
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.INFO)

    stderr_handler = logging.FileHandler(filename='errors.log')
    stderr_handler.setLevel(logging.ERROR)

    handlers = [stderr_handler, stdout_handler]

    format_output = "%(asctime)s %(message)s"

    logging.basicConfig(format=format_output, level=logging.DEBUG, handlers=handlers)

    app.run(host="0.0.0.0", port="3111")
