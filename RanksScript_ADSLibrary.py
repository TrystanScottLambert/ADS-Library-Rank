import requests
import json
from urllib.parse import urlencode, quote_plus
import subprocess as sp
import numpy as np
import matplotlib as mpl
import matplotlib.colors as colors
import matplotlib.cm as cmx
import matplotlib.pyplot as plt
import os
import pandas as pd

fsize = 12
mpl.rcParams.update({'font.size': fsize, 'xtick.major.size': 8, 'ytick.major.size': 8, 'xtick.major.width': 1, \
	'ytick.major.width': 1, 'ytick.minor.size': 4, 'xtick.minor.size': 4, 'xtick.direction': 'in', 'ytick.direction': 'in', \
	'axes.linewidth': 1, 'text.usetex': True, 'font.family': 'serif', 'font.serif': 'Times New Roman', 'legend.numpoints': 1, \
	'legend.columnspacing': 1, 'legend.fontsize': fsize-2, 'legend.frameon':False, 'legend.labelspacing':0.3, 'lines.markeredgewidth': 1.0, \
	'errorbar.capsize': 3.0, 'xtick.top': True, 'ytick.right': True, 'xtick.minor.visible':True, 'ytick.minor.visible':True})

def GetPaperRank(bibCode, token):
	'''
	function that identifies the publication date and citation number for a single paper
	based on a bibCode, and then extracts the distribution of citations for all refereed astronomy
	papers published in the same month. A perentage rank is then computed, rnking the paper against 
	other papers from the month based on citation count. 

	Arguments
	----------

	bibcode: ADS bibcode of the targeted paper. 

	token: ADS API token (user-specific, to be accessed online at https://ui.adsabs.harvard.edu/user/settings/token)

	Outputs
	-------

	NumberGreaterCitations: Number of refereed publications with greater citations than the target paper

	NumberTotalMonthPapers: Total number of refereed astro publications in the same month as target paper

	Percentage: Rank when compared against only papers with more citations

	Percentage_upper: Rank when compared against publications with more or equal number of citations. 

	Author: Name of lead-author for target paper. 

	PubDate: publication date of target paper. 

	'''
	encoded_query = urlencode({"q": "bibcode:"+str(bibCode),
	                           "fl": "title, bibcode, citation_count, property, pubdate, author",
	                           "rows": 1000
	                          })
	results = requests.get("https://api.adsabs.harvard.edu/v1/search/query?{}".format(encoded_query), \
	                       headers={'Authorization': 'Bearer ' + token})
	print(bibCode, results.json()['response']['docs'][0]['pubdate'][0:7], 'Citations:', \
		results.json()['response']['docs'][0]['citation_count'], results.json()['response']['docs'][0]['author'][0])
	CitationCount = results.json()['response']['docs'][0]['citation_count']
	PubDate = results.json()['response']['docs'][0]['pubdate'][0:7]
	Author = results.json()['response']['docs'][0]['author'][0].replace(" ", "")
	
	Citationbounds = [0, 1, 2, 4, 10] # dividing the citation ditribution into chunks with fewer than 2000 hits, so as not to hit limit. 

	citations = np.array([])

	for citeBound in range(len(Citationbounds)):
		CiteStart = Citationbounds[citeBound]
		if citeBound == len(Citationbounds)-1:
			CiteEnd = 100000
		else:
			CiteEnd = Citationbounds[citeBound+1]-1

		encoded_query = urlencode({"q": "pubdate:["+PubDate+" TO "+PubDate+"] AND collection:astronomy AND property:refereed AND citation_count:["+str(CiteStart)+" TO "+str(CiteEnd)+"]",
	                           "fl": "title, bibcode, citation_count, property, pubdate",
		                           "rows": 2000
		                          })
		results = requests.get("https://api.adsabs.harvard.edu/v1/search/query?{}".format(encoded_query), \
		                       headers={'Authorization': 'Bearer ' + token})
		
		if len(results.json()['response']['docs'])==2000:
			print('WARNING: number of results in citation range ', CiteStart, 'to', CiteEnd, ' reached query limit')
			print('Need to add value to citationBounds ')
	
		# now extracting the histogram of citations
		for ii in range(len(results.json()['response']['docs'])):
			citations = np.append(citations, results.json()['response']['docs'][ii]['citation_count'])
	
	# now identifying the fraction with citations greater than or equal to the reference
	NumberGreaterCitations = len(citations[citations>=CitationCount])
	NumberTotalMonthPapers = len(citations)
	Percentage = (NumberGreaterCitations/NumberTotalMonthPapers)*100
	Percentage_upper = (len(citations[citations>CitationCount])/NumberTotalMonthPapers)*100
	print('Total astro refereed papers this month:', NumberTotalMonthPapers)
	print('Percentage rank of paper:', Percentage)
	print('############################################################')
	
	return([NumberGreaterCitations, NumberTotalMonthPapers, Percentage, Percentage_upper, Author, PubDate])


