SECRET_KEY = 'dev'  # does not matter - for lab only

JSON_SORT_KEYS = False
TEMPLATES_AUTO_RELOAD = True

SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2:///voting'

JWT_SECRET_KEY = 'dev-jwt-secret'  # does not matter - for lab only
JWT_ACCESS_TOKEN_EXPIRES = False
