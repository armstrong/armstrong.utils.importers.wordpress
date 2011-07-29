from ._utils import *
from ..parser import WordpressFileParser
from os import path
from armstrong.apps.articles.models import Article


class SimpleImportTestCase(TestCase):
    def setUp(self):
        simple_xml = path.join(path.split(__file__)[0], 'xml_files/simple.xml')
        self.parser = WordpressFileParser(simple_xml)

    def test_import_sections(self):
        sections = self.parser.get_sections()
        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[0].title, 'outer')
        self.assertEqual(sections[2].parent, sections[0])
        for s in sections:
            s.save()

    def test_import_articles(self):
        authors = self.parser.get_authors()
        for auth in authors:
            auth.save()
        articles = self.parser.get_articles()
        self.assertEqual(len(articles), 4)
        for art in articles:
            art.save()
            art.authors = art.authors_list
            art.save()
        author_articles = Article.objects.filter(authors=authors[0])
        for art in articles:
            self.assertTrue(art in author_articles)

    def test_import_authors(self):
        authors = self.parser.get_authors()
        self.assertEqual(len(authors), 1)
        self.assertEqual(authors[0].username, 'armstrongexport')
        self.assertEqual(authors[0].is_active, False)
        for a in authors:
            a.save()

    def test_import_flat_pages(self):
        pages = self.parser.get_pages()
        self.assertEqual(len(pages), 1)
        page = pages[0]
        self.assertEqual(page.url,
                         'http://armstrongexport.wordpress.com/about/')
        self.assertEqual(page.title, 'About')
        page.save()
