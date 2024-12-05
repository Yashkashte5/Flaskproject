from flask import Flask
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from app.main.routes import main  # Import the main blueprint

app = Flask(__name__)

# Setup MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'your_mysql_user'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'your_database_name'

# Setup Bcrypt for password hashing
bcrypt = Bcrypt(app)

# Initialize MySQL
mysql = MySQL(app)

# Register blueprint
app.register_blueprint(main)

if __name__ == '__main__':
    app.run(debug=True)
