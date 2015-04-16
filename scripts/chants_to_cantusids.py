#!/usr/bin/env python3

DEBUG = False

# Convert a file of "Chant" resources to one of "CantusID" resources
#
# A "cantusid" resource will have the following fields pulled from a "chant"
# - id (the Cantus ID)
# - genre_id
# - incipit
# - full_text (the regularized one)
# - member_ids (list of Chant resources with this Cantus ID)

from collections import namedtuple, OrderedDict
import sys
try:
    import lxml.etree as ETree
except ImportError:
    print('Info: Using built-in ElementTree API rather than preferred "lxml" library.')
    import xml.etree.ElementTree as ETree


CantusID = namedtuple('CantusID', ['incipit', 'genre_id', 'full_text', 'member_ids'])


def process_chant(chant, records):
    '''
    Given a <chant> element and a dict, create a CantusID namedtuple in the dict that corresponds
    to the data in the <chant> element. If some fields are missing, they will be an empty string
    in the namedtuple. The dict is organized so the Cantus ID is the key. If a corresponding
    namedtuple already exists, it is updated with information from the <chant> element.

    This function returns nothing---you must retain a reference to the "records" dictionary!
    '''
    cantusid = chant.find('cantus_id')
    if cantusid is None:
        return
    else:
        cantusid = cantusid.text

    incipit = chant.find('incipit')
    incipit = incipit.text if incipit is not None else ''
    genre_id = chant.find('genre_id')
    genre_id = genre_id.text if genre_id is not None else ''
    full_text = chant.find('full_text')
    full_text = full_text.text if full_text is not None else ''
    chant_id = chant.find('id').text

    if cantusid in records:
        this_cantusid = records[cantusid]
        # append this chant's ID to the master list
        this_cantusid.member_ids.append(chant_id)

        # see if we're missing data from previous chants
        if '' == this_cantusid.incipit and incipit != '':
            # new incipit!
            records[cantusid] = CantusID(incipit,
                                         this_cantusid.genre_id,
                                         this_cantusid.full_text,
                                         this_cantusid.member_ids)
        if '' == this_cantusid.genre_id and genre_id != '':
            # new genre_id!
            records[cantusid] = CantusID(this_cantusid.incipit,
                                         genre_id,
                                         this_cantusid.full_text,
                                         this_cantusid.member_ids)
        if '' == this_cantusid.full_text and full_text != '':
            # new full_text!
            records[cantusid] = CantusID(this_cantusid.incipit,
                                         this_cantusid.genre_id,
                                         full_text,
                                         this_cantusid.member_ids)
    else:
        records[cantusid] = CantusID(incipit, genre_id, full_text, [chant_id])


def cantusids_to_xml(cantusid_records):
    '''
    Convert a dict of CantusID namedtuple objects into an element tree. The root element's tag is
    "cantusids" and each element's tag is "cantusid". If one of the namedtuple members is an empty
    string it is omitted from the output. Data is put in @text attributes like this:

    >>> a = {'001001': CantusID('Good morning', '', 'Good morning ladies and gentlemen.", ['2', '3'])}
    >>> cantusids_to_xml(a)
    <cantusids>
        <cantusid>
            <id text="001001" />
            <incipit text="Good morning" />
            <full_text text="Good morning ladies and gentlemen." />
            <member_id text="2" />
            <member_id text="3" />
        </cantusid>
    </cantusids>

    Note that the "genre_id" member was an empty string in the CantusID, so it was omitted from
    the ElementTree output.
    '''
    output_root = ETree.Element('cantusids')
    CANTUS_ID = 'id'
    INCIPIT = 'incipit'
    GENRE_ID = 'genre_id'
    FULL_TEXT = 'full_text'
    MEMBER_ID = 'member_id'
    TEXT = 'text'

    for cantusid in iter(cantusid_records):
        elem = ETree.Element('cantusid')
        ETree.SubElement(elem, CANTUS_ID, {TEXT: cantusid})
        if cantusid_records[cantusid].incipit != '':
            ETree.SubElement(elem, INCIPIT, {TEXT: cantusid_records[cantusid].incipit})
        if cantusid_records[cantusid].genre_id != '':
            ETree.SubElement(elem, GENRE_ID, {TEXT: cantusid_records[cantusid].genre_id})
        if cantusid_records[cantusid].full_text != '':
            ETree.SubElement(elem, FULL_TEXT, {TEXT: cantusid_records[cantusid].full_text})
        for member_id in cantusid_records[cantusid].member_ids:
            ETree.SubElement(elem, MEMBER_ID, {TEXT: member_id})

        output_root.append(elem)

    return output_root


if __name__ == '__main__':
    if len(sys.argv) < 3:
        if 'python' in sys.argv[0]:
            print('Usage: python3 chants_to_cantusids.py *filename*')
            print('')
            print('Convert a file of "Chant" resources to one of "CantusID" resources.')
            raise SystemExit()
        else:
            filename = sys.argv[1]
    else:
        filename = sys.argv[2]

    input_tree = ETree.parse(filename)
    if input_tree.getroot().tag != 'chants':
        print('This script requires a <chants><chant/></chants> structure.')
        raise SystemExit(1)

    # we use an OrderedDict so the output order is deterministic, which greatly eases testing
    cantusid_records = OrderedDict()

    for each_chant in input_tree.iterfind('./chant'):
        process_chant(each_chant, cantusid_records)

    output_root = cantusids_to_xml(cantusid_records)

    output_filename = 'list_of_cantusids.xml'
    if DEBUG:
        output_me = '\n'.join(ETree.tostringlist(output_root, encoding='unicode'))
        with open(output_filename, 'w') as the_file:
            written = the_file.write(output_me)
        if written < len(output_me):
            print('Error: unable to write full file to "{}"'.format(output_filename))
            raise SystemExit(1)
    else:
        output_tree = ETree.ElementTree(output_root)
        output_tree.write(output_filename, encoding='utf-8', xml_declaration=True)

    print('Info: results outputted to "{}"'.format(output_filename))
