"""
Main file for utils job
"""

import os
import re
import json
import argparse
import pandas as pd

from tqdm import tqdm
from collections import Counter
from textractor import Textractor
from pdf2image import convert_from_path
from textractor.data.constants import TextractFeatures

extractor = Textractor(profile_name="default")

def extract_page_as_image(pdf_path, page_number, output_image_path, crop_coords=None, extra_margin_mm=0, default_dpi=300):
    """
    This Python function extracts a specific page from a PDF file as an image and saves it to a
    specified output path, with an option to crop the image based on provided coordinates.

    Args:
      pdf_path: The `pdf_path` parameter in the `extract_page_as_image` function is the file path to the
    PDF from which you want to extract a specific page as an image. This function uses the
    `convert_from_path` function to extract images from the PDF file.
      page_number: The `page_number` parameter in the `extract_page_as_image` function represents the
    specific page number in the PDF document that you want to extract as an image. This function will
    extract the page with the corresponding page number from the PDF and save it as an image file.
      output_image_path: The `output_image_path` parameter in the `extract_page_as_image` function is
    the file path where the extracted image will be saved as a PNG file. You should provide the full
    file path including the file name and extension where you want the image to be saved. For example,
    it could be
      crop_coords: The `crop_coords` parameter in the `extract_page_as_image` function is a list of
    coordinates that define a rectangular region to crop from the extracted page image. The coordinates
    should be in the format of `(x, y)` pairs, where `x` represents the horizontal position and `y`
    represents the vertical position.
      extra_margin_mm: The `extra_margin_mm` parameter specifies the extra margin to add to each side
    of the cropping rectangle in millimeters. Default is 2mm.
      default_dpi: The `default_dpi` parameter specifies the default DPI to use if the image does not
    have DPI information. Default is 300 DPI.
    """

    images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number)

    if crop_coords:
        dpi = images[0].info.get('dpi', (default_dpi,))[0]  
        extra_margin_px = int(extra_margin_mm * dpi / 25.4)  

        left = min(point[0] for point in crop_coords) - extra_margin_px
        top = min(point[1] for point in crop_coords) - extra_margin_px
        right = max(point[0] for point in crop_coords) + extra_margin_px
        bottom = max(point[1] for point in crop_coords) + extra_margin_px

        left = max(0, left)
        top = max(0, top)
        right = min(images[0].width, right)
        bottom = min(images[0].height, bottom)

        images[0] = images[0].crop((left, top, right, bottom))

    images[0].save(output_image_path, 'PNG')



def parse_cells(raw_cells):
    """
    The function `parse_cells` extracts relevant information from raw cell data in a specific format and
    returns a list of tuples containing row, column, rowspan, colspan, and text for each cell.
    
    Args:
      raw_cells: It looks like the code you provided is a function called `parse_cells` that takes a
    list of raw cell data as input and parses each cell to extract relevant information such as row,
    column, rowspan, colspan, text, etc.
    
    Returns:
      The `parse_cells` function is returning a list of tuples, where each tuple represents a cell in a
    table. Each tuple contains the following information about the cell: row number, column number,
    rowspan, colspan, and the text content of the cell.
    """

    cells = []

    for cell in raw_cells:
        match = re.match(r'<Cell: \((\d+),(\d+)\), Span: \((\d+), (\d+)\), Column Header: (True|False), MergedCell: (True|False)>', str(cell))
        row, col, rowspan, colspan, is_header, is_merged = match.groups()
        row, col, rowspan, colspan = int(row), int(col), int(rowspan), int(colspan)
        text = str(cell).split('>')[1].strip()
        cells.append((row, col, rowspan, colspan, text))

    return cells


def create_expanded_dataframe(cells):
    """
    The function `create_expanded_dataframe` takes a list of cells with row, column, rowspan, colspan,
    and text information and creates a pandas DataFrame with the cells expanded based on the rowspan and
    colspan values.
    
    Args:
      cells: A list of tuples where each tuple represents a cell in a table. Each tuple contains the
    following elements:
    
    Returns:
      The function `create_expanded_dataframe` returns a pandas DataFrame that has been created and
    expanded based on the input cells provided. The DataFrame is structured with the text values from
    the cells expanded into the appropriate rows and columns based on the rowspan and colspan values
    specified in the input.
    """

    max_row = max(cell[0] for cell in cells)
    max_col = max(cell[1] for cell in cells)
    table = [['' for _ in range(max_col)] for _ in range(max_row)]

    for cell in cells:
        row, col, rowspan, colspan, text = cell
        for r in range(rowspan):
            for c in range(colspan):
                table[row - 1 + r][col - 1 + c] = text

    df = pd.DataFrame(table)
    df.columns = df.iloc[0]
    df = df.drop(0).reset_index(drop=True)
    
    return df


