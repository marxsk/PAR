#!/usr/bin/python
#-- coding: utf-8 --
# 2015 Matej Stepanek

import par
import cgi

form = cgi.FieldStorage()
if 'input' in form:
    input = form.getfirst('input')
    SE = form.getfirst('SE')
else:
    input = ''

print 'Content-Type: text/html; charset=utf-8\n\n'
print '<html>'
print '<head>'
print '<link rel="stylesheet" type="text/css" href="style.css">'
print ' <title>PAR testing</title>'
print '</head>'
print '<body>'

if input:
    lines = input.split('\n')[:-1]
    tester = par.Tester()
    for line in lines:
	print '%s<br>' %line
	result = tester.test(line, SE)
	print '%s<br>' %result

print '</body>'
print '</html>'