def GetLibraryRanks(LibraryCode, OutputName, rows=1000):
	'''
	For a given ADS library, identify the relevant bibcodes, and compile the rank statistics, saving an output dataframe. 

	Arguments
	---------
	LibraryCode: ADS library access code 

	OutputName: Name of output files

	rows: maximum number of papers to extract from library
			(default 1000)


	'''
	# now extracting my first-author library
	results = requests.get("https://api.adsabs.harvard.edu/v1/biblib/libraries/"+LibraryCode+"?rows="+str(rows),
	                       headers={'Authorization': 'Bearer ' + token})
	# print(results.json()['solr']['response']['docs'])
	Bibcodes = np.array([])
	for ii in range(len(results.json()['solr']['response']['docs'])):
		Bibcodes = np.append(Bibcodes, results.json()['solr']['response']['docs'][ii]['bibcode'])

	print(Bibcodes)
	
	ranks = np.array([])
	ranks_upper = np.array([])
	paper_number = np.array([])
	Authors = np.array([])
	pubDate = np.array([])
	for bibcode in Bibcodes:
		Statistics = GetPaperRank(bibCode = bibcode, token=token)
		ranks = np.append(ranks, Statistics[2])
		ranks_upper = np.append(ranks_upper, Statistics[3])
		paper_number = np.append(paper_number, Statistics[1])
		Authors = np.append(Authors, Statistics[4])
		pubDate = np.append(pubDate, Statistics[5])
	
	# now saving the outputs
	
	Output = pd.DataFrame({'Bibcode':Bibcodes, \
		'Author':Authors, \
		'PublicationDate':pubDate, \
		'Rank':ranks, \
		'Rank_upper':ranks_upper, \
		'PaperNumber':paper_number})
	Output.to_csv(OutputName+'.csv', index=False)

	
	
def MakeLibraryRanksPlot(LibraryCode, OutputName):
	'''
	For a given ADS library, either read-in a pre-generated output dataframe if available, or generate a new 
	one one using the GetLibraryRanks function, then generate a plot presenting the ranks for all paper in the library. 

	Arguments
	---------
	LibraryCode: ADS library access code (identifiable though the library url https://ui.adsabs.harvard.edu/user/libraries/<LibraryCode>)

	OutputName: Name of output files


	'''
	if not os.path.isfile(OutputName+'.csv'):
		GetLibraryRanks(LibraryCode, OutputName)
	
	Output = pd.read_csv(OutputName+'.csv')

	for ii in range(len(Output['Rank'])):
		if '&' in Output['Bibcode'][ii]:
			Output.loc[ii, 'Bibcode'] = Output['Bibcode'][ii].split('&')[0] + '\&' +  Output['Bibcode'][ii].split('&')[1]

	# now finally making a plot of the output
	fig=plt.figure(figsize = (len(Output['Rank'])*0.25, 3))
	ax1 = plt.subplot(111) 
	
	ax1.scatter(np.arange(len(Output['Rank'])), (Output['Rank']+Output['Rank_upper'])/2, c='k')
	Sel = ((Output['Rank']+Output['Rank_upper'])/2) < 5
	ax1.scatter(np.arange(len(Output['Rank']))[Sel], (Output['Rank'][Sel]+Output['Rank_upper'][Sel])/2, c='orange')
	# ax1.scatter(np.arange(len(Output['Rank_upper'])), Output['Rank_upper'], c='k', marker='_')
	for jj in range(len(Output['Rank'])):
		ax1.plot([jj, jj], [Output['Rank'][jj], Output['Rank_upper'][jj]], c='k')
	ax1.axhline(np.median((Output['Rank']+Output['Rank_upper'])/2), c='k', linestyle='--')
	
	ax1.set_xlim([-0.5, len(Output['Rank'])-0.5])	
	ax1.set_ylim([100, 0])	
	ax1.set_ylabel('Rank of paper')
	ax1.set_xticks(np.arange(len(Output['Rank'])))
	ax1.set_xticklabels(np.array(Output['Bibcode']), rotation = 90)

	ax1.grid()

	ax2 = ax1.twiny()
	ax2.set_xlim([-0.5, len(Output['Rank'])-0.5])	
	ax2.set_xticks(np.arange(len(Output['Rank'])))
	ax2.set_xticklabels(np.array(Output['Author']), rotation = 90)
	
	plt.savefig(OutputName+'.pdf', bbox_inches='tight')
	plt.close()

#############################################################
################ NEED TO ADD TOKEN HERE #####################
#############################################################
# personal access token 
# (user-specific, to be accessed online at https://ui.adsabs.harvard.edu/user/settings/token)
token='' 
#############################################################

# making the full output for a single ADS library. 
MakeLibraryRanksPlot(LibraryCode="g3xxlnShS_iiymcLRdSUFg", OutputName='Ranks_BellstedtFirstAuthor')

# extracting the statistics for just a single paper. 
# Statistics = GetPaperRank(bibCode = '2022MNRAS.517.6035T', token=token)



# check the remaining calls that a user can make in a day. 
# curl -v -H "Authorization: Bearer <token here>" 'https://api.adsabs.harvard.edu/v1/search/query?q=star'



