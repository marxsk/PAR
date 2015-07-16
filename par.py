#!/usr/bin/python
#-- coding: utf-8 --
# 2015 Matej Stepanek

import subprocess
import urllib2
import requests
import justext
import time

UNITOK_PATH = '/nlp/corpora/programy/unitok.py'
MAJKA_PATH = '/nlp/projekty/ajka/bin/majka'
DESAMB_PATH = '/nlp/corpora/programy/desamb.utf8.sh'
STOPLIST_QUESTION = './stoplists/stopquestion.txt'
STOPLIST_PARAGRAPH = './stoplists/stoppar.txt'


class Seznam:
    """Python interface to Seznam search API. 
    """
    def get_json(self, query):
	"""Sends query to seznam search API and returns JSON search results.
	"""
        query_parameters = {'format':'json', 'client':'muni_fi_nlplab',
			    'source':'web', 'query':query,
			    'userId':'muni_fi_nlplab'}
        results = requests.get("http://searchapi.seznam.cz/api2/search",
                               params = query_parameters)
        json_results = results.json()
        return json_results

    def get_links_titles(self, query):
        """Returns list of links to search results and their titles.
	
	Returns 10 links at most. If a query fails returns an empty list.       
        """
        json_results = self.get_json(query)
        links_titles = []
        if json_results.has_key('web'):
	    if json_results['web'].has_key('totalResults'):	    
            	num_results = json_results['web']['totalResults']
		if num_results != '0':
		    items = json_results['web']['result']
        	    for i in range(min(len(items),10)):
        		link = items[i][u'url']
			if u'title' in items[i]:
			    title = items[i][u'title']
			else:
			    title = u'unknown title'
			links_titles.append((link,title))
        return links_titles


class Google:
    """Python interface to google custom search engine (CSE).
    
    Uses request library to get search results in JSON format.
    (See http://docs.python-requests.org/)
    
    There are two prepared searchers by me (both are focused on czech):
    GENERAL - searches over all web pages
    CSWIKI  - searches over czech Wikipedia
    Usage is limited - 100 questions per day. I use GENERAL searcher as default.
    
    You can create your own searcher on https://www.google.cz/cse/ 
    and incorporate it into project in google developers console 
    on https://console.developers.google.com/.
    """
    
    CSWIKI_ID = "000286326552965592600:vhde1zkujt0"
    # https://www.google.cz/cse/publicurl?cx=000286326552965592600:vhde1zkujt0
    GENERAL_ID = "000286326552965592600:ujcjofmbh7w"
    # https://www.google.cz/cse/publicurl?cx=000286326552965592600:ujcjofmbh7w
    
    def __init__(self):
        self.cse_id = self.GENERAL_ID
	# When you exceed the limit of queries, simply use another project.
        self.project_key = "AIzaSyDP25rjvTeMtKETbkxll5O6xfeT2sbN5ow"
	#self.project_key = "AIzaSyDBSZCCUdN9E2WdYPcBK7_63vyoRzoEZnE"        

    def get_json(self, query):
        """Returns JSON results of CSE for given query.
        
        Returns only first 10 results. Results are in JSON format. 
        For structure of json results see documentation of custom search JSON API
        https://developers.google.com/custom-search/json-api/v1/reference/cse/list
        """
        query_parameters = {'q':query, 'num': '10',
                            'key': self.project_key, 'cx': self.cse_id}
        results = requests.get("https://www.googleapis.com/customsearch/v1",
                               params = query_parameters)    
        json_results = results.json()
        return json_results     
    
    def get_links_titles(self, query):
        """Returns list of links to search results and their titles.       

	Returns 10 links at most. If a query fails returns an empty list.       
        """
        json_results = self.get_json(query)
        links_titles = []
        if not json_results.has_key('error'):
            num_results = json_results['searchInformation']['totalResults']
            if num_results != '0':
        	items = json_results["items"]
        	for i in range(min(len(items),10)):                
                    link = items[i][u'link']
                    if u'title' in items[i]:
                	title = items[i][u'title']
                    else:
                	title = u'unknown title'
                    links_titles.append((link,title))
        return links_titles


