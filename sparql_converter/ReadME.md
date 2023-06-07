# sparql_converter

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
