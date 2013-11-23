from flask import Flask
from flask import request
app = Flask(__name__)

result_list = dict()
result_list['http://www.google.com'] = 5
result_list['http://www.yahoo.com'] = 4
result_list['http://www.bing.com'] = 3
result_list['http://www.ask.com'] = 2
result_list['http://www.blackle.com'] = 1 

 
@app.route("/")
def main_page():
	return """

<!DOCTYPE html>
<html>
<body>
<h1> Example UI </h1>
<br>
<form action="search" method="post">
<input type="text" name="keywords" />
<input type="submit" value="Search"/>
</form>
</body>
</html>
"""
 
@app.route("/search", methods=['POST'])
def search():
	query = request.form['keywords']
	output = ""
	i= 1
	for link,score in result_list.iteritems():
		output += str(i) + ") <a href=\"" + link + "\">" + link + "</a> Score: " + str(score) + "<br>"
		i+=1
	return """

<!DOCTYPE html>
<html>
<body>
<h1>Here are the results</h1>
<h3>Query: """ + query + """ </h3>
""" + output + """
<br>
*We have to sort these obviously...
</body>
</html>
"""

 
if __name__ == "__main__":
    app.run()
