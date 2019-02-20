import re
from nltk.stem import PorterStemmer 
import math

class QueryParsers:

	def __init__(self, file):
		self.filename = file
		self.query= self.get_queries()

	def get_queries(self):
		q = open(self.filename,'r').read().lower()
		#subsitute all non-word characters with whitespace
		pattern = re.compile('\W+')
		q = pattern.sub(' ', q)
		# split text into words (tokenized list for a document)
		q = q.split()
		# stemming words
		stemmer = PorterStemmer()
		q = [stemmer.stem(w) for w in q ]
		return q

class BuildIndex:
	
	b = 0.75
	k = 1.2
	

	def __init__(self, files):
		self.tf = {}
		self.df = {}
		self.filenames = files
		self.file_to_terms = self.process_files()
		self.regdex = self.regular_index(self.file_to_terms)
		self.invertedIndex = self.inverted_index()
		self.dltable = self.docLtable()
		self.dl = self.docLen()
		self.avgdl = self.avgdocl()
		self.N = self.doc_n()
		self.idf = self.inverse_df()
		q = QueryParsers('queries.txt')
		query = q.query
		self.total_score  = self.BM25scores(query)
		self.rankedDocs = self.ranked_docs()


	def process_files(self):
		'''
		input: filenames
		output: a dictionary keyed by filename, and with values of its term list
		'''
		file_to_terms = {}

		for file in self.filenames:
			#read the whole text of a file into a single string with lowercase
			file_to_terms[file] = open(file,'r').read().lower()
			#subsitute all non-word characters with whitespace
			pattern = re.compile('\W+')
			file_to_terms[file] = pattern.sub(' ', file_to_terms[file])
			# split text into words (tokenized list for a document)
			file_to_terms[file] = file_to_terms[file].split()
			# stemming words
			stemmer = PorterStemmer()
			file_to_terms[file] = [stemmer.stem(w) for w in file_to_terms[file] ]
		
		return file_to_terms

	def doc_n(self):
		'''
		return the number of docs in the collection
		'''
		return len(self.file_to_terms)


	def index_one_file(self, termlist):
		'''
		input: termlist of one document.
		map words to their position for one document
		output: a dictionary with word as key, position as value.
		'''
		fileIndex = {}
		for index,word in enumerate(termlist):
			if word in fileIndex.keys():
				fileIndex[word].append(index)
			else:
				fileIndex[word] = [index]

		return fileIndex

	def regular_index(self,termlists):
		'''
		input: output of process_files(filenames)
		output: a dictionary. key: filename, value: a dictionary with word as key, position as value  
		'''
		regdex = {}

		for filename in termlists.keys():
			regdex[filename] = self.index_one_file(termlists[filename])

		return regdex


	def inverted_index(self):
		'''
		input： output of make_indexes function.
		output: dictionary. key: word, value: a dictionary keyed by filename with values of term position for that file.
		'''
		total_index = {}
		regdex = self.regdex

		for filename in regdex.keys():
			
			self.tf[filename] = {}

			for word in regdex[filename].keys():
				# tf dict key: filename, value: dict key is word, value is count
				self.tf[filename][word] = len(regdex[filename][word])
				
				if word in self.df.keys():
					# df dict key: word, value: counts of doc containing that word
					self.df[word] += 1
				else:
					self.df[word] = 1

				if word in total_index.keys():
					if filename in total_index[word].keys():
						total_index[word][filename].extend(regdex[filename][word])
					else:
						total_index[word][filename] = regdex[filename][word]
				else:
					total_index[word] = {filename: regdex[filename][word]}

		return total_index

	def docLtable(self):
		'''
		output: dict, key:word, value:dict(key: number of docs contaiing that word, value:total_freq)
		'''
		dltable = {}
		for w in self.invertedIndex.keys():	
			total_freq = 0
			for file in self.invertedIndex[w].keys():
				total_freq += len(self.invertedIndex[w][file])
			
			dltable[w] = {len(self.invertedIndex[w].keys()):total_freq}
		
		return dltable


	def docLen(self):
		'''
		return a dict, key: filename, value: document length
		'''
		dl = {}
		for file in self.filenames:
			dl[file]=len(self.file_to_terms[file])
		return dl

	def avgdocl(self):
		sum = 0
		for file in self.dl.keys():
			sum += self.dl[file]
		avgdl = sum/len(self.dl.keys())
		return avgdl


	def inverse_df(self):
		'''
		output: inverse doc freq with key:word, value: idf
		'''
		idf = {}
		for w in self.df.keys():
			# idf[w] = math.log((self.N - self.df[w] + 0.5)/(self.df[w] + 0.5))
			idf[w] = math.log((self.N +1 )/self.df[w])
		return idf

    
	def get_score (self,filename,qlist):
		'''
		filename: filename
		qlist: termlist of the query 
		output: the score for one document
		'''
		score = 0
		for w in self.file_to_terms[filename]:
			if w not in qlist:
				continue
			wc = len(self.invertedIndex[w][filename])
			score += self.idf[w] * ((wc)* (self.k+1)) / (wc + self.k * 
                                                         (1 - self.b + self.b * self.dl[filename] / self.avgdl))
		return score


	def BM25scores(self,qlist):
		'''
		output: a dictionary with filename as key, score as value
		'''
		total_score = {}
		for doc in self.file_to_terms.keys():
			total_score[doc] = self.get_score(doc,qlist)
		return total_score


	def ranked_docs(self):
		ranked_docs = sorted(self.total_score.items(), key=lambda x: x[1], reverse=True)
		return ranked_docs



