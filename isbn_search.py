import streamlit as st
st.set_page_config(
    page_title="ISBN Search",
    page_icon="cl_favicon.png",
    layout="wide",
    initial_sidebar_state="expanded")
import streamlit.components.v1 as components
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import re 
import time
import socket



# side bar navigation 
st.sidebar.markdown('''
    ### ISBN Search  
    ''')
st.sidebar.markdown('''
    various tools for gathering book metadata  
    works best with print isbns
    ''')
# side bar navigation 


# main page
# st.title('Content Librarian Tool Kit')



with st.expander(label="custom google search of publisher websites",expanded=False):
    with st.container():        
        components.html("""
            <style>
                body {  display: block;
                        overflow: auto;
                        height: fit-content;
            }

            </style>
            <script async src="https://cse.google.com/cse.js?cx=72e8818333f454e28"></script>
            <div class="gcse-searchbox"></div>

            <div class="gcse-searchresults"></div>




            """,
        height=400, scrolling=True
            )
@st.cache_data
def get_results(isbn):
    url = 'https://www.loc.gov/search/?q='+isbn+'&fo=json'
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    response = session.get(url)
    time.sleep(1)
    if response.status_code == 200:
        data = response.json()              
        results= data['results']
    else:
        results = []
    return results


with st.form("loc_isbn_search"):
    st.write("Search the Library of Congress catalog")
    isbn = st.text_input('Enter an isbn',label_visibility="hidden",placeholder='isbn')
    submitted = st.form_submit_button("Search")
    if submitted:
        results = get_results(isbn)
        if len(results) > 0:
            book_title = results[0]['item']['title']
            book_title = book_title.title()
            author = results[0]['item']['contributors']
            if len(author) > 1:
                authors = []
                for i in author:
                    author_string = i
                    if re.search(r'(author)|(editor)',author_string):
                        author_string = re.sub(r'(author)|(editor)','',author_string)
                        author_string = author_string.strip(" ,")
                        author_list = author_string.split(',')
                        author_first = author_list[1].strip()
                        author_last = author_list[0].strip()
                        author_string = author_first + ' ' + author_last
                        authors.append(author_string)
                        author = '; '.join(authors)
            else:
                author_string = author[0]
                author_string = re.sub(r'(author)|(editor)','',author_string)
                author_string = author_string.strip(" ,")
                author_list = author_string.split(',')
                author_first = author_list[1].strip()
                author_last = author_list[0].strip()
                author_string = author_first + ' ' + author_last
                author = author_string
            created_published = results[0]['item']['created_published']
            publishing = created_published[0]
            publishing = publishing.split(":")[1]
            publishing = publishing.strip(" ,.")
            publisher = publishing[:-4]
            publisher = publisher.strip(" ,.")
            publisher = publisher.title()
            year = publishing[-4:]
            marc = results[0]['id']
            catalog_page = results[0]['aka'][1]            
            st.write('Title: ',book_title)
            st.write('Author: ',author)
            st.write('Publisher: ',publisher)
            st.write('Copyright Date: ',year)
            st.write()
            st.write('MARC record: ',marc)
            st.write('Library of Congress catalog: ',catalog_page)

        else:
            st.write('No results found for ',isbn)
        with st.expander('json',expanded=False):
            st.json(results)


with st.form("gb_isbn_search"):
    st.write("Search Google Books")
    isbn = st.text_input('Enter an isbn',label_visibility="hidden",placeholder='isbn')
    submitted = st.form_submit_button("Search")
    if submitted:
        url = 'https://www.googleapis.com/books/v1/volumes?q=isbn:'+isbn
        proxy = socket.gethostbyname(hostname)
        response = requests.get(url,proxies=proxy)
        data = response.json()
        if 'items' in data:
            if 'title' in data['items'][0]['volumeInfo']:
                book_title = data['items'][0]['volumeInfo']['title']
                st.write('Title: ',book_title)
            if 'authors' in data['items'][0]['volumeInfo']:
                author = data['items'][0]['volumeInfo']['authors'] 
                if len(author) > 1:
                    authors = []
                    for i in author:
                        author_string = i
                        if re.search(r'(author)|(editor)',author_string):
                            author_string = re.sub(r'(author)|(editor)','',author_string)
                            author_string = author_string.strip(" ,")
                            author_string = author_string.split(',')
                            authors.append(author_string)
                            author = '; '.join(authors)
                else:
                    author_string = author[0]
                    author_string = re.sub(r'(author)|(editor)','',author_string)
                    author_string = author_string.strip(" ,")
                author = author_string
                author = author.title()
                st.write('Author: ',author)
            if 'publisher' in data['items'][0]['volumeInfo']:
                publisher = data['items'][0]['volumeInfo']['publisher']
                st.write('Publisher: ',publisher)
            if 'publishedDate' in data['items'][0]['volumeInfo']:
                year = data['items'][0]['volumeInfo']['publishedDate']
                year = year[:4]
                st.write('Copyright Date: ',year)
        else:
            st.write('No results found for ',isbn)
        with st.expander('json',expanded=False):
            st.json(data)

