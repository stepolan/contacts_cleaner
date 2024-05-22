import vobject
import pandas as pd
from fuzzywuzzy import fuzz
import logging
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='vobject')

# Configure logging to write to both console and a file
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler('contacts_cleanup.log', mode='a')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Set debug mode
DEBUG = False  # Set to True to enable debug mode, which processes only the first 100 contacts for faster testing

def scan_vcf_fields(file_path):
    """Scan the VCF file to identify all unique fields."""
    logging.info("Scanning VCF file for fields.")
    
    with open(file_path, 'r') as f:
        vcard_data = f.read()

    vcards = vobject.readComponents(vcard_data)
    fields = set()

    for vcard in vcards:
        for key in vcard.contents.keys():
            fields.add(key)

    logging.info(f"Identified fields: {fields}")
    return fields

def clean_notes_field(note):
    """Clean the notes field by removing the specific unwanted line."""
    unwanted_text = "Exported from Microsoft Outlook (Do not delete)"
    if unwanted_text in note:
        return note.split(unwanted_text)[0].strip()
    return note

def parse_vcf_dynamic(file_path, fields):
    """Parse the VCF file and create a DataFrame with the identified fields."""
    logging.info("Parsing VCF file.")
    
    with open(file_path, 'r') as f:
        vcard_data = f.read()
    
    vcards = vobject.readComponents(vcard_data)
    contacts = []

    for vcard in vcards:
        contact = {}
        for field in fields:
            if field in vcard.contents:
                if field in ['tel', 'email']:
                    contact[field] = [item.value for item in vcard.contents[field] if item.value.lower() != 'nan']
                elif field == 'photo':
                    contact[field] = vcard.contents[field][0].value
                elif field == 'note':
                    contact[field] = clean_notes_field(vcard.contents[field][0].value)
                else:
                    contact[field] = vcard.contents[field][0].value
        contact.pop('prodid', None)  # Remove 'prodid' field if it exists
        contacts.append(contact)

    logging.info("Finished parsing VCF file.")
    return pd.DataFrame(contacts[:100] if DEBUG else contacts)

def highlight_similarities(contact, contact_compare, relevant_fields):
    """Highlight similarities in red for two contacts."""
    highlighted_contact = contact.copy()
    highlighted_contact_compare = contact_compare.copy()

    for field in relevant_fields:
        if field in contact and field in contact_compare:
            value = ' '.join([str(contact.get(field, ''))])
            value_compare = ' '.join([str(contact_compare.get(field, ''))])
            if fuzz.ratio(value, value_compare) > 90:  # You can adjust this threshold
                highlighted_contact[field] = f"\033[91m{contact[field]}\033[0m"
                highlighted_contact_compare[field] = f"\033[91m{contact_compare[field]}\033[0m"

    return highlighted_contact, highlighted_contact_compare

def find_duplicates(df, threshold=90):
    """Find potential duplicate contacts based on name and other relevant fields."""
    logging.info("Finding duplicates in contacts.")
    
    relevant_fields = ['name', 'email', 'tel']  # Specify the fields to be considered for duplicate detection
    duplicate_pairs = []
    total_comparisons = len(df) * (len(df) - 1) // 2  # Total number of comparisons
    progress_bar = tqdm(total=total_comparisons, desc='Finding duplicates', unit='comparison')  # Initialize tqdm progress bar
    
    for i, contact in df.iterrows():
        for j, contact_compare in df.iterrows():
            if i >= j:
                continue
            # Combine fields for similarity comparison, ignoring NaN values
            contact_str = ' '.join([str(item) for field in relevant_fields for item in (contact.get(field, []) if isinstance(contact.get(field, []), list) else [contact.get(field, [])]) if not pd.isna(item) and str(item).lower() != 'nan'])
            contact_compare_str = ' '.join([str(item) for field in relevant_fields for item in (contact_compare.get(field, []) if isinstance(contact_compare.get(field, []), list) else [contact_compare.get(field, [])]) if not pd.isna(item) and str(item).lower() != 'nan'])
            score = fuzz.ratio(contact_str, contact_compare_str)
            logging.debug(f"Comparing contact {i} and {j}: score={score}")
            if score > threshold:
                duplicate_pairs.append((i, j, score))
            progress_bar.update(1)  # Update progress bar for each comparison
    
    progress_bar.close()  # Close progress bar when done
    logging.info(f"Found {len(duplicate_pairs)} potential duplicate pairs.")
    return duplicate_pairs

