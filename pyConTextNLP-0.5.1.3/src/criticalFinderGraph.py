#!/usr/bin/env python
#-*-coding: utf-8 -*- 
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

#Adapted by Danielle Mowery from pyConTextNLP originally written by Brian Chapman

"""criticalFinderGraph is a program that processes the impression section of dictated
radiology reports. pyContext is used to look for descriptions of acute critical
fidnings.

At this state, the program assumes that the reports are stored in a SQLite3 database.
The database should have a table named 'reports' with a field named 'impression'
although these values can be specified through the command line options."""
import sys

import os
from optparse import OptionParser
import sqlite3 as sqlite
import networkx as nx
import datetime, time
import pyConTextNLP.pyConTextGraph as pyConText
import pyConTextNLP.helpers as helpers
import pyConTextNLP.itemData as itemData
import pyConTextNLP.html as html
import cPickle
import getpass
import xml.dom.minidom as minidom
import codecs

#from graphviz import *
"""helper functions to compute final classification"""

class criticalFinder(object):
    """This is the class definition that will contain the majority of processing
    algorithms for criticalFinder.
    
    The constructor takes as an argument the name of an SQLite database containing
    the relevant information.
    """
    def __init__(self, options):#dbname, outfile, save_dir, table, idcolumn, txtcolumn, doGraphs):
        """create an instance of a criticalFinder object associated with the SQLite
        database.
        dbname: name of SQLite database
        """

        # Define queries to select data from the SQLite database
        # this gets the reports we will process
        self.query1 = '''SELECT %s,%s,%s FROM %s'''%(options.id,options.report_text,options.reportType, options.table)
        
        #print options.table;raw_input()
        t = time.localtime()
        self.save_dir = options.save_dir#+"-%s-%s-%s"%(t[0],t[1],t[2])
        self.html_dir=options.html_dir
        tmp = self.save_dir[:]
        count = 1
        while( os.path.exists(tmp) ):
            tmp = self.save_dir+"-%d"%count
            count += 1
        self.save_dir = tmp
        if( not os.path.exists(self.save_dir) ):
            os.mkdir(self.save_dir)
  
        print options.dbname
        self.doGraphs = options.doGraphs
        self.allow_uncertainty = options.allow_uncertainty
        self.proc_category = options.category
        self.conn = sqlite.connect(os.getcwd()+options.dbname+".db")
        print os.getcwd()+options.dbname+".db"
        self.cursor = self.conn.cursor()
        print self.query1
        self.cursor.execute(self.query1)
        self.reports = self.cursor.fetchall()

        
        print "number of reports to process",len(self.reports)


        tmp = os.path.splitext(options.odbname)
        outfile = tmp[0]+self.proc_category+"%s.db"%(self.allow_uncertainty)
        rsltsDB = os.path.join(self.save_dir,outfile)
        if( os.path.exists(rsltsDB) ):
            os.remove(rsltsDB)
            
        tmp = os.path.splitext(options.adbname)
        outfile = tmp[0]+self.proc_category+"%s.db"%(self.allow_uncertainty)
        rsltsOtherDB = os.path.join(self.save_dir,outfile)

            
        
        #old database output by DM
        self.resultsConn = sqlite.connect(rsltsDB)
        self.resultsCursor = self.resultsConn.cursor()

#         
        self.resultsCursor.execute("""CREATE TABLE alerts (
            reportid TEXT,
            rptType TEXT,
            alert INT,
            report TEXT)""")
        
        self.resultsConnOther = sqlite.connect(rsltsOtherDB)
        self.resultsCursorOther = self.resultsConnOther.cursor()

