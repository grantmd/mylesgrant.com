import feedparser, os, sys, csv

#posts = csv.writer(open('posts.csv', 'w'))
#comments = csv.writer(open('comments.csv', 'w'))

url = 'http://www.mylesgrant.com/wordpress.xml'
d = feedparser.parse(url)

for item in d['items']:
	#print "%s,%s" % (item.title, item.author)
	print '.'
	
	if item.title == "I have a code.flickr.com blog post!":
		for key in item:
			print "%s: %s" % (key, item[key])
		
	#if item.has_key('comment'):
		#if item['comment_approved'] == 'spam':
		#	continue
		# post, author, email, url, date, body
		#comments.writerow([item.post_name, item.comment_author, item.comment_author_email, item.comment_author_url, item.comment_date, item.comment_content.encode('ascii', 'ignore')])
	
	# author, title, stub, body, date_created, date_published
	#posts.writerow([item.author, item.title.encode('ascii', 'ignore'), item.post_name, item.content[0].value.encode('ascii', 'ignore'), item.post_date, item.post_date])
