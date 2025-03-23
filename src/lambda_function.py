import psycopg2
import boto3
import json
import os
from botocore.exceptions import BotoCoreError, ClientError

# Configuração do banco RDS PostgreSQL
RDS_HOST = os.environ['RDS_HOST']
RDS_USER = os.environ['RDS_USER']
RDS_PASSWORD = os.environ['RDS_PASSWORD']
RDS_DATABASE = os.environ['RDS_DATABASE']

# Configuração do Cognito
COGNITO_USER_POOL_ID = os.environ['COGNITO_USER_POOL_ID']

# Inicializando serviços AWS
cognito = boto3.client('cognito-idp')

def lambda_handler(event, context):
    connection = None

    try:
        connection = psycopg2.connect(
            host=RDS_HOST,
            database=RDS_DATABASE,
            user=RDS_USER,
            password=RDS_PASSWORD
        )

        cpf = event.get('cpf')
        nome = event.get('nome')
        email = event.get('email')

        with connection.cursor() as cursor:
            # Cliente anônimo
            if not cpf:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'cliente_id': None,
                        'mensagem': 'Cliente anônimo identificado.'
                    })
                }

            # Verificar se o cliente já existe
            cursor.execute("SELECT id FROM customers WHERE cpf = %s", (cpf,))
            cliente = cursor.fetchone()

            if cliente:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'cliente_id': cliente[0],
                        'mensagem': 'Cliente já cadastrado.'
                    })
                }

            # Criar novo cliente na base de dados
            cursor.execute(
                "INSERT INTO customers (cpf, name, email) VALUES (%s, %s, %s) RETURNING id",
                (cpf, nome, email)
            )
            cliente_id = cursor.fetchone()[0]
            connection.commit()

            # Criar usuário no Cognito
            try:
                cognito_response = cognito.admin_create_user(
                    UserPoolId=COGNITO_USER_POOL_ID,
                    Username=cpf,
                    UserAttributes=[
                        {'Name': 'email', 'Value': email},
                        {'Name': 'custom:cpf', 'Value': cpf},
                        {'Name': 'name', 'Value': nome}
                    ]
                )

            except (BotoCoreError, ClientError) as e:
                # Se a criação no Cognito falhar, remove o cliente criado na tabela
                cursor.execute("DELETE FROM customers WHERE id = %s", (cliente_id,))
                connection.commit()
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': f'Erro ao criar usuário no Cognito: {str(e)}'})
                }

            return {
                'statusCode': 201,
                'body': json.dumps({
                    'cliente_id': cliente_id,
                    'mensagem': 'Cliente cadastrado com sucesso.'
                })
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    finally:
        if connection:
            connection.close()
