from tagcounter import tagcounter
import sqlalchemy as db
import pytest
import datetime
import os

class TestParser:

    def __init__(self):
        self.src = tagcounter.MyHTMLParser()
        self.src.feed('<html><html><html><test></body></body></html>')

    def test_init(self):
        assert "Start Tags" in  self.src.TagCollection

    def test_add_start_tag(self):
        assert self.src.TagCollection.get("Start Tags") == {"html" :3, "test" :1}, "Should be {'html' :3, 'test' :1}"

    def test_add_end_tag(self):
        assert self.src.TagCollection.get("End Tags") == {"body" :2, "html" :1}, "Should be {'body' :2, 'html' :1}"

class TestSqlLite:

    def __init__(self):
        if os.path.exists("tag.sqllite"):
            os.remove("tag.sqllite")
        self.src = tagcounter.SqlLiteWorker()
        self.site_name = 'google.com'
        self.site_url = 'https://google.com/'
        self.curdt = datetime.datetime.now()
        self.tagdict = {"Start Tags":{"html":10, "body":11}, "End Tags":{"html":5, "body":1}}

    @pytest.mark.run(order=1)
    def test_init_table_exists(self):
        assert self.src.engine.dialect.has_table(self.src.engine, self.src.TagTableName)

    @pytest.mark.run(order=2)
    def test_save(self):
        self.src.save(self.site_name,self.site_url,self.curdt,self.tagdict)
        query = db.select([self.src.TagTable]).where(self.src.TagTable.c.url == self.site_url)
        results = self.src.connection.execute(query).fetchone()
        assert self.site_name == results[0]
        assert self.site_url == results[1]
        assert self.curdt == results[2]
        assert self.tagdict == results[3]

    @pytest.mark.run(order=3)
    def test_load(self):
        results = self.src.load("google.com")
        assert self.site_name == results[0]
        assert self.site_url == results[1]
        assert self.curdt == results[2]
        assert self.tagdict == results[3]

class TestTagWorker:

    def __init__(self):
        self.worker = tagcounter.TagWorker()