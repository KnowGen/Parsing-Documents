from utils import (
    parse_command_line_arguments,
    prepare_counter,
    create_parsed_dictionary,
    save_parsed_document
)

import os
import warnings

from unstructured.partition.pdf import partition_pdf
from transformers import logging



def main():
    """
    The main function parses a PDF document, creates a parsed dictionary, and saves it as a JSON file.
    """
    args = parse_command_line_arguments()

    logging.set_verbosity_error()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        elements = partition_pdf(filename=args.document_path, infer_table_structure=True, include_page_breaks=True, languages=['ita', 'eng'])
        all_counter = prepare_counter(elements=elements)
    
    parsed_doc = create_parsed_dictionary(elements, all_counter, args.document_path)
    
    base_filename = os.path.splitext(os.path.basename(args.document_path))[0]
    output_filename = base_filename + '.json'
    
    if args.save_folder:
        if not os.path.exists(args.save_folder):
            os.makedirs(args.save_folder)
        save_path = os.path.join(args.save_folder, output_filename)
    else:
        save_path = os.path.join(os.path.dirname(args.document_path), output_filename)
    
    save_parsed_document(parsed_doc, save_path)

if __name__ == "__main__":
    main()
