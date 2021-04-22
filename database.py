from flask import g
import sqlite3

def connect_db():
    """AI is creating summary for connect_db
    Returns:
        sql: SQLite Object 
    """
    sql = sqlite3.connect('food_log.db')
    sql.row_factory = sqlite3.Row
    return sql


def get_db():
    """get database

    Returns:
        g: return g.sqlite3
    """
    if not hasattr(g, 'sqlite3'):
        g.sqlite3 = connect_db()
    return g.sqlite3

