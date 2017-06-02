#!/bin/bash

ODOO_PATH="/home/mat/odoo/odoo"
COMMIT_RELEASE_10="780869879b00d5772985e7c11003ac8a94451a61"
LAST_RELEASE_DATE="October 5th 2016"

# email addresses belonging to odoo employees to exclude
regex_odoo="@odoo.com\|@openerp.com\|@tinyerp.com\|arthurmaniet@me.com\|xmo-odoo@users.noreply.github.com\|fvdessen@gmail.com"

cd $ODOO_PATH
# git checkout master

# all commits in 10.0
commits=$(git log --no-merges --pretty=format:'%ae' --since="$LAST_RELEASE_DATE")
commits_count=$(echo "$commits" | wc -l)
echo -e "$commits_count commits since last release"

# all commits from the community
community_commits=$(echo "$commits" | grep -v $regex_odoo)
community_commits_count=$(echo "$community_commits" | wc -l)
echo -e "  ... including $community_commits_count from external contributors\n"

# most popular email
top_community=$(echo "$community_commits" | sort | uniq -c | sort -nr | head -n 20)
echo -e "Top 10 individual!\n$top_community\n"

# most popular domain name (without gmail or github), assuming compagnies mostly use their coroporate email
top_company=$(echo "$community_commits" | grep -v "@gmail.com\|@users.noreply.github.com" | cut -d @ -f2 | sort | uniq -c | sort -nr | head -n 10)
echo -e "Top 10 company!\n$top_company\n"

# echo "$commits" | sort | uniq -c | sort -nr

# count translations progress
for pofile in odoo/addons/base/i18n/*.po
do
    localname=${pofile##*/}
    # total number of translations for one language
    total=$(pocount --short-string {addons/*/i18n/$localname,odoo/addons/base/i18n/$localname} | grep -v "total: 0" | awk '{print $4}' | awk '{s+=$1} END {print s}')
    echo $localname,$total
done

echo ","

# same since release 10.0
git checkout $COMMIT_RELEASE_10
for pofile in odoo/addons/base/i18n/*.po
do
    localname=${pofile##*/}
    # total number of translations for one language
    total=$(pocount --short-string {addons/*/i18n/$localname,odoo/addons/base/i18n/$localname} | grep -v "total: 0" | awk '{print $4}' | awk '{s+=$1} END {print s}')
    echo $localname,$total
done

# ... and now use a spreadsheet
