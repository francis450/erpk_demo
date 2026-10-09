import click


def after_install():
	"""Nothing destructive here: fixtures sync automatically, data comes from the seed."""
	click.secho("erpk_demo installed. Next step, seed a prospect profile:", fg="green")
	click.echo(
		"  bench --site <site> execute erpk_demo.seed.run "
		"--kwargs \"{'profile': 'furniture', 'company': '<Company>', 'abbr': '<ABBR>'}\""
	)
