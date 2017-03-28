"""
Take data from old site, generate master yaml file, and directory of encoded
songs.
"""
import mysql.connector
import os
import subprocess
import taglib
import yaml

from operator import itemgetter
from slugify import slugify

from . import HERE, WWWDATA, VAR
APPDATA = os.path.join(VAR, 'appdata')
ARTWORK = os.path.join(APPDATA, 'artwork')
OGG_COVER_ART = os.path.join(HERE, 'ogg-cover-art')
SONGS = os.path.join(APPDATA, 'songs')

SINGLES = 'CyTunes Singles'


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
    make_audio_files(data)

    with open(os.path.join(WWWDATA, 'cytunes.yaml'), 'w') as out:
        print(yaml.dump(data), file=out)


image_types = {
    b'\xff\xd8\xff\xe1': '.jpg',
    b'\xff\xd8\xff\xe0': '.jpg',
    b'II*\x00': '.tif',
    b'\x89PNG': '.png',
    b'GIF8': '.gif',
}


def typeof(fn):
    with open(fn, 'rb') as f:
        return image_types[f.read(4)]


def fix_artwork(o):
    artwork = o['artwork']
    if not artwork:
        return

    raw = os.path.join(ARTWORK, artwork)
    jpg = raw + '.jpg'
    if os.path.exists(jpg):
        o['artwork'] = jpg
    else:
        o['artwork'] = fix_image(raw)


def fix_image(raw):
    typed = raw + typeof(raw)
    subprocess.check_call(['mv', raw, typed])
    if typed.endswith('.jpg'):
        return typed

    jpg = raw + '.jpg'
    subprocess.check_call(['convert', typed, jpg])
    subprocess.check_call(['rm', typed])
    return jpg


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
        fix_artwork(album)
        artist = artist_by_id[album['artist']]
        artist_albums = artist.setdefault('albums', {})
        artist_albums[album['title']] = album

    cur.execute('select * from song where album is not null')
    songs = list(fetch(cur))
    for song in songs:
        fix_artwork(song)
        album = album_by_id[song['album']]
        album_songs = album.setdefault('songs', {})
        album_songs[song['title']] = song

    cur.execute('select * from song where album is null')
    singles = list(fetch(cur))
    for single in singles:
        fix_artwork(single)
        artist = artist_by_id[single['artist']]
        artist_albums = artist.setdefault('albums', {})
        album = artist_albums.setdefault(SINGLES, {
            'title': SINGLES,
            'songs': {}})
        album['songs'][single['title']] = single
        single['tracknum'] = len(album['songs'])

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
            album_title = SINGLES
        album = artist['albums'].setdefault(album_title, {
            'title': album_title,
            'songs': {},
            'review': comment,
        })

        if not tracknum:
            tracknum = len(album['songs']) + 1
        else:
            tracknum = int(tracknum)
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
        if key not in merged:
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


