import sys
import string
import operator
import math

#we run porterStemmer so the class is available for the StemAnalyser
execfile("C:\\Users\\Azn0Richard0\\Desktop\\Project2\\porter_stemmer.py")

class Parser:
	def __init__(self):
		pass
		
	def parse(self, path):
		input_file = open(path).read()
		collection = dict()
		while True:
			try:
				i = input_file.index("<DATE>") + 6
				j = input_file.index("</DATE>")
				filename = path[len(path)-6:len(path)-4] + "_" + input_file[i:j]
				i = input_file.index("<BODY>") + 6
				j = input_file.index("</BODY>")
				collection[filename] = input_file[i:j]
				input_file = input_file[j+7:]
			except:
				break
		return collection

	#return the document for a specific doc_id. gets content between <title> </body>
	def get_document(self, doc_id):
		doc_id_info = doc_id.split("_")
		fileNumber = doc_id_info.pop(0)
		documentDate = doc_id_info.pop(0)
		path = "C:\\Users\\Azn0Richard0\\Desktop\\Project2\\corpus\\reut2-0"+fileNumber+".sgm"
		input_file = open(path).read()
		while True:
			try:
				i = input_file.index("<DATE>") + 6
				j = input_file.index("</DATE>")
				if documentDate == input_file[i:j]:
					#We need it like this because its possible it will read the previous article
					input_file = input_file[j+7:]
					i = input_file.index("<TITLE>")
					j = input_file.index("</BODY>") + 7
					
					#strange fix to removed title of previous article. This is done because not all articles have a body tag. 
					while True:
						try:
							temp_i = input_file[i+7:j].index("<TITLE>")
							i = temp_i+i+7
						except:
							return input_file[i:j]
							break
				else:
					input_file = input_file[j+7:]
			except:
				#just in case the getDocument was not working or the doc_id is incorrect. Testing purpose
				print "unable to find "+doc_id
				break
		

#General Analyser that deals with case folding
class Analyser:
	def __init__(self):
		pass
		
	def tokenize(self,doc):
		tokens = list()
		doc = doc.lower()
		for char in string.punctuation:
			doc = doc.replace(char, "")
		for char in "\n\t":
			doc = doc.replace(char, " ")
		for token in doc.split(" "):
			if not self.str_is_number(token):
				tokens.append(token)
		return tokens
	
	def str_is_number(self,token):
		try:
			float(token)
			return True
		except ValueError:
			return False

#Analyser that does not filter		
class UnfilteredAnalyser(Analyser):
	def __init__(self):
		pass
		
	def tokenize(self,doc):
		tokens = list()
		for char in "\n\t":
			doc = doc.replace(char, " ")
		for token in doc.split(" "):
			tokens.append(token)
		return tokens

#Analyser that does filters numbers	
class NoNumberAnalyser(Analyser):
	def __init__(self):
		pass
		
	def tokenize(self,doc):
		tokens = list()
		for char in "\n\t":
			doc = doc.replace(char, " ")
		for token in doc.split(" "):
			if not self.str_is_number(token):
				tokens.append(token)
		return tokens
#Analyser that stems.
class StemAnalyser(Analyser):
	def __init__(self, stopwords):
		self.stopwords = stopwords
		pass
		
	def tokenize(self,doc):
		tokens = list()
		doc = doc.lower()
		for char in string.punctuation:
			doc = doc.replace(char, "")
		for char in "\n\t":
			doc = doc.replace(char, " ");
		for token in doc.split(" "):
			if(token in self.stopwords): 
				continue
			p = PorterStemmer()
			token = p.stem(token, 0, len(token)-1)
			if not self.str_is_number(token):
				tokens.append(token)
		return tokens

#analyser that removes stop words
class StopWordAnalyser(Analyser):
	def __init__(self, stopwords):
		self.stopwords = stopwords
		pass
		
	def tokenize(self,doc):
		tokens = list()
		doc = doc.lower()
		for char in string.punctuation:
			doc = doc.replace(char, "")
		for char in "\n\t":
			doc = doc.replace(char, " ");
		for token in doc.split(" "):
			if(token in self.stopwords): 
				continue
			if not self.str_is_number(token):
				tokens.append(token)
		return tokens

