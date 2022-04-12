from html.parser import HTMLParser
import requests
import sqlalchemy as db
from url_normalize import url_normalize as url
import validators
import datetime
from tkinter import *
from tkinter.ttk import Combobox as tkcombo
import yaml
import click
import logging

class MyHTMLParser(HTMLParser):

    def __init__(self):
        self.TagCollection = {"Start Tags":{}, "End Tags":{}}
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        self.TagCollection["Start Tags"].update({tag: self.TagCollection["Start Tags"].get(tag, 0) + 1})

    def handle_endtag(self, tag):
        self.TagCollection["End Tags"].update({tag: self.TagCollection["End Tags"].get(tag, 0) + 1})

class SqlLiteWorker:

    def __init__(self):
        self.TagTableName =  'tagtable'
        self.engine = db.create_engine("sqlite:///tag.sqllite")
        self.connection = self.engine.connect()
        self.metadata = db.MetaData()

        self.TagTable = db.Table(self.TagTableName, self.metadata,
                            db.Column('sitename', db.String(255)),
                            db.Column('url', db.String(255), nullable=False),
                            db.Column('checkdtime', db.DateTime, default=datetime.datetime.now()),
                            db.Column('tags', db.PickleType))

        # create table if not exists
        if not self.engine.dialect.has_table(self.engine,self.TagTableName):
            self.TagTable.create(self.engine)

    def save(self,psitename,purl,pcheckdtime,ptags):
        query = db.insert(self.TagTable).values(sitename=psitename, url=purl, checkdtime=pcheckdtime, tags=ptags)
        self.connection.execute(query)

    def load(self,purl):
        query = db.select([self.TagTable]).where(self.TagTable.c.url == purl)
        results = self.connection.execute(query).fetchall()
        return results

class TagWorker():

    def __init__(self,config_path):
        self.parser = MyHTMLParser()
        self.classdb = SqlLiteWorker() # link on class sqllite worker
        self.BaseObject = {"SiteName":"","Url":"","CheckDateTime":"","Tags":{"Start Tags":{}, "End Tags":{}}}
        logging.basicConfig(filename='tagcounter.log',format='%(asctime)s - %(message)s', level=logging.INFO)
        with open(config_path) as source:
            self.synonym_dict = yaml.safe_load(source)

    def formatter(self, vdict, **kwargs):
        outputstring = ""
        if isinstance(vdict, dict) :
            self.BaseObject = {"SiteName":kwargs.get('psitename'),"Url":kwargs.get('purl'),"CheckDateTime":kwargs.get('currentdtime'),"Tags":vdict}
            outputstring = 'Site name: {SiteName} \nURL: {Url}\nCheck datetime: {CheckDateTime}\nTags: {Tags}'.format(**self.BaseObject)
        else :
            for row in vdict:
                rowDict = row.items()
                self.BaseObject = {"SiteName": rowDict[0], "Url": rowDict[1], "CheckDateTime": rowDict[2], "Tags": rowDict[3]}
                logging.info(rowDict[0])
                textobject = kwargs.get('msglink')
                stringtowrite = 'Site name: {SiteName} \nURL: {Url}\nCheck datetime: {CheckDateTime}\nTags: {Tags}'.format(**self.BaseObject)
                if textobject == "console":
                    print(stringtowrite + '\n')
                else :
                    textobject.insert("end-1c", stringtowrite + "\n ============================================================== \n" )
        return outputstring

    def parse_and_save(self,psitename,purl):
        logging.info(psitename)
        currentdtime = datetime.datetime.now()
        with (requests.get(purl)) as request:
            self.parser.feed(request.text)
        self.classdb.save(psitename,purl,currentdtime,self.parser.TagCollection)
        return self.formatter(self.parser.TagCollection, psitename=psitename,purl=purl,currentdtime=currentdtime)

    def show_from_db(self,purl,**kwargs):
        printsrc = kwargs.get('msglink')
        if printsrc is "console":
            self.formatter(self.classdb.load(purl), msglink=printsrc)
        else :
            return self.formatter(self.classdb.load(purl), msglink=printsrc)

