import os
import json
import boto3
import hmac, hashlib, base64
from botocore.exceptions import ClientError

cognito_client = boto3.client('cognito-idp')

USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
CLIENT_ID = os.getenv('COGNITO_CLIENT_ID')
CLIENT_SECRET = os.getenv('COGNITO_CLIENT_SECRET')


def get_secret_hash(username, client_id, client_secret):
    message = username + client_id
    dig = hmac.new(client_secret.encode('utf-8'), message.encode('utf-8'), digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


def verify_cpf_format(cpf: str) -> bool:
    return len(cpf) == 11 and cpf.isdigit()


def lambda_handler(event, context):
    user = event.get("username")
    pwd = event.get("password")

    if not user or not pwd:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "CPF e/ou senha não fornecidos."})
        }

    if not verify_cpf_format(user):
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "CPF inválido!"})
        }

    # Calculate the SECRET_HASH
    secret_hash = get_secret_hash(user, CLIENT_ID, CLIENT_SECRET)

    try:
        response = cognito_client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': user,
                'PASSWORD': pwd,
                'SECRET_HASH': secret_hash
            },
            ClientId=CLIENT_ID
        )
        challenge = response.get('ChallengeName')

        if challenge == 'NEW_PASSWORD_REQUIRED':
            challenge_response = cognito_client.respond_to_auth_challenge(
                ClientId=CLIENT_ID,
                ChallengeName='NEW_PASSWORD_REQUIRED',
                Session=response.get('Session'),
                ChallengeResponses={
                    'USERNAME': user,
                    'NEW_PASSWORD': pwd,
                    'SECRET_HASH': secret_hash
                }
            )
            token = challenge_response.get("AuthenticationResult", {}).get("IdToken")
        else:
            token = response.get("AuthenticationResult", {}).get("IdToken")

        return {
            "statusCode": 200,
            "body": json.dumps({"token": token})
        }
    except ClientError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": str(e)})
        }
