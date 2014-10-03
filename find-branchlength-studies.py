import json
import requests
import sys, argparse

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
            study_list.append(s['study_id'])
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


def find_branchlengths(tree, t):
    branch_lengths = False
    tree_json = tree[t]
    branch_length_keys = ['^ot:branchLengthDescription', 
                          '^ot:branchLengthTimeUnit', 
                          '^ot:branchLengthMode']
    description = []
    for x in branch_length_keys:
        value = tree_json.get(x)
        if value is not None and value is not '':
            branch_lengths = True
            if branch_length_keys.index(x) is 0:
                description.append(tree_json['^ot:branchLengthDescription'])
            elif branch_length_keys.index(x) is 1:
                description.append(tree_json['^ot:branchLengthTimeUnit'])
            elif branch_length_keys.index(x) is 2:
                description.append(tree_json['^ot:branchLengthMode'])

    return branch_lengths, description


default_output = 'branch_length_studies.tsv'
def getargs(argv):
    """reads command-line arguments"""

    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--filter', 
                        help="<all | accepted | used> - which studies are reviewed")
    parser.add_argument('-r', '--format', help="<csv | json> - output format")
    parser.add_argument('-o', '--outname', help="name of file for output")
    args = parser.parse_args()

    filter = args.filter
    format = args.format
    outname = args.outname

    return filter, format, outname
            
            
api_url = 'http://api.opentreeoflife.org/v2/'
study_url = 'http://api.opentreeoflife.org/v2/study/'

if __name__ == "__main__":

    print "Processing: %s" % sys.argv[1:]
    filter, format, outname= getargs(sys.argv[1:])
    print "Got filter: %s, format: %s, outname: %s" % (filter, format, outname)

    if filter.lower() == 'used':
        print "Test list of studies supporting synthetic tree"
        study_list =  get_synthetic_tree_support_study_list(api_url)
    elif filter.lower() == 'accepted':
        print "Test list of studies accepted by checker"
        study_list = get_study_list(api_url,accepted=True)
    else:
        print "Getting list of all studies"
        study_list = get_study_list(api_url,accepted=False)
    print "...complete"


    results = []
    if outname is None:
        handle = sys.stdout
    else:
        handle = open('branch_length_studies.tsv', 'a')
    print "Outname is %s" % repr(outname)
    print "Handle is %s" % str(handle)
    for s in study_list:
        study = s
        print "Checking study %s for branch lengths..." % study
        tree_ids = get_remote_tree_ids(study, study_url)
        branch_length_trees = []
        for t in tree_ids:
            tree = get_tree(t, study_url, study)
            branch_lengths, description = find_branchlengths(tree, t)
            if branch_lengths:
                branch_length_trees.append(t)
        if len(branch_length_trees) > 0:
            results.append({"study": s, "trees": branch_length_trees})
            
            # if len(branch_length_trees) > 1:
            #    tree_string = ",".join(branch_length_trees)
            # else:
            #    tree_string = branch_length_trees[0]
        #handle.write("".join([s, '\t', tree_string]) + '\n')

    if format.lower() == 'json':
        json.dump(results,handle)
    else:
        for item in results:
            if len(item['trees'])>1:
                tree_string = ",".join(item['trees'])
            else:
                tree_string = item['trees'][0]
            handle.write("".join([item['study'], '\t', tree_string]) + '\n')
        
    if handle != sys.stdout:
        handle.close()
