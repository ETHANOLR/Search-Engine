import json
import heapq

# Heap item in order to put them all in a priority queue.
# We customize it because we need to find the smallest term and merge them
class HeapItem:
    def __init__(self, token, data, index_file, position_iter):
        self.token = token
        self.data = data
        self.index_file = index_file
        self.position_iter = position_iter

    def __lt__(self, other):
        return self.token < other.token

    def __le__(self, other):
        return self.token <= other.token

# read the next term from index by using position iterator we write when we write inverted index
def read_next_term(index_file, position_iter):
    try:
        position = next(position_iter)
        index_file.seek(position[1])
        line = index_file.readline()
        token, data = next(iter(json.loads(line).items()))
        return HeapItem(token, data, index_file, position_iter)
    except StopIteration:
        return None

# get attribute from a heapitem so that we can pick out the data
def getattribute_from_heap(heapitem):
    return heapitem.token, heapitem.data, heapitem.index_file, heapitem.position_iter

# merge function implementing using a heap
def merge_subindex(file_paths, position_paths, output_file, output_position_file):
    #open all the index and position file so that we can make them one to one
    files = [open(single_file) for single_file in file_paths]
    position_iters = [iter(json.load(open(position)).items()) for position in position_paths]
    print(file_paths)
    print(position_paths)

    # initialize a priority queue
    heap = []

    # add the first term and data into the heap
    for file, position_iter in zip(files, position_iters):
        data = read_next_term(file, position_iter)
        if data:
            heapq.heappush(heap, data)

    # final position file
    current_position = 0
    output_position = {}

    # write the output
    with (open(output_file, 'w') as output_f):

        # while there is something in heap, we extract the smallest one(which is automatically implemented by priorityqueue)
        # we extract all the heapitem having the same token with the smallest one and get their data and frequency, merge them and write them to the output file
        # for all the file we have extracted a element, we get their next_term one by one and add them to the priorityqueue for extracting in the next loop
        # this can be done in getting the next term because we have already sorted the inverted index by their terms.
        while heap:
            smallest = heapq.heappop(heap)
            token = smallest.token
            [freq, postings] = smallest.data
            origin_file = smallest.index_file
            origin_position_iter = smallest.position_iter

            freq_merge = freq
            postings_merge = postings.copy()
            files_to_update = [(origin_file, origin_position_iter)]

            while heap and heap[0].token == token:
                _, [next_freq, next_postings], next_file, next_position_iter = getattribute_from_heap(heapq.heappop(heap))
                freq_merge += next_freq
                for docID, tfidf in next_postings.items():
                    postings_merge[docID] = tfidf
                files_to_update.append((next_file, next_position_iter))

            for file, position_iter in files_to_update:
                next_data = read_next_term(file, position_iter)
                if next_data:
                    heapq.heappush(heap, next_data)

            # for merge we sort the final result by tfidf
            postings_merge = {key: postings_merge[key] for key in sorted(postings_merge,key = lambda k:postings_merge[k], reverse = True)}
            output_f.write(json.dumps({token: [freq_merge, postings_merge]}) + '\n')

            # also we record where we write the term, and make them into position index
            output_position[token] = current_position
            current_position = output_f.tell()

    # write position index
    with open(output_position_file, 'w') as position_f:
        json.dump(output_position, position_f)

    # close all the files.
    for f in files:
        f.close()


