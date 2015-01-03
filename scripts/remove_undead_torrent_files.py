#!/usr/bin/env python

import argparse
import pprint
import glob
import os

# becode decoder from here http://effbot.org/zone/bencode.htm

import re

def tokenize(text, match=re.compile("([idel])|(\d+):|(-?\d+)").match):
    i = 0
    while i < len(text):
        m = match(text, i)
        s = m.group(m.lastindex)
        i = m.end()
        if m.lastindex == 2:
            yield "s"
            yield text[i:i+int(s)]
            i = i + int(s)
        else:
            yield s

def decode_item(next, token):
    if token == "i":
        # integer: "i" value "e"
        data = int(next())
        if next() != "e":
            raise ValueError
    elif token == "s":
        # string: "s" value (virtual tokens)
        data = next()
    elif token == "l" or token == "d":
        # container: "l" (or "d") values "e"
        data = []
        tok = next()
        while tok != "e":
            data.append(decode_item(next, tok))
            tok = next()
        if token == "d":
            data = dict(zip(data[0::2], data[1::2]))
    else:
        raise ValueError
    return data

def decode(text):
    try:
        src = tokenize(text)
        data = decode_item(src.next, src.next())
        for token in src: # look for more tokens
            raise SyntaxError("trailing junk")
    except (AttributeError, ValueError, StopIteration):
        raise SyntaxError("syntax error")
    return data


def main(args):
    if args.target.endswith(".torrent"):
        target_files = [args.target]
    else:
        target_files = glob.glob(args.target + "/*.torrent")
    for torrent_file_path in target_files:
        torrent_info = decode(open(torrent_file_path,'rb').read())
        #pprint.pprint(torrent_info)
        is_dead_torrent = True
        if "info" in torrent_info:
            if "name" in torrent_info["info"]:
                file_path = torrent_info["info"]["name"]
                if args.target.endswith(".torrent"):
                    join_directory = os.path.dirname(args.target)
                else:
                    join_directory = args.target
                torrent_real_file_path = os.path.join(
                            join_directory, file_path)
                if os.path.exists( torrent_real_file_path):
                    is_dead_torrent = False
            elif "files" in torrent_info["info"]:
                for file in torrent_info["info"]["files"]:
                    if type(file["path"]) == list:
                        file_path = file["path"][0]
                    else:
                        file_path = file["path"]
                    if args.target.endswith(".torrent"):
                        join_directory = os.path.dirname(args.target)
                    else:
                        join_directory = args.target
                    torrent_real_file_path = os.path.join(
                            join_directory, file_path)
                    if os.path.exists(
                            torrent_real_file_path):
                        is_dead_torrent = False
        if args.print_active_torrent is True:
            if is_dead_torrent is False:
                print torrent_file_path
        else:
            if is_dead_torrent is True:
                print torrent_file_path
                if args.remove_torrent_files:
                    os.remove(torrent_file_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', dest='target', required=True)
    parser.add_argument('-a', action='store_true', dest='print_active_torrent', default=False)
    parser.add_argument('-d', action='store_true', dest='dryrun', default=True)
    parser.add_argument('-r', action='store_true', dest='remove_torrent_files')
    args = parser.parse_args()
    main(args)
