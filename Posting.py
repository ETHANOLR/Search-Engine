
class Posting:
    # Posting: docID, frequency, tfidf
    def __init__(self,docID, frequency,tfidf = 0):
        self.docID= docID
        self.frequency = frequency
        self.tfidf = 0

    # Comparing equality between 2 postings
    # This is design in Milestone 2 but not useful in Milestone 3.
    def __hash__(self):
        return self.docID

    def __eq__(self, other):
        self.frequency += other.frequency
        if self.docID == other.docID:
            return True
        return False

    # When we write to the inverted index, we only want the docID and tfidf so we return this
    def to_dict(self):
        return {
            self.docID:
            self.tfidf
        }


