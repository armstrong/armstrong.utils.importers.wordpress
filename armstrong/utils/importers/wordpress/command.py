import os


class ImportWordpressCommand(object):
    """Import a Wordpress xml export file"""
    def build_parser(self, parser):
        parser.description = \
                'Initialize a new Armstrong project from a template'
        parser.add_argument('--dryrun', '-d', action='store_true',
                help="only parse the data file, don't change the db")
        parser.add_argument('import_file', type=os.path.abspath,
                help='location of the xml file')

    def __call__(self, import_file, dryrun=False, **kwargs):
        from .parser import WordpressFileParser
        parser = WordpressFileParser(import_file)
        authors = parser.get_authors()
        sections = parser.get_sections()
        articles = parser.get_articles()
        pages = parser.get_pages()
        if not dryrun:
            for auth in authors:
                auth.save()
            for section in sections:
                section.save()
            for article in articles:
                article.save()
                article.authors = article.authors_list
                article.tags.add(*article.tags_list)
                article.sections.add(*article.sections_list)
                article.save()
            for page in pages:
                page.save()

        print "Found %i new authors" % len(authors)
        print "Found %i new sections" % len(sections)
        print "Found %i articles" % len(articles)
        print "Found %i pages" % len(pages)

    @property
    def requires_armstrong(self):
        return True


import_wp = ImportWordpressCommand()
