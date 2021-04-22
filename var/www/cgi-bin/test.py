#!/usr/bin/python3
# Import modules for CGI handling
import cgi, cgitb
# Create instance of FieldStorage
form = cgi.FieldStorage()

print("Content-Type: text/html")    # HTML is following
print()
print("<TITLE>CGI script output</TITLE>")
print("<H1>This is my first CGI script</H1>")
print("Hello, world!")
ticket = form.getvalue('ticket')
host = form.getvalue('host')
useCase = form.getvalue('useCase')
print(ticket,host,useCase)
