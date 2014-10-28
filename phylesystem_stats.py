import requests
import json
import csv
import time
import timeit
import os.path
import sys
import argparse

'''
Basic script to retreive a count of OTUs from all studies in phylesystem and all studies in synthesis.
In Short:
Grabs the files via API
Parses the adding OTUS to lists
Keeps a unique set
Counts and returns those values in JSON file
Peter E. Midford 2014, derived from code by Lyndon Coghill
'''


def _decode_list(data): # used for parsing out unicode
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv

def _decode_dict(data): # used to parse out unicode
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv


def load_old_results_json(in_name):
    if os.path.isfile(in_name):
        with open(in_name, 'r') as jsonfile:
            return json.load(jsonfile, object_hook=_decode_dict)
    else:
        return {}


date_format = '%Y-%m-%dT%HZ'
def save_results_to_json(outname, new_result, results):
    datestamp = time.strftime(date_format)
    results[datestamp] = new_result
    with open(outname, 'w') as jsonfile:
        json.dump(results, jsonfile)


def parse_synth_study_ids(synthesis_list):
    synth_study_list = [] # parses the return from getSynthesisSourceList
    for s in synthesis_list['study_list']:  
        id = s['study_id']
        if 'taxonomy' not in id:  # exclude 'taxonomy'
            prefix = id.split("_")[0]
            if prefix not in ["ot", "pg"]:
                id = "pg_" + str(id)
            synth_study_list.append(id)

    return synth_study_list

def get_study_list(api_url):
    study_list = []
    url = "%s/studies/find_studies" %api_url
    headers = {'content-type': 'application/json'}
    response = requests.post(url, headers=headers)
    studies = json.loads(response.text, object_hook=_decode_dict)
    for o in studies['matched_studies']:
        study_list.append(o['ot:studyId'])
    return study_list


def get_synth_study_list(api_url):
    url = "%s/tree_of_life/about" % api_url
    synth_response = requests.post(url,
                                   headers={'content-type': 'application/json'},
                                   params={'study_list': 'true'})
    synthesis_list = json.loads(synth_response.text, object_hook=_decode_dict)
    return parse_synth_study_ids(synthesis_list) 


def load_study_json(study, study_api_url):
    url = '%s%s/' %(study_api_url, study)
    response = requests.get(url)
    return json.loads(response.text, object_hook=_decode_dict)
    

def get_remote_otus(json_data): # grabs the json of each study via the OpenTree API and parses the JSON for the OTU ids
    otus = []
    for otu in json_data['data']['nexml']['otus']['otu']:
        otus.append(otu['@id'])

    return otus
    

def _is_nominated(json_data):
    annotations = json_data['data']['nexml']['meta']
    validated = True  #_is_validated(annotations)
    for_synthesis = _is_for_synthesis(annotations)
    return validated and for_synthesis


def _is_validated(study_annotations):
    for ann in study_annotations:
        if '@property' in ann:
            if ann['@property'] == 'ot:annotationEvents':
                events = ann['annotation']
                for event in events:
                    if event['@id'] == 'peyotl-validator-event':
                        return event['@passedChecks']
    return False


def _is_for_synthesis(study_annotations):
    for ann in study_annotations:
        if '@property' in ann:
            if ann['@property'] == 'ot:notIntendedForSynthesis':
                val = ann['$']
                print "val in for_synthesis is {0}".format(repr(val))
                if val is True:
                    return False
    return True


default_output = 'phylesystem_stats.json'
def getargs():
    """reads command-line arguments"""

    filename = default_output
    server = 'http://api.opentreeoflife.org/'
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', 
                        help="specifies server to query as http URI")
    parser.add_argument('-f',
                        '--filename',
                        help="file with json object to receive results object")
    args = parser.parse_args()
    if args.filename:
        filename = args.filename
    if args.server:
        server = args.server
    return server, filename




def process():
    ''' 
    Generalized API locations in case they change in the future. 
    Though the functions may require minor tweaks if there are changes
    '''

    server, filename = getargs()

    api_url = server + 'v2/'
    # 'http://api.opentreeoflife.org/treemachine/v1/getSynthesisSourceList' # point where needed
    study_list_url = 'http://api.opentreeoflife.org/phylesystem/v1/study_list' # point where needed
    study_api_url = 'http://api.opentreeoflife.org/phylesystem/v1/study/' # point where needed, but see get_remote_otus


    
    

    old_data = load_old_results_json(filename)

    start_time = timeit.default_timer() # used to calc run time

    ''' Get list of all studies and just those in synthesis, and process for otus '''

    study_list = get_study_list(api_url)  # all studies

    
    synth_nominated_list = []
    all_unique_otus = []
    all_synth_otus = []
    all_otus = []
    unique_synth_otus = []
    all_nominated_otus = []
    unique_nominated_otus = []
    count = 1
    for s in study_list:
        print "Loading study {0}, {1} / {2}".format(str(s), count, len(study_list))
        json_study = load_study_json(s, study_api_url)
        otus = get_remote_otus(json_study)
        if _is_nominated(json_study):
            synth_nominated_list.append(s)
        for o in otus:
            all_otus.append(o)
        if s in synth_nominated_list:
            for o in otus:
                all_nominated_otus.append(o)
        count += 1

    all_unique_otus = set(all_otus) # keep only unique values in all otus
    total_otus = len(all_otus) 
    unique_synth_otus = set(all_synth_otus) # keep only unique values in synth otus
    unique_nominated_otus = set(all_nominated_otus)


    # process it all, and save it to to a json file
    stop_time = timeit.default_timer()
    run_time = stop_time - start_time


    results = {}
    results['Unique OTUs'] = len(all_unique_otus)
    results['Total OTUs'] = total_otus
    results['Total Studies'] = len(study_list)
    results['Studies nominated for Synthesis'] = len(synth_nominated_list)
    results['OTUs in nominated studies'] = len(all_nominated_otus)
    results['Unique OTUs in nominated studies'] = len(unique_nominated_otus)
    results['Run Time (seconds)'] = run_time

    save_results_to_json(filename, results, old_data)


if __name__ == "__main__":
    process()
