import requests
import simplejson as json
import csv
import time
import timeit
import os.path


'''
Basic script to retreive a count of OTUs from all studies in phylesystem and all studies in synthesis.
In Short:
Grabs the files via API
Parses the adding OTUS to lists
Keeps a unique set
Counts and returns those values in TSV file
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

def get_remote_otus(study, study_api_url): # grabs the json of each study via the OpenTree API and parses the JSON for the OTU ids
    url = '%s%s/' %(study_api_url, study)
    response = requests.get(url)
    json_data = json.loads(response.text, object_hook=_decode_dict)
    otus = []
    for otu in json_data['data']['nexml']['otus']['otu']:
        otus.append(otu['@id'])

    return otus

# saves the results to a tab-delimited tsv file
def save_otu_count(otu_count, study_count, run_time, total_otus, synth_study_count, unique_synth_otus, total_synth_otus):
    if os.path.isfile('otu-count.tsv'): # if the file exists, write results without header
        with open('otu-count.tsv', 'a') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter="\t")
            csvwriter.writerow([time.strftime("%x")] + [otu_count] + [total_otus] + [study_count] + [unique_synth_otus] + [total_synth_otus] + [synth_study_count] + [run_time])
    else:
        with open('otu-count.tsv', 'w+') as csvfile: # if the file doesn't exist, write the header, then the results
            csvwriter = csv.writer(csvfile, delimiter="\t")
            csvwriter.writerow(['Date'] + ['Unique OTUs'] + ['Total OTUs'] + ['Total Studies'] + ['Unique OTUs in Synthesis'] + ['Total OTUs in Synthesis'] + ['Studies in Synthesis'] + ['Run Time (seconds)'])
            csvwriter.writerow([time.strftime("%x")] + [otu_count] + [total_otus] + [study_count] + [unique_synth_otus] + [total_synth_otus] + [synth_study_count] + [run_time])

def parse_synth_study_ids(synthesis_list): # works now, but will need revision once API stabilizes how naming is done. 
    # see issue 99 on tree machine
    synth_study_list = [] # parses the return from getSynthesisSourceList, exlcuding 'taxonomy'
    for s in synthesis_list:
        if 'taxonomy' not in s:
            id = s.split("_")[0]
            if "ot" or "pg" not in id:
                id = "pg_" + str(id)
        synth_study_list.append(id)

    return synth_study_list



if __name__ == "__main__":
   
''' 
    Generalized API locations in case they change in the future. 
    Though the functions may require minor tweaks if there are changes
'''
    synth_list_url = 'http://api.opentreeoflife.org/treemachine/v1/getSynthesisSourceList' # point where needed
    study_list_url = 'http://devapi.opentreeoflife.org/phylesystem/v1/study_list' # point where needed
    study_api_url = 'http://devapi.opentreeoflife.org/api/v1/study/' # point where needed, but see get_remote_otus



    
    start_time = timeit.default_timer() # used to calc run time

    ''' Get list of all studies and just those in synthesis, and process for otus '''

    synth_response = requests.post(synth_list_url)
    synthesis_list = json.loads(synth_response.text, object_hook=_decode_dict)
    synth_study_list = parse_synth_study_ids(synthesis_list) 
    study_response = requests.get(study_list_url)
    study_list = json.loads(study_response.text)
    all_otus = []
    all_unique_otus = []
    all_synth_otus = []
    unique_synth_otus = []
    count = 1
    for s in study_list:
        print "Getting OTUS for study %s, %s / %s..." %(s, count, len(study_list)) # tracker for testing purposes
        otus = get_remote_otus(s, study_api_url)
        for o in otus:
            all_otus.append(o)
        if s in synth_study_list:
            for o in otus:
                all_synth_otus.append(o)
        count += 1
     
    all_unique_otus = set(all_otus) # keep only unique values in all otus
    total_otus = len(all_otus) 
    unique_synth_otus = set(all_synth_otus) # keep only unique values in synth otus
    total_synth_otus = len(all_synth_otus)
 
    ## process it all, and save it to to a tsv file
    stop_time = timeit.default_timer()
    run_time = stop_time - start_time
    save_otu_count(str(len(all_unique_otus)), str(len(study_list)), str(run_time), str(total_otus), str(len(synth_study_list)), str(len(unique_synth_otus)), str(total_synth_otus))
