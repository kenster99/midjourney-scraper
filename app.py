from playwright.async_api import async_playwright
import asyncio
import pandas as pd
import json
import random

SITE = "https://github.com/willwulfken/MidJourney-Styles-and-Keywords-Reference"

async def scrape_subcategories(link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(link, timeout=60000)

        # extract the category from the link
        file_name = link.split('/')[-1]  # get the file name from the link
        file_root = file_name.split('.')[0]  # get the root of the file name (without extension)
        category = file_root.replace('_', ' ')  # replace underscores with spaces

        print('category: ', category)

        # find the details element containing the subcategory value
        details_handles  = await page.query_selector_all('details:has(summary:has(g-emoji))')
        subsubcategory_data = {'category': [], 'subcategory': [], 'subsubcategory': []}
      
        for details in details_handles:
            # extract subcategory from the summary
            summary_text = await details.evaluate('(element) => element.textContent', await details.query_selector('summary'))
            last_emoji_index = summary_text.rfind('</g-emoji>')
            subcategory = summary_text[last_emoji_index + len('</g-emoji>'):].strip()
            print('     subcategory: ', subcategory)

            # Find the DIV > TABLEs that contain sub-subcategories...
            div_handle = await details.query_selector('div')

            if div_handle:
                # find all the tables within the div
                table_handles = await div_handle.query_selector_all('table')
                for table_handle in table_handles:
                    th_handles = await table_handle.query_selector_all('thead tr th')
                    for th_handle in th_handles:
                        subsubcategory_data['category'].append(category)
                        subsubcategory_data['subcategory'].append(subcategory)
                        subsubcategory_text = await th_handle.evaluate('(element) => element.textContent')
                        subsubcategory_data['subsubcategory'].append(subsubcategory_text.strip())
                        print('         subsubcategory: ', subsubcategory_text)

        await browser.close()
    
    return pd.DataFrame(subsubcategory_data, columns=['category', 'subcategory', 'subsubcategory'])

async def scrape_links():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(SITE)

        # find the div containing the #styles link
        div_handle = await page.query_selector('div h3 a[href="#styles"]')
        if div_handle:
            div_element = await div_handle.evaluate_handle('(node) => node.closest("div")')
            # get all the links within the div
            links = await div_element.query_selector_all('a')
            links_href = [await link.evaluate('(node) => node.href') for link in links]
            
            # create an empty list to hold the subcategory and sub-subcategory data
            data_frames = []
            for href in links_href:
                wait_time = random.randint(5, 15)
                await asyncio.sleep(wait_time)
                data_frames.append(await scrape_subcategories(href))

            # concatenate all the data frames into a single DataFrame
            df = pd.concat(data_frames, ignore_index=True)

            # write DataFrame to CSV file
            df.to_csv('taxonomy.csv', index=False)

            return df 
                   
    #         # create an empty dictionary to hold the subcategory and sub-subcategory data
    #         category_data = {}
    #         for href in links_href:
    #             wait_time = random.randint(5, 15)
    #             await asyncio.sleep(wait_time)
    #             data = await scrape_subcategories(href)
    #             for _, row in data.iterrows():
    #                 category = row['category']
    #                 subcategory = row['subcategory']
    #                 subsubcategory = row['subsubcategory']
    #                 if category not in category_data:
    #                     category_data[category] = {}
    #                 if subcategory not in category_data[category]:
    #                     category_data[category][subcategory] = []
    #                 category_data[category][subcategory].append(subsubcategory)

    #         # concatenate all the data into a single DataFrame
    #         df = pd.concat(category_data, ignore_index=True)

    #         # write DataFrame to CSV file
    #         df.to_csv('taxonomy.csv', index=False)
    #         print(category_data)
        await browser.close()
    # return category_data

if __name__ == '__main__':
    df = asyncio.run(scrape_links())

