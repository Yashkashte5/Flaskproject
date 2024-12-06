import mysql.connector
from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, session, redirect, url_for, request, flash, render_template
import os

app = Flask(__name__)

app.secret_key = 'your_secret_key_here'


# MySQL connection setup
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="event_booking_system"
    )
@app.route('/')
def index():
    if 'user_id' in session:
        # User is logged in, check their user type
        user_type = session.get('user_type')
        if user_type == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user_type == 'user':
            return redirect(url_for('user_dashboard'))
    # If no user is logged in, redirect to login page
    return redirect(url_for('login'))


# User Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO users (name, email, password, user_type) VALUES (%s, %s, %s, 'user')", 
                           (name, email, password))  # No password hashing
            db.commit()
            flash("Registration successful!", "success")
        except Exception as e:
            db.rollback()  # In case of error, rollback changes
            flash("Error during registration. Please try again.", "danger")
            return render_template('register.html')
        finally:
            cursor.close()
            db.close()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        # Fetch data from the form
        event_name = request.form['name']
        event_date = request.form['date']
        event_description = request.form['description']
        event_location = request.form['location']
        event_time = request.form['time']  # Fetching time from form

        try:
            # Connect to the database
            db = get_db()
            cursor = db.cursor()
            
            # Debug: Print the event data being inserted
            print(f"Inserting event: {event_name}, {event_date}, {event_description}, {event_location}, {event_time}")
            
            # Execute the query (make sure the column names match your table)
            cursor.execute("""
                INSERT INTO events (event_name, event_date, event_time, event_description, location) 
                VALUES (%s, %s, %s, %s, %s)
            """, (event_name, event_date, event_time, event_description, event_location))
            
            # Commit the transaction
            db.commit()
            
            # Debug: Print success message
            print("Event added successfully!")
            
            flash("Event added successfully!", "success")
        except Exception as e:
            # Rollback if there's an error
            if db:
                db.rollback()

            # Debug: Print the full error message
            print(f"Error occurred while adding event: {e}")
            
            # Show the error to the user
            flash(f"Error while adding event: {e}", "danger")
        finally:
            # Ensure cursor and db connection are closed
            if cursor:
                cursor.close()
            if db:
                db.close()

        return redirect(url_for('admin'))

    return render_template('admin.html')

@app.route('/events')
def events():
    db = get_db()
    cursor = db.cursor()
    
    # Fetch all events from the database
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    
    # Close the cursor and database connection
    cursor.close()
    db.close()

    return render_template('events.html', events=events)

@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        event_name = request.form['name']
        event_date = request.form['date']
        event_description = request.form['description']
        event_location = request.form['location']
        event_time = request.form['time']

        try:
            cursor.execute("""
                UPDATE events
                SET event_name = %s, event_date = %s, event_time = %s, event_description = %s, location = %s
                WHERE id = %s
            """, (event_name, event_date, event_time, event_description, event_location, event_id))
            db.commit()
            flash("Event updated successfully!", "success")
        except Exception as e:
            db.rollback()
            flash(f"Error while updating event: {e}", "danger")
        finally:
            cursor.close()
            db.close()

        return redirect(url_for('events'))

    cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template('edit_event.html', event=event)

@app.route('/delete_event/<int:event_id>', methods=['POST', 'DELETE'])
def delete_event(event_id):
    # Check if the user is logged in and is an admin
    if 'user_id' not in session or session.get('user_type') != 'admin':
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Delete event only if it exists
    cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    
    if event:
        # Deleting event from the database
        cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
        db.commit()
        flash("Event deleted successfully", "success")
    else:
        flash("Event not found.", "danger")
    
    # Close the connection
    db.close()
    
    return redirect(url_for('admin_dashboard'))


@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if request.method == 'POST':
        event_name = request.form['name']
        event_date = request.form['date']
        event_description = request.form['description']
        event_location = request.form['location']
        event_time = request.form['time']

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute("""
                INSERT INTO events (event_name, event_date, event_time, event_description, location)
                VALUES (%s, %s, %s, %s, %s)
            """, (event_name, event_date, event_time, event_description, event_location))
            db.commit()
            flash("Event added successfully!", "success")
        except Exception as e:
            db.rollback()
            flash(f"Error while adding event: {e}", "danger")
        finally:
            cursor.close()
            db.close()

        return redirect(url_for('events'))

    return render_template('add_event.html')

