import subprocess
import sys
import os
import win32com.client
import time

outlook = None
nameAliasDict = {}
contacts = None
numEntries = None
file = None
mail_schema = "http://schemas.microsoft.com/mapi/proptag/0x800F101F"
alias_schema = "http://schemas.microsoft.com/mapi/proptag/0x3A00001F"
criticalCommit = False
svn_path ='https://svn.ali.global/gen7/mk7games/games/red_black_yellow/branches/'
temp_svn_path = None
lastRevision = None

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


#check if the last commit was critical or not
def isCriticalCommit():
    global criticalCommit, svn_path, temp_svn_path, lastRevision
    cmd = 'svn info > svn_log.txt'
    p = subprocess.Popen(cmd , shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, stderr = p.communicate()  
    for line in open('svn_log.txt'):
        if 'URL' in line:
            svn_path = line.split(' ')[1].strip()
            break
    temp_svn_path = svn_path
    svn_path = svn_path.split('branches')[0].strip()
    svn_path = svn_path + 'branches'

    lastRevision = getLastCommitRevision()
    while True:
        cmd = 'svn log '+svn_path+' -r '+lastRevision
        p = subprocess.Popen(cmd , shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, stderr = p.communicate()
        if 'No such revision' in output:
            print "Repository not synched yet, retrying in next 10 seconds..."
            time.sleep(10)
        elif 'Critical Commit' in output:
            criticalCommit = True
            break
        else:
            criticalCommit = False
            break
            

#get a substring between first and last
def find_between( s, first, last ):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start+1 )
        return s[start:end]
    except ValueError:
        return ""

#send a mail
def send_mail(branchname,recipient , manager):
    global outlook
    subject = "[IMPORTANT]Critical Check-in Information"
    body = "The branch " + branchname+" has got a critical issue checked in at revision: "+lastRevision+" , please have a look at the changes."
    mail = outlook.CreateItem(0)
    mail.To = recipient
    if manager != None :
        mail.CC  = manager
    mail.Subject = subject
    mail.Body = body
    print "Sending mail to the stakeholders"
    mail.Send()

def getMailId(contact) :
    prop_str = contact.PropertyAccessor.GetProperty(mail_schema)
    prop = str(prop_str).split(',')
    mail = find_between(prop[0],'\'','\'').split(':')[-1]
    return mail
    
#Get the global address list
def fillContactList():
    global contacts, nameAliasDict, file
    for i in contacts:
 #       name = i.Name
        prop_str_alias = i.PropertyAccessor.GetProperty(alias_schema)
        nameAliasDict[prop_str_alias.lower()] = i
        file.write(prop_str_alias.encode('utf-8').strip() + "\n")
    file.close()


def init():
    global outlook, contacts, numEntries, file
    outlook = win32com.client.gencache.EnsureDispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    file = open('mapping.txt', 'w')
    adrLi = ns.AddressLists.Item("Global Address List")
    contacts = adrLi.AddressEntries
    numEntries = adrLi.AddressEntries.Count

def getSvnLog():
    global temp_svn_path
    cmd = 'svn log -q '+svn_path+'> svn_log.txt'
    p = subprocess.Popen(cmd , shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, stderr = p.communicate()      
    authors = set()
    for line in open('svn_log.txt'):
        if 'r' in line:
            authors.add(line.split('|')[1].strip())
    author_mail = ""   
    manager_mail = ""    
    for author in sorted(authors):
        if author.lower() in nameAliasDict:
            author_mail = author_mail + ';' + getMailId(nameAliasDict[author.lower()])
            
            if nameAliasDict[author.lower()].Manager != None:
                manager_mail = manager_mail + ';' + getMailId(nameAliasDict[author.lower()].Manager)
    send_mail(temp_svn_path,"Anshul.Garg@ali.com.au", "Aman.Arora@ali.com.au;Anshul.Garg@ali.com.au")
    #send_mail(temp_svn_path,author_mail,manager_mail)

    
def removeFile():
    os.remove ('svn_log.txt')
    os.remove ('mapping.txt')


isCriticalCommit()
if criticalCommit == True:
    print "critical commit detected \n"
    init()
    fillContactList()
    getSvnLog()
removeFile()
