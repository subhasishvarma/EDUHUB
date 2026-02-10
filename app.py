import os
import click
from flask.cli import with_appcontext
from .__init__ import create_app, db
<<<<<<< HEAD
=======
from sqlalchemy import text

>>>>>>> b43b4c6 (Add auth, student dashboard, and templates)

app = create_app()

@click.command('init-db')
@with_appcontext
def init_db_command():
<<<<<<< HEAD
    """Initialize / migrate DB schema using schema.sql.

    Why this change?
    - schema.sql contains MANY SQL statements (CREATE TABLE, DO $$ blocks,
      CREATE VIEW, etc.).
    - Executing the whole file via SQLAlchemy's db.session.execute(...) often fails
      because it expects one statement at a time.

    This version uses a raw DB-API cursor so Postgres can execute the full script.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        sql_script = f.read()

    conn = db.engine.raw_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql_script)
        conn.commit()
        click.echo("Initialized the database (schema.sql applied).")
    finally:
        try:
            conn.close()
        except Exception:
            pass

app.cli.add_command(init_db_command)

if __name__ == "__main__":
=======
    """Clear the existing data and create new tables."""
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        db.session.execute(text(f.read()))
    db.session.commit()
    click.echo('Initialized the database.')

app.cli.add_command(init_db_command)

if __name__ == '__main__':
>>>>>>> b43b4c6 (Add auth, student dashboard, and templates)
    app.run(debug=True)
