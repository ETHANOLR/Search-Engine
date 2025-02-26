import tkinter as tk
from tkinter import ttk
from Retrive import  Retriever, NoResultException
import time
# build a retriever with inverted index, bigram index, position for inverted index and position for bigram.
Retriever = Retriever("invertedIndex.json", "docID.json", "positions.json", "positions2.json", "bigramindex.json")

# search button function, getting all the result url from Retriever.retrieve(query, number of result)
# we require the user to put how many result he wants
def search():
    start = time.perf_counter()
    query = entry.get()
    try:
        # Get the number of results specified by the user
        num_results = int(num_results_entry.get())
    except ValueError:
        listbox.insert(tk.END, "Please enter a valid number of results.")
        return

    listbox.delete(0, tk.END)
    try:
        results = Retriever.retrieve(query, num_results)
        for url in results:
            listbox.insert(tk.END, url)
    except NoResultException:
        listbox.insert(tk.END, "No results found for the query.")
    end = time.perf_counter()
    print(f"Search took {end - start} seconds.")

# A tkinter user interface.
root = tk.Tk()
root.title("Search Engine")

# Entry widget for query input
entry = ttk.Entry(root, width=50)
entry.grid(row=0, column=0, padx=10, pady=10)

# Entry widget for the number of results
num_results_entry = ttk.Entry(root, width=10)
num_results_entry.grid(row=1, column=1, padx=10, pady=10)

# Label for the number of results entry
num_results_label = ttk.Label(root, text="Number of Results:")
num_results_label.grid(row=1, column=0, sticky=tk.E, padx=10, pady=10)

# Normal search button
normal_search_button = ttk.Button(root, text="Search", command=search)
normal_search_button.grid(row=2, column=0, columnspan=2, padx=50, pady=10)

# Listbox to display results
listbox = tk.Listbox(root, width=80, height=20)
listbox.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

# Close button
close_button = ttk.Button(root, text="Close", command=root.destroy)
close_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

# Run the application
root.mainloop()