#         
        self.resultsCursorOther.execute("""CREATE TABLE alerts (
            reportid TEXT,
            rptType TEXT,
            alert INT,
            report TEXT)""")


        # Create the itemData object to store the modifiers for the  analysis
        # starts with definitions defined in pyConText and then adds
        # definitions specific for peFinder
        
        #DM - addition
        self.context=pyConText.ConTextDocument()
        mods=itemData.instantiateFromCSV(os.getcwd()+options.lexical_kb)
        trgs=itemData.instantiateFromCSV(os.getcwd()+options.carotid_kb)
        
        self.modifiers = itemData.itemData()
        for mod in mods.keys():
            self.modifiers.prepend(mods[mod])
        #print self.modifiers;raw_input()    
        self.targets = itemData.itemData()
        for trg in trgs.keys():
            self.targets.prepend(trgs[trg])

        
        
    def initializeOutput(self, rfile, lfile, dfile): 
        self.outString = u"""<?xml version="1.0"?>\n"""
        self.outString += u"""<markup>\n""" 
        #self.outString += u"""<pyConTextNLPVersion> %s </pyConTextNLPVersion>\n"""%pyConTextNLP.__version__
        self.outString += u"""<operator> %s </operator>\n"""%getpass.getuser()
        self.outString += u"""<date> %s </date>\n"""%time.ctime()
        self.outString += u"""<dataFile> %s </dataFile>\n"""%rfile
        self.outString += u"""<lexicalFile> %s </lexicalFile>\n""" %lfile
        self.outString += u"""<domainFile> %s </domainFile>\n""" %dfile  
        
    def closeOutput(self):
        self.outString +=u"""</markup>\n"""
        
    def getOutput(self):
        return self.outString
 

    def analyzeReport(self, idName,report, modFilters = ['indication','pseudoneg','probable_negated_existence',
                          'definite_negated_existence', 'probable_existence',
                          'definite_existence', 'historical', 'carotid_critical', 'carotid_noncritical', 'right_sidedness', 'left_sidedness',
                          'bilateral_sidedness', 'sidedness', 'common_carotid_neurovascularanatomy', 'bulb_carotid_neurovascularanatomy',
                          'internal_carotid_neurovascularanatomy']
        ):
        """given an individual radiology report, creates a pyConTextSql
        object that contains the context markup

        report: a text string containing the radiology reports
        mode: which of the pyConText objects are we using: disease
        modFilters: """
        self.context = pyConText.ConTextDocument()
        targets=self.targets
        modifiers = self.modifiers
        if modFilters == None :
           modFilters = ['indication','pseudoneg','probable_negated_existence',
                          'definite_negated_existence', 'probable_existence',
                          'definite_existence', 'historical', 'carotid_critical', 'carotid_noncritical', 'right_sidedness', 'left_sidedness',
                          'bilateral_sidedness', 'sidedness', 'bulb_carotid_neurovascularanatomy','common_carotid_neurovascularanatomy', 'internal_carotid_neurovascularanatomy', ]

        splitter = helpers.sentenceSplitter()
        sentences = splitter.splitSentences(report)
        count = 0
        print idName
        
        for s in sentences:
            markup=pyConText.ConTextMarkup()
            markup.setRawText(s)
            markup.cleanText() 
            
            markup.markItems(modifiers, mode="modifier")
            markup.markItems(targets, mode="target")
            
            #markup.pruneMarks()
            #markup.dropMarks('Exclusion')
            markup.applyModifiers()
            #markup.pruneModifierRelationships()
            markup.dropInactiveModifiers()
            count += 1
            
            self.context.addMarkup(markup)
        idName, sevFlag, htmlStr = html.mark_document_with_html(idName,self.context)#;raw_input()
