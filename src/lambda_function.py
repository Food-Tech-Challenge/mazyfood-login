import base64
import json
import psycopg2
import boto3
import requests
from botocore.exceptions import BotoCoreError, ClientError

cognito = boto3.client('cognito-idp')

def create_response(status_code, message):
    return {"statusCode": status_code, "body": json.dumps(message)}

def handle_exception(e, status_code=500):
    return create_response(status_code, {"error": str(e)})

def get_secrets():
    try:
        client = boto3.client("secretsmanager", region_name="us-east-1")
        secret_response = client.get_secret_value(SecretId="mazyfood-secrets")
        return json.loads(secret_response['SecretString'])
    except ClientError as e:
        raise RuntimeError(f"Error retrieving credentials: {str(e)}")

def get_customer_data(cursor, cpf):
    cursor.execute("SELECT id FROM customers WHERE cpf = %s", (cpf,))
    return cursor.fetchone()

def create_customer(cursor, connection, cpf, name, email):
    cursor.execute(
        "INSERT INTO customers (cpf, name, email) VALUES (%s, %s, %s) RETURNING id",
        (cpf, name, email)
    )
    connection.commit()
    return cursor.fetchone()[0]

def get_tokens(config, code):
    token_url = f"https://{config['COGNITO_DOMAIN']}/oauth2/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": config['COGNITO_CLIENT_ID'],
        "redirect_uri": config['COGNITO_REDIRECT_URI'],
        "code": code
    }
    auth_header = base64.b64encode(f"{config['COGNITO_CLIENT_ID']}:{config['COGNITO_CLIENT_SECRET']}".encode()).decode()
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": f"Basic {auth_header}"}

    response = requests.post(token_url, data=payload, headers=headers)
    if response.status_code != 200:
        raise RuntimeError("Failed to exchange code for tokens")

    tokens = response.json()
    return tokens.get("access_token")

def get_user_info(config, access_token):
    user_info_url = f"https://{config['COGNITO_DOMAIN']}/oauth2/userInfo"
    response = requests.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})

    if response.status_code != 200:
        raise RuntimeError("Failed to retrieve user info")

    return response.json()

def lambda_handler(event, context):
    try:
        config = get_secrets()
        code = event.get("queryStringParameters", {}).get("code")
        if not code:
            return create_response(400, {"error": "Code is required"})

        access_token = get_tokens(config, code)
        if not access_token:
            return create_response(400, {"error": "Failed to retrieve access token"})

        user_info = get_user_info(config, access_token)
        cpf, email, name = user_info.get('username'), user_info.get('email'), user_info.get('name')

        if not cpf:
            return create_response(200, {"customer_id": None, "message": "Anonymous customer identified."})

        with psycopg2.connect(
            host=config["RDS_HOST"],
            database=config["RDS_DATABASE"],
            user=config["RDS_USER"],
            password=config["RDS_PASSWORD"]
        ) as connection:
            with connection.cursor() as cursor:
                customer_record = get_customer_data(cursor, cpf)

                if customer_record:
                    return create_response(200, {"customer_id": customer_record[0], "message": "Customer already registered."})

                customer_id = create_customer(cursor, connection, cpf, name, email)
                return create_response(201, {"customer_id": customer_id, "message": "Customer successfully registered."})

    except (ValueError, RuntimeError) as e:
        return handle_exception(e, 401)

    except Exception as e:
        return handle_exception(e)