class GUI(Frame):

    def __init__(self):
        super().__init__()

        self.tagprocessor = TagWorker('config.yaml')
        self.message_text = StringVar()
        self.url_list = [self.tagprocessor.synonym_dict[i] for i in self.tagprocessor.synonym_dict]

        self.initGUI()

    def initGUI(self):

        self.master.title("Счётчик тегов")
        self.pack(fill=BOTH, expand=True)

        frame1 = Frame(self)
        frame1.pack(fill=X)

        lbl1 = Label(frame1,text="Варианты", width=10)
        lbl1.pack(side=LEFT, padx=5, pady=5)

        self.combo1 = tkcombo(frame1, values=self.url_list)
        self.combo1.pack(side=LEFT, padx=5, pady=5)

        button1 = Button(frame1,text="Выбрать", command=self.button_enter)
        button1.pack(side=LEFT, padx=5, pady=5)

        frame2 = Frame(self)
        frame2.pack(fill=X)

        lbl2 = Label(frame2, text="Введите сайт", width=10)
        lbl2.pack(side=LEFT, padx=5, pady=5)

        self.entry2 = Entry(frame2,textvariable=self.message_text)
        self.entry2.pack(fill=X, padx=5, pady=5, expand=True)

        frame3 = Frame(self)
        frame3.pack(fill=X)

        lbl3 = Label(frame3, text=" ", width=10)
        lbl3.pack(side=LEFT, padx=5, pady=5)

        button3a = Button(frame3, text="Загрузить", command=self.button_process)
        button3a.pack(side=LEFT, padx=5, pady=5)

        button3b = Button(frame3, text="Показать из базы", command=self.load_from_db)
        button3b.pack(side=LEFT, padx=5, pady=5)

        frame4 = Frame(self)
        frame4.pack(fill=BOTH, expand=True)

        lbl4 = Label(frame4, text="Детали", width=10)
        lbl4.pack(side=LEFT, padx=5, pady=5)

        self.txt4 = Text(frame4)
        yscrollbar4 = Scrollbar(frame4, command=self.txt4.yview)
        yscrollbar4.pack(side=RIGHT, padx=(0,5), pady=5, fill="y", anchor=N )
        self.txt4['yscrollcommand'] = yscrollbar4.set
        self.txt4.pack(fill=BOTH, padx=(5,0), pady=5, expand=True)

    def process_tags(self):
        ulr_string = url(self.message_text)
        if self.url_check(self.message_text):
            self.txt4.delete(1.0, "end-1c")
            self.txt4.insert("end-1c", self.tagprocessor.parse_and_save(self.message_text, url(ulr_string)))
        else:
            self.txt4.delete(1.0, "end-1c")
            self.txt4.insert("end-1c", "Invalid URL!!!")

    def button_enter(self):
        self.message_text = self.combo1.get()
        self.process_tags()

    def button_process(self):
        self.message_text = self.entry2.get()
        self.process_tags()

    def load_from_db(self):
        self.message_text = self.entry2.get()
        ulr_string = url(self.message_text)
        if self.url_check(self.message_text):
            self.txt4.delete(1.0, "end-1c")
            self.tagprocessor.show_from_db(ulr_string, msglink=self.txt4)
        else:
            self.txt4.delete(1.0, "end-1c")
            self.txt4.insert("end-1c", "Invalid URL!!!")

    def url_check(self,purl):
        return validators.domain(purl)

@click.command()
@click.option('--get', help='Get tag count for given site name')
@click.option('--view', help='Load tag count data from sqllite')

def main(get,view):
    lget=get
    lview=view
    tagprocessor = TagWorker('tagcounter\config.yaml')
    if lget:
        site_name = tagprocessor.synonym_dict.get(lget, lget)
        ulr_string = url(site_name)
        print(tagprocessor.parse_and_save(site_name, url(ulr_string)))
    else :
        site_name = tagprocessor.synonym_dict.get(lview, lview)
        ulr_string = url(site_name)
        tagprocessor.show_from_db(url(ulr_string), msglink="console")

if __name__ == '__main__':
    root = Tk()
    root.geometry("800x600")
    app = GUI()
    root.mainloop()