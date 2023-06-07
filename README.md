# WhiteBookDialogue
A test demo ontology driven dialogue system. Subject - The White Book of Rehabilitation (Ukrainian)

## General description

The system consist of three separate python applications: client_service, ontology_service, and sparql_converter. For the system to operate RabbitMQ and Redis are needed. Also an RDF triples store for the ontology to deal with is required, for example, Jena Fuseki. Dependencies of the python packages could be installed through pip from the *requirements.txt* files. Each of the three applications needs a separate python virtual environment with its own dependences.



