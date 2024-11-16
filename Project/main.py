from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import random
import string
from datetime import datetime
from werkzeug.utils import secure_filename 
import mysql.connector

app = Flask(__name__,template_folder="templates")

# Secret key for session management (you need to set this for session to work)
app.secret_key = 'your_secret_key_here'

# Database connection function
def create_connection():
    """Establish a connection to the database."""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",       # Replace with your database username
            password="system", # Replace with your database password
            database="housing_rental"  # Replace with your database name
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Route to handle Index page
@app.route('/')
def index():
    return render_template('index.html')

# About Route
@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['Password']

        # Establish database connection
        connection = create_connection()
        if connection is None:
            flash("Database connection failed", "error")
            return redirect(url_for('login'))

        cursor = connection.cursor()

        # SQL Query to get the user with the given email
        cursor.execute("SELECT password FROM user WHERE email_id = %s", (email,))
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        if result:
            stored_password = result[0]  # The password from the database

            # Compare the input password with the stored password
            if password == stored_password:
                session['message'] = "Login Successfully"
                flash("Login Successfully", "success")
                return redirect(url_for('main'))  # Redirect to main page after successful login
            else:
                flash("Invalid password", "error")
                return redirect(url_for('login'))  # Redirect back to login page
        else:
            flash("No user found with that email", "error")
            return redirect(url_for('login'))  # Redirect back to login page


    return render_template('login.html')

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        role = request.form['role']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template('register.html')

        # Establish database connection
        connection = create_connection()
        cursor = connection.cursor()

        # Insert the user into the database
        query = "INSERT INTO user (name, email_id, phone_no, role, password, confirm_password) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (name, email, phone, role, password, confirm_password)

        try:
            cursor.execute(query, values)
            connection.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))  # Redirect to login page after successful registration
        except mysql.connector.Error as err:
            flash(f"Error: {err}", "error")
            return render_template('register.html')
        finally:
            cursor.close()
            connection.close()

    return render_template('register.html')

# Rent Route
@app.route('/rent')
def rent():
    return render_template('rent.html')

# PG Route
@app.route('/pg')
def pg():
    return render_template('pg.html')  # Make sure this exists

# Property Listings Route
@app.route('/property-listings')
def property_listings():
    # Get query parameters from the URL (city, area)
    city = request.args.get('city')
    area = request.args.get('area')

    # Initialize the SQL query
    sql = "SELECT property_id, title, price, location FROM property WHERE 1"
    params = []
    
    if city:
        sql += " AND location LIKE %s"
        params.append(f"%{city}%")
    if area:
        sql += " AND location LIKE %s"
        params.append(f"%{area}%")

    try:
        # Execute the query
        conn = create_connection()  # Assuming this returns a MySQL connection object
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        properties = cursor.fetchall()
        cursor.close()
        conn.close()

    except create_connection.Error as e:
        # Handle database connection or query errors here
        print(f"Database error: {e}")
        properties = []

    # Render the template with properties
    return render_template('property_listings.html', properties=properties)

# Property Details Route
@app.route('/property-details/<int:property_id>')
def property_details(property_id):
    # Fetch property details based on the ID
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM property WHERE property_id = %s', (property_id,))
    property = cursor.fetchone()
    cursor.close()
    conn.close()

    if property is None:
        return 'Property not found!', 404

    # Check if user is logged in
    user_id = session.get('user_id', None)
    return render_template('property_details.html', property=property, user_id=user_id)

