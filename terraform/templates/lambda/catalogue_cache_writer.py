import json
import json
import urllib.parse
import urllib.request
import os
import boto3

def upload_dict_to_s3(data, object_key):
    s3 = boto3.client("s3")

    body = json.dumps(data).encode("utf-8")

    s3.put_object(
        Bucket=os.environ["CACHE_BUCKET"],
        Key=object_key,
        Body=body,
        ContentType="application/json",
    )


def json_from_request(request):
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode("utf-8")
        return json.loads(response_body)

def get_oauth2_token(token_url, client_id, client_secret):
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    encoded_data = urllib.parse.urlencode(data).encode("utf-8")

    request = urllib.request.Request(
        token_url,
        data=encoded_data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        method="POST",
    )
    return json_from_request(request)



def lambda_handler(event, context):
    for record in event['Records']:
        update = json.loads(record['body'])
    print(event)
    token_response = get_oauth2_token(
        token_url="https://metadata-store.auth.eu-west-2.amazoncognito.com/oauth2/token",
        client_id=os.environ["CLIENT_ID"],
        client_secret=os.environ["CLIENT_SECRET"]
    )

    access_token = token_response.get("access_token")
    record_id = update['record_id']
    request = urllib.request.Request(
        f"{os.environ["API_HOST"]}/api/records/{record_id}",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        method="GET",
    )
    upload_dict_to_s3(json_from_request(request), record_id)
    return {}
