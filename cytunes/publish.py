import os
import yaml

from operator import itemgetter
from jinja2 import Environment, PackageLoader

from . import WWWDATA


def main():
    templates = Environment(loader=PackageLoader(__package__, 'templates'))
    artists = yaml.load(open(os.path.join(WWWDATA, 'cytunes.yaml')))
    artists.sort(key=itemgetter('name'))

    # Home page
    home_page_template = templates.get_template('home.j2')
    with open(os.path.join(WWWDATA, 'index.html'), 'w') as f:
        f.write(home_page_template.render(artist=None, artists=artists))

    # Artist pages
    artist_template = templates.get_template('artist.j2')
    for artist in artists:
        index_html = os.path.join(WWWDATA, artist['slug'], 'index.html')
        with open(index_html, 'w') as f:
            f.write(artist_template.render(artist=artist, artists=artists))
