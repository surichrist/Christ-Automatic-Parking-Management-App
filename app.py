import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(layout='wide')

# Database initialization
def init_db():
    conn = sqlite3.connect('vehicles.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Number TEXT,
            Img TEXT,
            Status TEXT,
            DateTime DATETIME
        )
    ''')
    conn.commit()
    conn.close()


def add_vehicle(number, img, status=None):
    conn = sqlite3.connect('vehicles.db')
    c = conn.cursor()
    now = datetime.now()
    c.execute('''
        INSERT INTO vehicles (Number, Img, Status, DateTime)
        VALUES (?, ?, ?, ?)
    ''', (number, img, status, now))
    conn.commit()
    conn.close()

def get_pending_vehicles():
    conn = sqlite3.connect('vehicles.db')
    c = conn.cursor()
    c.execute('SELECT id, Number, Img FROM vehicles WHERE Status IS NULL')
    rows = c.fetchall()
    conn.close()
    return rows

def update_vehicle_status(number, status):
    conn = sqlite3.connect('vehicles.db')
    c = conn.cursor()
    c.execute('''
        UPDATE vehicles
        SET Status = ?
        WHERE Number = ?
    ''', (status, number))
    conn.commit()
    conn.close()

def get_all_vehicles():
    conn = sqlite3.connect('vehicles.db')
    c = conn.cursor()
    c.execute('SELECT * FROM vehicles')
    rows = c.fetchall()
    conn.close()
    return rows

def search_vehicle(number=None, start_datetime=None, end_datetime=None):
    conn = sqlite3.connect('vehicles.db')
    c = conn.cursor()
    
    query = 'SELECT * FROM vehicles WHERE 1=1'
    params = []
    
    if number:
        query += ' AND Number LIKE ?'
        params.append('%' + number + '%')
    
    if start_datetime:
        query += ' AND DateTime >= ?'
        params.append(start_datetime.strftime("%Y-%m-%d %H:%M:%S"))
    
    if end_datetime:
        query += ' AND DateTime <= ?'
        params.append(end_datetime.strftime("%Y-%m-%d %H:%M:%S"))
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

# Initialize the database
init_db()

# Sidebar for navigation
st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", ["Manage Vehicles", "View Database"])

if selection == "Manage Vehicles":
    st.title("Parking Management System")

    # Retrieve pending vehicles from the database
    pending_vehicles = get_pending_vehicles()

    if pending_vehicles:
        st.write("Vehicles Awaiting Approval")
        print(pending_vehicles)

        # Set the number of columns for the grid layout
        cols = st.columns(2, gap="large")  # Adjust the number of columns as needed
        
        # Display each vehicle in a grid
        for idx, (id, number, img) in enumerate(pending_vehicles):
            with cols[idx % 2]:  # This will create a 2-column grid
                st.image(img, caption=number, use_column_width=True)
                
                action = st.selectbox(
                    f"Action for {number}",
                    ("Select Action", "Approve", "Assign Guest Tag", "Reject"),
                    key=id
                )
                button_id = "button"+str(id)
                if st.button(f"Submit Action for {number}", key=button_id):
                    if action != "Select Action":
                        status = action.lower()  # Convert action to lowercase for status
                        if status == "assign guest tag":
                            status = "Guest"
                        elif status == "reject":
                            status = "Rejected"
                        elif status == "approve":
                            status = "Approved"
                        
                        update_vehicle_status(number, status)  # Update status in database
                        st.success(f"Action '{status}' submitted for {number}")
                        st.experimental_rerun()

        # Add spacing between the images
        st.markdown("<br><br>", unsafe_allow_html=True)
    else:
        st.write("No vehicles awaiting approval.")

elif selection == "View Database":
    st.title("Vehicle Database Viewer")

    # Search functionality
    st.subheader("Search for Vehicles")

    search_term = st.text_input("Search vehicle by number (leave blank for all)")

    # Create columns for date and time inputs
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Start Date", min_value=datetime(2020, 1, 1))
        start_time = st.time_input("Start Time", value=datetime.min.time())

    with col2:
        end_date = st.date_input("End Date", min_value=datetime(2020, 1, 1))
        end_time = st.time_input("End Time", value=datetime.max.time())

    search_button = st.button("Search")

    if search_button:
        if end_date < start_date:
            st.error("End date must be after start date.")
        elif end_time < start_time:
            st.error("End time must be after start time.")
        else:
            # Combine date and time
            start_datetime = datetime.combine(start_date, start_time)
            end_datetime = datetime.combine(end_date, end_time)

            # Fetch and display the filtered vehicle data
            vehicles = search_vehicle(number=search_term, start_datetime=start_datetime, end_datetime=end_datetime)
            
            if vehicles:
                # Create a DataFrame from the retrieved data
                df = pd.DataFrame(vehicles, columns=["id", "Number", "Img", "Status", "DateTime"])
                
                # Display the DataFrame without the image column
                st.write("Vehicle List", df)

            else:
                st.write("No Vehicles found.")