import click
from flask.cli import with_appcontext
from .__init__ import create_app, db

app = create_app()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    with open('schema.sql', 'r') as f:
        db.session.execute(f.read())
    db.session.commit()
    click.echo('Initialized the database.')

app.cli.add_command(init_db_command)

if __name__ == '__main__':
    app.run(debug=True)
