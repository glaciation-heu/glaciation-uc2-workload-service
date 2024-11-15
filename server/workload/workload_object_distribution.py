import time
import os
import argparse
import requests
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from collections import defaultdict
from pprint import pprint
from metadata import coco_labels


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
            ?yolo glc:makesMeasurement ?label .
            ?label saref:relatesToProperty glc:name .
            ?label saref:hasValue ?v .
            ?yolo glc:makesMeasurement ?conf .
            ?conf saref:relatesToProperty glc:confidence .
            ?conf saref:hasValue ?confVal .
            }
        } 
        FILTER (STRSTARTS(STR(?g), 'https://glaciation-project.eu/uc/2'))
    } 
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
    det_confidence = defaultdict(lambda: pd.DataFrame(columns=coco_labels))
    object_frequency = defaultdict(int)
    zone_distribution = defaultdict(lambda: defaultdict(int))
    high_priority_objects = ["person", "chair"]

    for result in data.get("results", {}).get("bindings", []):
        timestamp = result.get("g", {}).get("value")
        obj = result.get("v", {}).get("value")
        zone = result.get("robotId", {}).get("value")#.split('/')[-1]
        confi = result.get("confVal", {}).get("value")
        print(f'Zone: {zone}, timestamp: {timestamp}, confi: {confi}')

        if obj and zone:
            # Count the total occurrences of each object
            object_frequency[obj] += 1

            # Count the occurrences of objects in specific zones
            zone_distribution[zone][obj] += 1

            # Update confidence dataframe
            if obj in coco_labels:
                if timestamp not in det_confidence[zone].index:
                    row = [0.0] * len(coco_labels)
                    row[coco_labels.index(obj)] = float(confi)
                    new_row_df = pd.DataFrame([row], columns=coco_labels, index=[timestamp])
                    det_confidence[zone] = pd.concat([det_confidence[zone], new_row_df])
                else:
                    det_confidence[zone].at[timestamp, obj] = float(confi)

    pprint(det_confidence)

    return object_frequency, zone_distribution, high_priority_objects, det_confidence


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
    occurence = list(stats.values())
    plt.bar(objects, occurence)
    plt.title(title)
    plt.xlabel('Objects')
    plt.ylabel('Occurrence')
    plt.savefig('_'.join(title.split())+'.pdf', dpi=720)
    plt.close()


def generate_heatmaps(confi_dict: dict, bootstrap_num: int = 10000) -> None:
    """ Generate heatmaps with bootstrapping

    Args:
        confi_dict: dictionary with each key to be robot id and value to be Pandas DataFrame
        bootstrap_num: how many samples to be bootstrapped
    """
    for zone in confi_dict.keys():
        df = confi_dict[zone]
        pprint(df)
        bootstrapped_df = df.sample(
            bootstrap_num, 
            replace=True
        ).reset_index(drop=True)
        pprint(bootstrapped_df)
        print(bootstrapped_df.dtypes)

        # Heatmap
        plt.figure(figsize=(30, 30))
        sns.heatmap(bootstrapped_df, annot=True)
        plt.savefig(f"heatmap_{zone}.pdf", dpi=720)


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
        object_frequency, zone_distribution, high_priority_objects, det_confidence = process_response(response_data)

        # Step 4: Generate insights and print the results
        generate_insights(object_frequency, zone_distribution, high_priority_objects)

        visualize(object_frequency)
        for zone, stats in zone_distribution.items():
            visualize(stats, f'Object distribution for zone: {zone}')

        # Generate heatmap with bootstrapping
        generate_heatmaps(det_confidence)
    else:
        print('No response from metadata service')

    print(f'{time.perf_counter()-start_time}s elapsed')


if __name__ == "__main__":
    main()

