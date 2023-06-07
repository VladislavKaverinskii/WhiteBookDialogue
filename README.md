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

The general settings of the project as a Django application could be found in the *WhiteBook/settings.py*. There you can change the values of **SECRET_KEY**, **DEBUG** mode flag, **ALLOWED_HOSTS**, **DATABASES** connection settings, and **TIME_ZONE**.

More specific settings are collected in the file *chatbot_config.xml*. It’s better not to change the technical settings, however, here is their brief description:

    <name> - the name of the application as a service
    <conversation_limitation> - time (in seconds) for the dialogue session to be expired being idle
    <garbage_deleting> - periodicity (in seconds) of expired temporary data deleting
    <wait_time> - max time (in seconds) for the response waiting
    <db_clean_time> - periodicity (in seconds) to clean data base from expired temporary data
    <cache_clean_time> - time (in seconds) of keeping the obtained responses cached

Other setting are information for the quick and supplementary responses. It has the following sections:

    <answers_comments> - comments to supplement the main response (answer) depending on their relevance assurance degree
    <greeting_phrases> - standard phrases to great the user
    <standard_answers> - standard answer phrases for typical problematic situations 
        (i.e. no answer obtained, program “does not understand” the user’s message,
            an error appear during the query execution, the input was empty)
    <explanations> - phrases for the failures explanation
    <dialog_answers> - standard answers for the typical situation in a dialogue for quick responses without involving the other services.
    <goodbye_phrases> - phrases to stop the dialogue






