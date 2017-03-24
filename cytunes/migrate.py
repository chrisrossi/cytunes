import mysql.connector
import yaml

from operator import itemgetter


def main():
    raw = {}
    migrate_db(raw)

    fix_song = fixer('tracknum', 'title', 'file_src', 'comment', 'artwork')
    fix_album = fixer(
        'title', 'review', 'artwork',
        children='songs', sort_children='tracknum', fix_child=fix_song)
    fix_artist = fixer(
        'name', 'bio', 'photo',
        children='albums', sort_children='title', fix_child=fix_album)

    data = [fix_artist(artist) for artist in raw.values()]
    print(yaml.dump(data))


def migrate_db(data):
    con = mysql.connector.connect(user='chris', database='cytunes')
    cur = con.cursor()

    cur.execute('select * from artist')
    artists = list(fetch(cur))
    artist_by_id = {a['id']: a for a in artists}

    cur.execute('select * from album')
    albums = list(fetch(cur))
    album_by_id = {a['id']: a for a in albums}
    for album in albums:
        artist_albums = artist_by_id[album['artist']].setdefault('albums', {})
        artist_albums[album['title']] = album

    cur.execute('select * from song where album is not null')
    songs = list(fetch(cur))
    for song in songs:
        album = album_by_id[song['album']]
        album_songs = album.setdefault('songs', {})
        album_songs[song['title']] = song

    cur.execute('select * from song where album is null')
    singles = list(fetch(cur))
    for single in singles:
        artist = artist_by_id[single['artist']]
        artist_albums = artist.setdefault('albums', {})
        album = artist_albums.setdefault('__singles__', {
            'title': 'Singles',
            'songs': {}})
        album['songs'][single['title']] = single
        single['tracknum'] = len(album)

    # FIXME will need merge if we also get data from song files
    data.update({artist['name']: artist for artist in artists})


def fetch(cursor):
    cols = [x[0] for x in cursor.description]
    for row in iter(cursor.fetchone, None):
        yield dict(zip(cols, row))


def fixer(*keys, children=None, sort_children=None, fix_child=None):
    def fix(raw):
        fixed = {key: raw.get(key) for key in keys}

        if children and children in raw:
            kids = sorted(raw[children].values(),
                          key=itemgetter(sort_children))
            fixed[children] = [fix_child(kid) for kid in kids]

        return fixed

    return fix