class Answerer:
    """Class for getting paragraph that contains answer to the given question.
    
    Paragraphs are gained from documents - search results of web search engine.
    Call function get_best_par to get the most relevant paragraph to your question.
    """
    def get_stoplist(self, file_name):
        """Returns list of stop words.
	
	(From utf-8 text file with one stopword per line.)
        """
        stoplist = []
        with open(file_name, 'r') as stopfile:
            for line in stopfile:
                stoplist.append(line[:-1])
        stopfile.closed
        return stoplist

    def tokenize(self, text):
        """Splits given text to tokens (one token per line).

        Uses unitok.py
        https://www.sketchengine.co.uk/documentation/attachment/wiki/Website/LanguageResourcesAndTools/unitok.py
        """
	start = time.time()
        p1 = subprocess.Popen(['echo', '-n', text], stdout=subprocess.PIPE)
        unitok_output = subprocess.check_output([UNITOK_PATH, '-n', '-a', '-l', 'czech'],
                                                stdin=p1.stdout)
        p1.stdout.close()
	cil = time.time()
	self.unitok += (cil - start)
        return unitok_output
        
    def add_lemmata_tags(self, tokens):
        """For every token finds its lemma and morfological tag.

        Uses majka tagger. http://nlp.fi.muni.cz/czech-morphology-analyser/ 
        Returns list of tuples (token,lemma,tag).
        """
	start = time.time()
        p1 = subprocess.Popen(['echo', '-n', tokens], stdout=subprocess.PIPE)
	majka_output  = subprocess.check_output([MAJKA_PATH, '-p'], stdin=p1.stdout)
        p1.stdout.close()

        lines = majka_output.split('\n')
        tokens_lemmata_tags = []

        for line in lines:
            trio  = line.split(':')
	    if len(trio) >= 3:
                token = trio[0]
                lemma = trio[1]
            	tag = trio[2]
	    else:
		token = trio[0]
		lemma = token
		tag = 'unknown'
            tokens_lemmata_tags.append((token,lemma,tag))
		
        cil = time.time()
	self.majka += (cil - start)    
        return tokens_lemmata_tags
    
    def get_main_words(self, tokens, stopfile=None, output='lemmata'):
        """For given text returns list of "main words". That means words
           that are semantically significant.
        """
        tlt = self.add_lemmata_tags(tokens)

        # remove pronouns, prepositions, conjunctions, "by, aby, kdyby"
        unwanted = ('k3','k7','k8','kY')
        tlt = [(token,lemma,tag) for (token,lemma,tag) in tlt if not tag.startswith(unwanted)]
 
        # remove tokens with length 1
        tlt = [(token,lemma,tag) for (token,lemma,tag) in tlt if len(token) > 1]
        
        if stopfile:
            # remove stopwords
            stoplist = self.get_stoplist(stopfile)
            tlt = [(token,lemma,tag) for (token,lemma,tag) in tlt if lemma not in stoplist]
        
        if output == 'lemmata':
            result = [lemma for (token,lemma,tag) in tlt]
        elif output == 'tokens':
            result = [token for (token,lemma,tag) in tlt]

        return result
    
    def process_question(self, question, num_keywords=20):
        """Given a question in natural language returns query to use
	in search engine and keywords to identify the relevant paragraph
	in the web page.  
        
        Both keywords and query have limited length - num_keywords.
        Keywords contains unique lemmata.
        """
	tokens = self.tokenize(question)

        keywords = self.get_main_words(tokens, STOPLIST_QUESTION)
        keywords = keywords[:num_keywords]

        seen = set()
        seen_add = seen.add
        keywords = [k for k in keywords if not (k in seen or seen_add(k))] 

        query = self.get_main_words(tokens, STOPLIST_QUESTION, 'tokens')
        query = ' '.join(query[:num_keywords])

        return query, keywords
    
    def get_paragraphs(self, url):
        """From given url address returns content of the page without boilerplate.
        (Boilerplate is semanticaly unimportant page content.)
        
        Returns list of paragraphs. Library justext is used.
        See https://code.google.com/p/justext/.
        max_link_density is set higher than default because links are very
        frequently used in the Wikipedia.
        """
        page = urllib2.urlopen(url).read()
        # 'Czech' is stoplist in justext library.
        stoplist = justext.get_stoplist('Czech')
        paragraphs = justext.justext(page, stoplist, no_headings=True,
                                     max_link_density=0.9)
        # Removes paragraphs with too few and too much words.
        useful = [p['text'] for p in paragraphs if p['class']=='good' and p['word_count'] >= 6 and p['word_count'] < 350]  
        # Encode from unicode to utf-8
        useful = [par.encode('utf-8','replace') for par in useful]
        return useful

    def get_relevant_par(self, paragraphs, keywords, num_paragraphs=50):
        """Returns the most relevant paragraph, score and matches.
        
        For given paragraphs and keywords of question returns the paragraph, 
        that contains the most keywords.
        
        There is parameter num_paragraphs to reduce time of the computation. 
        It says how many paragraphs on the page you want to process.
        (Let's assume that the most important information is at 
        the beginning of the web page.)
        """
        record = []
	together = '#'.join(paragraphs)
	tokens = self.tokenize(together)
	tokenized_pars = tokens.split('#')

        for i,par in enumerate(tokenized_pars):
            if i == num_paragraphs:
                break
            main_words = self.get_main_words(par, STOPLIST_PARAGRAPH) 
            (score, matches) = self.rank_par(main_words, keywords)
            record.append((score,matches))
        best = record.index(max(record))
   
        return paragraphs[best], record[best] 
    
    def rank_par(self, par, keywords):
        """Given paragraph and keywords returns score of paragraph based on 
        the number of keywords it contains.
        
        Both paragraph and keywords are in the lemmatic form.
        """
        search_words = list(keywords)
        score = 0
        matches = []
        for lemma in par:
            if lemma in search_words:
                score += 1
                matches.append(lemma)
                search_words.remove(lemma)
        return score, matches    
    
    def get_best_par(self, question, SE):
        """Given a question in Czech returns a paragraph that most likely
           contains an answer.
        
        1) Gets web search engine results.
        2) Finds the most relevant paragraph in 3 pages from the step 1).
        3) Compares paragraphs from the step 2) and returns the one that
           contains the most keywords from the question.
        """
	zacatek = time.time()
	self.unitok = 0
	self.majka = 0

        # process question 
        query, keywords = self.process_question(question)  

	#for k in keywords: 
	#    print k, '<br>'

        # get web search engine results
        if SE == 'seznam':
	    cse = Seznam()
	else:
	    cse = Google()
        links_titles = cse.get_links_titles(query)

        # if CSE returns no results, reduce the query
        while not links_titles and len(keywords) > 2:
            # reduce both query and keywords
            if len(keywords) > 10:
                diff = -5
            elif len(keywords) < 5:
                diff = -1
            else:
                diff = -2
            query = " ".join(query.split(" ")[:diff])
            keywords = keywords[:diff]
            links_titles = cse.get_links_titles(query)
                
        # if still no CSE results, exit
        if not links_titles:
            return (None,None,None,None,None)

      	stred = time.time()

	#print '- mam search results <br>'

	# get relevant paragraphs
        rel_paragraphs = []
        for (link,title) in links_titles:
            paragraphs = self.get_paragraphs(link)
            if paragraphs:
                relevant_par, (score, matches) = self.get_relevant_par(paragraphs, keywords)
                rel_paragraphs.append((relevant_par,link,title,score,matches))
            if len(rel_paragraphs) == 3:
                break

	#print '- mam relevant par pro kazdy dokument <br>'

	# if no rel_paragraphs, exit
        if not rel_paragraphs:
            return (None,None,None,None,None)	

        # get best paragraph          
        scores = [s for (_p,_l,_t,s,_m) in rel_paragraphs]
        best_index = 0
        for s in scores:
            if s > scores[best_index]:
                best_index = scores.index(s)
         
        (best_par,best_link,best_title,best_score,best_matches) = rel_paragraphs[best_index]
        best_link = best_link.encode('utf-8','replace')
        best_title = best_title.encode('utf-8','replace')

	konec = time.time()
	#print '<br>vse: ',konec - zacatek,'<br>'
	#print 'otazka + SE: ', stred - zacatek, '<br>'
	#print 'unitok: ', self.unitok, '<br>'
	#print 'majka: ', self.majka, '<br>'

        return (best_par,best_link,best_title,best_score,best_matches)


