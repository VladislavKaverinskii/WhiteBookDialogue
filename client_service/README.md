# white_book_client
Interface shell for White Book chatbot

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
