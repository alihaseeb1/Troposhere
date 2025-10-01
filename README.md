To install the fastapi app:

1. Create a venv on your machine after pulling the code in using "python3 -m venv venv"
2. Then do "pip install requirements.txt"

To setup the database:
1. Run the venv
2. Write "alembic upgrade head" in the vs terminal

To access the documentation:
1. Write "localhost:8000/docs" in the browser
   
To run the server type "fastapi dev app/main.py"
Note: use localhost:8000 instead of the IP address (won't work with the google auth)
