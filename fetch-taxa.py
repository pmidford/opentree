import requests
import json
import sys, getopt

''' 
Get a list of taxa for two studies that are in synthesis
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

def main(argv):
   tree1 = ''
   tree2 = ''
   outstyle = ''
   outformat = ''
   outfile = ''

   try:
      opts, args = getopt.getopt(argv,"h1:2:s:f:o:",["tree1=","tree2="])
   except getopt.GetoptError:
      print 'fetch-taxa.py -1 <tree1> -2 <tree2> -s <all/unique> -f <text/json> -o <output filename>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'fetch-taxa.py -1 <tree1> -2 <tree2> -s <all/unique> -f <text/json> -o <output filename>'
         sys.exit()
      elif opt in ("-1", "--tree1"):
         tree1 = arg
      elif opt in ("-2", "--tree2"):
         tree2 = arg
      elif opt in ("-s", "--outstyle"):
         outstyle = arg
      elif opt in ("-f", "--outformat"):
         outformat = arg
      elif opt in ("-o", "--outfile"):
         outfile = arg

   return tree1, tree2, outstyle, outformat, outfile 

def get_study_otus(study, source):

    url = study_fetch_url + source + "_" + study + "/otus"
    response = requests.get(url)
    study_json = json.loads(response.text, object_hook=_decode_dict)

    return study_json


def get_taxa(tree_study, tree_id, study_otus, tree_study_source):

    tree_taxa = []
    if tree_study_source == "pg": 
         otu_label = "otus" + tree_study
         for otu in study_otus[otu_label]['otuById']:
            if study_otus[otu_label]['otuById'][otu].has_key('^ot:ottTaxonName'):
                tree_taxa.append(study_otus[otu_label]['otuById'][otu]['^ot:ottTaxonName'])

    elif tree_study_source == "ot":
         otu_label = "otus" + tree_id[4:]
         for otu in study_otus[otu_label]['otuById']:
            if study_otus[otu_label]['otuById'][otu].has_key('^ot:ottTaxonName'):
                tree_taxa.append(study_otus[otu_label]['otuById'][otu]['^ot:ottTaxonName'])   


    return tree_taxa

def print_taxa_list (tree1_taxa, tree2_taxa, target1, target2, outstyle):

    print "#"*25
    print "Results"
    print "#"*25
    print "Tree 1: %s" %target1
    print "Tree 2: %s" %target2
    print "Out Style: %s" %outstyle
    
    print "\n"
    print "#"*25
    print "Tree 1 Taxa"
    print "#"*25
    for t in tree1_taxa:
        print t
   
    print "\n" 
    print "#"*25
    print "Tree 2 Taxa"
    print "#"*25
    for t in tree2_taxa:
        print t

    

study_fetch_url = 'http://api.opentreeoflife.org/v2/study/' # point where needed

if __name__ == "__main__":
    
    target1, target2, outstyle, outformat, outfile = main(sys.argv[1:])
    tree1_study_source = target1.split("_")[0]
    tree2_study_source = target2.split("_")[0]
    tree1_study =  target1.split("_")[1]
    tree2_study = target2.split("_")[1]
    tree1 = "tree" + target1.split("_")[2]
    tree2 = "tree" + target2.split("_")[2]


    study1_otus = get_study_otus(tree1_study, tree1_study_source)
    study2_otus = get_study_otus(tree2_study, tree2_study_source)

    tree1_taxa = get_taxa(tree1_study, tree1, study1_otus, tree1_study_source)
    tree2_taxa = get_taxa(tree2_study, tree2, study2_otus, tree2_study_source)


    if outfile == '':
        if outstyle == 'all':
            if outformat == 'text':
                print_taxa_list(tree1_taxa, tree2_taxa, target1, target2, outstyle)
            elif outformat == 'json':
                print_taxa_json(tree1_taxa, tree2_taxa, target1, target2, outstyle)
        elif outstyle == 'unique':
            if outformat == 'text':
                print_taxa_list(set(tree1_taxa), set(tree2_taxa), target1, target2, outstyle)
            elif outformat == 'json':
                print_taxa_json(set(tree1_taxa), set(tree2_taxa), target1, target2, outstyle)

    else:

        f = open(outfile, 'w')
        f.write("Tree 1: %s\n" %target1) 
        f.write("Tree 2: %s\n" %target2)
        f.write("Output Style: %s\n" %outstyle)
        f.write("### Tree 1 Taxa ###\n")
        
        for taxa in tree1_taxa:
            f.write("%s\n" % taxa)

        f.write("### Tree 2 Taxa ###\n")

        for taxa in tree2_taxa:
            f.write("%s\n" %taxa)