class Tester:
    """Class with a few functions for testing of the PAR answerer.
    """
    def __init__(self):
        self.ans = Answerer()
    
    def search(self, answer, par_title):
        """Given a paragraph and an answer tests if this paragraph
           contains the answer.
           
           If the paragraph contains all main lemmata from answer, returns '1'.
           Otherwise returns '0'.
        """
        main_answer = self.ans.get_main_words(answer)
        #print '<br>main lemmata of answer: ',main_answer,'<br>' #for debugging

        main_par = self.ans.get_main_words(par_title)
        #print '<br>main lemmata of par_title: ',main_par,'<br><br>' #for debugging

        success = '1'

        for lemma in main_answer:
            if lemma not in main_par:
                success = '0'
                break
        return success
    
    def test(self, line, SE):
        """Given a line (utf-8 string 'question#answer') finds a relevant paragraph
        and tests if this paragraph contains the answer from line.
        !!Note: paragraphs is expanded by title of the source page.
        
        Returns string in this form: success#title#link#paragraph, where 
        success is 1 when the found paragraph contains the given answer and
        0 otherwise. Link is the link to the page where the paragraph was found
        and title is the title of that page.
        """
        sline = line.split('#')
        try:
            question = sline[0]
            answer = sline[1]

            (best_par,best_link,best_title,_,_) = self.ans.get_best_par(question, SE)
            par_title = ' '.join([best_title, best_par])

        except:
            best_par = 'error'
            
        if best_par == 'error':
            result = 'Error: line in a bad format or system PAR error.' 
        elif not best_par:
            result = 'Sorry, no results for given question.'
        else:
            success = self.search(answer,par_title)
            html_link = '<a href="%s" target="_blank">%s</a>' %(best_link,best_link)
            result = '#'.join([success,best_title,html_link,best_par])
        return result
