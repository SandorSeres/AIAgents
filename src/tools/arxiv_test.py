
import urllib.request
import feedparser

# Base api query url
base_url = 'http://export.arxiv.org/api/query?'

# Search parameters
search_query = urllib.parse.quote('all:What is multi agent AI') # search 
start = 0                     # retrieve the first 5 results
max_results = 5

query = f'search_query={search_query}&start={start}&max_results={max_results}'

# perform a GET request using the base_url and query
response = urllib.request.urlopen(base_url + query).read()

# parse the response using feedparser
feed = feedparser.parse(response)

# print out feed information
print(f'Feed title: {feed.feed.title}')
print(f'Feed last updated: {feed.feed.updated}')

# print opensearch metadata
print(f'totalResults for this query: {feed.feed.opensearch_totalresults}')
print(f'itemsPerPage for this query: {feed.feed.opensearch_itemsperpage}')
print(f'startIndex for this query: {feed.feed.opensearch_startindex}')

# Run through each entry, and print out information
for entry in feed.entries:
    print('e-print metadata')
    print(f'arxiv-id: {entry.id.split("/abs/")[-1]}')
    print(f'Published: {entry.published}')
    print(f'Title:  {entry.title}')
    
    # feedparser v5.0.1 correctly handles multiple authors, print them all
    try:
        print(f'Authors:  {", ".join(author.name for author in entry.authors)}')
    except AttributeError:
        pass

    # get the links to the abs page and pdf for this e-print
    for link in entry.links:
        if link.rel == 'alternate':
            print(f'abs page link: {link.href}')
        elif link.title == 'pdf':
            print(f'pdf link: {link.href}')
    
    # The journal reference, comments and primary_category sections live under 
    # the arxiv namespace
    try:
        journal_ref = entry.arxiv_journal_ref
    except AttributeError:
        journal_ref = 'No journal ref found'
    print(f'Journal reference: {journal_ref}')
    
    try:
        comment = entry.arxiv_comment
    except AttributeError:
        comment = 'No comment found'
    print(f'Comments: {comment}')
    
    # Primary category
    print(f'Primary Category: {entry.tags[0]["term"]}')
    
    # Lets get all the categories
    all_categories = [t['term'] for t in entry.tags]
    print(f'All Categories: {", ".join(all_categories)}')
    
    # The abstract is in the <summary> element
    print(f'Abstract: {entry.summary}')
