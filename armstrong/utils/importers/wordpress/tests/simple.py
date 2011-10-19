from ._utils import *
from ..parser import WordpressFileParser
from os import path
from armstrong.apps.articles.models import Article
from armstrong.core.arm_sections.models import Section
from django.contrib.auth.models import User


class SimpleImportTestCase(TestCase):
    # TODO: move these methods to their proper home
    def assertModelCanSave(self, model, msg=None):
        try:
            model.save()
        except Exception, e:
            if msg is None:
                msg = "%s.save should not have raised exception: %s" % (
                    model.__class__.__name__, e)
            self.fail(msg)

    def assertModelsCanSave(self, models, msg=None):
        for model in models:
            self.assertModelCanSave(model)

    def setUp(self):
        simple_xml = path.join(path.split(__file__)[0], 'xml_files/simple.xml')
        self.parser = WordpressFileParser(simple_xml)

    def test_import_sections(self):
        sections = self.parser.get_sections()
        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[0].title, 'Outer')
        self.assertEqual(sections[2].parent, sections[0])
        self.assertModelsCanSave(sections)

    def test_import_will_use_existing_sections(self):
        s = Section.objects.create(title="Inner", slug='inner')
        sections = self.parser.get_sections()
        self.assertEqual(len(sections), 2)

    def test_import_only_builds_authors_once(self):
        with self.assertNumQueries(1):
            self.parser._initialize_authors_map()
        with self.assertNumQueries(0):
            self.parser._initialize_authors_map()

    def test_import_only_builds_sections_once(self):
        with self.assertNumQueries(1):
            self.parser._initialize_section_map()
        with self.assertNumQueries(0):
            sections = self.parser.get_sections()
            self.assertEqual(sections, self.parser.get_sections())

    def test_import_articles(self):
        authors = self.parser.get_authors()
        self.assertModelsCanSave(authors)
        articles = self.parser.get_articles()
        self.assertEqual(len(articles), 4)
        for art in articles:
            self.assertModelCanSave(art)
            art.authors = art.authors_list
            self.assertModelCanSave(art)
        author_articles = Article.objects.filter(authors=authors[0])
        for art in articles:
            self.assertTrue(art in author_articles)

    def test_import_authors(self):
        authors = self.parser.get_authors()
        self.assertEqual(len(authors), 1)
        self.assertEqual(authors[0].username, 'armstrongexport')
        self.assertEqual(authors[0].is_active, False)
        self.assertModelsCanSave(authors)

    def test_import_will_use_existing_authors(self):
        user = User.objects.create(username='armstrongexport')
        authors = self.parser.get_authors()
        self.assertEqual(len(authors), 0)

    def test_import_flat_pages(self):
        pages = self.parser.get_pages()
        self.assertEqual(len(pages), 1)
        page = pages[0]
        self.assertEqual(page.url,
                         'http://armstrongexport.wordpress.com/about/')
        self.assertEqual(page.title, 'About')
        self.assertModelCanSave(page)
