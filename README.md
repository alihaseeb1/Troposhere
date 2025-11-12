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

To test locally you need a token:
1. type localhost:8000/auth in the browser
2. copy the token
3. Use this in HTTP Authorization header with type bearer (can also use the likes of postman)

To run the the api locally with docker and s3 bucket online
1. fix the .env file (with the values provided)
2. run docker build -t fastapi-app .
3. docker run -d --name fastapi-container --env-file .env -p 8000:80 fastapi-app
4. make sure to allow access in the rds for your pc
