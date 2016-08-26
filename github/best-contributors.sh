#!/bin/bash

ODOO_PATH="/home/mat/odoo/odoo"
COMMIT_RELEASE_90="b5ae7659ff4386b9d9098b5c8e9738b5db4697f2"

# email addresses belonging to odoo employees to exclude
regex_odoo="@odoo.com\|@openerp.com\|@tinyerp.com\|arthurmaniet@me.com\|xmo-odoo@users.noreply.github.com\|fvdessen@gmail.com"

cd $ODOO_PATH
git checkout 9.0

# all commits in 9.0 since the open days 2015
commits=$(git log --pretty=format:'%ae' --since="June 5th 2015")
commits_count=$(echo "$commits" | wc -l)
echo -e "$commits_count commits since last Odoo Experience"

# all commits from the community
community_commits=$(echo "$commits" | grep -v $regex_odoo)
community_commits_count=$(echo "$community_commits" | wc -l)
echo -e "  ... including $community_commits_count from external contributors\n"

# most popular email
top_community=$(echo "$community_commits" | sort | uniq -c | sort -nr | head -n 10)
echo -e "Top 10 individual!\n$top_community\n"

# most popular domain name (without gmail or github), assuming compagnies mostly use their coroporate email
top_company=$(echo "$community_commits" | grep -v "@gmail.com\|@users.noreply.github.com" | cut -d @ -f2 | sort | uniq -c | sort -nr | head -n 10)
echo -e "Top 10 company!\n$top_company\n"



# count translations progress
for pofile in openerp/addons/base/i18n/*.po
do
    localname=${pofile##*/}
    # total number of translations for one language
    total=$(pocount --short-string {addons/*/i18n/$localname,openerp/addons/base/i18n/$localname} | grep -v "total: 0" | awk '{print $4}' | awk '{s+=$1} END {print s}')
    echo $localname,$total
done

echo ","

# same since release 9.0
git checkout $COMMIT_RELEASE_90
for pofile in openerp/addons/base/i18n/*.po
do
    localname=${pofile##*/}
    # total number of translations for one language
    total=$(pocount --short-string {addons/*/i18n/$localname,openerp/addons/base/i18n/$localname} | grep -v "total: 0" | awk '{print $4}' | awk '{s+=$1} END {print s}')
    echo $localname,$total
done

# ... and now use a spreadsheet
