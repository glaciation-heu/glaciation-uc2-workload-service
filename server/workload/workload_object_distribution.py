import time
import os
import argparse
import requests
import matplotlib.pyplot as plt

from collections import defaultdict


# Define function to parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Run the workload with configurable metadata service URL")
    parser.add_argument(
        "--url",
        type=str,
        default=None,  # Default is None; will fall back to environment variable or hardcoded value later
        help="Metadata service URL"
    )
    return parser.parse_args()


# Step 1: Construct the SPARQL Query
def construct_sparql_query():
    sparql_query = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX glc: <https://glaciation-project.eu/MetadataReferenceModel#>
    PREFIX saref: <https://saref.etsi.org/core/>

    SELECT * WHERE {
        { GRAPH ?g 
            {
            ?s saref:hasIdentifier ?robotId .
            ?s glc:hasSubResource ?yolo .
            ?yolo glc:makesMeasurement ?m .
            ?m saref:relatesToProperty glc:name .
            ?m saref:hasValue ?v .
            }
        } 
    } LIMIT 10
    """
    return sparql_query


# Step 2: Submit the SPARQL query to the metadata service using GET request
def submit_sparql_query(sparql_query, metadata_service_url):
    try:
        response = requests.get(metadata_service_url, params={'query': sparql_query}, headers={'Accept': 'application/json'})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying metadata service: {e}")
        return None


# Step 3: Process the response data to calculate frequency and distribution
def process_response(data):
    object_frequency = defaultdict(int)
    zone_distribution = defaultdict(lambda: defaultdict(int))
    high_priority_objects = ["person", "chair"]

    for result in data.get("results", {}).get("bindings", []):
        obj = result.get("v", {}).get("value")
        zone = result.get("robotId", {}).get("value")#.split('/')[-1]
        print(f'Zone: {zone}')

        if obj and zone:
            # Count the total occurrences of each object
            object_frequency[obj] += 1

            # Count the occurrences of objects in specific zones
            zone_distribution[zone][obj] += 1

    return object_frequency, zone_distribution, high_priority_objects


# Step 4: Generate insights and print metrics
def generate_insights(object_frequency, zone_distribution, high_priority_objects):
    print("---- Object Frequency Across All Zones ----")
    for obj, count in object_frequency.items():
        print(f"{obj}: {count} detections")

    print("\n---- Object Distribution by Zone ----")
    for zone, objects in zone_distribution.items():
        print(f"Zone {zone}:")
        for obj, count in objects.items():
            print(f"  {obj}: {count} detections")

    print("\n---- High-Priority Object Distribution ----")
    for zone, objects in zone_distribution.items():
        print(f"Zone {zone}:")
        for obj, count in objects.items():
            if obj in high_priority_objects:
                print(f"  {obj}: {count} detections (high priority)")


def visualize(stats: dict, title: str='Object distribution'):
    """Generate visualization with statistics
    """
    #print(stats)
    objects = list(stats.keys())
    print(objects)
    occurence = list(stats.values())
    print(occurence)
    plt.bar(objects, occurence)
    plt.title(title)
    plt.xlabel('Objects')
    plt.ylabel('Occurrence')
    plt.savefig('_'.join(title.split())+'.png')
    plt.close()


# Main function to run the workload
def main():
    # Parse command-line arguments
    args = parse_arguments()

    # Check if the command-line argument is provided, then check environment variable, then fallback to default
    metadata_service_url = args.url or os.getenv("METADATA_SERVICE_URL", "http://metadata.validation/api/v0/graph")

    print(f"Using Metadata Service URL: {metadata_service_url}")
    
    start_time = time.perf_counter()
    # Step 1: Construct the SPARQL query
    sparql_query = construct_sparql_query()

    # Step 2: Submit the query to the metadata service and get the response
    response_data = submit_sparql_query(sparql_query, metadata_service_url)
    print(f'Response')
    print(response_data)

    if response_data:
        # Step 3: Process the response data
        object_frequency, zone_distribution, high_priority_objects = process_response(response_data)

        # Step 4: Generate insights and print the results
        generate_insights(object_frequency, zone_distribution, high_priority_objects)

        visualize(object_frequency)
        for zone, stats in zone_distribution.items():
            visualize(stats, f'Object distribution for zone: {zone}')
    else:
        print('No response from metadata service')

    print(f'{time.perf_counter()-start_time}s elapsed')


if __name__ == "__main__":
    main()

