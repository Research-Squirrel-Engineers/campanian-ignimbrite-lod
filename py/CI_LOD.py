__author__ = "Florian Thiery"
__copyright__ = "MIT Licence 2023, Florian Thiery"
__credits__ = ["Florian Thiery"]
__license__ = "MIT"
__version__ = "beta"
__maintainer__ = "Florian Thiery"
__email__ = "mail@fthiery.de"
__status__ = "beta"
__update__ = "2025-07-16"

import pandas as pd
import os
import datetime
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, SKOS, FOAF, PROV, XSD, DCTERMS
from rdflib.namespace import Namespace as NS

# Define namespaces
GEOSPARQL = NS("http://www.opengis.net/ont/geosparql#")
SF = NS("http://www.opengis.net/ont/sf#")
PLEIADES = NS("https://pleiades.stoa.org/places/vocab#")
FSL = NS("http://fuzzy-sl.squirrel.link/ontology/")
FSLD = NS("http://fuzzy-sl.squirrel.link/data/")

def create_graph():
    """Initialize RDF graph with namespace bindings"""
    g = Graph()
    
    # Bind namespaces
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("skos", SKOS)
    g.bind("foaf", FOAF)
    g.bind("prov", PROV)
    g.bind("xsd", XSD)
    g.bind("dct", DCTERMS)
    g.bind("geosparql", GEOSPARQL)
    g.bind("sf", SF)
    g.bind("pleiades", PLEIADES)
    g.bind("fsl", FSL)
    g.bind("fsld", FSLD)
    
    return g

def add_site_triples(g, row, starttime):
    """Add all site-related triples to graph including agents, activities, and geometry"""
    site_uri = FSLD[f"cisite_{row['id']}"]
    
    # Basic typing
    g.add((site_uri, RDF.type, FSL.Site))
    g.add((site_uri, RDF.type, PROV.Entity))
    g.add((site_uri, RDF.type, PLEIADES.Place))
    g.add((site_uri, FSL.partOf, FSL.CampanianIgnimbriteProject))
    g.add((site_uri, FSL.siteType, FSL.ArchaeologicalSite))
    
    # Labels and descriptions
    g.add((site_uri, RDFS.label, Literal(row['label'], lang="en")))
    g.add((site_uri, SKOS.prefLabel, Literal(row['label'], lang="en")))
    
    if not pd.isna(row['desc']):
        g.add((site_uri, SKOS.scopeNote, Literal(row['desc'], lang="en")))
        g.add((site_uri, RDFS.comment, Literal(row['desc'], lang="en")))
    
    # Certainty
    g.add((site_uri, FSL.certaintyLevel, Literal(row['certainty'])))
    g.add((site_uri, FSL.certaintyDesc, Literal(row['certaintyinfo'], lang="en")))
    
    # Relations
    if not pd.isna(row['relatedto']):
        relations = str(row['relatedto']).split(";")
        for relation in relations:
            g.add((site_uri, URIRef(row['relatedtohow']), URIRef(relation)))
    
    # Spatial types
    if not pd.isna(row['spatialtype']):
        spatial_types = str(row['spatialtype']).split(";")
        for spatial_type in spatial_types:
            g.add((site_uri, FSL.spatialType, URIRef(spatial_type)))
    
    # Literature
    if not pd.isna(row['literature']):
        literature = str(row['literature']).split(";")
        for lit in literature:
            g.add((site_uri, FSL.hasReference, Literal(lit)))
    
    # Geometry
    geom_uri = URIRef(str(site_uri) + "_geom")
    g.add((site_uri, GEOSPARQL.hasGeometry, geom_uri))
    g.add((geom_uri, RDF.type, SF.Point))
    
    # WKT Literal
    wkt_literal = Literal(f"<http://www.opengis.net/def/crs/EPSG/0/4326> {row['wkt']}", 
                         datatype=GEOSPARQL.wktLiteral)
    g.add((geom_uri, GEOSPARQL.asWKT, wkt_literal))
    
    # Certainty for geometry
    g.add((geom_uri, FSL.certaintyLevel, Literal(row['certainty'])))
    g.add((geom_uri, FSL.certaintyDesc, Literal(row['certaintyinfo'], lang="en")))
    
    # Add agent triples
    if not pd.isna(row['agent']):
        agents = str(row['agent']).split(";")
        for agent_url in agents:
            agent_id = agent_url.replace("http://orcid.org/", "")
            agent_uri = FSLD[f"agent_{agent_id}"]
            
            g.add((agent_uri, RDF.type, FOAF.Person))
            g.add((agent_uri, RDF.type, PROV.Agent))
            g.add((agent_uri, SKOS.exactMatch, URIRef(agent_url)))
    
    # Add activity triples
    activity_uri = FSLD[f"cisite_{row['id']}_activity"]
    
    # Basic typing
    g.add((activity_uri, RDF.type, PROV.Activity))
    g.add((activity_uri, RDF.type, URIRef(row['methodtype'])))
    
    # Timestamps
    start_time = Literal(starttime, datatype=XSD.dateTime)
    end_time = Literal(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"), 
                      datatype=XSD.dateTime)
    g.add((activity_uri, PROV.startedAtTime, start_time))
    g.add((activity_uri, PROV.endedAtTime, end_time))
    
    # Activity data
    g.add((activity_uri, FSL.hasSource, URIRef(row['source'])))
    g.add((activity_uri, FSL.hasSourceType, URIRef(row['sourcetype'])))
    g.add((activity_uri, FSL.activityDesc, Literal(row['methoddesc'], lang="en")))
    g.add((activity_uri, FSL.certaintyLevel, Literal(row['certainty'])))
    g.add((activity_uri, FSL.certaintyDesc, Literal(row['certaintyinfo'], lang="en")))
    
    # Literature references for activity
    if not pd.isna(row['literature']):
        literature = str(row['literature']).split(";")
        for lit in literature:
            g.add((activity_uri, FSL.hasReference, Literal(lit)))
    
    # Images
    if not pd.isna(row['relatedto']):
        relations = str(row['relatedto']).split(";")
        for relation in relations:
            if "png" in relation or "jpg" in relation:
                g.add((activity_uri, FSL.image, URIRef(relation)))
    
    # PROV-O relationships
    g.add((site_uri, PROV.wasGeneratedBy, activity_uri))
    g.add((activity_uri, PROV.used, site_uri))
    
    # Agent associations
    if not pd.isna(row['agent']):
        agents = str(row['agent']).split(";")
        for agent_url in agents:
            g.add((site_uri, PROV.wasAttributedTo, URIRef(agent_url)))
            g.add((activity_uri, PROV.wasAssociatedWith, URIRef(agent_url)))
    
    return site_uri

