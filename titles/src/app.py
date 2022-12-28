import os
import boto3
import json
import logging
import jwt
from datetime import datetime;

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TITLES_TABLE = os.environ.get('TITLES_TABLE', 'titles')
SUB_LAMBDA   = os.environ.get('SUB_LAMBDA', '')
if TITLES_TABLE:
    dynamodb_client = boto3.client('dynamodb')
if SUB_LAMBDA:
    lambda_client = boto3.client('lambda')

def handle(event, context):
    #logger.info("Authorization: %s", headers['Authorization'])
    body = event.get('body')
    headers = event.get('headers')
    logger.info("Headers: %s", headers)

    if body:
        response_body, response_code = request_post(body, headers)
    else:
        response_body, response_code = request_get(body, headers)

    response = {
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'statusCode': response_code,
        'body': json.dumps(response_body)
    }

    logger.info("Response: %s", response)
    return response

def request_get(body, headers):
    response_body = {'error': 'Unprocessable Entity'}
    response_code = 422
    try:
        titles = []
        response = dynamodb_client.scan(
            TableName=TITLES_TABLE
        )
        for item in response['Items']:
            titles.append({
                'title': item['title']['S'],
                'price': item['price']['S'],
                'symbol': item['symbol']['S'],
                'url': item['url']['S'],
                'type': item['type']['S'],
                'date': item['date']['S'],
                'price_target': item['price_target']['S'],
                'event_id': item['event_id']['S'] if 'event_id' in item else ''
            })
        response_body = titles
        response_code = 200
    except Exception as e:
        logger.error("Error: %s", e)
    return response_body, response_code

def request_post(body, headers):
    response_body = {'error': 'Unprocessable Entity'}
    response_code = 422
    try:
        # decodedToken = jwt.decode(headers['Authorization'], algorithms=["RS256"], options={"verify_signature": False})
        if validate_fields(json.loads(body)):
            list_titles = json.loads(body)
            for title in list_titles:
                save_title(title)
            response_body = {'list': 'ok', 'count': list_titles.__len__() } #, 'username': decodedToken["cognito:username"]}
            response_code = 200
    except Exception as e:
        logger.error("Error: %s", e)
    return response_body, response_code

def save_title(title):
    if not os.environ.get('IS_OFFLINE'):
        date_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        response = dynamodb_client.put_item(
            TableName=TITLES_TABLE,
            Item={
                'id': {'S': date_now},
                'site': {'S': title['url']},
                'title': {'S': 'comming soon'},
                'price': {'S': ''},
                'symbol': {'S': ''},
                'url': {'S': title['url']},
                'type': {'S': ''},
                'date': {'S': date_now},
                'price_target': {'S': title['price_target']}
            }
        )
    # response['Item']['id']['S'])
    #if os.environ.get('IS_OFFLINE'):
    #    dynamodb_client = boto3.client(
    #        'dynamodb', region_name='localhost', endpoint_url='http://localhost:8000'
    #   )
    return True

def validate_fields(body_elements):
    if type(body_elements) is not list:
        return False

    list_fields = ['url', 'price_target']

    for elements in body_elements:
        for key in elements:
            if key not in list_fields:
                return False
    return True
