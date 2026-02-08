import os
import click
from flask.cli import with_appcontext
from .__init__ import create_app, db
from sqlalchemy import text


app = create_app()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        db.session.execute(text(f.read()))
    db.session.commit()
    click.echo('Initialized the database.')

app.cli.add_command(init_db_command)

if __name__ == '__main__':
    app.run(debug=True)