def parse_command_line_arguments():
    """
    The function `parse_command_line_arguments` defines a parser for command line arguments related to
    input PDF document and output JSON document paths.
    
    Returns:
      The function `parse_command_line_arguments` is returning the parsed command line arguments using
    the `argparse` module in Python. It defines two arguments `--document_path` and `--save_path` with
    their respective types and help messages. The function then parses the command line arguments and
    returns the parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Parse a PDF document and save it as a JSON file.')
    parser.add_argument('--document_path', type=str, required=True, help='Path to the PDF document to be parsed')
    parser.add_argument('--save_folder', type=str, help='Folder to save the JSON file', default=None)
    return parser.parse_args()


def prepare_counter(elements):
    """
    The function `prepare_counter` takes a list of elements, extracts text based on their category,
    combines the text, and returns a Counter object with the frequency of each text element.
    
    Args:
      elements: It seems like the code snippet you provided is a function called `prepare_counter` that
    takes a list of elements as input and categorizes them based on their category attribute. It then
    creates a counter of the text content for elements with categories "Title", "Text", and
    "NarrativeText", and
    
    Returns:
      The function `prepare_counter` returns a Counter object that contains the count of each unique
    text element from the input list of elements, categorized by "Title", "Text", and "NarrativeText".
    """

    titles_text = [el.text for el in elements if el.category == "Title"]
    text_text = [el.text for el in elements if el.category == "Text"]
    narrtext_text = [el.text for el in elements if el.category == "NarrativeText"]

    all_text = titles_text + narrtext_text + text_text
    all_counter = Counter(all_text)

    return all_counter


def clean_text(text):
    """
    The `clean_text` function takes a text input, removes any newline characters, extra whitespaces, and
    then returns the cleaned text.
    
    Args:
      text: The `clean_text` function takes a text input and performs the following cleaning operations:
    
    Returns:
      The clean_text function returns the cleaned text with removed extra whitespaces and newline
    characters. If the input text is not a string, it returns the input text as it is.
    """

    if isinstance(text, str):
        text = text.replace('\n', ' ') 
        text = ' '.join(text.split())
        return text.strip()
    else:
        return text
    

def create_parsed_dictionary(elements, all_counter, pdf_path):
    """
    This Python function `create_parsed_dictionary` parses elements based on their category and
    generates a dictionary with parsed content organized by pages.
    
    Args:
      elements: Elements is a list of objects representing different components of a document, such as
    text, titles, lists, tables, etc. Each element has a category attribute indicating the type of
    component it represents (e.g., ListItem, NarrativeText, Table, Text, Title, PageBreak). The function
    `create
      all_counter: The `all_counter` parameter seems to be a dictionary that likely stores the count of
    occurrences for different elements. It is used in the function to check if the count of a specific
    element is less than 10 and not equal to 0 before including it in the parsed document.
      pdf_path: The `pdf_path` parameter in the `create_parsed_dictionary` function is the file path to
    the PDF document that you want to parse and extract information from. This function processes
    different elements within the PDF document such as PageBreak, ListItem, NarrativeText, Table, Text,
    and Title to create a
    
    Returns:
      The function `create_parsed_dictionary` returns a parsed document in the form of a dictionary
    where each key represents a page and the value is the parsed content for that page.
    """

    parsed_doc = {'page_1': ''}
    curr_page = 'page_1'
    page_number = 1

    for el in tqdm(elements, desc="Processing elements"):
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
            parsed_doc[curr_page] += '\n'
            page_number = el.metadata.page_number 
            coords = el.metadata.coordinates.points 

            output_image_path = 'output.png'
            extract_page_as_image(pdf_path, page_number, output_image_path, coords)
            document = extractor.analyze_document(file_source='output.png', features=[TextractFeatures.TABLES])
            if len(document.tables) > 0:
                for k in range(len(document.tables)):
                    raw_cells = document.tables[k].table_cells[:]  
                    parsed_cells = parse_cells(raw_cells)
                    df = create_expanded_dataframe(parsed_cells)
                    df_cleaned = df.applymap(clean_text)
                    df_cleaned.columns = [clean_text(col) for col in df_cleaned.columns]
                    parsed_doc[curr_page] += df_cleaned.to_markdown(index=False)
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
  The function `save_parsed_document` saves a parsed document to a specified file path in JSON format.

  Args:
    parsed_doc: The `parsed_doc` parameter is typically a Python dictionary or list that has been
  parsed from a document or data source. It contains structured data that you want to save to a file.
    save_path: The `save_path` parameter in the `save_parsed_document` function is the file path where
  the parsed document will be saved. It should be a string representing the location where you want to
  save the parsed document in JSON format.
  """
  with open(save_path, 'w') as f:
      json.dump(parsed_doc, f)