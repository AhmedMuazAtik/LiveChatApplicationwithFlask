from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase
from flask import request
import os

# Creating the bases of the code 
app = Flask(__name__) #  Create a Flask application object
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app) #  Create a SocketIO object
rooms = {} # Create an empty dictionary named rooms

# Generating a random code of length size 
def generate_unique_code(length):
    # Function to generate a unique room code
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase) # Creating a random code from ASCII uppercase letters
        
        if code not in rooms: # If there is no room with the provided code break 
            break
    
    return code

# The route for home page URL 
@app.route("/", methods=["POST", "GET"])
def home():
    print("1")
    session.clear() # Clears session data

    if request.method == "POST": # If the request method is POST retrieve the values submitted
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name: # If the "name" field is empty, display an error message
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        if join is not False and not code: # If the "join" field has a value and the "code" field is empty , display an error message
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        if create is not False: # If the "create" field has a value
            room = generate_unique_code(4) # Generate random 4 letter code
            rooms[room] = {"members": 0, "messages": []} # If the "create" field is not False, a new room is created with the generated code as the identifier.
        elif code not in rooms: # If the "code" value does not exist in the "rooms" dictionary, display an error message
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        
        # The session data is updated with the "room" and "name" values.
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room")) # The user is redirected to the "room" route to show the chat room page

    return render_template("home.html")

# The route for chat room page URL 
@app.route("/room")
def room():
    print("2")

    room = session.get("room") # Retrieves the value of the "room" from the session
    
    # If the "room" value is None or if the "name" value is not set in the session
    # or if the "room" value is not present in the "rooms" dictionary the function redirects the user to the "home"
    if room is None or session.get("name") is None or room not in rooms: 
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")

# Prints the received data to the console surrounded by newlines ("\n") for better readability.
def message(data):
    print("\n", data, "\n")
    room = session.get("room")
    if room not in rooms: # If the "room" value is not present in the "rooms" dictionary, return
        return
    
    # Retrieves the value of the "room" from the session and creates a dictionary called "content" to represent the message content.
    content = {
        "name": session.get("name"),
        "message": data["data"],
        "type": "text"  # Adding the "type" property with a default value of "text"
    }

    # If the received data has a property called "type" with the value "image", 
    # the "type" property in the "content" dictionary is set to "image".
    if data.get("type") == "image":
        content["type"] = "image"

    # The "content" dictionary is sent to the specified chat room
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

# Handles the "connect" event.
@socketio.on("connect")
def connect(auth):
    print("4")
    # Retrieves the value of the "room" and "name" from the session. 
    room = session.get("room")
    name = session.get("name")
    if not room or not name: # If either the "room" or "name" values are not set in the session, return
        return
    
    
    # If the "room" value is not present in the "rooms" dictionary,
    #the client is removed from the current room by calling leave_room(room),then return
    if room not in rooms:
       
        leave_room(room)
        return
    
    # The client is added to the specified chat room by calling join_room(room).
    join_room(room)
    
    # A message is sent to the specified room using the send function to notify other clients that a new member has joined.
    send({"name": name, "message": "has entered the room"}, to=room) 
    rooms[room]["members"] += 1 # Adds one to the number of members in a room
    print(f"{name} joined room {room}")

# Handles the "disconnect" event.
@socketio.on("disconnect")
def disconnect():
    print("5")
    # Retrieves the value of the "room" and "name" from the session.
    room = session.get("room")
    name = session.get("name")
    leave_room(room) # The client is removed from the current room by calling leave_room(room)

    if room in rooms: # If the "room" value is present in the "rooms" dictionary
        rooms[room]["members"] -= 1 # The number of members in the room is reduced by one
        if rooms[room]["members"] <= 0: # If the member count in the room becomes less than or equal to 0, the room is deleted 
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room) # A message is sent to the specified chat room to notify other chatters
    print(f"{name} has left the room {room}")

# The file route
@app.route("/file", methods=["GET", "POST"])
def file():
    print("6")
    room = session.get("room") # Retrieves the value of the "room" from the session
    if room is None or session.get("name") is None or room not in rooms: # If the the values are not set return to home page
        return redirect(url_for("home"))

    # If the request method is POST 
    if request.method == "POST" and "file" in request.files:
        file = request.files["file"] # The file object is retrieved from the "file" field in the request files.
        content = { # A dictionary called "content" is created to represent the message content.
            "name": session.get("name"),
            "message": file.read().decode("utf-8") # The content of the file, read and decoded as UTF-8 text.
        }
        send(content, to=room) # The "content" dictionary is sent to the specified room using the send function,
        rooms[room]["messages"].append(content)

    return render_template("file.html", code=room, files=rooms[room]["messages"])
   
if __name__ == "__main__":
    socketio.run(app, debug=True) # Starts the Socket.IO server and runs the Flask application.