def add_provenance(g, row, site_uri, starttime):
    """Add provenance triples including license and script provenance"""
    # License
    g.add((site_uri, DCTERMS.license, URIRef("https://creativecommons.org/licenses/by/4.0/")))
    g.add((site_uri, DCTERMS.creator, URIRef("https://orcid.org/0000-0002-3246-3531")))
    g.add((site_uri, DCTERMS.creator, URIRef("https://orcid.org/0000-0003-1100-6494")))
    g.add((site_uri, DCTERMS.rightsHolder, URIRef("https://orcid.org/0000-0002-3246-3531")))
    g.add((site_uri, DCTERMS.rightsHolder, URIRef("https://orcid.org/0000-0003-1100-6494")))
    
    # General provenance
    g.add((site_uri, PROV.wasDerivedFrom, URIRef("https://github.com/Research-Squirrel-Engineers/campanian-ignimbrite-geo")))
    
    # PROV-O for script
    script_uri = FSLD[f"cisite_{row['id']}_pyscript"]
    
    g.add((site_uri, PROV.wasAttributedTo, URIRef("https://github.com/Research-Squirrel-Engineers/campanian-ignimbrite-geo/blob/main/py/CI.py")))
    g.add((site_uri, PROV.wasDerivedFrom, URIRef("https://github.com/Research-Squirrel-Engineers/campanian-ignimbrite-geo")))
    g.add((site_uri, PROV.wasGeneratedBy, script_uri))
    
    g.add((script_uri, RDF.type, PROV.Activity))
    g.add((script_uri, PROV.startedAtTime, Literal(starttime, datatype=XSD.dateTime)))
    g.add((script_uri, PROV.endedAtTime, Literal(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"), datatype=XSD.dateTime)))
    g.add((script_uri, PROV.wasAssociatedWith, URIRef("https://github.com/Research-Squirrel-Engineers/campanian-ignimbrite-geo/blob/main/py/CI.py")))

def main():
    # Set starttime
    starttime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    
    # Set paths
    file_name = "cifindspots_part_full.csv"
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_in = dir_path.replace("\\py", "\\data") + "\\" + file_name
    
    # Read CSV file
    data = pd.read_csv(
        file_in,
        encoding='utf-8',
        sep=',',
        usecols=['id', 'label', 'desc', 'certainty', 'certaintyinfo', 'relatedto', 'relatedtohow', 'source',
                 'sourcetype', 'spatialtype', 'methodtype', 'agent', 'methoddesc', 'literature', 'wkt'],
        na_values=['.', '??', 'NULL']
    )
    
    print("*****************************************")
    print(data.info())
    
    # Create RDF graph
    g = create_graph()
    
    # Process each row
    for index, row in data.iterrows():
        # Add site triples (includes agents, activities, and geometry)
        site_uri = add_site_triples(g, row, starttime)
        
        # Add provenance (includes license and script provenance)
        add_provenance(g, row, site_uri, starttime)
    
    # Write output file
    output_file = dir_path.replace("\\py", "\\rdf") + "\\ci_full.ttl"
    g.serialize(destination=output_file, format='turtle')
    
    print(f"SUCCESS: Generated {len(g)} triples in {output_file}")
    print("*****************************************")

if __name__ == "__main__":
    main()