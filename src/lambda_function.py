import psycopg2
import boto3
import json
from botocore.exceptions import BotoCoreError, ClientError

cognito = boto3.client('cognito-idp')

def get_secrets():
    session = boto3.session.Session()
    client = session.client("secretsmanager", region_name="us-east-1")
    
    try:
        secret_response = client.get_secret_value(SecretId="mazyfood-secrets")
        return json.loads(secret_response['SecretString'])
    except ClientError as e:
        raise RuntimeError(f"Error retrieving credentials: {str(e)}")

def get_cognito_user(token):
    try:
        return cognito.get_user(AccessToken=token)
    except cognito.exceptions.NotAuthorizedException:
        raise ValueError("Invalid token in Cognito")

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

def lambda_handler(event, context):
    try:
        config = get_secrets()
        
        with psycopg2.connect(
            host=config["RDS_HOST"],
            database=config["RDS_DATABASE"],
            user=config["RDS_USER"],
            password=config["RDS_PASSWORD"]
        ) as connection:

            token = event.get('token')
            cognito_response = get_cognito_user(token)

            cpf = cognito_response.get("Username")
            
            # Extract user attributes
            attributes = {attr['Name']: attr['Value'] for attr in cognito_response.get("UserAttributes", [])}
            email, name = attributes.get('email'), attributes.get('name')

            # Handle anonymous customer
            if not cpf:
                return {
                    'statusCode': 200,
                    'body': json.dumps({'customer_id': None, 'message': 'Anonymous customer identified.'})
                }

            with connection.cursor() as cursor:
                customer_record = get_customer_data(cursor, cpf)

                if customer_record:
                    return {
                        'statusCode': 200,
                        'body': json.dumps({'customer_id': customer_record[0], 'message': 'Customer already registered.'})
                    }

                customer_id = create_customer(cursor, connection, cpf, name, email)
                return {
                    'statusCode': 201,
                    'body': json.dumps({'customer_id': customer_id, 'message': 'Customer successfully registered.'})
                }

    except ValueError as e:
        return {'statusCode': 401, 'body': json.dumps({'error': str(e)})}

    except RuntimeError as e:
        return {'statusCode': 401, 'body': json.dumps({'error': str(e)})}

    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
