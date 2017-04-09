import os
import yaml

from markdown import markdown
from operator import itemgetter
from jinja2 import Environment, PackageLoader

from . import WWWDATA


def main():
    templates = Environment(loader=PackageLoader(__package__, 'templates'))
    artists = yaml.load(open(os.path.join(WWWDATA, 'cytunes.yaml')))
    artists.sort(key=itemgetter('name'))

    for artist in artists:
        if artist['bio']:
            artist['bio'] = more_or_less(artist['bio'])
        artist['albums'].sort(key=itemgetter('title'))
        for album in artist['albums']:
            if album['review']:
                album['review'] = more_or_less(album['review'])

        artist['singles'].sort(key=itemgetter('title'))
        for single in artist['singles']:
            if single['comment']:
                single['comment'] = more_or_less(single['comment'])

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


LEN = 180


def more_or_less(text):
    if len(text) <= LEN:
        return {'less': markdown(text)}
    else:
        return {
            'more': markdown(text),
            'less': less(text),
        }


def less(text):
    shortened = text.split('\n')[0][:LEN]
    while shortened[-1].isalnum():
        shortened = shortened[:-1]
    return shortened
