Contributing
===

This project has several components that can be worked at concurrently.

1. The scrapers
2. The database models
3. The UI
4. Linking the UI to the Database and logic
	1. User authentication
	2. User settings
	3. Searching
	4. Javascript responsible for maps and other things
	5. Widgets like recently added and discussions
	6. Comments code

You can help with any of these parts. If you are planning to work on something please let us know by commenting on
the corresponding issue, or opening a new one.

[Checkout the Wiki for more info](https://github.com/radremedy/radremedy/wiki).

The UI
===

Currently, the team is waiting on a redesign of the pages before any more work on the UI takes place. 

The css and html files should take care of generating all the static UI. Keep in mind that forms and other logic
isn't being implemented yet.

Forms and Searching
===

Once the template(view) of something has been mocked up, you can work on connecting it to the database. Most of this
can happen with forms. For example searching the database for a provider. You can do this using
[Flask forms](http://flask.pocoo.org/docs/patterns/wtforms/). Using the Flask WTF forms extension should make this work
easier.

Others might argue that some of this logic would be better in the client side. If you think so open an issue with your
arguments. At this point, the project can go either way.

The Scrapers
===

The Howard Brown scraper is in good shape right now.

Database Models
===

They are in the [models.py file](https://github.com/radremedy/radremedy/blob/master/remedy/rad/models.py).
Any change to the models should be accompanied by a database migration.

Other logic
===

The rest of the logic like user authentication and searching is pretty abstract.
Until we get the models and the scrapers linked up, not much can be done in this department.
After we get those working, the fun can begin.

