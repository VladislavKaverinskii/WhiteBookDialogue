# WhiteBookDialogue
A test demo ontology driven dialogue system. Subject - The White Book of Rehabilitation (Ukrainian)

## General description

The system consist of three separate python applications: client_service, ontology_service, and sparql_converter. For the system to operate RabbitMQ and Redis are needed. Also an RDF triples store for the ontology to deal with is required, for example, Jena Fuseki. Dependencies of the python packages could be installed through pip from the *requirements.txt* files. Each of the three applications needs a separate python virtual environment with its own dependences.

For better operating the *client_service*, which is a Django application it would be better to use an SQL database, for instance driven by a PostgreSQL, instead of the default *sql light*.
Also for the production it is recommended to replace the Django demo service of the *client_service* application with something more sufficient such as *Gunicorn*.
However, merely for the demonstration and acquaintance purposes even the default settings could be used.

## The applications structure and deployment

### client_service

The client_service is by its structure a Django application. It is responsible for the users web interface. Also it executes some preprocessing and post processing operations with the text messages and ontology responses. 

The entry point for the application to start is the file *manage.py*, as it is usual for Django projects.

The general settings of the project as a Django application could be found in the *WhiteBook/settings.py*. There you can change the values of **SECRET_KEY**, **DEBUG** mode flag, **ALLOWED_HOSTS**, **DATABASES** connection settings.



