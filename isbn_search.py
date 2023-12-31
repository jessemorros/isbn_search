import streamlit as st
st.set_page_config(
    page_title="ISBN Search",
    page_icon="cl_favicon.png",
    layout="wide",
    initial_sidebar_state="expanded")
import streamlit.components.v1 as components
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import re 
import time
import socket
from isbnlib import *
import itertools
import pandas as pd
from bs4 import BeautifulSoup
import lxml


# side bar navigation 
st.sidebar.markdown('''
    ### ISBN Search  
    ''')
st.sidebar.markdown('''
    various tools for gathering book metadata  
    works best with print isbns
    ''')
# side bar navigation 

# set session state
if 'isbn_message' not in st.session_state:
    st.session_state['isbn_message'] = None

# turn metadata into a dataframe
@st.cache_data
def loc_df(metadata):
    df = pd.DataFrame.from_dict(metadata,orient='index')                
    return df

@st.cache_data
def goob_df(metadata):
    df = pd.DataFrame.from_dict(metadata,orient='index')                
    return df

# main page
with st.form("Google books search"):
    
    isbn = st.text_input('Enter an isbn',label_visibility="hidden",placeholder='isbn')
    submitted = st.form_submit_button("Search")
    if submitted:
        new_isbns = []
        if is_isbn13(isbn):
            st.session_state['isbn_message'] = st.write(isbn,'is a valid ISBN 13')
            new_isbns.append(isbn)
        elif is_isbn10(isbn):
            st.session_state['isbn_message'] =st.write(isbn, 'is a valid ISBN 10')
            isbn13=to_isbn13(isbn)
            st.session_state['isbn_message'] =st.write(isbn,'as isbn 13: ',isbn13)
            new_isbns.append(isbn13)
        else:
            st.session_state['isbn_message'] =st.write(isbn,'not valid. Try one of these:')
            if len(isbn) == 13:
                if isbn.startswith('987'):
                    isbn_attempt = isbn.replace('987','978')
                    if is_isbn13(isbn_attempt):
                        new_isbns.append(isbn_attempt)
                else:
                    isbn_attempts = []
                    isbn_last_4 = isbn[-4:]
                    isbn_last_4_permutations = itertools.permutations(isbn_last_4)
                    
                    for permutation in isbn_last_4_permutations:
                        new_isbn = isbn[:-4] + "".join(permutation)
                        if is_isbn13(new_isbn):
                            new_isbns.append(new_isbn)
        if st.session_state['isbn_message'] is not None:
            st.write(st.session_state['isbn_message'])

        new_isbns = list(set(new_isbns))
        for isbn in new_isbns:
            isbn = isbn.strip()
            with st.expander(label=isbn,expanded=False):
                url = 'https://www.googleapis.com/books/v1/volumes?q=isbn:'+isbn+'&country=US'
                response = requests.get(url)
                data = response.json()
                if 'items' in data:
                    metadata= {'isbn':isbn}
                    if 'canonicalVolumeLink' in data['items'][0]['volumeInfo']:
                        gb_page = data['items'][0]['volumeInfo']['canonicalVolumeLink']                    
                    if 'imageLinks' in data['items'][0]['volumeInfo']:
                        cover_image = data['items'][0]['volumeInfo']['imageLinks']['thumbnail']
                        
                        st.markdown(
                            '''
                            [![Foo](''' + cover_image + ''')]('''+gb_page+''')
                            ''')
                    else:
                        st.markdown(''' 
                            [no cover image]('''+gb_page+''')
                        ''')      
                    if 'title' in data['items'][0]['volumeInfo']:
                        book_title = data['items'][0]['volumeInfo']['title']
                        metadata['title'] = book_title                    
                    if 'authors' in data['items'][0]['volumeInfo']:
                        author = data['items'][0]['volumeInfo']['authors']
                        if len(author) > 1:
                            authors = []
                            for i in author:
                                author_string = i
                                authors.append(author_string)
                            author = '; '.join(authors)
                        else:
                            author_string = author[0]
                            author_string = re.sub(r'(author)|(editor)','',author_string)
                            author_string = author_string.strip(" ,")
                            author = author_string
                        author = author.title()
                        metadata['author'] = author
                    if 'publisher' in data['items'][0]['volumeInfo']:
                        publisher = data['items'][0]['volumeInfo']['publisher']
                        metadata['publisher'] = publisher
                    if 'publishedDate' in data['items'][0]['volumeInfo']:
                        year = data['items'][0]['volumeInfo']['publishedDate']
                        year = year[:4]
                        metadata['copyright date'] = year
                    df = goob_df(metadata)                
                    st.table(df)
                else:
                    st.write('No metadata found for',isbn)


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
@st.cache_data
def get_loc_isbns(lccn):
    lccn = results[0]['number_lccn'][0]
    marc = 'https://lccn.loc.gov/'+lccn+'/marcxml'
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    response = session.get(marc)
    time.sleep(1)
    soup = BeautifulSoup(response.content, "lxml")
    isbns = soup.find_all('datafield', tag="020")
    return isbns
@st.cache_data
def sort_isbns(isbns):
    alt_isbns = []
    for isbn in isbns:
        alt = isbn.findAll('subfield')
        if len(alt) > 1:
            alt_isbn = alt[0].text
            isbn_format = alt[1].text
            alt_isbn_dict = {'format':isbn_format, 'alt_isbn':alt_isbn}
            alt_isbns.append(alt_isbn_dict)
        else:
            alt_isbn = alt[0].text
            isbn_format = 'alt_isbn'
            alt_isbn_dict = {'format':isbn_format, 'alt_isbn':alt_isbn}
            alt_isbns.append(alt_isbn_dict)
    return alt_isbns
@st.cache_data
def get_loc_isbns(results):
    if len(results) > 0:
        metadata= {'isbn':isbn}
        book_title = results[0]['item']['title']
        book_title = book_title.title()
        author = results[0]['item']['contributors']
        return_dict = {}
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
        return_dict['marc'] = marc
        lccn = results[0]['number_lccn'][0]
        isbns = get_loc_isbns(lccn)
        isbns = sort_isbns(isbns)            
        catalog_page = results[0]['aka'][1]
        return_dict['catalog_page'] = catalog_page            
        metadata['title'] = book_title
        metadata['author'] = author
        metadata['publisher'] = publisher
        metadata['copyright year'] = year
        for isbn_pair in isbns:
            for key,value in isbn_pair.items():
                if key == 'format':
                    isbn_format = value
                    isbn_format = isbn_format.strip(" ()'") 
                    format_label = isbn_format + ' isbn:'
                if key == 'alt_isbn':
                    alt_isbn = value
                    metadata[format_label] = alt_isbn
                    return_dict['metadata'] = metadata
    else:
        return_dict = {}             
    return return_dict



with st.form("loc_isbn_search"):
    st.write("Search the Library of Congress catalog")
    isbn = st.text_input('Enter an isbn',label_visibility="hidden",placeholder='isbn')
    submitted = st.form_submit_button("Search")
    if submitted:
        results = get_results(isbn)
        display = get_loc_isbns(results)
        if len(display) > 0:
            marc = display['marc']
            catalog_page = display['catalog_page']
            metadata = display['metadata'] 
            st.write('MARC record: ',marc)
            st.write('Library of Congress catalog: ',catalog_page)
            df = loc_df(metadata)                
            st.table(df)
        else:
            st.write('No metadata found for',isbn)
        with st.expander('json',expanded=False):
            st.json(results)



