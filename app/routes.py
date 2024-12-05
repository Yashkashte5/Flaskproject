from flask import Blueprint

main = Blueprint('main', __name__)

@main.route('/')
def index():
    from app import mysql  # Import mysql inside the function
    try:
        cur = mysql.connection.cursor()
        cur.execute("SHOW TABLES;")
        tables = cur.fetchall()
        cur.close()
        return {"tables": tables}
    except Exception as e:
        return str(e)
