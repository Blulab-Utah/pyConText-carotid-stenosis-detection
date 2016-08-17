# pyConText-carotid-stenosis-detection

This package is maintained by Danielle Mowery at the University of Utah (danielle.mowery@utah.edu). Other active and past developers include:

Wendy W. Chapman
Brian Chapman
Sumithra Velupillai

This information extraction tool, pyConText, has been adapted by Danielle Mowery from original code written by Brian Chapman for a series of stroke research studies supported by funding from the Veteran Affairs (VA HSR&D Stroke QUERI RRP 12-185), National Heart, Lung, and Blood Institute (NHLBI 1R01HL114563-01A1), National Library of Medicine (NLM R01 LM010964), & National Institute for General Medical Sciences (NIGMS R01GM090187).

The purpose of this tool is to extract mentions of carotid stenosis, categorize the mentions into 3 classes (no stenosis, insignificant stenosis, or significant stenosis) and, then classify the whole document according to the most significant mention level encoded within the document. Relevant publications can be found below. Please be sure to cite the first two manuscripts when applying this tool for other studies and presenting/publishing your results.

Mowery DL, Chapman BE, Conway M, South BR, Madden E, Keyhani S, Chapman WW. Extracting a Stroke Phenotype Risk Factor from Veteran Health Administration Clinical Reports: An Information Content Analysis. Journal of Biomedical Semantics. 2016. 7:26

Chapman BE, Lee S, Kang HP, Chapman WW. Document-level classification of CT pulmonary angiography reports based on an extension of the ConText algorithm. J Biomed Inform. 2011 Oct;44(5):728-37

Mowery DL, Chapman WW, Chapman BE, Conway M, South BR, Madden E, Keyhani S. Evaluating the Usage of Sections, Structures, and Expressions for Reporting and Extracting a Stroke Phenotype Risk Factor. Intelligent Systems for Molecular Biology: Phenotype Day 2015. Dublin, Ireland.

Mowery DL, South BR, Garvin J, Franc D, Ashfaq S, Zamora T, Cheng E, Chapman BE, Keyhani S, Chapman WW. Adapting a Natural Language Processing Algorithm to Support Stroke Cohort Generation. HSR&D/QUERI National Day. July 2015

Mowery DL, South BR, Madden E, Chapman BE, Chapman WW, Keyhani S. Filtering Negative Reports for a Comparative Effectiveness Study of Stroke. AMIA 2015 Summits on Translational Bioinformatics. San Francisco, CA. Late Breaking Research Presentation.

Mowery DL, Franc D, Ashfaq S, Zamora T, Cheng E, Chapman WW, Chapman BE. Developing a knowledge base for detecting carotid stenosis with pyConText. AMIA Symp Proc. Washington DC. 2014.

This tool requires a series of python packages:
- python 2.7 or 2.6
- networkx
- sqlite3
- unicodecsv

A tutorial and code examples can be found at the sister site hosted and maintained by Brian Chapman at https://github.com/chapmanbe/pyConTextNLP. Please note that this code is an earlier version of the pyConTextNLP code so there could be differences in functionality and outputs.

To run this code, on your local installation, simple enter into the directory containing the file criticalFinderGraph.py, then type "python criticalFinderGraph.py" to run the sqlite3 database of reports from testData.db through the algorithm. You will find several outputs under reportsOutput:
- encoded mentions in XML (/pyConTextNLP-0.5.1.3/src/docsConText_output_mentions.mentions_carotidStenosis.xml)
- flagged documents with significant stenosis (/pyConTextNLP-0.5.1.3/src/reportOutputs/Significant_Testing_Carotid_ResultsALLFalse.db)
- flagged documents with no or insignificant stenosis (/pyConTextNLP-0.5.1.3/src/reportOutputs/Other_Testing_Carotid_ResultsALLFalse.db)
- time for processing each document (/pyConTextNLP-0.5.1.3/src/reportOutputs/timePerDocument.txt)