def merge_contacts(contact1, contact2):
    """Merge two contact records."""
    merged_contact = contact1.copy()
    for key in contact2.keys():
        if key in ['prodid', 'org']:
            continue  # Ignore prodid and org fields
        if pd.isna(merged_contact.get(key)) and not pd.isna(contact2[key]):
            merged_contact[key] = contact2[key]
        elif key in ['tel', 'email']:
            merged_contact[key] = list(set(merged_contact.get(key, []) + contact2[key]))
    return merged_contact

def interactive_merge_delete(df, duplicate_pairs):
    """Interactively merge or delete duplicate contacts."""
    logging.info("Starting interactive merge/delete process.")
    
    for (i, j, score) in duplicate_pairs:
        highlighted_contact, highlighted_contact_compare = highlight_similarities(df.iloc[i], df.iloc[j], ['name', 'email', 'tel'])
        
        print(f"\033[94mDuplicate found with {score}% similarity:\033[0m")
        print(f"\033[93mContact {i}:\033[0m")
        print(highlighted_contact)
        print("\n")
        print(f"\033[93mContact {j}:\033[0m")
        print(highlighted_contact_compare)
        print("\n")

        choice = input("Merge (m), Delete Contact 2 (d), Skip (s): ").strip().lower()
        if choice == 'm':
            df.iloc[i] = merge_contacts(df.iloc[i], df.iloc[j])
            df.drop(index=j, inplace=True)
            logging.info(f"Merged contacts {i} and {j}.")
        elif choice == 'd':
            df.drop(index=j, inplace=True)
            logging.info(f"Deleted contact {j}.")
        else:
            logging.info(f"Skipped contacts {i} and {j}.")
        print("\n")
    
    logging.info("Finished interactive merge/delete process.")
    return df

def save_to_vcf(df, output_file):
    """Save the cleaned contacts to a new VCF file."""
    logging.info(f"Saving cleaned contacts to {output_file}.")
    
    with open(output_file, 'w') as f:
        for _, contact in df.iterrows():
            vcard = vobject.vCard()
            if 'name' in contact and not pd.isna(contact['name']):
                vcard.add('fn').value = contact['name']
            if 'tel' in contact and contact['tel']:
                for phone in contact['tel']:
                    tel = vcard.add('tel')
                    tel.value = phone
            if 'email' in contact and contact['email']:
                for email in contact['email']:
                    mail = vcard.add('email')
                    mail.value = email
            for key in ['address', 'note']:  # Exclude 'photo' field
                if key in contact and not pd.isna(contact[key]):
                    vcard.add(key).value = contact[key]
            f.write(vcard.serialize())

    logging.info("Finished saving contacts.")

def save_to_csv(df, output_file):
    """Save the contacts DataFrame to a CSV file."""
    logging.info(f"Saving contacts to {output_file}.")
    df.drop(columns=['photo'], errors='ignore').to_csv(output_file, index=False)  # Exclude 'photo' field
    logging.info("Finished saving contacts to CSV.")

if __name__ == '__main__':
    logging.info("Starting contacts cleanup script.")

    # Load and process contacts
    fields = scan_vcf_fields('./contacts.vcf')
    contacts_df = parse_vcf_dynamic('./contacts.vcf', fields)

    # Save initial contacts to CSV
    save_to_csv(contacts_df, './contacts_initial.csv')

    # Find duplicates and perform interactive merge/delete
    duplicate_pairs = find_duplicates(contacts_df)
    cleaned_df = interactive_merge_delete(contacts_df, duplicate_pairs)

    # Save cleaned contacts to a new VCF file
    save_to_vcf(cleaned_df, './cleaned_contacts.vcf')

    logging.info("Contacts cleanup script finished.")