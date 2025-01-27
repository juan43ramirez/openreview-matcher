"""
Downloads the papers for a set of a subsample of assignments for manual inspection.
Expects a 'data/sample_matchings_manual.pkl' file obtained from the evaluation script.
"""
import openreview
from rich import print
import pickle
import os
import pandas as pd
from tqdm import tqdm
import json

    
USERNAME = os.environ.get('OPEN_REVIEW_USERNAME')
PASSWORD = os.environ.get('OPEN_REVIEW_PASSWORD')


    
def get_pdf(client1, client2, note):
    """Very hacky as the note types can be List, Note, or dict"""
    errors = {}        
    # Try to get the pdf from the correct client
    try: 
        f = client2.get_attachment(note.id,'pdf')
        return f
    except Exception as e:
        errors["Client2"] = e
    try:
        f = client1.get_attachment(note.id,'pdf')
        return f
    except Exception as e:
        errors["Client1"] = e
    print("Error fetching pdf for note:", note.id)
    print(errors)
    return None
      
       
def get_note(client1, client2, note_id):
    try:
        return client2.get_notes(note_id)
    except openreview.OpenReviewException as e:
        print("Client2: Error fetching note. Trying client1", e)
        
    try:
        return client1.get_notes(note_id)
    except Exception as e:
        print("Client1: Error fetching note. Error was:", e)
    return None   

def get_notes_cache(client1, client2, sample_matchings, output_path):
    cache_file = f'{output_path}/.notes_cache.pkl'
    if not os.path.exists(cache_file):
        paper_notes = {}
    else:
        paper_notes = pickle.load(open(cache_file, 'rb'))
        
    all_papers = []
    for _, sample_df in sample_matchings.items():
        # For each paper in the assignment, save the paper note and paper pdf 
        papers = list(set(sample_df['paper_id']))
        reviewers = list(sample_df['max_affinity_papers'])
        reviewers = [r for sublist in reviewers for r in sublist]
        all_papers.extend(papers + reviewers)
    unique_papers = list(set(all_papers)) 
    
    notes_not_found = 0
    for paper_id in unique_papers:
        if paper_id in paper_notes:
            note = paper_notes[paper_id]
        else:
            note = get_note(client1, client2, paper_id)
            paper_notes[paper_id] = note
        if note is None:
            notes_not_found += 1
            continue
    print("Notes not found:", notes_not_found, "Total:", len(unique_papers))
    # Save the paper notes to a cache
    pickle.dump(paper_notes, open(cache_file, 'wb'))
    return paper_notes

def get_pdfs_cache(client1, client2, all_notes, output_path):
    cache_file = f'{output_path}/.pdf_cache.pkl'
    if not os.path.exists(cache_file):
        all_pdfs = {}
    else:
        all_pdfs = pickle.load(open(cache_file, 'rb'))
    could_not_fetch = 0
    for paper_id, note in all_notes.items():
        if note is None:
            all_pdfs[paper_id] = None
            could_not_fetch += 1
            continue
        
        if paper_id in all_pdfs:
            pdf_bin = all_pdfs[paper_id]
        else:
            pdf_bin = get_pdf(client1, client2, note)
            all_pdfs[paper_id] = pdf_bin
        if pdf_bin is None:
            could_not_fetch += 1
    print("PDFs not found:", could_not_fetch, "Total:", len(all_notes))
    pickle.dump(all_pdfs, open(cache_file, 'wb'))
    return all_pdfs
        


if __name__ == '__main__':
    sample_matchings_path = 'data/sample_matchings_manual.pkl'
    output_path = 'data/matching_info'
    
    # client1 = openreview.Client(
    #     baseurl='https://api.openreview.net',
    #     username=USERNAME, password=PASSWORD,
    # ) 
    # client2 = openreview.api.OpenReviewClient(
    #     baseurl='https://api2.openreview.net',
    #     username=USERNAME, password=PASSWORD,
    # )
    client1, client2 = None, None

    if not os.path.exists(output_path):
        os.makedirs(output_path)
    sample_matchings = pickle.load(open(sample_matchings_path, 'rb'))
    # paper_id -> note
    _all_notes = get_notes_cache(client1, client2, sample_matchings, output_path)
    all_notes = {}
    for paper_id, note in _all_notes.items():
        if isinstance(note, list):
            assert len(note) == 1, "Note list should have only one element"
            note = note[0]
        all_notes[paper_id] = note
            
    all_pdfs = get_pdfs_cache(client1, client2, all_notes, output_path)
   
    # Write the papers and notes to disk; one directory per matching and a 
    # sub-directory per paper 
    for matching_name, sample_df in sample_matchings.items():        
        mname = ''.join(matching_name.split('.')[:-1])
        if not os.path.exists(f'{output_path}/{mname}'):
            os.makedirs(f'{output_path}/{mname}')
            
        # Save the assignment as a jsonl file 
        sample_df = sample_df.drop('quality_metrics', axis=1)
        sample_df.to_json(f'{output_path}/{mname}/assignment.jsonl', index=False,
                          orient='records', lines=True, indent=2)
       
        papers = list(set(sample_df['paper_id'])) 
        for paper_id in papers: 
            note = all_notes.get(paper_id)
            if note is None:
                continue
            # Create a directory for the paper
            paper_path = f'{output_path}/{mname}/{paper_id}'
            if not os.path.exists(paper_path):
                os.makedirs(paper_path)
            # Save the paper note as a json 
            with open(f'{paper_path}/paper_note_{paper_id}.json', 'w') as f:
                json.dump(note.to_json(), f, indent=2)
            # Save the paper pdf
            pdf_path = f'{paper_path}/paper_pdf_{paper_id}.pdf'
            pdf_bin = all_pdfs.get(paper_id)
            if pdf_bin is not None:
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_bin)
            # Save the reviewer notes and pdfs 
            reviewers = sample_df[sample_df['paper_id'] == paper_id]['reviewers'].values[0]
            reviewers_papers = sample_df[sample_df['paper_id'] == paper_id]['max_affinity_papers'].values[0]
            for rid, rpaper_id in list(zip(reviewers, reviewers_papers)):
                # Returns dict of {paper_id: note}
                rnote = all_notes.get(rpaper_id)
                if rnote is None:
                    continue
                reviewer_note_path = f'{paper_path}/reviewer_note_{rid}_{rpaper_id}'
                # Save the reviewer's note as a json
                with open(f'{reviewer_note_path}.json', 'w') as f:
                    json.dump(rnote.to_json(), f, indent=2)
                # Save the reviewer's pdf
                reviewer_pdf_path = f'{paper_path}/reviewer_pdf_{rid}_{rpaper_id}'
                pdf_path = f'{reviewer_pdf_path}.pdf'
                pdf_bin = all_pdfs.get(rpaper_id)
                if pdf_bin is not None:
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_bin)
                