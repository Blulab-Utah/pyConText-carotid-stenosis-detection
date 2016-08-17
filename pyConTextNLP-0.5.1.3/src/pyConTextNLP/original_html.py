'''
Created on May 22, 2015

@author: daniellemowery
'''
"""Module containing functions for generating various display options for pyConTextNLP

Courtesy of Brian Chapman"""

import copy
from utils import get_document_markups

def __sort_by_span(nodes):
    n = copy.copy(nodes)
    n.sort(key=lambda x: x.getSpan())
    return n
# def __insert_color(txt,s,c):
#     """insert HTML span style into txt. The span will change the color of the 
#     text located between s[0] and s[1]:
#     txt: txt to be modified
#     s: span of where to insert tag
#     c: color to set the span to"""
# 
#     return txt[:s[0]]+'<span style="color: %s;">'%c+\
#            txt[s[0]:s[1]]+'</span>'+txt[s[1]:]
#original
def __insert_color(txt,s,c):
    """insert HTML span style into txt. The span will change the color of the 
    text located between s[0] and s[1]:
    txt: txt to be modified
    s: span of where to insert tag
    c: color to set the span to"""
#     print '<span style="color: %s;">'%c+\
#            txt +'</span>'
    return '<span class="%s">'%c+\
           txt +'</span>'

def mark_text(txt,nodes,colors = {"name":"red","pet":"blue"}):
    if not nodes:
        return txt
    else:
        predicateFlag=False
        nodesLst=[]
        for n in nodes:
        #n = nodes.pop(-1)
            #print txt
            #print "------";raw_input()
            if (n.getCategory()=="INTERNAL_CAROTID_NEUROVASCULARANATOMY"): predicateFlag=True
            elif (n.getCategory()=="COMMON_CAROTID_NEUROVASCULARANATOMY"): predicateFlag=True
            elif (n.getCategory()=="BULB_CAROTID_NEUROVASCULARANATOMY"): predicateFlag=True
            
#             if (n.getCategory()=="CAROTID_CRITICAL"):t="2"
#             elif (n.getCategory()=="CAROTID_NONCRITICAL"): t="1"
#             elif (n.getCategory()=="PROBABLE_NEGATED_EXISTENCE") or (n.getCategory()=="DEFINITE_NEGATED_EXISTENCE"): t="0"
#             else:  t="None"                
#           
#            #no significant stenosis cases
            if (n.getCategory()=="PROBABLE_NEGATED_EXISTENCE") or (n.getCategory()=="DEFINITE_NEGATED_EXISTENCE"): t="0"
            elif (n.getCategory()=="CAROTID_CRITICAL"):t="2"
            elif (n.getCategory()=="CAROTID_NONCRITICAL"): t="1"
            else:  t="None"
            nodesLst.append(t)
        nodesLst.sort()
        #print nodesLst;raw_input()
        if predicateFlag==True:
            
#             if "2" in nodesLst: cSent="severity2"
#             elif "1" in nodesLst: cSent="severity1"
#             elif "0" in nodesLst: cSent="severity0"
            if "0" in nodesLst: cSent="severity0"
            elif "2" in nodesLst: cSent="severity2"
            elif "1" in nodesLst: cSent="severity1"
            
            
            else: cSent="severityNone"
        else: cSent="severityNone"
        return  __insert_color(txt,n.getSpan(),colors.get(n.getCategory()[0],cSent))
                          
        
#         return mark_text(__insert_color(txt,
#                                         n.getSpan(),
#                                         colors.get(n.getCategory()[0],c)),
#                          nodes,
#                          colors=colors)

def mark_document_with_html(imageID,doc,colors = {"name":"red","pet":"blue"}):
    """takes a ConTextDocument object and returns an HTML paragraph with marked phrases in the 
    object highlighted with the colors coded in colors
    
    doc: ConTextDocument
    colors: dictionary keyed by ConText category with values valid HTML colors
    
    """
    findingsStr= """<p> %s </p>\n\n\n\n</body>\n</html>"""%" ".join([mark_text(m.graph['__txt'],
                                                 __sort_by_span(m.nodes()),
                                                 colors=colors) for m in get_document_markups(doc)])
    headerStr="""<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n\n"""
    
    if "severity2" in findingsStr: sevFlag="2"
    elif "severity1" in findingsStr: sevFlag="1"
    elif "severity0" in findingsStr: sevFlag="0"
    
    else: sevFlag="non-carotid image"
    
    #print imageID;raw_input()
    
    docCSS="""<html>\n\n<head>\n<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n\n<meta http-equiv="Content-Style-Type" content="text/css">\n\n<style type="text/css">\n
    \t.severity2 {color: #ff0000}\n
    \t.severity1 {color: #009900}\n
    \t.severity0 {color: #009900}\n
    \t.severityNone {color: #000000}\n</style>\n<title>\n</title>\n</head>\n<body>\n\n<p>Image ID: <imageid>%s</imageid></p>\n<p>Severity: <severity>%s</severity></p>\n"""%(imageID,sevFlag)
    
    #print headerStr+docCSS+findingsStr;raw_input()
    return sevFlag, headerStr+docCSS+findingsStr