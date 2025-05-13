
def get_query():
    from sqlalchemy import create_engine
    import os
    # Database connection parameters
    db_params = {
                    'username': os.getenv('POSTGRES_USERNAME'),
                    'password': os.getenv('POSTGRES_PASSWORD'),
                    'host': os.getenv('POSTGRES_HOST'),
                    'port': os.getenv('POSTGRES_PORT'),
                    'database': os.getenv('POSTGRES_DBNAME')
                }

                # Create a connection string
    connection_string = f"postgresql+psycopg2://{db_params['username']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
    engine = create_engine(connection_string)
    query = 'select * from instagram';
    return query
