import psycopg2

class PostgresDB:
    def __init__(self, host, dbname, user, password, port):
        self.conn = psycopg2.connect(
            host=host, dbname=dbname, user=user, password=password, port=port
        )
        self.cur = self.conn.cursor()
        self._create_companies_table()
        self._create_reviews_table()
        self.create_automatic_timestamps()  # Create the trigger function
        self._create_trigger()

    def _create_companies_table(self):
        create_companies_query = """
            CREATE TABLE IF NOT EXISTS companies (
                company_id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                search_url TEXT NOT NULL,
                avaliations_sum INT NOT NULL,
                scraped INT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """
        self.cur.execute(create_companies_query)
        self.conn.commit()

    def _create_reviews_table(self):
        create_reviews_query = """
            CREATE TABLE IF NOT EXISTS reviews (
                id SERIAL PRIMARY KEY,
                avaliation INT,
                company_id INT NOT NULL,
                comment TEXT,
                reviewer_name TEXT NOT NULL,
                review_date VARCHAR(255) NOT NULL
            );
        """
        self.cur.execute(create_reviews_query)
        self.conn.commit()

    def create_automatic_timestamps(self):
        create_trigger_function_query = """
            CREATE OR REPLACE FUNCTION trigger_set_timestamp()
                RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """
        self.cur.execute(create_trigger_function_query)
        self.conn.commit()

    def _create_trigger(self):
        create_trigger_query = """
            DROP TRIGGER IF EXISTS set_timestamp ON companies;
            CREATE TRIGGER set_timestamp
                BEFORE UPDATE ON companies
                FOR EACH ROW
                EXECUTE FUNCTION trigger_set_timestamp();
        """
        self.cur.execute(create_trigger_query)
        self.conn.commit()

    def insert_company(self, name, search_url, avaliations_sum=0, scraped=0):
        insert_query = """
            INSERT INTO companies (name, search_url, avaliations_sum, scraped)
            VALUES (%s, %s, %s, %s);
        """
        self.cur.execute(insert_query, (name, search_url, avaliations_sum, scraped))
        self.conn.commit()

    def insert_review(self, avaliation, company_id, comment, reviewer_name, review_date):
        insert_query = """
            INSERT INTO reviews (avaliation, company_id, comment, reviewer_name, review_date)
            VALUES (%s, %s, %s, %s, %s);
        """
        self.cur.execute(insert_query, (avaliation, company_id, comment, reviewer_name, review_date))
        self.conn.commit()

    def get_companies(self):
        self.cur.execute("SELECT * FROM companies;")
        return self.cur.fetchall()
    
    def get_company_reviews(self, company_id):
        select_query = """
        SELECT * FROM reviews WHERE company_id = %s;
        """
        self.cur.execute(select_query, (company_id,))
        return self.cur.fetchall()
    
    def get_company_by_name(self, name):
        select_query = """
            SELECT * FROM companies
            WHERE name = %s;
        """
        self.cur.execute(select_query, (name,))
        return self.cur.fetchone()

    def get_reviews_by_company_id(self, company_id):
        select_query = """
            SELECT reviewer_name, avaliation, comment, review_date
            FROM reviews
            WHERE company_id = %s;
        """
        self.cur.execute(select_query, (company_id,))
        return self.cur.fetchall()

    def update_avaliations_sum(self, company_id, avaliations_sum):
        update_query = """
            UPDATE companies
            SET avaliations_sum = %s, scraped = 1
            WHERE company_id = %s;
        """
        self.cur.execute(update_query, (avaliations_sum, company_id))
        self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()
