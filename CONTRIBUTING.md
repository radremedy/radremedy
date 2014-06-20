Contributing
===

This project has several components that can be worked at concurrently.

1. the scrapers
2. the database models
3. the UI
4. linking the scrapers to the database
5. linking the UI to the Database and logic
	1. user athentication
	2. user settings
	3. searching
	4. javascript responsible for maps and other things
	5. widgets like recently added and discussions
	6. comments code

You can help with any of these parts.

The UI
===

You need to create a [template](https://github.com/radremedy/radremedy/tree/master/remedy/templates) and add it [to a url](https://github.com/radremedy/radremedy/tree/master/remedy/templates). If you don't know Python or Flask, you can still help by addind the html file.

Currently Wil is focusing on creating the [templates for the UI](https://github.com/radremedy/radremedy/issues/4). You can help with thaht by implementing one of the templates. The css should be pretty global. Making of the navigation bar and find a medical provider should of taken care of most of it. The css and html files should take care of generating all the static UI. Keep in mind that forms and other logic isn't being implemented yet. Just being layed out.

The Scrapers
===

The [scrapers](https://github.com/radremedy/radremedy/tree/master/scripts) are black magic right now. They need to be [refactored, documented and be integrated](https://github.com/radremedy/radremedy/issues/1) to our app instead of using the ddlgenerator. Currently they reside the scripts directory with unrelated files. The have to be moved to [another directory](https://github.com/radremedy/radremedy/issues/21).

Database Models
===

We sort of have to reverse engineer these from the views until we can better outline what they should be. They are in the [models.py file](https://github.com/radremedy/radremedy/blob/master/remedy/models.py). Any change to the models should be accompanied by a database migration.

Other logic
===

The rest of the logic like user authentication and searching is pretty abstract. Until we get the models and the scrapers linked up, not much can be done in this department. After we get those working, the fun can begin.

