#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains Web Application
"""
from __future__ import print_function

import argparse
import hashlib

import pandas as pd
import requests
import oscar

ght_url = 'http://localhost:9002/repos/{slug}/commits'
sh_url = 'http://localhost:5009/graph/visit/nodes/swh:1:ori:{url_SHA1}' \
         '?edges=ori:snp,snp:rev,rev:rev,snp:rel,rel:rev'

def sha1(s):
    sha = hashlib.sha1()
    sha.update(s.encode('utf8'))
    return sha.hexdigest()


def combine_data(project_handle):
    owner, proj = project_handle.split("_", 1)
    url = 'https://github.com/%s/%s' % (owner, proj)
    url_sha = sha1(url)
    sh_data = requests.get(sh_url.format(url_SHA1=url_sha)).text
    sh_commits = [line[-40:] for line in sh_data.split("\n")
                  if line.startswith('swh:1:rev:')]
    df = pd.read_csv(ght_url.format(slug = owner + '/' + proj), index_col='sha')
    df['GHT'] = True
    df['SH'] = pd.Series(True, index=sh_commits)
    df['WoC'] = pd.Series(True, index=oscar.Project(project_handle).commit_shas)
    return df.fillna(False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Compare data across datasets")
    parser.add_argument('project_name', action='store_true',
                        help="Log progress to stderr")
    args = parser.parse_args()
    df = combine_data(args.project)
