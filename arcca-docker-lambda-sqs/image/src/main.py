import json
import boto3
from db import PostgresDB
import os
from dotenv import load_dotenv

HOST = os.getenv("HOST")
DBNAME = os.getenv("DBNAME")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
PORT = os.getenv("PORT")
AWS_ACCESS_KEY_ID = "AKIAJLXQWQJLQ"
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION_NAME = "us-east-1"
QUEUE_URL = os.getenv("QUEUE_URL")


def handler(event, context):
    message = "Companies added to sqs"
    status = 200
    error = ''
    
    try:
        db = PostgresDB(host=HOST, dbname=DBNAME, user=USER, password=PASSWORD, port=PORT)
        companies = db.get_companies()
        db.close()

        sqs = boto3.client('sqs', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=REGION_NAME)
        for company in companies:
            sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(company[0]))
    except Exception as e:
        message = "Not possible to add companies to sqs."
        status = 500
        error = str(e)

    
    body = {
        "message": message,
        "input": event,
        "error": error
    }

    response = {"statusCode": status, "body": json.dumps(body)}

    return response