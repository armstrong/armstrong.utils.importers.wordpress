from lxml import etree
from armstrong.core.arm_sections.models import Section
from armstrong.apps.articles.models import Article
from django.contrib.auth.models import User
from django.contrib.flatpages.models import FlatPage
from django.template.defaultfilters import slugify


STATUS_MAP = {
            'private': 'D',
            'publish': 'P',
            'future': 'P',
            'pending': 'D',
            'draft': 'D',
            'auto-draft': 'D',
        }


def find(item, tag):
    return item.find(tag, namespaces=item.nsmap)


class WordpressFileParser(object):
    def __init__(self, import_file=None, dryrun=False):
        parser = etree.XMLParser(recover=True)
        self.xml = etree.parse(import_file, parser)
        self.root = self.xml.getroot()
        self.channel = find(self.root, 'channel')
        self.section_map = None
        self.sections = []
        self.authors_map = None
        self.articles = None
        self.pages = None

    def _initialize_section_map(self):
        if self.section_map is not None:
            return
        self.section_map = {}
        for s in Section.objects.all():
            self.section_map[s.slug] = s

    def get_sections(self):
        if 0 < len(self.sections):
            return self.sections
        self._initialize_section_map()
        for section in self.channel.findall('wp:category',
                                            namespaces=self.root.nsmap):
            slug = find(section, 'wp:category_nicename').text
            if slug in self.section_map:
                continue
            title = find(section, 'wp:cat_name').text
            summary = find(section, 'wp:category_description')
            if summary is not None:
                summary = summary.text or ''
            else:
                summary = ''
            parent = find(section, 'wp:category_parent')
            if parent is not None:
                if parent.text is not None:
                    for s in self.sections:
                        if parent.text == s.title:
                            parent = s
                            break
                else:
                    parent = None
            s = Section(title=title,
                        summary=summary,
                        slug=slug,
                        parent=parent)
            self.sections.append(s)
            self.section_map[slug] = s
        return self.sections

    def process_items(self):
        if self.articles is not None and self.pages is not None:
            return
        self.articles = []
        self.pages = []
        self.get_sections()
        self._initialize_authors_map()
        for item in self.channel.findall('item'):
            title = find(item, 'title').text
            summary = find(item, 'excerpt:encoded').text
            slug = find(item, 'wp:post_name').text
            if slug is None or slug == '':
                slug = slugify(title)
            post_type = find(item, 'wp:post_type').text
            body = find(item, 'content:encoded').text
            author = find(item, 'dc:creator').text
            if author in self.authors_map:
                author = self.authors_map[author]
            else:
                author = User(username=author,
                              is_active=False)
                author.set_password('password')
                self.authors_map[author.username] = author
            date = find(item, 'wp:post_date').text
            pub_status = STATUS_MAP.get(find(item, 'wp:status').text, 'D')
            sections, tags = self._get_sections_and_tags_for_item(item)

            if post_type == 'post':
                a = Article(title=title,
                            summary=summary,
                            slug=slug,
                            body=body,
                            pub_date=date,
                            pub_status=pub_status)
                a.authors_list = (author,)
                a.sections_list = sections
                a.tags_list = tags
                self.articles.append(a)
            if post_type == 'page':
                url = find(item, 'link').text
                p = FlatPage(url=url,
                             title=title,
                             content=body)
                self.pages.append(p)

    def _get_sections_and_tags_for_item(self, item):
        sections = []
        tags = []
        for cat in item.findall('category'):
            if 'nicename' in cat.attrib:
                if cat.attrib['domain'] == 'tag':
                    tags.append(cat.attrib['nicename'])
                if cat.attrib['domain'] == 'category':
                    sections.append(self.section_map[cat.attrib['nicename']])
        return sections, tags

    def _initialize_authors_map(self):
        if self.authors_map is not None:
            return
        self.authors_map = {}
        for u in User.objects.all():
            self.authors_map[u.username] = u

    def get_authors(self):
        self._initialize_authors_map()
        self.process_items()
        return [a for a in self.authors_map.values() if a.id is None]

    def get_pages(self):
        self.process_items()
        return self.pages

    def get_articles(self):
        self.process_items()
        return self.articles