from werkzeug.security import check_password_hash  # Import for password hashing check

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("SELECT id, password, user_type FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user and password == user[1]:  # Compare passwords directly
                session['user_id'] = user[0]
                session['user_type'] = user[2]

                flash("Login successful!", "success")
                if user[2] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
            else:
                flash("Invalid email or password.", "danger")
        except Exception as e:
            flash(f"Error while logging in: {e}", "danger")
        finally:
            cursor.close()
            db.close()

    return render_template('login.html')



@app.route('/admin_dashboard')
def admin_dashboard():
    # Check if the user is logged in and is an admin
    if 'user_id' not in session or session.get('user_type') != 'admin':
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('login'))

    # Get the database connection
    db = get_db()
    cursor = db.cursor()

    # Fetch events from the database
    cursor.execute("SELECT * FROM events")  # Adjust this query to match your database schema
    events = cursor.fetchall()

    # Close the database connection
    db.close()  # Corrected from conn.close() to db.close()

    # Render the template with the events data
    return render_template('admin.html', events=events)



@app.route('/user_dashboard')
def user_dashboard():
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('login'))
    
    # Fetch user's name from the database
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    # Access the user's name using tuple indexing
    user_name = user[0] if user else 'User'
    
    # Fetch events as usual
    cursor.execute("SELECT id, event_name, event_date, event_time, location FROM events")
    events = cursor.fetchall()
    
    cursor.close()
    db.close()

    return render_template('user_dashboard.html', user_name=user_name, events=events)




@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


@app.route('/admin_manage_events')
def admin_manage_events():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('login'))

    # Admin-specific functionality here
    return render_template('manage_events.html')


@app.route('/book_event/<int:event_id>', methods=['GET', 'POST'])
def book_event(event_id):
    if 'user_id' not in session:
        flash("You must be logged in to book an event.", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
        event = cursor.fetchone()

        if not event:
            flash("Event not found.", "danger")
            return redirect(url_for('events'))

        # Check if the user has already booked this event
        cursor.execute("SELECT * FROM bookings WHERE user_id = %s AND event_id = %s", (user_id, event_id))
        existing_booking = cursor.fetchone()

        if existing_booking:
            flash("You have already booked this event.", "info")
            return redirect(url_for('events'))

        # Insert the booking into the database
        cursor.execute("""
            INSERT INTO bookings (user_id, event_id)
            VALUES (%s, %s)
        """, (user_id, event_id))
        db.commit()
        flash("Event booked successfully!", "success")

    except Exception as e:
        db.rollback()
        flash(f"Error while booking event: {e}", "danger")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for('events'))

@app.route('/book/<int:event_id>', methods=['GET', 'POST'])
def book(event_id):
    if request.method == 'POST':
        num_seats = request.form['num_seats']  # Getting the number of seats from the form
        user_id = session.get('user_id')  # Getting the current logged-in user ID

        db = get_db()
        cursor = db.cursor()

        try:
            # Insert booking details into the database
            cursor.execute("INSERT INTO bookings (user_id, event_id, num_seats, booking_date) VALUES (%s, %s, %s, NOW())",
                           (user_id, event_id, num_seats))
            db.commit()

            flash("Booking confirmed!", "success")
            return redirect(url_for('my_bookings'))  # Redirect to My Bookings page after successful booking
        except Exception as e:
            flash(f"Error while booking: {e}", "danger")
            db.rollback()
        finally:
            cursor.close()
            db.close()

    # Retrieve event details for the booking page (optional)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    cursor.close()

    return render_template('book.html', event=event)


    # Fetch event details to display on the booking page
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template('book.html', event=event)


@app.route('/mybookings')
def my_bookings():
    if 'user_id' not in session:
        flash("You must log in first.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Connect to the database and fetch the user's bookings along with the number of seats
    db = get_db()
    cursor = db.cursor(dictionary=True)
    query = '''
        SELECT events.event_name, events.event_date, events.event_time, events.location, bookings.booking_date, bookings.num_seats
        FROM bookings
        JOIN events ON bookings.event_id = events.id
        WHERE bookings.user_id = %s
    '''
    cursor.execute(query, (user_id,))
    bookings = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('mybookings.html', bookings=bookings)



if __name__ == '__main__':
    app.run(debug=True)
