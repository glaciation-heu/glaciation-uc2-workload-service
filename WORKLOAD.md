# Description
* This UC2 workload built upon the collected dataset described below
* The collected dataset has been ingested into the GLACIATION platform via the [semantification component](https://github.com/glaciation-heu/glaciation-semantification-service)
* The workload is configured as a cronjob to run periodically in which it queries the ingested dataset from DKG via the [metadata service](https://github.com/glaciation-heu/glaciation-metadata-service)

## Dataset
* The dataset contains YOLO (a computer vision model) results containing detected objects run on snapshots of video stream captured by a camera attached to robots
* A subset of data can be found in DELL UC [repo](https://github.com/glaciation-heu/DELL-UC/tree/main/datasets) while the full data is stored in XR12 of the validation cluster
* The data can be sent to the semantification component of the GLACIATION platfrom from XR12.
* Check ```~/DELL-UC/datasets$ python send_data.py --help``` for more details

## Workload
* The workload aims to analyze the object distribution of detected objects overall, across different robots (or zones), and regarding high priority objects (e.g., human)
* To this end, it queries DKG to retrieve the ingested and semantified UC2 data, and runs a script to analyze the distributions
* At the end, it generates a heatmap of each distribution as PDF files

## Schedule
* Cronjob is configured to run every 15 min as specified in the [cronjob YAML file](https://github.com/glaciation-heu/glaciation-uc2-workload-service/blob/main/server/charts/server/templates/cronjob.yaml)
* Currently each run takes less than 500 seconds (varies by different clusters)
