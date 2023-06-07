# ontology_service

The *ontology_service* application is responsible to dialing with an RDF triples store where ontology is kept. 
It executes the SPARQL queries and process their results.

The entry point of the application is the script *ontology_agent.py*. To run in you should type:

    python ontology_agent.py

It sets **ontology_queue** in RabbitMQ and serves in during its running. Also it needs Radis to store the results.

The business logic of the application is in the directory *query_execution*.

The ontology should be stored in Jena Fuseki with the name **WhiteBook**. The ontology endpoint is **http://localhost:3030/WhiteBook**. 
It could be changed in the script *query_execution.py* from the *query_execution* directory.
