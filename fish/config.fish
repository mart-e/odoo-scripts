alias emacs='emacs -nw'
set EDITOR emacs

alias p='ipython3'
alias p2='ipython2'
alias p3='ipython3'

alias o7='python2 /home/mat/odoo/odoo/openerp-server --addons-path=/home/mat/odoo/odoo/addons'

function odoo2
	if test -e /home/mat/odoo/odoo/odoo.py
		python2 /home/mat/odoo/odoo/odoo.py --log-handler=werkzeug:WARNING --log-handler=bus:WARNING $argv[1..-1]
	else
		if test -e /home/mat/odoo/odoo/openerp-server
			python2 /home/mat/odoo/odoo/openerp-server --addons-path=/home/mat/odoo/odoo/addons $argv[1..-1]
		else
			python2 /home/mat/odoo/odoo/odoo-bin --log-handler=werkzeug:WARNING --log-handler=bus:WARNING $argv[1..-1]
		end
	end
end
alias odoo='python /home/mat/odoo/odoo/odoo-bin --log-handler=werkzeug:WARNING --log-handler=odoo.addons.bus:WARNING --log-handler=odoo.service.server:WARNING'
alias odoo3='odoo'

function odoo2shell
	if test -e /home/mat/odoo/odoo/odoo.py
		python2 /home/mat/odoo/odoo/odoo.py shell --log-handler=werkzeug:WARNING $argv[1..-1]
	else
		python2 /home/mat/odoo/odoo/odoo-bin shell --log-handler=werkzeug:WARNING $argv[1..-1]
	end
end
alias odooshell='python /home/mat/odoo/odoo/odoo-bin shell --log-handler=werkzeug:WARNING --log-handler=bus:WARNING'
alias odoo3shell='odooshell'

function odooent2
	if test -e /home/mat/odoo/odoo/odoo.py
		set odoofile "/home/mat/odoo/odoo/odoo.py"
	else
		set odoofile "/home/mat/odoo/odoo/odoo-bin"
	end
	python2 $odoofile --log-handler=werkzeug:WARNING --addons-path=/home/mat/odoo/enterprise,/home/mat/odoo/odoo/addons $argv[1..-1]
end
alias odooent='python /home/mat/odoo/odoo/odoo-bin --log-handler=werkzeug:WARNING --log-handler=bus:WARNING --addons-path=/home/mat/odoo/enterprise,/home/mat/odoo/odoo/addons'
alias odooent3='odooent'

function odooent2shell
	if test -e /home/mat/odoo/odoo/odoo.py
		set odoofile "/home/mat/odoo/odoo/odoo.py"
	else
		set odoofile "/home/mat/odoo/odoo/odoo-bin"
	end
	python2 $odoofile shell --log-handler=werkzeug:WARNING --addons-path=/home/mat/odoo/enterprise,/home/mat/odoo/odoo/addons $argv[1..-1]
end
alias odooentshell='python /home/mat/odoo/odoo/odoo-bin shell --log-handler=werkzeug:WARNING --log-handler=bus:WARNING --addons-path=/home/mat/odoo/enterprise,/home/mat/odoo/odoo/addons '
alias odooent3shell='odooentshell'


# git time
alias g='git'
alias gs='git stash'
alias gsp='git stash pop'
alias commit='git commit -v'
alias amend='git commit -v --amend'

function gc
	git checkout $argv[1]
	find . -name "*.pyc" | xargs rm
	git clean -df
end

# commit everything with random commit message
function somuchwow
	set prefix "much" "so" "very" "wow"
	set suffix "commit" "fix" "push" "bug"
	set first $prefix[(math (random)%(count $prefix)+1)]
	if [ $first = "wow" ]
		set message $first
	else
		set message $first\ $suffix[(math (random)%(count $suffix)+1)]
	end
	git commit -a -m "$message"
end

function apply-pr
	wget -O- https://github.com/odoo/odoo/pull/$argv[1].diff | patch -p1
end

function apply-pr-ent
	wget -O- https://github.com/odoo/enterprise/pull/$argv[1].diff | patch -p1
end

function patch-pr
	wget -O- https://github.com/odoo/odoo/pull/$argv[1].patch | git am
	git rebase -i
end


# share text command line
alias spr="curl -F 'sprunge=<-' http://pastesha.re"


# show visual representation of the key
alias ssh='ssh -o VisualHostKey=yes'

alias mailcatcher='python -m smtpd -c DebuggingServer -n localhost:1025'
alias pserver='python -m http.server'

# drop and create postgresql db
function dropcreatedb
	dropdb $argv[1]
	createdb $argv[1]
end



function fuckyou
    killall -15 $argv
    echo
    echo  \(╯°□°）╯︵ (echo $argv)
    echo
end
function ffuckyou
    killall -9 $argv
    echo
    echo  \(╯°□°）╯︵ (echo $argv)
    echo
end

alias psql='pgcli'
