import random
import argparse
import os
import cv2
import time
import logging

from SPARQLWrapper import SPARQLWrapper, JSON


logger = logging.getLogger(__name__)


def run(
    endpoint: str, 
    save_folder: str, 
    repeat: int = 1, 
    save: bool = True,
    test: bool = False,
):
    """ Run workload based on semantified results on Fuseki
        
    Parameters:
        endpoint: SPARQL endpoint to run query
        save_folder: Where to save the annotated files with detected people
        repeat: Repeat how many times for generating the workload with current data
        save: save the processed results or not
    """
    if test:
        logger.info('running in test mode...')
        image = cv2.imread('test.jpg')
        
        for _ in range(repeat):
            for box in range(random.randint(1, 5)):
                # Draw bounding box
                start_x, start_y = random.randint(0, image.shape[0]), random.randint(0, image.shape[1])
                end_x = start_x + random.randint(0, image.shape[0] - start_x)
                end_y = start_y + random.randint(0, image.shape[1] - start_y)
                new_img = cv2.rectangle(
                    image, 
                    (start_x, start_y),
                    (end_x, end_y),
                    (0, 255, 0),
                    5
                )
                if save:
                    # Save into separate folder
                    cv2.imwrite(
                        'output.png', new_img
                    ) 
        
    else:
        sparql = SPARQLWrapper(endpoint)
        sparql.setReturnFormat(JSON)
        ## Query frames inserted into Fuseki
        sparql.setQuery("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX glc: <https://glaciation-project.eu/reference_model#>

            SELECT *
            WHERE {
            ?frame rdf:type glc:YOLOResult .
            ?frame glc:fileLocation ?loc .
            ?frame glc:hasDetection ?detection .
            ?detection glc:hasLabel ?label;
              		   glc:hasConfidence ?conf .
            ?detection glc:hasBBox ?bbox .
            ?bbox glc:hasX ?x;
                  glc:hasY ?y;
                  glc:hasWidth ?w;
                  glc:hasHeight ?h .
            }
        """)

        try: 
            for i in range(repeat):
                print(f'{i}-th repeat')
                res = sparql.queryAndConvert()
                for r in res['results']['bindings']:
                    # Get UUID
                    uuid = r['frame']['value'].split('#')[1]
                    # Get label
                    label = r['label']['value']
                    #if label == 'person':
                    # Get image location
                    file_loc = os.path.join(r['loc']['value'], uuid)
                    image = cv2.imread(file_loc)
                    # Draw bounding box
                    new_img = cv2.rectangle(
                        image, 
                        (int(r['x']['value']), int(r['y']['value'])),
                        (int(r['x']['value'])+int(r['w']['value']), int(r['y']['value'])+int(r['h']['value'])),
                        (0, 255, 0),
                        5
                    )
                    if save:
                        # Save into separate folder
                        cv2.imwrite(
                            os.path.join(save_folder, uuid+'.png'), new_img
                        ) 
        except Exception as e:
            print(e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--endpoint', default='http://10.244.0.37:3030/ds/query')
    parser.add_argument('-d', '--destination', default='/home/ubuntu/UC/data/results')
    parser.add_argument('-r', '--repeat', type=int, default=100)
    parser.add_argument('-s', '--save', action='store_true')
    parser.add_argument('-t', '--test', action='store_true')
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)

    start_time = time.perf_counter()

    ## Workload
    run(
        args.endpoint,
        args.destination,
        args.repeat,
        args.save,
        args.test
    )

    end_time = time.perf_counter()

    print(f'{end_time - start_time} seconds elapsed')

