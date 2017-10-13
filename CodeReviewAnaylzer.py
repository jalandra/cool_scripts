import subprocess
import sys
import os
import time
import re

outlook = None
nameAliasDict = {}
contacts = None
numEntries = None
file = None
mail_schema = "http://schemas.microsoft.com/mapi/proptag/0x800F101F"
alias_schema = "http://schemas.microsoft.com/mapi/proptag/0x3A00001F"
criticalCommit = False
svn_path = ''
temp_svn_path = None
lastRevision = None
repository_root = ''
base = None
current = None

#get a substring between first and last
def find_between( s, first, last ):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start+1 )
        return s[start:end]
    except ValueError:
        return ""

#get the list of branches associated directly of indirectly with the current one
def getAllBaseBranches():
    base_branches_list = set()
    valid = re.compile(r"\.(c|h|cpp|avl)+")
    for line in open('svn_log.txt'):
        #print line
        if '(from ' in line:
            #print line
            if valid.search(line,re.I) is not None:
                continue
            branch = find_between(line.strip(),'(from ',')')
            if 'branches' in branch:
                base_branches_list.add(branch.strip().split('branches')[0])
            elif 'trunk' in branch:
                base_branches_list.add(branch.strip().split('trunk')[0])
            elif 'tags' in branch:
                base_branches_list.add(branch.strip().split('tags')[0])

    base_branches_list_comb = set()
    for entry in base_branches_list:
        base_branches_list_comb.add(str(repository_root) + str(entry) + 'branches/')
        base_branches_list_comb.add(str(repository_root) + str(entry) + 'tags/')
        base_branches_list_comb.add(str(repository_root) + str(entry) + 'trunk/')

    #print base_branches_list_comb
    return base_branches_list_comb

#get the svn revision number for the critical fix, all svn logs are written here
def getLastCommitRevision():
    svn_revision_file = os.path.expanduser('~/AppData/Local/TortoiseSVN/logfile.txt')
    revision_num_generated = False
    revision_list = []
    for line in open(svn_revision_file):
        if revision_num_generated:
            if 'At revision' in line:
                revision_num = line.split(':')[-1]
                revision_list.append(revision_num.strip())
                revision_num_generated = False
        if 'Committing transaction' in line:
            revision_num_generated = True
    #print revision_list
    return revision_list[-1]
    
#Get the global address list
def fillContactList():
    global contacts, nameAliasDict, file
    for i in contacts:
 #       name = i.Name
        prop_str_alias = i.PropertyAccessor.GetProperty(alias_schema)
        nameAliasDict[prop_str_alias.lower()] = i
        file.write(prop_str_alias.encode('utf-8').strip() + "\n")
    file.close()

def getSvnDiff():
    global base, current
    cmd = 'svn diff '+base+' '+current+'> svn_log.txt'
    p = subprocess.Popen(cmd , shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, stderr = p.communicate()      
        #get All the base branches, i.e. branches from which current branch has been copied
    for line in open('svn_log.txt'):
        print line
    exit(0)
    
def removeFile():
    os.remove ('svn_log.txt')

def GetInputs():
    global base,current
    base = raw_input("Please provide the Base tag:\n")
    current = raw_input("Please provide the Current tag:\n")


def main():
    GetInputs()
    getSvnDiff()
    #removeFile()

if __name__ == '__main__':
    main()