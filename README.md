# Contacts Cleaner

This project is a Python script designed to clean and deduplicate contacts from a VCF (vCard) file.

## Features

- **Scan VCF Fields:** Identifies all unique fields in the VCF file.
- **Parse VCF File:** Parses the VCF file and creates a DataFrame with the identified fields.
- **Clean Notes Field:** Removes specific unwanted lines from the notes field.
- **Find Duplicates:** Identifies potential duplicate contacts based on name and other relevant fields.
- **Interactive Merge/Delete:** Allows interactive merging or deletion of duplicate contacts.
- **Save to CSV:** Exports the cleaned contacts to a CSV file, excluding certain fields.
- **Save to VCF:** Saves the cleaned contacts to a new VCF file.

## Requirements

- Python 3.11
- tqdm
- pandas
- fuzzywuzzy
- vobject

## Usage

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/contacts_cleaner.git
   cd contacts_cleaner

2. **Create and Activate the Conda Environment:**
    ```bash
    conda env create -f environment.yml
    conda activate contacts_cleaner

3. **Run The Script**
    ```bash
    python contacts_cleaner.py

## Debug Mode

To enable debug mode, which processes only the first 100 contacts for faster testing, set the `DEBUG` flag to `True` in the script.

    ```python
    DEBUG = False  # Set to True to enable debug mode, which processes only the first 100 contacts for faster testing
    
## Exporting Contacts to VCF

### iOS

1. Open the **Contacts** app.
2. Select the contacts you want to export.
3. Tap **Share Contact** and choose the **Mail** option.
4. Send the VCF file to your email address and download it.

### macOS

1. Open the **Contacts** app.
2. Select the contacts you want to export.
3. Go to **File** > **Export** > **Export vCard**.
4. Save the VCF file to your desired location.

### Google Contacts

1. Open [Google Contacts](https://contacts.google.com/).
2. Select the contacts you want to export.
3. Click on the **More** button (three vertical dots) and select **Export**.
4. Choose the **vCard (for iOS Contacts)** option and click **Export**.
5. Download the VCF file to your computer.

### Microsoft Outlook

1. Open **Microsoft Outlook**.
2. Go to the **People** section.
3. Select the contacts you want to export.
4. Click on **File** > **Open & Export** > **Import/Export**.
5. Choose **Export to a file** and select **Comma Separated Values** or **vCard**.
6. Follow the prompts to export your contacts to a VCF file.
