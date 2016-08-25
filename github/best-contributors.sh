#!/bin/bash

ODOO_PATH="/home/mat/odoo/odoo"

regex_odoo="@odoo.com\|@openerp.com\|@tinyerp.com\|arthurmaniet@me.com\|xmo-odoo@users.noreply.github.com\|fvdessen@gmail.com"

cd $ODOO_PATH

commits=$(git log --pretty=format:'%ae' --since="June 5th 2015")
commits_count=$(echo "$commits" | wc -l)
echo -e "$commits_count commits since last Odoo Experience"

community_commits=$(echo "$commits" | grep -v $regex_odoo)
community_commits_count=$(echo "$community_commits" | wc -l)
echo -e "  ... including $community_commits_count from external contributors\n"

top_community=$(echo "$community_commits" | sort | uniq -c | sort -nr | head -n 10)
echo -e "Top 10 individual!\n$top_community\n"

top_company=$(echo "$community_commits" |grep -v "@gmail.com\|@users.noreply.github.com" | cut -d @ -f2 | sort | uniq -c | sort -nr | head -n 10)
echo -e "Top 10 company!\n$top_company\n"
