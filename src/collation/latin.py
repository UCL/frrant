import tempfile
import os

# list of folds; each list of folds begins with the
# string to be folded to.
# We are assuming that each single character is sorted according to the
# order in which they appear in this list, which might not always be great.
order = [
['a', 'A'],
#['ast', 'a est'], -- seems spaces mysteriously don't work.
['am', 'an'],
['ausa', 'aussa'],
['b', 'B'],
['nn', 'bn'],
['tt', 'bt'],
['pp', 'bp'],
['rr', 'br'],
['c', 'C'],
['ch', 'cch'],
['clu', 'culu'],
['Claud', 'Clod'],
['d', 'D'],
['e', 'E'],
['f', 'F'],
['g', 'G'],
['h', 'H'],
['has', 'hasce'],
['his', 'hisce'],
['hos', 'hosce'],
['i', 'I', 'ii', 'j', 'J'],
['um', 'im'],
['k', 'K'],
['l', 'L'],
['lagr', 'lagl'],
['m', 'M'],
['n', 'N'],
['mb', 'nb'],
['ll', 'nl'],
['mm', 'nm'],
['mp', 'np', 'ndup'],
['rr', 'nr'],
['o', 'O'],
#['ost', 'o est'],
['um', 'om'],
['p', 'P'],
['q', 'Q'],
['r', 'R'],
['s', 'S'],
['t', 'T'],
['u', 'U', 'v', 'V', 'y', 'Y'],
['uu', 'w', 'W'],
['ulc', 'ulch'],
#['umst', 'um est'],
['uul', 'uol', 'vul', 'vol'],
['ui', 'uui', 'uvi'],
['uum', 'uom'],
['x', 'X', 'xs'],
['z', 'Z']
]

lc_identification = '''LC_IDENTIFICATION
title      "Latin folding for Frrant"
source     ""
address    ""
contact    ""
email      ""
tel        ""
fax        ""
language   "Latin"
territory  "Rome"
revision   "1.0"
date       "2021-08-06"
END LC_IDENTIFICATION
#'''

default_section = '''{0}
copy "{1}"
END {0}
#'''

def initial(fd):
    print(lc_identification, file=fd)

    for section in [
        'LC_PAPER',
        'LC_NAME',
        'LC_ADDRESS',
        'LC_TELEPHONE',
        'LC_MEASUREMENT']:
        print(default_section.format(section, 'i18n'), file=fd)

    for section in [
        'LC_CTYPE',
        'LC_NUMERIC',
        'LC_TIME',
        'LC_MONETARY',
        'LC_MESSAGES']:
        print(default_section.format(section, 'POSIX'), file=fd)

def make_id(cluster):
    return cluster.replace(' ', '-')

def letter_list(cluster):
    st = '"'
    st1 = ''
    for letter in cluster:
        st1 = '<U{0:04X}>'.format(ord(letter))
        st += st1
    return len(cluster) == 1 and st1 or st + '"'

def lc_collate(fd):
    print('LC_COLLATE', file=fd)

    for fld in order:
        for cluster in [v for v in fld[1:] if 1 < len(v)]:
            print('collating-element <{0}> from {1}'.format(
                make_id(cluster), letter_list(cluster)
            ), file=fd)

    print('order_start forward;forward', file=fd)
    print('UNDEFINED IGNORE;IGNORE', file=fd)

    for fld in order:
        fold_to = letter_list(fld[0])
        if len(fld[0]) == 1:
            print('{0} {0};{0}'.format(fold_to), file=fd)
        for cluster in fld[1:]:
            llc = letter_list(cluster)
            if len(cluster) == 1:
                print('{0} {1};{0}'.format(llc, fold_to), file=fd)
            else:
                print('<{2}> {1};{0}'.format(llc, fold_to, make_id(cluster)), file=fd)

    print('order_end', file=fd)
    print('END LC_COLLATE', file=fd)
    print('#', file=fd)

with tempfile.NamedTemporaryFile('w+', delete=False) as locale_def_file:
    initial(locale_def_file)
    lc_collate(locale_def_file)
    name = locale_def_file.name
    locale_def_file.close()
    with tempfile.NamedTemporaryFile('w+', delete=False) as utf8_charmap_fd:
        utf8_charmap = utf8_charmap_fd.name
        utf8_charmap_fd.close()
        charmap_gz = '/usr/share/i18n/charmaps/UTF-8.gz'
        os.system('gunzip -c {0} > {1}'.format(charmap_gz, utf8_charmap))
        os.system('localedef -i {0} -f {1} latin'.format(name, utf8_charmap))

# How to use in Postgres:
#
# create table names (id int, name text);
# insert into names (name) values ('ursula'),('bethany'),('victoria');
# select * from names order by name collate "latin";
# This doesn't work, and I don't seem to be able to create the collation either, with:
# create collation latin (LOCALE="latin");
# As it claims the OS doesn't know about it, which isn't true because
# LC_COLLATE=latin ls
# does use this new collation.
# Might need to use locale-gen (and maybe dpkg-reconfigure locales), but
# locale-gen latin
# fails (also with --archive)