# Add Property Route
@app.route('/add-property', methods=['GET', 'POST'])
def add_property():
    if request.method == 'POST':
        # Get form data
        property_id = request.form['property_id']
        name = request.form['name']
        title = request.form['title']
        description = request.form['description']
        property_type = request.form['property_type']
        location = request.form['location']
        price = request.form['price']
        size = request.form['size']
        furnished_status = request.form['furnished_status']
        availability_status = request.form['availability_status']
        contact_info = request.form['contact_info']
        pets_allowed = request.form['pets_allowed']
        lease_terms = request.form['lease_terms']
    
        # Insert data into the database
        conn = create_connection()
        cursor = conn.cursor()

        sql = '''INSERT INTO property (property_id,owner_name, title, description, property_type, location, price, 
                                       size, furnished_status, availability_status, contact_info, pets_allowed, 
                                       lease_terms) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        values = (property_id,name, title, description, property_type, location, price, size, furnished_status, 
                  availability_status, contact_info, pets_allowed, lease_terms)

        try:
            cursor.execute(sql, values)
            conn.commit()
            flash('Property submitted successfully!')
            return redirect(url_for('main'))
        except mysql.connector.Error as err:
            flash(f"Error: {err}", "error")
            conn.rollback()
        
        finally:
            cursor.close()
            conn.close()

    return render_template('add_property.html')

# Route to view all properties (for testing)
@app.route('/properties')
def view_property():
    # Connect to the database
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    # Query to fetch all properties from the database
    cursor.execute("SELECT * FROM property")
    properties = cursor.fetchall()

    # Close the connection
    cursor.close()
    conn.close()

    return render_template('view_property.html', properties=properties)

@app.route('/update_property/<int:property_id>', methods=['GET', 'POST'])
def update_property(property_id):
    # Create a cursor object to interact with the database
    conn = create_connection()
    cur = conn.cursor(dictionary=True)

    # Fetch the property details from the database
    cur.execute("SELECT * FROM property WHERE property_id = %s", (property_id,))
    property = cur.fetchone()

    if property is None:
        flash("Property not found.", 'error')
        return redirect(url_for('main'))  # Ensure 'main' route exists

    if request.method == 'POST':
        try:
            # Retrieve form data
            name = request.form['name']
            title = request.form['title']
            description = request.form['description']
            property_type = request.form['property_type']
            location = request.form['location']
            price = request.form['price']
            size = request.form['size']
            furnished_status = request.form['furnished_status']

            # Prepare the SQL query for updating the property
            update_query = """
                UPDATE property 
                SET owner_name=%s, title=%s, description=%s, property_type=%s, location=%s, 
                    price=%s, size=%s, furnished_status=%s 
                WHERE property_id=%s
            """
            cur.execute(update_query, (name, title, description, property_type, location, 
                                       price, size, furnished_status, property_id))

            # Commit the changes
            conn.commit()

            flash("Property updated successfully!", 'success')

            # Redirect to the view property page (ensure the route 'view_property' is valid)
            return redirect(url_for('view_property', property_id=property_id))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", 'error')
            conn.rollback()  # Rollback the transaction on error

        finally:
            # Close the cursor and connection
            cur.close()
            conn.close()

    # If the request method is GET, render the form with current property data
    return render_template('update_property.html', property=property)

@app.route('/payment/<int:property_id>', methods=['GET', 'POST'])
def payment(property_id):

    if request.method == 'POST':
        # Get payment method
        payment_method = request.form['payment_method']

        # Declare variables for form data
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry')
        cvv = request.form.get('cvv')
        bank_name = request.form.get('bank_name')
        account_number = request.form.get('account_number')
        ifsc_code = request.form.get('ifsc_code')
        upi_id = request.form.get('upi_id')

        # Payment method-specific logic
        if payment_method == 'card':

            try:
                conn = create_connection()
                cursor = conn.cursor()

                query = """
                    INSERT INTO payment (property_id, payment_method, card_number, expiry_date, cvv, payment_status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = (property_id, payment_method, card_number, expiry_date, cvv, 'pending')
                cursor.execute(query, params)
                conn.commit()

                flash('Payment initiated successfully. Your payment is pending.', 'success')
                cursor.close()
                conn.close()

                return redirect(url_for('main', payment_id=cursor.lastrowid))

            except mysql.connector.Error as err:
                flash(f"Error processing payment: {err}", 'error')
                return redirect(url_for('payment', property_id=property_id))

        elif payment_method == 'net_banking':

            # Process net banking payment
            try:
                conn = create_connection()
                cursor = conn.cursor()

                query = """
                    INSERT INTO payment (property_id, payment_method, bank_name, account_number, ifsc_code, payment_status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = (property_id, payment_method, bank_name, account_number, ifsc_code, 'pending')
                cursor.execute(query, params)
                conn.commit()

                flash('Payment initiated successfully. Your payment is pending.', 'success')
                cursor.close()
                conn.close()

                return redirect(url_for('main', payment_id=cursor.lastrowid))

            except mysql.connector.Error as err:
                flash(f"Error processing payment: {err}", 'error')
                return redirect(url_for('payment', property_id=property_id))

        elif payment_method == 'upi':
    
            # Process UPI payment
            try:
                conn = create_connection()
                cursor = conn.cursor()

                query = """
                    INSERT INTO payment (property_id, payment_method, upi_id, payment_status)
                    VALUES (%s, %s, %s, %s)
                """
                params = (property_id, payment_method, upi_id, 'pending')
                cursor.execute(query, params)
                conn.commit()

                flash('Payment initiated successfully. Your payment is pending.', 'success')
                cursor.close()
                conn.close()

                return redirect(url_for('main', payment_id=cursor.lastrowid))

            except mysql.connector.Error as err:
                flash(f"Error processing payment: {err}", 'error')
                return redirect(url_for('payment', property_id=property_id))

        else:
            flash('Invalid payment method selected.', 'error')
            return redirect(url_for('payment', property_id=property_id))

    # Render payment form for GET request
    return render_template('payment.html', property_id=property_id)

if __name__ == '__main__':
    app.run(debug=True)
