# This file is part of Booktype.
# Copyright (c) 2013 Borko Jandras <borko.jandras@sourcefabric.org>
#
# Booktype is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Booktype is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Booktype.  If not, see <http://www.gnu.org/licenses/>.

import os
import json
import codecs
import urllib2
import logging
from lxml import etree


import ebooklib
import ebooklib.epub
import ebooklib.utils

from copy import deepcopy

from django.conf import settings
from django.template.loader import render_to_string

from ..base import BaseConverter
from ..utils.epub import parse_toc_nav
from .. import utils
from .styles import create_default_style, get_page_size, CROP_MARGIN
from booktype.apps.themes.utils import (
    read_theme_style, get_single_frontmatter, get_single_endmatter, get_body)
from booktype.apps.convert.templatetags.convert_tags import (
    get_refines, get_metadata)


logger = logging.getLogger("booktype.convert.pdf")


class MPDFConverter(BaseConverter):
    """

    This code creates all required files and then passed them to booktype2mpdf.php script to produce
    final PDF output.

    These are the files we pass to the PHP script:
    - body.html 
    - frontmatter.html
    - endmatter.html
    - style.css
    - config.json

    config.json file keeps all required input information like page settings, styling, metadata and etc.
    This file is really just the way how we pass the information to PHP script.

    style.css is produced from Django template we defined. It holds all default, theme and custom styling for 
    this specific book.

    frontmatter.html, body.html and endmatter.html are produced from Django template files we defined. 

    Customisation can be done in two different ways:

    **Templates**

    List of template files:
    - convert/frontmatter_mpdf.html
    - convert/endmatter_mpdf.html
    - convert/body_mpdf.html
    - convert/style_mpdf.css

    **Extending code**

    You need to create your own convert module and extend this class. After that
    you have a set of methods which you could extend to take full control over your
    PDF production:

    - pre_convert
    - post_convert
    - get_extra_data
    - get_extra_style
    - get_extra_configuration
    - get_extra_body_data
    - get_metadata
    """

    name = "mpdf"

    _images_dir = "images/"
    _body_pdf_name = "body.pdf"
    _body_html_name = "body.html"

    def __init__(self, *args, **kwargs):
        super(MPDFConverter, self).__init__(*args, **kwargs)

        # absolute path to directory where images are saved
        self.images_path = os.path.join(self.sandbox_path, self._images_dir)
        # image item name -> file name mappings
        self.images = {}

    def pre_convert(self, book):
        """Called before entire process of conversion is called.

        :Args:
          - book: EPUB book object
        """
        # Not that much needed at the moment
        self.config['page_width'], self.config['page_height'] = get_page_size(self.config['settings'])

        try:
            if 'crop_marks' in self.config['settings'] and self.config['settings']['crop_marks'] == 'on':
                crop_margin = CROP_MARGIN
            else:
                crop_margin = 0

            self.config['page_width_bleed'] = int(round(self.config['page_width'] + crop_margin))
            self.config['page_height_bleed'] = int(round(self.config['page_height'] + crop_margin))
        except:
            self.config['page_width_bleed'] = self.config['page_width']
            self.config['page_height_bleed'] = self.config['page_height']

    def post_convert(self, book, output_path):
        """Called after entire process of conversion is done.

        :Args:
          - book: EPUB Book object
          - output_path: file path to output file
        """

        return

    def get_extra_data(self, book):
        """Returns extra data which will be passed to the front matter and end matter templates.

        :Args:
          - book: EPUB Book object

        :Returns:
          Returns dictionary.
        """
        return {}

    def get_extra_body_data(self, book):
        """Returns extra data which will be passed to the body templates.

        :Args:
          - book: EPUB Book object

        :Returns:
          Returns dictionary.          
        """

        return {}

    def get_extra_style(self, book):
        """Returns extra data which will be passed to the template rendering styling files.

        :Args:
          - book: EPUB Book object

        :Returns:
          Returns dictionary.
        """

        return {}

    def get_extra_configuration(self):
        """Returns extra data which will be passed to the configuration file.

        Configuration file is read by booktype2mpdf.php script which calls mPDF library.
        The idea is that we can extend this method and pass some additional information
        to the PHP script.

        :Returns:
          Returns dictionary.
        """

        return {'mirror_margins': True}

    def get_metadata(self, book):
        """Returns metadata which will be passed to the PHP script.

        The idea is that we return certain metadata information which will be written 
        to the configuration file. The idea is that booktype2mpdf.php script could
        also get some of the metadata information.

        :Args:
          - book: EPUB Book object

        :Returns:
          Returns dictionary with metadata information.
        """

        dc_metadata = {
            key: value[0][0] for key, value in
            book.metadata.get("http://purl.org/dc/elements/1.1/").iteritems()
        }

        return dc_metadata

    def convert(self, book, output_path):
        """Starts conversion process.

        :Args:
          - book: EPUB Book object
          - output_path: directory path where output files will be saved

        :Returns:
          Returns dictionary with number of pages and file size of output file
        """

        if 'theme' in self.config:
            self.theme_name = self.config['theme'].get('id', '')

        self.pre_convert(book)

        self._save_images(book)

        self._create_body(book)
        self._write_configuration(book)
        self._create_frontmatter(book)
        self._create_endmatter(book)

        self._write_style(book)

        html_path = os.path.join(self.sandbox_path, self._body_html_name)
        pdf_path = os.path.join(self.sandbox_path, self._body_pdf_name)
        data_out = self._run_renderer(html_path, pdf_path)

        os.rename(pdf_path, output_path)

        self.post_convert(book, output_path)

        return {
            "pages": data_out.get('pages', 0),
            "size": os.path.getsize(output_path)
        }

    def _get_chapter_content(self, chapter_item):
        """Returns content of the chapter after some postprocessing.

        This function will also fix certain things in the content. Clear up the links
        pointing to images, remove links for PDF output and etc.

        :Returns:
          Returns strings with HTML content of the chapter.
        """

        base_path = os.path.dirname(chapter_item.file_name)

        try:
            chapter = ebooklib.utils.parse_html_string(chapter_item.content)
            chapter_child = chapter.find("body")

            if chapter_child is not None:
                cnt = deepcopy(chapter_child)
                self._fix_images(cnt, base_path)
                cnt = self._fix_content(cnt)

                return etree.tostring(cnt, method='html', pretty_print=True)[6:-9]
        except etree.XMLSyntaxError:
            pass

        return u''

    def _fix_horrible_mpdf(self, content):
        content = content.replace('></columnbreak>', " />\n")
        content = content.replace('></columns>', " />\n")

        return content

    def _create_body(self, book):
        """Create body html file with main content of the book.

        Created html file will be used by booktype2mpdf.php script
        to create finial PDF file.

        :Args:
          - book: EPUB Book object
        """

        def _toc(depth, toc_items):
            items = []

            for toc_item in toc_items:
                if isinstance(toc_item[1], list):
                    section_title, chapters = toc_item

                    items += [{
                        'type': 'section',
                        'level': depth,
                        'title': section_title
                    }]
                    items += _toc(depth + 1, chapters)
                else:
                    chapter_title, chapter_href = toc_item
                    chapter_item = book.get_item_with_href(chapter_href)
                    content = self._get_chapter_content(chapter_item)
                    content = self._fix_horrible_mpdf(content)

                    items.append({
                        'type': 'chapter',
                        'level': depth,
                        'title': chapter_title,
                        'href': chapter_href,
                        'content': content})

            return items

        book_toc = _toc(0, parse_toc_nav(book))

        data = self._get_data(book)
        data.update(self.get_extra_data(book))
        data.update({
            'book_items': book_toc
            })

        if self.theme_name != '':
            body_name = get_body(self.theme_name, self.name)
        else:
            body_name = 'body_{}.html'.format(self.name)

        html = render_to_string('convert/{}'.format(body_name), data)

        html_path = os.path.join(self.sandbox_path, self._body_html_name)
        f = codecs.open(html_path, 'wt', 'utf8')
        f.write(html)
        f.close()

    def _write_style(self, book):
        """Creates style file.

        Style file will include default styling, theme styling and custom styling
        provided by the user.

        Created style file will be used by booktype2mpdf.php script
        to create final PDF file.

        :Args:
          - book: EPUB Book object
        """

        if 'settings' not in self.config:
            return

        css_style = create_default_style(self.config, self.name, self.get_extra_style(book))
        theme_style = u''

        if self.theme_name != '':
            theme_style = read_theme_style(self.theme_name, self.name)

        custom_style = self.config.get('settings', {}).get('styling', u'')

        f = codecs.open('{}/style.css'.format(self.sandbox_path), 'wt', 'utf8')
        f.write(css_style)
        f.write(theme_style)
        f.write(custom_style)
        f.close()

    def _write_configuration(self, book):
        """Creates configuration file for booktype2mpdf.php script.

        Configuration fill is read by the booktype2mpdf.php script. It is 
        how we pass information to the PHP script which will finially 
        create and format PDF file.

        :Args:
          - book: EPUB Book object
        """

        dc_metadata = self.get_metadata(book)

        data = {'metadata': dc_metadata, 'config': self.config}
        data.update(self.get_extra_configuration())

        f = codecs.open('{}/config.json'.format(self.sandbox_path), 'wt', 'utf8')
        f.write(unicode(json.dumps(data), 'utf8'))
        f.close()

    def _save_images(self, book):
        """Saves all the images from EPUB file to the temporary directory.

        :Args:
          - book: EPUB Book object
        """
        
        if not os.path.exists(self.images_path):
            os.makedirs(self.images_path)

        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            self._save_image(item)

    def _save_image(self, item):        
        """Saves single image to the temporary library.

        :Args:
          - item: ebooklib item object
        """

        file_name = os.path.basename(item.file_name)
        file_path = os.path.join(self.images_path, file_name)

        if os.path.exists(file_path):
            file_name = '{}-{}'.format(item.id, file_name)
            file_path = os.path.join(self.images_path, file_name)

        with open(file_path, 'wb') as file:
            file.write(item.content)

        self.images[item.file_name] = file_name

    def _fix_columns(self, content):
        """Removed broken endnotes from the content.

        :Args:
          - content: lxml node tree with the chapter content

        """
        for column in content.xpath("//div[@class='bk-columns']"):
            column_count = column.get('data-column', '3')
            column_valign = column.get('data-valign', '')
            column_gap = column.get('data-gap', '5')

            columns_start = etree.Element('columns', {
                'column-count': column_count,
                'vAlign': column_valign,
                'column-gap': column_gap
                })
            columns_end = etree.Element('columns', {'column-count': '1'})

            parent = column.getparent()
            parent.insert(parent.index(column), columns_start)
            parent.insert(parent.index(column)+1, columns_end)
            column.drop_tag()

        for column_break in content.xpath("//div[@class='bk-column-break']"):
            column_break.tag = 'columnbreak'
            del column_break.attrib['class']

    def _fix_broken_endnotes(self, content):
        """Removed broken endnotes from the content.

        :Args:
          - content: lxml node tree with the chapter content

        """
        for endnote in content.xpath("//ol[@class='endnotes']"):
            for link in endnote.xpath("//li[@class='orphan-endnote']"):                
                endnote.remove(link)

    def _fix_broken_links(self, content):
        """Removes links from the output and replaces them with textual url.

        :Args:
          - content: lxml node tree with the chapter content

        """

        for link in content.iter('a'):
            if link.attrib.get('href', '') != '':
                text = link.tail or ''
                link.tail = ' [' + link.attrib.get('href', '') + '] ' + text
                link.tag = 'span'

    def _fix_content(self, content):
        """Removes unwanted formatting from the content.

        This function will remove links from the content and put
        URL link outside of the link.

        :Args:
          - content: lxml node tree with the chapter content

        :Returns:
          - Returns changed lxml node tree
        """

        if content is None:
            return content

        self._fix_broken_links(content)
        self._fix_broken_endnotes(content)
        self._fix_columns(content)

        # Fix links to other URL places
        return content

    def _fix_images(self, root, base_path):
        """Fixes links to the images in the content.

        :Args:
          - root: lxml node tree with the content
          - base_path: directory where our images are placed
        """

        for element in root.iter('img'):
            _src = element.get('src', None)

            if _src is None:
                continue
            src_url = urllib2.unquote(_src)
            item_name = os.path.normpath(os.path.join(base_path, src_url))
            try:
                file_name = self.images[item_name]
                element.set('src', self._images_dir + file_name)
            except Exception as e:
                # TODO: discuss what to do in case of missing image
                logger.error(
                    'MPDF::_fix_images: image not found %s (%s)' %
                    (item_name, e)
                )
                continue

    def _get_data(self, book):
        """Returns default data for the front and end matter templates.

        It mainly has default metadata from the book.

        :Returns:
          - Dictionary with default data for the templates
        """

        show_header, show_footer = True, True
        if 'settings' in self.config:
            show_header = self.config['settings'].get('show_header', '') == 'on'
            show_footer = self.config['settings'].get('show_footer', '') == 'on'

        return {
            "title": get_refines(book.metadata, 'title-type', 'main'),
            "subtitle": get_refines(book.metadata, 'title-type', 'subtitle'),
            "shorttitle": get_refines(book.metadata, 'title-type', 'short'),
            "author": get_refines(book.metadata, 'role', 'aut'),

            "publisher": get_metadata(book.metadata, 'publisher'),
            "isbn": get_metadata(book.metadata, 'identifier'),
            "language": get_metadata(book.metadata, 'language'),

            "metadata": book.metadata,

            "show_header": show_header,
            "show_footer": show_footer
        }

    def _create_frontmatter(self, book):
        """Creates front matter file.

        Front matter HTML file will be used by booktype2mpdf.php script to create
        PDF file.

        :Args:
          - book: EPUB Book object
        """

        data = self._get_data(book)
        data.update(self.get_extra_data(book))

        if self.theme_name != '':
            frontmatter_name = get_single_frontmatter(self.theme_name, self.name)
        else:
            frontmatter_name = 'frontmatter_{}.html'.format(self.name)

        html = render_to_string('convert/{}'.format(frontmatter_name), data)

        f = codecs.open('{}/frontmatter.html'.format(self.sandbox_path), 'wt', 'utf8')
        f.write(html)
        f.close()

    def _create_endmatter(self, book):
        """Creates end matter file.

        End matter HTML file will be used by booktype2mpdf.php script to create
        PDF file.
        
        :Args:
          - book: EPUB Book object
        """

        data = self._get_data(book)
        data.update(self.get_extra_data(book))

        if self.theme_name != '':
            endmatter_name = get_single_endmatter(self.theme_name, self.name)
        else:
            endmatter_name = 'endmatter_{}.html'.format(self.name)

        html = render_to_string('convert/{}'.format(endmatter_name), data)

        f = codecs.open('{}/endmatter.html'.format(self.sandbox_path), 'wt', 'utf8')
        f.write(html)
        f.close()

    def _run_renderer(self, html_path, pdf_path):
        """Calls booktype2mpdf.php script to create PDF file.

        :Args:
          - html_path: path to the html file
          - pdf_path: path to he output PDF file

        :Returns:
          Returns dictionary with output returned by the PHP script
        """

        MPDF_DIR = settings.MPDF_DIR
        PHP_PATH = settings.PHP_PATH
        MPDF_SCRIPT = settings.MPDF_SCRIPT

        params = ['--mpdf={}'.format(MPDF_DIR),
                  '--dir={}'.format(self.sandbox_path),
                  '--output={}'.format(pdf_path)]

        cmd = [PHP_PATH, MPDF_SCRIPT] + params

        try:
            (_, out, err) = utils.run_command(cmd)
            data = json.loads(out)

            return data
        except Exception as e:
            logger.error(
                'MPDF Converter::Fail running the command "{}".'.format(e))

        return {}
