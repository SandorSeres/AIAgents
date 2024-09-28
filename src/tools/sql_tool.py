from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import SQLAlchemyError

class SQLTool:
    """
    Class Name: SQLTool
    Description: A utility class designed to execute SQL queries on various databases (Oracle, MS SQL Server, PostgreSQL) using SQLAlchemy and return the results.

    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of what the tool does.
        parameters (list): A list of parameters required by the tool, including the database type, connection parameters, and SQL query.

    Methods:
        _run(database_type, connection_params, query):
            Executes the provided SQL query on the specified database and returns the results or an error message.

        clone():
            Returns a new instance of SQLTool.
    """

    name: str = "SQLTool"
    description: str = "A tool to execute SQL queries on various databases using SQLAlchemy and return the results."
    parameters: list = ["database_type", "connection_params", "query"]

    def _run(self, database_type: str, connection_params: dict, query: str) -> tuple:
        """
        Executes the provided SQL query on the specified database.

        Parameters:
            database_type (str): The type of the database ('oracle', 'mssql', 'postgresql').
            connection_params (dict): A dictionary containing connection parameters specific to the database type.
            query (str): The SQL query to execute.

        Returns:
            tuple: A tuple containing the query results as a string or an error message, along with a task_completed flag.

        Notes:
            - Uses SQLAlchemy to create a database engine.
            - Executes the query and fetches all results.
            - Returns results in a uniform string format.
        """
        try:
            engine = self._create_engine(database_type, connection_params)
            with engine.connect() as connection:
                result_set = connection.execute(text(query))
                rows = result_set.fetchall()
                # Convert rows to string
                result = "\n".join([str(row) for row in rows])
            return result, True
        except SQLAlchemyError as e:
            return f"An error occurred: {str(e)}", False

    def _create_engine(self, database_type: str, params: dict):
        """
        Creates a SQLAlchemy engine based on the database type and connection parameters.

        Parameters:
            database_type (str): The type of the database.
            params (dict): Connection parameters.

        Returns:
            Engine: A SQLAlchemy engine instance.
        """
        if database_type.lower() == 'oracle':
            # Oracle connection string format
            oracle_url = URL.create(
                drivername='oracle+cx_oracle',
                username=params.get('user'),
                password=params.get('password'),
                host=params.get('host'),
                port=params.get('port', 1521),
                database=params.get('service_name')  # For Oracle, 'database' is the service name
            )
            return create_engine(oracle_url)

        elif database_type.lower() == 'mssql':
            # MS SQL Server connection string format
            mssql_url = URL.create(
                drivername='mssql+pyodbc',
                username=params.get('user'),
                password=params.get('password'),
                host=params.get('host'),
                port=params.get('port', 1433),
                database=params.get('database'),
                query={'driver': 'ODBC Driver 17 for SQL Server'}
            )
            return create_engine(mssql_url)

        elif database_type.lower() == 'postgresql':
            # PostgreSQL connection string format
            postgres_url = URL.create(
                drivername='postgresql+psycopg2',
                username=params.get('user'),
                password=params.get('password'),
                host=params.get('host'),
                port=params.get('port', 5432),
                database=params.get('database')
            )
            return create_engine(postgres_url)

        else:
            raise ValueError(f"Unsupported database type: {database_type}")

    def clone(self):
        """
        Creates a clone of the SQLTool instance.

        Returns:
            SQLTool: A new instance of SQLTool.
        """
        return SQLTool()

"""
# Define connection parameters
connection_params = {
    'user': 'your_username',
    'password': 'your_password',
    'host': 'localhost',
    'port': '5432',  # Default port for PostgreSQL
    'database': 'your_database'
}

# Create an instance of SQLTool
sql_tool = SQLTool()

# Execute a query
result, success = sql_tool._run('postgresql', connection_params, 'SELECT * FROM your_table')

if success:
    print("Query Results:")
    print(result)
else:
    print("Error:")
    print(result)

"""