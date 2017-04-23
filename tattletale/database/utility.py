import sqlalchemy


CONNECTION_STRING_MAP = {
    "sqlite_memory": "sqlite://",
    "sqlite_file": "sqlite:///{id}.db",
    "mysql": "mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_server}/{id}",
}


def connection_string_for_workspace(database_type, workspace_identifier, config):
    # Get the right format string for the database type
    connection_format = CONNECTION_STRING_MAP[database_type]

    # Generate a corpus of information to pass to the format function
    conn_info = {
        "id": workspace_identifier
    }

    if database_type == "mysql":  # pragma: no cover
        # Have additional information to add for mysql
        for key in ["mysql_user", "mysql_password", "mysql_server"]:
            conn_info[key] = config[key]

    # Using the given information, fill in the format string.
    return connection_format.format(**conn_info)


def get_or_create(session, model, defaults=None, **kwargs):
    """
    Given a database session and a model (and some parameters), either get or create the object in question.
    
    :param session: 
    :param model: 
    :param defaults: 
    :param kwargs: 
    :return: Tuple of object instance and a boolean describing if the object was created or not. 
    """

    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, sqlalchemy.sql.expression.ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        session.commit()
        return instance, True