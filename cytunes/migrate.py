import mysql.connector
import os
import taglib
import yaml

from operator import itemgetter

from . import APPDATA
SONGS = os.path.join(APPDATA, 'songs')


def main():
    raw = merge_tree(migrate_db(), migrate_songs())

    fix_song = fixer('tracknum', 'title', 'file_src', 'comment', 'artwork')
    fix_album = fixer(
        'title', 'review', 'artwork',
        children='songs', sort_children='tracknum', fix_child=fix_song)
    fix_artist = fixer(
        'name', 'bio', 'photo',
        children='albums', sort_children='title', fix_child=fix_album)

    data = [fix_artist(artist) for artist in raw.values()]
    print(yaml.dump(data))

    """
    songs = raw['Chamber Corps']['albums']['Bonne Fin du Monde']['songs']
    songs = sorted(songs.values(), key=lambda x: int(x['tracknum']))
    for song in songs:
        print(song['tracknum'], song['title'])
    """


def migrate_db():
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
        album = artist_albums.setdefault('Singles', {
            'title': 'Singles',
            'songs': {}})
        album['songs'][single['title']] = single
        single['tracknum'] = len(album)

    # FIXME will need merge if we also get data from song files
    return {artist['name']: artist for artist in artists}


def fetch(cursor):
    cols = [x[0] for x in cursor.description]
    for row in iter(cursor.fetchone, None):
        yield dict(zip(cols, row))


def migrate_songs():
    def get(tags, name):
        if name in tags:
            value = tags[name]
            assert len(value) == 1
            return value[0]

    artists = {}
    flacs = [os.path.join(SONGS, fname)
             for fname in os.listdir(SONGS)
             if fname.endswith('flac')]
    for flac in flacs:
        song = taglib.File(flac)
        tags = song.tags
        title = get(tags, 'TITLE')
        artist_name = get(tags, 'ARTIST')
        album_title = get(tags, 'ALBUM')
        comment = get(tags, 'DESCRIPTION')
        tracknum = get(tags, 'TRACKNUMBER')

        artist = artists.setdefault(artist_name, {
            'name': artist_name,
            'albums': {},
        })

        if not album_title or album_title == 'CyTunes Exclusive Single':
            album_title = 'Singles'
        album = artist['albums'].setdefault(album_title, {
            'title': album_title,
            'songs': {},
            'review': comment,
        })

        if not tracknum:
            tracknum = len(album) + 1
        album['songs'][title] = {
            'title': title,
            'tracknum': tracknum,
            'comment': comment,
            'file_src': flac,
        }

    return artists


def merge_tree(one, two):
    """
    two wins in conflicts
    """
    merged = {}
    for key, value in two.items():
        if isinstance(value, dict) and key in one:
            merged[key] = merge_tree(one[key], value)
        else:
            merged[key] = value

    for key, value in one.items():
        if key not in one:
            merged[key] = value

    return merged


def fixer(*keys, children=None, sort_children=None, fix_child=None):
    def fix(raw):
        fixed = {key: raw.get(key) for key in keys}

        if children and children in raw:
            kids = sorted(raw[children].values(),
                          key=itemgetter(sort_children))
            fixed[children] = [fix_child(kid) for kid in kids]

        return fixed

    return fix
