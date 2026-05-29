import json
import boto3
import os

sqs = boto3.client('sqs')

def lambda_handler(event, context):
    sqs.send_message(
        QueueUrl=os.environ["QUEUE_URL"],
        MessageBody=json.dumps(event),
    )
    return {}
