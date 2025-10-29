from playwright.async_api import async_playwright
import re
import asyncio
import pandas as pd
from datetime import datetime
import logging

logger=logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter=logging.Formatter('%(asctime)s : %(levelname)s: Message : %(message)s from  Function-> %(funcName)s by logger %(name)s')
stream_handler=logging.StreamHandler()
stream_handler.setFormatter(formatter)

stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)
logger.propagate=False


"""
News Aggregator
Scrape headlines from 3 news sites and combine into one CSV

Sites:
1. Times of India - Tech section
2. The Hindu - Business section  
3. Indian Express - Any section

Extract:
- Headline
- Link
- Source (TOI/Hindu/Express)
- Date scraped

Save to: news_headlines_[timestamp].csv
"""


async def toi(context,url):
    page=await context.new_page()
    selectors=[
        ".wAaWq",
        ".GLeza",
        ".adKsS"
    ]
    articles=[]
    try:
        await page.goto(url)
        await page.wait_for_load_state('domcontentloaded')
        for selector in selectors:
            try:
                loc=page.locator(selector)
                total=await loc.count()

                if(total<=0):
                    logger.info(f'No locator for {selector} found')
                else:
                    for i in range(total):
                        try:
                            
                            item=loc.nth(i)
                            
                            try:
                                headline=await item.locator('h5').first.inner_text()
                            except Exception :
                                headline='N/A'
                            try:
                                link =await item.locator('a').first.get_attribute('href')
                            except Exception :
                                link='N/A'
                            try:
                                source=await page.title()
                            except Exception :
                                source='N/A'
                            try:
                                date=await item.locator('.c6AKk').first.inner_text()
                            except Exception :
                                date='N/A'

                            print(f'HeadLine: {headline} , Link: {link} , Source: {source} ,Date: {date} \n')
                            articles.append({
                                "Headline": headline,
                                "Link": link,
                                "Source": source,
                                "Date": date
                            })
                        except Exception as e:
                            logger.exception(f'Exception Occured in item {i} for selector : {selector}\nException: {e}')
                            continue
            except Exception as e:
                logger.warning(f'Exception occured in TOI scraper : {e}')
                continue
    except Exception :
        logger.critical('Times Of India Scraper Failed')
    finally:
        await page.close()
    return articles


async def theHinduNews(context,url):
    page=await context.new_page()
    selectors=["div[class^='element']"]
    articles=[]
    try:
        await page.goto(url)
        await page.wait_for_load_state('domcontentloaded')
        for selector in selectors:

            try:
                loc=page.locator(f"{selector}")
                total=await loc.count()

                if(total<=0):
                    logger.info(f'No locator found for selector {selector}')
                else:
                    for i in range(total):
                        try:
                                
                            item=loc.nth(i)
                            try:
                                headline=await item.locator('.title').get_by_role('link').first.inner_text(timeout=8000)
                            except Exception :
                                headline='N/A'
                            try:
                                link=await item.locator('.title').get_by_role('link').first.get_attribute('href',timeout=8000)
                            except Exception :
                                link='N/A'
                            try:
                                source=await page.title()
                            except Exception :
                                source='N/A'

                            date='N/A' #the theHinduNews doesn't provide date of it
                            print(f'HeadLine: {headline} , Link: {link} , Source: {source} ,Date: {date} \n')
                            articles.append({
                                "Headline": headline,
                                "Link": link,
                                "Source": source,
                                "Date": date
                            })
                        except Exception as e:
                            logger.exception(f'Exception Occured in item {i} for selector : {selector}\nException: {e}')
                            continue
            except Exception as e:
                logger.warning(f'Exception occured in Hindu scraper : {e}')
                continue
    except Exception as e:
        logger.critical(f'Hindu Scraper Failed : {e}')
    finally:
        await page.close()
    return articles



async def indianExpress(context,url):
    page=await context.new_page()
    selectors=[
       ".story_title ",
       ".parliament-content ",
       ".text-cols "
    ]
    try:
        await page.goto(url)
        await page.wait_for_load_state('domcontentloaded')
        articles=[]
        for selector in selectors:
            try:
                loc=page.locator(selector)
                total=await loc.count()

                if(total<=0):
                    logger.info(f'No locator for {selector} found')
                else:
                    for i in range(total):
                        try:
                            item=loc.nth(i)
                            try:
                                headline=await item.locator('a').first.inner_text()
                            except Exception:
                                headline='N/A'
                            try:
                                link =await item.locator('a').first.get_attribute('href')
                            except Exception:
                                link='N/A'
                            try:
                                source=await page.title()
                            except Exception:
                                source='N/A'

                            date="N/A"# the indian express doesn't provide dates 

                            print(f'HeadLine: {headline} , Link: {link} , Source: {source} ,Date: {date} \n')
                            articles.append({
                                "Headline": headline,
                                "Link": link,
                                "Source": source,
                                "Date": date
                            })
                        except Exception as e:
                            logger.exception(f'Exception Occured in item {i} for selector : {selector}\nException: {e}')
                            continue
            except Exception as e:
                logger.warn(f'Exception occured in Indian Express scraper : {e}')
                continue
    except Exception :
        logger.critical('Indian Express Scraper Failed')
    finally:
        await page.close()
    
    return articles

async def main():
    async with async_playwright() as p:
        browser= await p.chromium.launch()# you can add headless=False to see the UI ,and slow_mo=500 to see it the working in a slow manner
        context=await browser.new_context()

        result=await asyncio.gather(
            toi(context,'https://timesofindia.indiatimes.com/technology'),
            theHinduNews(context,'https://www.thehindubusinessline.com/'), # you can comment out theHinduNews function to get results faster
            indianExpress(context,'https://indianexpress.com/section/explained/')
        )


        await browser.close()
        
        all_articles=[item for site_data in result  for item in site_data]
        if not all_articles:
            print("No articles ")
            return
        df=pd.DataFrame(all_articles)
        filename=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_news_scraped.csv"
        df.to_csv(filename,index=False,encoding='utf-8')
        print(f'Data Saved to {filename}')

asyncio.run(main())