class IndexWriter: 
	def __init__(self, analyser, memory):
		self.terms = dict()
		self.analyser = analyser
		self.memory = memory
		self.fileCount = 0
		self.tokenCount = 0
		self.document_length_dict = dict()
		
		
	#normal processing
	def process(self,collection):
		for doc_id in collection:
			document_tokens = self.analyser.tokenize(collection[doc_id])
			for token in document_tokens:
				posting_list = self.terms.get(token, [])
				if not doc_id in posting_list:
					posting_list.append(doc_id)
					self.terms[token] = posting_list
		return self.terms
	
	#processing for SPIMI
	def processSPIMI(self,collection):
		for doc_id in collection:
			document_tokens = self.analyser.tokenize(collection[doc_id])
			for token in document_tokens:
				self.tokenCount += 1
				posting_list = self.terms.get(token, [])
				if not doc_id in posting_list:
					posting_list.append(doc_id)
					self.terms[token] = posting_list
				if self.tokenCount == self.memory:
					self.write()
		
	#process with positional information
	def processPositional(self,collection):
		for doc_id in collection:
			document_tokens = self.analyser.tokenize(collection[doc_id])
			#store each doc_id's document length
			self.document_length_dict[doc_id] = len(document_tokens)
			for token in document_tokens:
				counter = 0
				posting_list = self.terms.get(token, {})
				#add new term to dict and store position
				if not posting_list:
					posting_list[doc_id] = [counter]
					self.terms[token] = posting_list
				else:
					#append to existing doc_id's positional list the new position
					if doc_id in posting_list:
						temp = posting_list.get(doc_id,[])
						temp.append(counter)
						posting_list[doc_id] = temp
					#add new doc_id to posting list and the position
					else:
						posting_list[doc_id] = [counter]
				counter += 1
	
	def get_terms(self):
		return self.terms
		
	def get_document_length(self):
		return self.document_length_dict
	
	#get's the merged index
	def get_merge_index(self):
		#Used the previous fileCount since write() used fileCount to save the index. 
		#Could have just given it a different name but it works like this.
		fileNumber = self.fileCount - 1;
		fileNumber = str(fileNumber)
		filename = "C:\\Users\\Azn0Richard0\\Desktop\\Project2\\"+fileNumber+".txt"
		file = open(filename, 'rb')
		data = pickle.load(file)
		return data
		
	#writes terms into document.
	def write(self):
		fileNumber = str(self.fileCount)
		filename = "C:\\Users\\Azn0Richard0\\Desktop\\Project2\\"+fileNumber+".txt"
		pickle.dump(self.terms, open(filename, "wb"))
		#reset memory
		self.tokenCount = 0
		#reset dictionary
		self.terms = dict()
		#increment number of index files created.
		self.fileCount += 1

	#merges all documents to a single index. 
	def merge(self):
		mergeTerms = dict()
		#iterate all block indexes created
		for x in range (0, self.fileCount):
			#load up file 
			fileNumber = str(x)
			filename = "C:\\Users\\Azn0Richard0\\Desktop\\Project2\\"+fileNumber+".txt"
			file = open(filename, 'rb')
			data = pickle.load(file)
			
			#tokens get posting_list that are added to mergeTerms
			for token in data:
				posting_list = data.get(token, [])
				merge_posting = mergeTerms.get(token, [])
				#if any terms are not found in the posting_list of the token put them in. 
				for doc_id in posting_list:
					if not doc_id in merge_posting:
						merge_posting.append(doc_id)
						mergeTerms[token] = merge_posting 
			file.close()
		
		#sort doc_ids in each posting list
		for token in mergeTerms:
			mergeTerms[token].sort()
		
		#sort dictionary
		sorted_token = sorted(mergeTerms.iterkeys())
		sorted_merge_terms = dict()
		for token in sorted_token:
			sorted_merge_terms[token] = mergeTerms.get(token)
			
		self.terms = sorted_merge_terms 
		self.write()
		