#         fo=open(self.html_dir+"\\%s.html"%idName, "w")
#         fo.write(htmlStr)
#         fo.close()
            
        self.outString+= self.context.getXML()+u"\n"
            
        print self.context.getXML()#;raw_input()
        
        return  idName, sevFlag,  htmlStr

            
    def classifyDocumentTargets(self):
        rslts = {}
        alerts = {}
        cntxt = self.context
        cntxt.computeDocumentGraph()
        g = cntxt.getDocumentGraph()
        targets = [n[0] for n in g.nodes(data = True) if n[1].get("category","") == 'target']

        
        if( not targets ):
            return alerts,rslts
        if(self.allow_uncertainty):
            pos_filters = ["definite_existence","probable_existence"]
        else:
            pos_filters = ["definite_existence"]
        for t in targets:
            mods = g.predecessors(t)
            rslts[t] = {}
            for t in targets:
                mods = g.predecessors(t)
                
                rslts[t] = {}
                if( not mods ): # an unmodified target is disease positive,certain, and acute
                    
                    rslts[t]['disease'] = 'Pos'
                    rslts[t]['uncertainty'] = 'No'
                    rslts[t]['uncertainty_value'] = "default"
                    rslts[t]['temporality'] = 'New'
                    rslts[t]['temporality_value'] = "default"
                    rslts[t]['severity'] = 'non-critical'
                    rslts[t]['severity_value'] = "default"
                    rslts[t]['neurovascularanatomy'] ='unspecified'
                    rslts[t]['neurovascularanatomy_value'] = "unspecified"
       
                    
                    
                else:
                    #re-wrote rule - not throwing positive
                    #print g.predecessors(t);raw_input()
                    if (modifies(g,t,pos_filters) and
                        not modifies(g,t,[#"definite_negated_existence",
                                          #"probable_negated_existence",
                                          "future","indication","pseudoneg"])):
                        rslts[t]['disease'] = 'Pos'
                        rslts[t]['uncertainty_value'] = "null"
                        
                    elif ( modifies(g,t,["definite_negated_existence",
                                          "probable_negated_existence",
                                          "future","indication","pseudoneg"])):
                        rslts[t]['disease'] = 'Neg'
                        rslts[t]['uncertainty_value'] = "default"
                    else:
                        rslts[t]['disease'] = 'Pos'
                        rslts[t]['uncertainty_value'] = "default"
                        #end of re-write
                    if( modifies(g,t,["probable_existence",
                                      "probable_negated_existence"]) ):
                        rslts[t]['uncertainty'] = 'Yes'
                        for m in mods:
                            if m.getCategory().lower()==('probable_existence' or "probable_negated_existence"):
                                rslts[t]['uncertainty_value'] = m.getPhrase()
                    else:
                        rslts[t]['uncertainty'] = 'No'
                        rslts[t]['uncertainty_value'] = "default"
                    if( modifies(g,t,["historical"]) ):
                        rslts[t]['temporality'] = 'Old'
                        for m in mods:
                            if m.getCategory().lower()=="historical":
                                rslts[t]['temporality_value'] = m.getPhrase()
                        
                    else:
                        if( rslts[t]['disease'] == 'Neg'):
                            rslts[t]['temporality'] = 'NA'
                            rslts[t]['temporality_value'] = "default"
                            
                            
                        else:
                            rslts[t]['temporality'] = 'New'
                            rslts[t]['temporality_value'] = "default"
                            
                if( modifies(g,t, ['internal_carotid_neurovascularanatomy']) ):
                    rslts[t]['neurovascularanatomy'] ='ICA'
                    
                    for m in mods:

                        if m.getCategory().lower()=='internal_carotid_neurovascularanatomy':
                            rslts[t]['neurovascularanatomy_value'] = m.getPhrase()
                    
                elif( modifies(g,t, ['common_carotid_neurovascularanatomy']) ):
                    rslts[t]['neurovascularanatomy'] ='CCA'
                    
                    for m in mods:

                        if m.getCategory().lower()=='common_carotid_neurovascularanatomy':
                            rslts[t]['neurovascularanatomy_value'] = m.getPhrase()
                
                elif( modifies(g,t, ['bulb_carotid_neurovascularanatomy']) ):
                    rslts[t]['neurovascularanatomy'] ='bulb'
                    
                    for m in mods:

                        if m.getCategory().lower()=='bulb_carotid_neurovascularanatomy':
                            rslts[t]['neurovascularanatomy_value'] = m.getPhrase()
                else:
                    rslts[t]['neurovascularanatomy'] ='unspecified' #default ICA causes too many FP
                    rslts[t]['neurovascularanatomy_value'] = "unspecified"
                    
                if( modifies(g,t, ['carotid_critical'])):
                    rslts[t]['severity'] ='critical'
                    for m in mods:
                        if m.getCategory().lower()=='carotid_critical':
                            
                            rslts[t]['severity_value'] = m.getPhrase()
                        
                elif( modifies(g,t, ['carotid_noncritical'])):
                    rslts[t]['severity'] ='non-critical'
                    for m in mods:
                        if m.getCategory().lower()=='carotid_noncritical':
                            rslts[t]['severity_value'] = m.getPhrase()
                    
                else:
                    rslts[t]['severity'] ='unspecified'
                    rslts[t]['severity_value'] = "unspecified"
                    
                if( modifies(g,t, ['left_sidedness'])):
                    rslts[t]['sidedness'] ='left'
                    for m in mods:
                        if m.getCategory().lower()=='left_sidedness':
                            rslts[t]['sidedness_value'] = m.getPhrase()
                    
                elif( modifies(g,t, ['right_sidedness'])):
                    rslts[t]['sidedness'] ='right'
                    for m in mods:
                        if m.getCategory().lower()=='right_sidedness':
                            rslts[t]['sidedness_value'] = m.getPhrase()
                        
                elif( modifies(g,t, ['bilateral_sidedness'])):
                    rslts[t]['sidedness'] ='bilateral'
                    for m in mods:
                        if m.getCategory().lower()=='bilateral_sidedness':
                            rslts[t]['sidedness_value'] = m.getPhrase()
                else:
                    rslts[t]['sidedness'] ='unspecified'
                    rslts[t]['sidedness_value'] = "unspecified"
                    
                    
                    
            
                rsum = alerts.get(t.getCategory(),0)

                if( rslts[t]["disease"] == 'Pos' and rslts[t]["severity"]=="critical" and ( rslts[t]["neurovascularanatomy"]=="ICA" or rslts[t]["neurovascularanatomy"]=="CCA" or rslts[t]["neurovascularanatomy"]=="bulb") ):
                    alert = 2
                elif ( rslts[t]["disease"] == 'Pos' and rslts[t]["severity"]=="non-critical" and ( rslts[t]["neurovascularanatomy"]=="ICA" or rslts[t]["neurovascularanatomy"]=="CCA" or rslts[t]["neurovascularanatomy"]=="bulb") ):
                    alert = 1
                elif ( rslts[t]["disease"] == 'Neg' and ( rslts[t]["neurovascularanatomy"]=="ICA" or rslts[t]["neurovascularanatomy"]=="CCA" or rslts[t]["neurovascularanatomy"]=="bulb") ):
                    alert = 0
                elif ( rslts[t]["neurovascularanatomy"]!="ICA") or (rslts[t]["neurovascularanatomy"]!="CCA") or (rslts[t]["neurovascularanatomy"]!="bulb") :
                    alert = "non-carotid image"
                else: #non-carotid image
                    alert = 0
                rsum = max(rsum,alert)


                alerts[t.getCategory()] = rsum

        return alerts, rslts   

    def plotGraph(self):
        cntxt = self.context["disease"]
        g = cntxt.getDocumentGraph()
        ag = nx.to_pydot(g, strict=True)
        gfile = os.path.join(self.save_dir,
                             "report_%s_unc%s_%s_critical.pdf"%(self.proc_category,
                                                                self.allow_uncertainty,
                                                          self.currentCase))
        ag.write(gfile,format="pdf")
    def processReports(self):
        """For the selected reports (training or testing) in the database,
        process each report with peFinder
        """
        count = 0
        print self.save_dir
        fout=open(self.save_dir+"/timePerDocument.txt","w")
        fout.write("documentName\tstart\tend\tdelta\n")
        for r in self.reports:
            #print r;raw_input()
            startTime=time.time()
            self.currentCase = r[0]
            #print self.currentCase;raw_input()
            self.currentText = r[1].lower()
            self.rptType=r[2]
            self.outString+= u"<case>\n"
            self.outString+= u"<docName> %s </docName>\n"%r[0]
            idName, sevFlag,findingsStr=self.analyzeReport(r[0],self.currentText, 
                                modFilters=['indication','probable_existence',
                                            'definite_existence',
                                          'historical','future','pseudoneg',
                                          'definite_negated_existence',
                                          'probable_negated_existence', 
                                          'carotid_critical', 'left_sidedness', 
                                          'right_sidedness','bilateral_sidedness', 
                                          'internal_carotid_neurovascularanatomy'])
            
            self.outString+= u"</case>\n"
            endTime=time.time()
            self.recordResults(self.rptType,sevFlag,findingsStr)  

            try: fout.write("%s\t%s\t%s\t%s\n"%(r[0], str(startTime),str(endTime), str(endTime-startTime)))
            except: pass
        fout.close()
    
    def recordResults(self, rptType, sevFlag, findingsStr):

        query = """INSERT INTO alerts (reportid, rptType, alert, report) VALUES (?,?,?,?)"""

        if sevFlag=="2":
            self.resultsCursor.execute(query,(self.currentCase[:-4],rptType,sevFlag,findingsStr,))
        else: 
            self.resultsCursorOther.execute(query,(self.currentCase[:-4],rptType,sevFlag,findingsStr,))

        
        
    def cleanUp(self):     
        self.resultsConn.commit()
        self.resultsConnOther.commit()

        
