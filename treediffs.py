import requests
import json
import sys, argparse

# need some library - this is one of many choices
import dendropy

# for each study tree
# find root or focal clade
# request subtree of synthetic tree
# for each tip taxon of study (syn) tree
#   find mrca to root
#   find mrca in other tree
#   compare paths and capture first incongruity
#     - what about multiple incongruities?  
#        *will they be picked up
#        *or some sort of tail matching
#   maintain set of incongruities (class?)
#   


# tree access

api_url = 'http://api.opentreeoflife.org/v2/'
study_url = 'http://api.opentreeoflife.org/v2/study/'


def get_study_list(api_url,accepted):
    study_list = []
    url = "%s/studies/find_studies" %api_url
    headers = {'content-type': 'application/json'}
    response = requests.post(url, headers=headers)
    studies = json.loads(response.text, object_hook=_decode_dict)
    for o in studies['matched_studies']:
        if accepted is False:
            study_list.append(o['ot:studyId'])
        else:
            study_list.append(o['ot:studyId'])
    return study_list


def get_synthetic_tree_support_study_list(api_url):
    study_list = []
    url = "%s/tree_of_life/about" % api_url
    headers = {'content-type': 'application/json'}
    params = {'study_list': 'true'}
    response = requests.post(url, headers=headers, params=params)
    json_data = json.loads(response.text, object_hook=_decode_dict)
    studies = json_data['study_list']
    for s in studies:
        print s
        if (s['study_id'] != 'taxonomy'):
            study_list.append(s)
    return study_list


def get_remote_tree_ids(study, study_url):
    """returns list of tree ids in study specified by study"""
    url = '%s%s/' % (study_url, study)
    response = requests.get(url)
    json_data = json.loads(response.text, object_hook=_decode_dict)
    trees = []
    for t in json_data['data']['nexml']['trees']['tree']:
        trees.append(t['@id'])

    return trees


def get_tree(tid, study_url, study):
    """returns json version of tree specified by study and tid (tree id)"""
    url = '%s%s/tree/%s' % (study_url, study, tid)
    response = requests.get(url)
    json_data = json.loads(response.text, object_hook=_decode_dict)


    return json_data


study_tree_newick_api = "http://api.opentreeoflife.org/v2/study"
# source_tree"

def _get_remote_tree_newick(tree_spec):
    """ """
    print "Will request %s" % tree_spec
    url = "%s/%s/tree/tree%s.tre" % (study_tree_newick_api,tree_spec['study_id'],tree_spec['tree_id'])
    response = requests.get(url)
    print "url was %s" % response.url
    newick = response.text
    return newick

# Utils

def _decode_list(data):  # used for parsing out unicode
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


def _decode_dict(data):  # used to parse out unicode
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

def _getargs(argv):
    """reads command-line arguments"""

    # defaults
    filter = 'used'
    format = 'json'
    outname = 'diffs.json'

    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--filter', 
                        help="<all | accepted | used> - which trees are reviewed")
    parser.add_argument('-r', '--format', help="<csv | json> - output format")
    parser.add_argument('-o', '--outname', help="name of file for output")
    args = parser.parse_args()

    if args.filter:
        filter = args.filter
    if args.format:
        format = args.format
    if args.outname:
        outname = args.outname

    return filter, format, outname

if __name__ == "__main__":
    
    print "Processing: %s" % sys.argv[1:]
    filter, format, outname= _getargs(sys.argv[1:])
    print "Got filter: %s, format: %s, outname: %s" % (filter, format, outname)

    tree_list = None
    study_list = None
    if filter.lower() == 'used':
        print "Test list of trees supporting synthetic tree"
        tree_list =  get_synthetic_tree_support_study_list(api_url)
    elif filter.lower() == 'accepted':
        print "Test list of studies accepted by checker"
        study_list = get_study_list(api_url,accepted=True)
    else:
        print "Getting list of all studies"
        study_list = get_study_list(api_url,accepted=False)
    print "...complete"

    if study_list:
        for s in study_list:
            pass
    else:
        for t in tree_list:
            newick_tree = _get_remote_tree_newick(t)
            study_tree = None
            try:
                study_tree = dendropy.Tree.get_from_string(newick_tree, schema="newick")
            except Exception as e:
                print "Parsing error: ", e
            if study_tree:
                my_seed = study_tree.seed_node
                print "root is %s" % str(my_seed.oid)

