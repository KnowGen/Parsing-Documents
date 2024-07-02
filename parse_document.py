import argparse
import json
import os

from textractor.data.constants import TextractFeatures
from unstructured.partition.pdf import partition_pdf
from pdf2image import convert_from_path
from textractor import Textractor
from collections import Counter

def extract_page_as_image(pdf_path, page_number, output_image_path, crop_coords=None):
    images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number)
    
    if crop_coords:
        left = min(point[0] for point in crop_coords)
        top = min(point[1] for point in crop_coords)
        right = max(point[0] for point in crop_coords)
        bottom = max(point[1] for point in crop_coords)
        images[0] = images[0].crop((left, top, right, bottom))
    images[0].save(output_image_path, 'PNG')


def parse_command_line_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('--document_path', type=str, help='The path to the input PDF document.')
    parser.add_argument('--save_path', type=str, help='The path where to print the parsed json document.')

    return parser.parse_args()

def prepare_counter(elements):
    # Extract Titles and text and setup the preprocess
    titles_text = [el.text for el in elements if el.category == "Title"]
    text_text = [el.text for el in elements if el.category == "Text"]
    narrtext_text = [el.text for el in elements if el.category == "NarrativeText"]

    all_text = titles_text + narrtext_text + text_text
    all_counter = Counter(all_text)

    return all_counter

def create_parsed_dictionary(elements, all_counter, pdf_path):
    parsed_doc = {'page_1': ''}
    curr_page = 'page_1'
    page_number = 1

    for el in elements:
        # New page -> Create new entry in the dictionary.
        if el.category == 'PageBreak':
            page_number += 1
            curr_page = f"page_{page_number}"
            parsed_doc[curr_page] = ''

        elif el.category == 'ListItem':
            if all_counter[el.text] < 10 and all_counter[el.text] != 0:
                parsed_doc[curr_page] += el.text
                parsed_doc[curr_page] += '\n'
        
        elif el.category == 'NarrativeText':
            if all_counter[el.text] < 10 and all_counter[el.text] != 0:
                parsed_doc[curr_page] += el.text
                parsed_doc[curr_page] += ' '

        elif el.category == 'Table':
            extractor = Textractor(profile_name="default")
            parsed_doc[curr_page] += '\n'
            page_number = el.metadata.page_number 
            coords = el.metadata.coordinates.points 
            output_image_path = 'output.png'
            extract_page_as_image(pdf_path, page_number, output_image_path, coords)
            document = extractor.analyze_document(file_source='output.png',features=[TextractFeatures.TABLES])
            if len(document.tables) > 0:
                for k in range(len(document.tables)):
                    table_format = document.tables[k].to_pandas().to_html()
                    parsed_doc[curr_page] += table_format
                    parsed_doc[curr_page] += '\n'
            else:
                pass

            if os.path.exists('output.png'):
                os.remove('output.png')
            else:
                pass

        elif el.category == 'Text':
            if all_counter[el.text] < 10 and all_counter[el.text] != 0:
                parsed_doc[curr_page] += el.text
                parsed_doc[curr_page] += ' '

        elif el.category == 'Title':
            if page_number == 1:
                parsed_doc[curr_page] += el.text
                parsed_doc[curr_page] += '\n'
            elif all_counter[el.text] < 10 and all_counter[el.text] != 0:
                parsed_doc[curr_page] += el.text
                parsed_doc[curr_page] += '\n'
        
    parsed_doc = {k:v for k,v in parsed_doc.items() if v}   

    return parsed_doc

def save_parsed_document(parsed_doc, save_path):
    """
    Saves the parsed document to the specified path
    """
    with open(save_path, 'w') as f:
        json.dump(parsed_doc, f)




def main():
    args = parse_command_line_arguments()
    elements = partition_pdf(filename=args.document_path, infer_table_structure=True, include_page_breaks=True, languages=['ita', 'eng'])
    all_counter = prepare_counter(elements=elements)

    parsed_doc = create_parsed_dictionary(elements, all_counter, args.document_path)

    save_path = args.document_path.replace('.pdf', '.json')
    save_parsed_document(parsed_doc, save_path)

if __name__ == "__main__":
    main()
