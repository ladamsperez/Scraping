import os
import sys
import requests
import json
from bs4 import BeautifulSoup


'''Beautiful Soup (BS4) is a parsing library that can use different parsers. 
the program that can extract data from HTML and XML documents.
it automatically detect encodings. This allows it to handle HTML documents with special characters.
with the help of requests to get the HTML, BS4 parses the data'''

url = 'https://apps.irs.gov/app/picklist/list/priorFormPublication.html'


# gets all info from irs site
def tax_info_forms(tax_search_list: list):
    
    # empty list stores list of lists for multiple forms
    data_list = []

    with requests.session() as session:
        # list of form names to get info
        for param in tax_search_list:
            params_return = {'value': param, 'criteria': 'formNumber', 'submitSearch': 'Find'}
            results = session.get(url, params=params_return).content
            data_list.append(results)
        # compiles list of lists w/ 
        return data_list


# gets form names,titles, and years from previous return to parse
def read_data(tax_search_list: list):
    responses = tax_info_forms(tax_search_list)
    # empty lists to fill with the received info for all names, years, and titles
    data_form_name, data_form_title, data_form_rev_year = [], [], []
    for response in responses:
        soup = BeautifulSoup(response, 'lxml')
        data_name = soup.find_all('td', {'class': 'LeftCellSpacer'})
        data_title = soup.find_all('td', {'class': 'MiddleCellSpacer'})
        data_rev_year = soup.find_all('td', {'class': 'EndCellSpacer'})
        data_form_name.extend(data_name)
        data_form_title.extend(data_title)
        data_form_rev_year.extend(data_rev_year)
    return data_form_name, data_form_title, data_form_rev_year

# func formats read_data for all forms recieved previously
def format_data(tax_search_list: list):
    data_names, data_titles, data_years = read_data(tax_search_list)
    names = [name.text.strip() for name in data_names]
    links = [link.find('a')['href'] for link in data_names]
    titles = [title.text.strip() for title in data_titles]
    years = [int(year.text.strip()) for year in data_years]
    set_names = set(names)
    final_data_dict = []
    
    for name in set_names: # loop creates dictionary of info with years of downloadable tax forms
        max_year = 0
        min_year = max(years)
        data_dict = {'form_number': name}
        for index, d_name in enumerate(names):
            if d_name == name:
                if years[index] > max_year:
                    max_year = years[index]
                elif years[index] < min_year:
                    min_year = years[index]
                data_dict['form_title'] = titles[index]
                data_dict['max_year'] = max_year
                data_dict['min_year'] = min_year
        final_data_dict.append(data_dict)
    print(json.dumps(final_data_dict, indent=2))
    return names, links, years  # :returns formated names, links, and years

# download pdf files of form_name w/ userinput
def IRS_file_downloads(tax_search_list):
    names, links, years = format_data(tax_search_list)
        #Prompts user input for start and end years
    form_name = input('Welcome! Which IRS form are you looking for? (For example, you can type: Form W-2) ')
    if form_name in names:
        print('Success! Form(s) have been found.')
        #Prompts user input for start and end years
        form_year1 = int(input('Enter year to begin analysis: '))
        form_year2 = int(input('Thanks! Now enter year to end analysis: '))
        try:
            os.mkdir(form_name)
        except FileExistsError:
            pass
        # indecies to define names range in list of all tax form names
        r_index = names.index(form_name)  # index of first form_name mention on list
        l_index = names.index(form_name)  # index of last form_name mention on list
        for name in names:
            if name == form_name:
                r_index += 1
        years = years[l_index:r_index]
        if form_year1 < form_year2:
            range_years = range(form_year1, form_year2 + 1)
            for year in range_years:
                if year in years:
                    link = links[years.index(year)]
                    form_file = requests.get(link, allow_redirects=True)
                    open(f'{form_name}/{form_name}_{str(year)}.pdf', 'wb').write(form_file.content)
            print(f'Success! Files have been downloaded to {form_name} directory.') # message to user successful files created
    else:
        print('User Error: Incorrect form name. Please try again.')


if __name__ == '__main__':
    irs_forms = sys.argv[1:]  # form names
    IRS_file_downloads(irs_forms)