def make_audio_files(artists):
    for artist in artists:
        artist['slug'] = slugify(artist['name'])
        for album in artist.get('albums', ()):
            album['slug'] = slugify(album['title'])
            songs = album.get('songs')
            if not songs:
                continue

            folder = os.path.join(WWWDATA, artist['slug'], album['slug'])
            if not os.path.exists(folder):
                os.makedirs(folder)

            all_zipped = False
            if album['title'] != SINGLES:
                all_zipped = True
                for ext in ('flac', 'mp3', 'ogg'):
                    zip_file = os.path.join(folder, '{}-{}-{}.zip'.format(
                        artist['slug'], album['slug'], ext))
                    if not os.path.exists(zip_file):
                        all_zipped = False
                        break

            album_artwork = album.get('artwork')
            if album_artwork:
                dest = os.path.join(folder, 'cover.jpg')
                subprocess.check_call(['cp', album_artwork, dest])
                album_artwork = dest
            elif album['title'] != SINGLES:
                first_song = album['songs'][0]['file_src']
                dest = os.path.join(folder, 'cover')
                subprocess.check_call([
                    'metaflac', '--export-picture-to', dest, first_song])
                album_artwork = fix_image(dest)
            album['artwork'] = album_artwork

            for song in songs:
                song['slug'] = '{:02d}-{}'.format(
                    song['tracknum'], slugify(song['title'])
                )
                base = os.path.join(folder, song['slug'])
                src = os.path.join(
                    APPDATA, 'submissions', song.pop('file_src'))

                artwork = song.get('artwork')
                if artwork:
                    dest = base + '.jpg'
                    subprocess.check_call(['cp', artwork, dest])
                    artwork = dest
                elif album['title'] == SINGLES:
                    subprocess.check_call([
                        'metaflac', '--export-picture-to', base, src])
                    artwork = fix_image(base)
                else:
                    artwork = album_artwork
                song['artwork'] = artwork

                # FLAC
                if not all_zipped:
                    fname = base + '.flac'
                    song['flac'] = fname
                    if not os.path.exists(fname):
                        print(fname)
                        if src.endswith('.flac') and 'submissions' not in src:
                            subprocess.check_call(['cp', src, fname])
                        else:
                            args = [
                                'flac', src, '-o', fname, '--verify', '--best',
                                '-T', 'ARTIST=' + artist['name'],
                                '-T', 'ALBUM=' + album['title'],
                                '-T', 'TITLE=' + song['title'],
                                '-T', 'TRACKNUMBER={}'.format(song['tracknum']),
                            ]
                            if song['comment']:
                                args += ['-T', 'DESCRIPTION=' + song['comment']]
                            if artwork:
                                args += ['--picture', '3||||' + artwork]
                            subprocess.check_call(args)

                # MP3
                if not all_zipped:
                    fname = base + '.mp3'
                    song['mp3'] = fname
                    if not os.path.exists(fname):
                        print(fname)
                        args = [
                            'lame', '--tt', song['title'], '--ta', artist['name'],
                            '--tl', album['title'], '--tn', str(song['tracknum']),
                        ]
                        if song['comment']:
                            args += ['--tc', song['comment']]
                        if artwork:
                            args += ['--ti', artwork]
                        args += ['-q', '0', '-V', '0', src, fname]
                        subprocess.check_call(args)

                fname = base + '-stream.mp3'
                song['mp3_stream'] = fname
                if not os.path.exists(fname):
                    print(fname)
                    args = [
                        'lame', '--tt', song['title'], '--ta', artist['name'],
                        '--tl', album['title'], '--tn', str(song['tracknum']),
                        '-q', '2', '-V', '3', src, fname]
                    subprocess.check_call(args)

                # Ogg Vorbis
                if not all_zipped:
                    fname = base + '.ogg'
                    song['ogg'] = fname
                    if not os.path.exists(fname):
                        print(fname)
                        args = [
                            'oggenc', '-o', fname, '-q', '8',
                            '--tracknum', str(song['tracknum']),
                            '--title', song['title'],
                            '--album', album['title'],
                            '--artist', artist['name'],
                        ]
                        if song['comment']:
                            args += ['--comment', song['comment']]
                        args.append(src)
                        subprocess.check_call(args)

                        if artwork:
                            subprocess.check_call([OGG_COVER_ART, artwork, fname])

                fname = base + '-stream.ogg'
                song['ogg_stream'] = fname
                if not os.path.exists(fname):
                    print(fname)
                    args = [
                        'oggenc', '-o', fname, '-q', '6',
                        '--tracknum', str(song['tracknum']),
                        '--title', song['title'],
                        '--album', album['title'],
                        '--artist', artist['name'],
                        src
                    ]
                    subprocess.check_call(args)

            # Zip files
            if album['title'] != SINGLES:
                for ext in ('flac', 'mp3', 'ogg'):
                    zip_file = os.path.join(folder, '{}-{}-{}.zip'.format(
                        artist['slug'], album['slug'], ext))
                    album['zip_' + ext] = zip_file
                    if not os.path.exists(zip_file):
                        print(zip_file)
                        file_list = [song.pop(ext) for song in album['songs']]
                        subprocess.check_call(
                            ['zip', '-D', '-j', zip_file] + file_list)
                        subprocess.check_call(['rm'] + file_list)
