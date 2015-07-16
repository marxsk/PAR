#!/usr/bin/python
#-- coding: utf-8 --
# 2015 Matej Stepanek

import par
import cgi

form = cgi.FieldStorage()
SE = 'seznam'

if 'question' in form: 
    question = form.getfirst('question')
    SE = form.getfirst('SE')
else:
    question = ''

print 'Content-Type: text/html; charset=utf-8\n\n'
print '<html>'
print '<head>'
print ' <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />'
print ' <link rel="stylesheet" type="text/css" href="style.css">'
print ' <title>PAR answerer</title>'
print '</head>'
print '<body>'
print '<table>'
print ' <tr><td><h1><a class="no_change" href="index.cgi">PAR answerer (%s)</a></h1>'%SE
print ' <tr><td>'
print '  <b><a href="index.cgi">answerer</a> | '
print '     <a href="testing.html">testing</a> | '
print '     <a href="about.html">about</a></b>'
print ' <tr><td>'
print '  Give a question in Czech and PAR will find the paragraph that most likely contains an answer.<br>'
print ' <form action="index.cgi">'
print ' <tr><td><b>Search engine to use:</b>'

if SE == 'seznam':
    print ' <tr><td><input type="radio" name="SE" value="seznam" checked>Seznam'
    print '		<input type="radio" name="SE" value="google">Google<br><br>'
else:
    print ' <tr><td><input type="radio" name="SE" value="seznam">Seznam'
    print '             <input type="radio" name="SE" value="google" checked>Google<br><br>'

print ' <tr><td><b>Your question:</b>'
print ' <tr><td><input type="text" name="question" size="70" value="%s">' %question
print ' <tr><td align="right"> <input type="submit" value="Get paragraph">'
print ' </form>'
print '</table>'
print '<br>'

if question:
    ans = par.Answerer()
    (best_par,best_link,best_title,best_score,best_matches) = ans.get_best_par(question,SE)
    if best_par:
	print '<table>'
	print ' <tr><td><b>Paragraph with the answer:</b>'
	print ' <tr><td><p class="best_par">'
	print best_par	
	print '  </p>'
	print ' <tr><td>'
	print ' <tr><td><b>Source:</b> <tr><td>%s' %best_title
	print ' <a href="%s" target="_blank">%s</a>' %(best_link,best_link)
	print '</table>'
    else:
	print '<i>&nbspSorry, PAR have found no results for your question.'
	print 'Try another one.</i>'

print '</body>'
print '</html>'
