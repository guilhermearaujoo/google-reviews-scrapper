import json
from db import PostgresDB
from scraper import GoogleScraper
import os
from dotenv import load_dotenv

HOST = os.getenv("HOST")
DBNAME = os.getenv("DBNAME")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
PORT = os.getenv("PORT")

def handler(event, context):
    message = "Reviews successfully added."
    status = 200
    error = ''

    try:
        company_name = event['Records'][0]['body']
        db = PostgresDB(host=HOST, dbname=DBNAME, user=USER, password=PASSWORD, port=PORT)
        company = db.get_company_by_name(json.loads(company_name))
        reviews = db.get_reviews_by_company_id(company[0])

        is_scraped = company[4]

        # # scrape for reviews
        scraper = GoogleScraper(
            search_url=company[2], reviews_from_db=reviews, is_scraped=is_scraped
        )
        items = scraper.get_updated_reviews()
        items.reverse()

        # insert items in db
        for item in items:
            db.insert_review(
                avaliation=item["avaliation"],
                company_id=company[0],
                comment=item["comment"],
                reviewer_name=item["reviewer_name"],
                review_date=item["date"],
            )

        # update avaliations in db
        items_scraped = scraper.get_reviews_count()
        avaliations_sum = len(reviews) + items_scraped
        db.update_avaliations_sum(company_id=company[0], avaliations_sum=avaliations_sum)

        scraper.quit()
        db.close()

    except Exception as e:
        message = "Not possible to get reviews."
        status = 500
        error = str(e)


    body = {
        "message": message,
        "input": event,
        "error": error
    }

    response = {"statusCode": status, "body": json.dumps(body)}

    return response