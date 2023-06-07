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

The file *WB.pdf* contains the test of the “White Book”, on which the dialogue system is based, to be rendered in the users interface.

Files *analitic_tools.py*, *cases_prep.xml*, *elementary_classes.py*, *foreign_libraries.py*, *marker_words.xml*, *marker_words_ru.xml*, *marker_words_uk.xml*, *text_analyser.py*, *text_analysis_handlers.py*, and *ukr_stemmer3.py* contain tools and program facilities for the natural language text parse, syntactic and semantic analysis.

links_dict.json file and the similar relate to the different ontologies includes keys which correspond to the phrases in the responses tests that require an outer recourse link. To each of the key corresponds a list of three items which are:

    1 – the link itself (URI);
    2 – name of the link to be displayed (if null merely the URL will de shown)
    3 – the OWL class name in relates to

File *nltk.txt* contains name of the required NLTK packages.

The main business logic of the application is included in the script * WhiteBookBot/vievs.py*.

### sparql_converter

The sparql_converter application is an important part of the system responsible for the forming of SPARQL queries basing on the input users’ messages.

The entry point here is the script *text_to_sparql.py*. It sets the **convert_queue** in RabbitMQ and serves it in an infinity loop when running. To run it you just need to type:

    python text_to_sparql.py

When operating as a part of the system in also needs **ontology_queue** to be set in RabbitMQ.

This application as well has scripts *analitic_tools.py*, *cases_prep.xml*, *elementary_classes.py*, *foreign_libraries.py*, *marker_words.xml*, *marker_words_ru.xml*, *marker_words_uk.xml*, *text_analyser.py*, *text_analysis_handlers.py*, and *ukr_stemmer3.py* for the natural language text parse, syntactic and semantic analysis.

File *tree.xml* is an XML representation of the decision tree used for the appropriate SPARQL query template selection basing on the words from the input user’s phrase.

The *query_template.xml* file contains the XML representation of the SPAEQL queries templates.

The file *abbreviations_dict.json* is a dictionary for the possible abbreviation used in the subject area the program is tuned for. It helps to the system to understand the specific abbreviations and link them with the named entities from the ontology.

Files *all_entities.json*, *keywords.json*, and *ontology_entities.json* are regenerated automatically after the application started using *ontology.owl* and *tree.xml* files. The scripts responsible to it are collected in the directory *keywords_generators*. They are needed on the one hand, to clear the input massages from the terms included neither in the ontology not in the decision tree, on the other hand, to fit the selected input named entities to the closest ones from the ontology.
It increases the reliability and the efficiency of the system operating.

The business logic scripts of the application are gathered in the directory *converter*.

### ontology_service

The *ontology_service* application is responsible to dialing with an RDF triples store where ontology is kept. It executes the SPARQL queries and process their results.

The entry point of the application is the script *ontology_agent.py*. To run in you should type:

    python ontology_agent.py

It sets **ontology_queue** in RabbitMQ and serves in during its running. Also it needs Radis to store the results.

The business logic of the application is in the directory *query_execution*.

The ontology should be stored in Jena Fuseki with the name **WhiteBook**. The ontology endpoint is **http://localhost:3030/WhiteBook**. It could be changed in the script *query_execution.py* from the *query_execution* directory.