def modifies(g,n,modifiers):
    pred = g.predecessors(n)
    if( not pred ):
        return False
    pcats = [n.getCategory().lower() for n in pred]
    
    return bool(set(pcats).intersection([m.lower() for m in modifiers]))
    
def getParser():
    """Generates command line parser for specifying database and other parameters"""
    parser = OptionParser()

    parser.add_option("-l","--lexical_kb",dest='lexical_kb',default='/docsConText_KnowledgeBase_lexical_filteredNewDefinition.txt',
                       help='name of file for lexical knowledge base')
    parser.add_option("-k","--carotid_kb",dest='carotid_kb',default='/docsConText_KnowledgeBase_carotid_filteredNewDefinition.txt',
                       help='name of file for carotid stenosis knowledge base')
    parser.add_option("-d","--db",dest='dbname',
                       help='name of db containing reports to parse', default="/testData")
    parser.add_option("-x","--xml",dest='xfile',default='./docsConText_output_mentions',
                       help='name of xml output file for carotid stenosis predictions')
    parser.add_option("-a","--adb",dest='adbname',
                       help='name of db containing no/non-significant/non-carotid results', default="Other_Testing_Carotid_Results")
    parser.add_option("-o","--odb",dest='odbname',
                       help='name of db containing results', default="Significant_Testing_Carotid_Results")
    parser.add_option("-s","--save_dir",dest='save_dir',default='./reportsOutput',
                       help='directory in which to store graphs of markups')
    parser.add_option("-z","--html_dir",dest='html_dir',default='./critFinderResults',
                       help='directory in which to store html markups per document')
    parser.add_option("-t","--table",dest='table',default='reports',
                       help='table in database to select data from')
    parser.add_option("-i","--id",dest='id',default='id',
                       help='column in table to select identifier from')
    parser.add_option("-g", "--graph",action='store_true', dest='doGraphs',default=False)
    parser.add_option("-r","--report",dest='report_text',default='impression',
                       help='column in table to select report text from')
    parser.add_option("-c","--category",dest='category',default='ALL',
                       help='category of critical finding to search for. If ALL, all categories are processed')
    parser.add_option("-u","--uncertainty_allowed",dest="allow_uncertainty",
                       action="store_true",default=False)
    parser.add_option("-b","--reportType",dest="reportType", default="reportType",
                      help='report type')
    return parser

def main():
    #python criticalFinderGraph.py -d testData.db
    

    parser = getParser()
    (options, args) = parser.parse_args()
    if( options.dbname == options.odbname ):
        raise ValueError("output database must be distinct from input database")        
    pec = criticalFinder(options)
    pec.initializeOutput(options.dbname+".db", options.lexical_kb, options.carotid_kb)
    pec.processReports()
    pec.closeOutput()
    xmlStr=pec.getOutput()
    fout=codecs.open(options.xfile+".mentions_carotidStenosis.xml","w","utf-8" )
    fout.write(xmlStr)
    fout.close()
    pec.cleanUp()

    
    
if __name__=='__main__':
    
    main()