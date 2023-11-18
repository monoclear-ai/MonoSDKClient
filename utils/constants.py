import os
from dotenv import load_dotenv

env = os.getenv('ENV_MODE', 'development')

load_dotenv(f'.env.{env}')

ENDPOINT_URL = os.getenv('ENDPOINT_URL')
MONOCLEAR_SDK_KEY = os.getenv('MONOCLEAR_SDK_KEY')

AWS_ACCESS_KEY = os.getenv('SERVER_AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('SERVER_AWS_SECRET_KEY')
AWS_REGION = os.getenv('SERVER_AWS_REGION')