from nltk.stem.porter import PorterStemmer
import re
from bs4 import BeautifulSoup
import os
import json
from Posting import Posting
from Write import write_invertedIndex,write_docID
import math
from Merge import merge_subindex
#all the stop words
finger_print = []
first = True
NUM_OF_DOCUMENTS = 55393
THRESHOLD = 10000
class InvertedIndexer:

    #initialize the inverted indexer
    # invertedDict
    #   key : token
    #   value : [frequency, [list of posting having the term]]
    # docDict:
    #   key: docID(int)
    #   value: doc_name
    # docCounter: the counter use to count the number of total files
    # num
    def __init__(self):
        self.bi_gram_invertedDict = {}
        self.invertedDict = {}
        self.docDict = {}
        self.docCounter = 0

    # stemmer
    def stem(self, tokens):
        #use the porterstemmer from nltk
        stemmer = PorterStemmer()
        stemmed_tokens = []
        for token in tokens:
            stemmed_tokens.append(stemmer.stem(token))
        return stemmed_tokens

    # tokenizer
    def tokenizer(self, content):
        # use re library for tokenizer
        tokens = self.stem(re.findall(r'[A-Za-z0-9]+', content.lower()))
        #tokens = re.findall(r'[A-Za-z0-9]+', content.lower())
        return tokens

    # compute the word frequency in each file
    def computeWordFrequencies(self, listToken):
        return_dic = {}
        for word in listToken:
            if word in return_dic:
                return_dic[word] += 1
            else:
                return_dic[word] = 1
        return return_dic

    # create a single posting for a token and a file, consisting docID and the token count in that file
    def createPosting(self, docID, fre):
        return Posting(docID, fre)


    # get the content from the html json file, return both the important file and normal file
    def getContent(self, html):
        important_tags = ["b", "strong", "h1", "h2", "h3", "title"]
        important_content = ""
        soup = BeautifulSoup(html, 'html.parser')
        #get all the text from important tag and extract the text for the following get_text() in order to not make duplicate token
        for tag in important_tags:
            for token in soup.find_all(tag):
                important_content += token.extract().get_text() + " "
        content = soup.get_text(separator = ' ', strip = True)
        return important_content.strip(), content.lower()

    # get all the text for similarity test
    def content_for_similarity(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        content = soup.get_text(separator = ' ', strip = True)
        return content.lower()

    # from the given token, we make each 2 words a pair and make them a bigram phrase
    def get_bi_gram(self, tokens):
        result = []
        for i in range(len(tokens)-1):
            result.append(tokens[i] + " " + tokens[i+1])
        return result

    # update the inverted index
    def updateInvertedDict(self, docID, tokens, important, invertedDict):
        # first update the important, if the word is in important tage, we make the 2 * frequency of that word
        for token in important:
            freq = 2 * important[token]
            if token in tokens:
                freq += tokens[token]
            singlePosting = self.createPosting(docID, freq)
            if token in invertedDict:
                invertedDict[token][0] += 1
                invertedDict[token][1].append(singlePosting)
            else:
                single_list = [1, [singlePosting]]
                invertedDict[token] = single_list
        # then update the normal file, in here we remove the file already in important list, we update frequency
        for token in tokens:
            if token not in important:
                singlePosting = self.createPosting(docID, tokens[token])
                if token in invertedDict :
                    invertedDict[token][0] += 1
                    invertedDict[token][1].append(singlePosting)
                else:
                    single_list = [1, [singlePosting]]
                    invertedDict[token] = single_list

    # tfidf = (1 + log(frequency)) * log(NUM_OF_DOCUMENT/ how many document have that word)
    def compute_tfidf(self, invertedDict):
        for token in invertedDict:
            for single_posting in invertedDict[token][1]:
                single_posting.tfidf = (1 + math.log(single_posting.frequency, 10)) * math.log(NUM_OF_DOCUMENTS * 1.0/invertedDict[token][0], 10)

    #sort each inverted index by their tfidf so that it is more efficient when we want to choose some contenders in the retrieve search
    def sort_by_tfidf(self, invertedDict):
        for token in invertedDict:
            invertedDict[token][1] = sorted(invertedDict[token][1], key = lambda posting: posting.tfidf, reverse = True)

    # sort the inverted index by term so we can merge them at the end
    def sort_by_term(self, invertedDict):
        return {key: invertedDict[key] for key in sorted(invertedDict)}

    # get the ID from url and add the counter by 1
    def getID(self, docName):
        self.docDict[self.docCounter] = docName
        temp = self.docCounter
        self.docCounter += 1
        return temp

    # get the html json file dict for future use
    def openHTML(self, path):
        with open(path, 'r') as single_html:
            data = json.load(single_html)
        return data


    # output all the result to result.txt and docID.txt(This is just a show result in M1 not for inverted index file)
    def writeResult(self):
        with open('result.txt', 'w') as result:
            result.write("unique page total:" + str(self.docCounter) + '\n')
            result.write("unique word: " + str(len(self.invertedDict)) + '\n')
            print_fre = dict(sorted(self.invertedDict.items(), key = lambda kv: kv[1][0], reverse = True))
            for token in print_fre:
                result.write(token + ':')
                result.write('frequency: ' + str(self.invertedDict[token][0]) + ', all the file: ')
                #result.write(str(len(self.invertedDict[token][1])) + " " + str(len(self.invertedDict[token][2])) + "\n")
                for one_posting in self.invertedDict[token][1]:
                    #result.write(self.docDict[fileId] + ', ')
                    result.write(str(one_posting.docID) + ' ' + str(one_posting.frequency))
                    result.write('\n')
        with open('docID.txt', 'w') as result:
            for ID, filename in self.docDict.items():
                result.write(str(ID) + ' ' + filename + '\n')

    # similarity test fingerprint, we make each three words a group hash and put them in a list if the hash is divisible by 4.
    # We calculate for every fg we have if it is similar to other files, if not, add the list to global finger_print if it is similar we skip that file
    def similarity_test(self, words):
        single_fg = []
        for index in range(len(words) - 2):
            single_list = [words[index], words[index + 1], words[index + 2]]
            single_hash = hash("".join(single_list))
            if single_hash % 4 == 0:
                single_fg.append(single_hash)
        # for every fingerprint we have, we compute the fingerprint using
        # intersection / union. if similarity is bigger than 0.8, not access it.
        global finger_print
        global first
        if first:
            finger_print.append(single_fg)
            first = False
        for fg in finger_print:
            intersection = len(set(single_fg).intersection(set(fg)))
            union = len(set(single_fg).union(set(fg)))
            if union != 0 and intersection * 1.0 / union > 0.8:
                print("it is similar!")
                return False
            else:
        # if valid, we append the new fingerprint to our fingerprint list
                finger_print.append(single_fg)
                print('correct')
                return True

    # the main running function. Loop through each file and tokenize it. Update the inverted index and doc counter and finally write result to result file.
    def getInvertedIndex(self, root):
        n = 0
        index = 1
        index_file = []
        index_file_bigram = []
        position_file = []
        position_file_bigram = []
        with open('url_to_filename.txt', 'w') as f:
            for dirpath, dirnames, filenames in os.walk(root):
                for filename in filenames:
                    #try:
                    filepath = os.path.join(dirpath, filename)
                    html_content = self.openHTML(filepath)['content']
                    url = self.openHTML(filepath)['url']
                    total = self.tokenizer(self.content_for_similarity(html_content))
                    if not self.similarity_test(total):
                        continue
                    important_content, content = self.getContent(html_content)
                    token_important = self.tokenizer(important_content)
                    token_content = self.tokenizer(content)
                    token_dict_important = self.computeWordFrequencies(token_important)
                    token_dict_content = self.computeWordFrequencies(token_content)

                    #process bigram
                    token_important_bigram = self.get_bi_gram(token_important)
                    token_normal_bigram = self.get_bi_gram(token_content)
                    token_dict_important_bigram = self.computeWordFrequencies(token_important_bigram)
                    token_dict_content_bigram = self.computeWordFrequencies(token_normal_bigram)
                    #print(filename)
                    #print(token_dict_content)
                    ID = self.getID(url)
                    self.updateInvertedDict(ID, token_dict_content, token_dict_important, self.invertedDict)
                    self.updateInvertedDict(ID, token_dict_content_bigram, token_dict_important_bigram, self.bi_gram_invertedDict)
                    n += 1
                    f.write(url + ' ' + filename + '\n')
                    print(n)
                    # If we have reach a threshold of file, we write it to the file to merge afterward
                    # index is the counter to count how many sub index we have and n is the number of file we have viewed.
                    # we store the sub index to subindex directory in this assignment directory
                    global THRESHOLD
                    if n >= THRESHOLD:
                        self.compute_tfidf(self.invertedDict)
                        self.sort_by_tfidf(self.invertedDict)
                        self.compute_tfidf(self.bi_gram_invertedDict)
                        self.sort_by_tfidf(self.bi_gram_invertedDict)
                        self.invertedDict = self.sort_by_term(self.invertedDict)
                        self.bi_gram_invertedDict = self.sort_by_term(self.bi_gram_invertedDict)
                        write_invertedIndex(self.bi_gram_invertedDict, f'subindex/bigramindex{index}.json',f'subindex/positions2{index}.json')
                        write_invertedIndex(self.invertedDict, f'subindex/invertedIndex{index}.json', f'subindex/positions{index}.json')
                        index_file.append(f'subindex/invertedIndex{index}.json')
                        position_file.append(f'subindex/positions{index}.json')
                        index_file_bigram.append(f'subindex/bigramindex{index}.json')
                        position_file_bigram.append(f'subindex/positions2{index}.json')
                        index+=1
                        n = 0
                        self.invertedDict = {}
                        self.bi_gram_invertedDict = {}

                #except Exception as e:
                    #print(str(e))
        self.compute_tfidf(self.invertedDict)
        self.sort_by_tfidf(self.invertedDict)
        self.compute_tfidf(self.bi_gram_invertedDict)
        self.sort_by_tfidf(self.bi_gram_invertedDict)
        self.invertedDict = self.sort_by_term(self.invertedDict)
        self.bi_gram_invertedDict = self.sort_by_term(self.bi_gram_invertedDict)
        write_invertedIndex(self.bi_gram_invertedDict, f'subindex/bigramindex{index}.json',f'subindex/positions2{index}.json')
        write_invertedIndex(self.invertedDict, f'subindex/invertedIndex{index}.json',f'subindex/positions{index}.json')
        index_file.append(f'subindex/invertedIndex{index}.json')
        position_file.append(f'subindex/positions{index}.json')
        index_file_bigram.append(f'subindex/bigramindex{index}.json')
        position_file_bigram.append(f'subindex/positions2{index}.json')

        #after wrote all the sub inverted index, we merge all them to our main inverted index and bigram index.
        merge_subindex(index_file, position_file, 'invertedIndex.json', 'positions.json')
        merge_subindex(index_file_bigram, position_file_bigram, 'bigramindex.json', 'positions2.json')
        write_docID(self.docDict, 'docID.json')

#main function
if __name__ == "__main__":
    # this is where I put my DEV document, if TA are testing this, you should change the base to where DEV.
    # DEV is too large to put in the submitted assignment
    #base = "C:\\Users\\10609\\Downloads\\developer\\DEV\\www_stat_uci_edu"
    base = "C:\\Users\\10609\\Downloads\\developer\\DEV"
    InvertedIndexer().getInvertedIndex(base)