class IndexReader:
	def __init__(self, analyser, term_index, document_length_dict):
		self.analyser = analyser
		self.term_index = term_index
		self.document_length_dict = document_length_dict
		
	def term_frequency_query(self, query):
		#pre-process query
		queryTokens = self.analyser.tokenize(query)
		#calculate token frequency in query
		queryTokenFrequency = dict()
		for token in queryTokens:
			count = queryTokenFrequency.get(token, 0)
			count = count+1
			queryTokenFrequency[token] = count
		results = []
		#stores the rank of each document
		ranking = dict()
		
		#joins the posting list of each unique term in query and calculate score for ranking
		for token in queryTokenFrequency:
			#ignore the "or" in the queries.
			if not token == "or":
				#get the tokens in query put them in the results if the doc_id is not already there.
				posting_list = self.term_index.get(token, [])
				for doc_id in posting_list:	
					#generate score
					score = ranking.get(doc_id, 0)
					score = score + len(posting_list[doc_id])*queryTokenFrequency.get(token, 0)
					ranking[doc_id] = score
					if not doc_id in results:
						results.append(doc_id)
						
		#sort the ranking
		sorted_ranking = sorted(ranking.iteritems(), key=operator.itemgetter(1))
		
		#display ranking
		self.controlledDisplay(sorted_ranking)
		
	def okapi_BM25_query(self, query, k, b):
		#pre-process query
		queryTokens = self.analyser.tokenize(query)
		results = []
		
		#joins the posting list of each unique term in query and calculate score for ranking
		for token in queryTokens:
			#ignore the "or" in the queries.
			if not token == "or":
				#get the tokens in query put them in the results if the doc_id is not already there.
				posting_list = self.term_index.get(token, [])
				for doc_id in posting_list:	
					if not doc_id in results:
						results.append(doc_id)
		
		#compute idf
		token_idf = dict()
		for token in queryTokens:
			token_idf[token] = self.IDF(token)
		
		#compute average doc_length
		total_doc_length = 0.0
		for doc_id in self.document_length_dict:
			total_doc_length = total_doc_length + self.document_length_dict[doc_id]
		avg_doc_len = total_doc_length/len(self.document_length_dict)
		
		ranking = dict()
		#ranks the doc_ids
		for doc_id in results:
			score = 0
			for token in token_idf:
				posting_list = self.term_index.get(token, [])
				term_frequency_in_doc = 0
				if doc_id in posting_list:
					#generate score
					term_frequency_in_doc = len(posting_list[doc_id])
					doc_length = self.document_length_dict[doc_id]+0.0
					numerator = term_frequency_in_doc * (k + 1)
					denominator = term_frequency_in_doc + k * ( 1 - b + b * (doc_length/avg_doc_len))
					score = score + token_idf[token] * (numerator/denominator)
			ranking[doc_id] = score	
		
		#sort the ranking
		sorted_ranking = sorted(ranking.iteritems(), key=operator.itemgetter(1))	
		
		#display ranking
		self.controlledDisplay(sorted_ranking)
	
	def IDF(self, token):
		num_of_docs = len(self.document_length_dict)
		num_of_docs_with_q = len(self.term_index.get(token, []))
		
		#calculate idf
		numerator = num_of_docs - num_of_docs_with_q + 0.5
		denominator = num_of_docs_with_q + 0.5
		idf = math.log10(numerator/denominator)
		
		#return 0 if idf is negative
		if idf > 0:
			return idf
		else:
			return 0
	
	def or_query(self, query):
		#pre-process query
		queryTokens = self.analyser.tokenize(query)
		results = []
		for token in queryTokens:
			#ignore the "or" in the queries.
			if not token == "or":
				#get the tokens in query put them in the results if the doc_id is not already there.
				posting_list = self.term_index.get(token, [])
				for doc_id in posting_list:
					if not doc_id in results:
						results.append(doc_id)
		results.sort()
		self.display(results)
	
	def and_query(self, query):
		#pre-process query
		queryTokens = self.analyser.tokenize(query)
		results = []
		#append the posting list into results.
		for token in queryTokens:
			if not token == "and":
				results.append(self.term_index.get(token, []))
		#sort results by the term frequency, since multiple "and" should process from smallest frequency to largest
		results = self.sort_by_frequency(results)
		
		#intersect method as seen in FIGURE 1.7 of the course book
		and_result = results.pop(0)
		while and_result and results:
			and_result = self.intersect(and_result, results.pop(0))
		
		self.display(and_result)
		
	#sort array by term frequency. (smallest to largest)
	def sort_by_frequency(self, results):
		sorted_results = []
		#basically remove the smallest term frequency from one array and push into another sorting upon append. 
		while len(results) > 0:
			#get smallest term frequency
			small = None
			for posting_list in results:
				if not small:
					small = posting_list
				if len(posting_list) < len(small):
					small = posting_list
			
			#append to sorted array and remove from the unsorted 
			sorted_results.append(small)
			results.remove(small)
			
		return sorted_results
	
	#Method to get the doc_ids that match two posting lists. Method seen in FIGURE 1.6 of the book
	def intersect(self, list1, list2):
		answer = []
		iterator1 = iter(list1)
		iterator2 = iter(list2)
		doc1 = iterator1.next()
		doc2 = iterator2.next()
		while True:
			try:
				if doc1 == doc2:
					answer.append(doc1)
					doc1=iterator1.next()
					doc2=iterator2.next()
				elif doc1 < doc2:
					doc1 = iterator1.next()
				else:
					doc2 = iterator2.next()
			except:
				break
		return answer
	
	#display the results of the query
	def display(self, result):
		parser = Parser()
		#print each article in the result.
		for doc_id in result:
			print parser.get_document(doc_id)
			print " ------------ "
			
	#display the results one at a time and controlled by user input
	def controlledDisplay(self, sorted_ranking):
		parser = Parser()
		
		#reverse list to display highest to lowest
		reverseRank = reversed(sorted_ranking)
		#display the doc_id and rank
		self.showRank(reverseRank)	

		#reverse list to display highest to lowest
		reverseRank = reversed(sorted_ranking)
		#display one document at a time
		for doc in reverseRank:
			print parser.get_document(doc[0])
			print " ------------ "
			selection = raw_input("Press 'Enter' to continue, else enter 'q' to quit: ")
			if selection == "q":
				break;
				
	#display document and score 		
	def showRank(self, sorted_ranking):
		rank = 1
		for doc_id in sorted_ranking:
			print str(rank)+". "+doc_id[0]+" - score: "+str(doc_id[1])
			rank = rank+1
			if (rank-1)%5 == 0:
				selection = raw_input("Press 'Enter' to continue, else enter 'q' to quit: ")
				if selection == "q":
					break;
		print " ------------ "
			
if __name__ == '__main__':		
	collection = dict()
	parser = Parser()
	analyser = Analyser()
	index_writer = IndexWriter(analyser, 0)

	
	print "now parsing document"
	for x in range(0, 22):
		fileNumber = "%02d" % (x,)
		path = "C:\\Users\\Azn0Richard0\\Desktop\\Project2\\corpus\\reut2-0"+fileNumber+".sgm"
		collection = parser.parse(path)
		index_writer.processPositional(collection)
		
	index_reader = IndexReader(analyser, index_writer.get_terms(), index_writer.get_document_length())
	print "parsing documents complete"
	
	while True:
		print "------------------------------------"
		print "Enter '1' to Query By Term Frequency"
		print "Enter '2' to Query By Okapi BM25"
		print "Enter 'q' to Quit"
		print "------------------------------------"
		selection = raw_input("Enter your choice: ")
		if selection == "q":
			break;
		elif selection == "1":
			query = raw_input("Enter Query: ")
			index_reader.term_frequency_query(query)
		elif selection == "2":
			print "b is default to 0.75"
			query = raw_input("Enter Query: ")
			k = float(raw_input("Enter k: "))
			index_reader.okapi_BM25_query(query, k, 0.75)
			

	
		
	