"""
folksonomy.py

Reference: http://en.wikipedia.org/wiki/Folksonomy
Quick Guide to Installing Folksonomy: http://www.timfanelli.com/item/folksonomy_update

Folksonomy infers relationships between your tags and entries by locating entries with 
the same tags, providing navigation links through your site based on how your entries are 
tagged.

Tagging your entries is simple, you just have to add a "tags" element to your entry's 
metadata section. A typical entry will then looks like this:
  
    My Entry Title
    #tags apples,oranges,orangatangues
    This is my post about apples oranges and orangatangues.

Your entry is then tagged with those three things, apples, oranges, and orangatangues.

Folksonomy populates three template variables, $tags, $relatedtags and $relatedstores, for
use in your story template. 

Adding $tags to your story template will create links to your tags. The links are somewhat 
customizable, using the following config entries:

	py['tag_url']
	py['pretext']
	py['posttext']
	py['tagsep']

The default tag_url should be set to http://yoursite/tags/, but you can also set 
it to something like http://technorati.com/tags/.  Please make sure to have the trailing slash.

The pretext and posttext will appear on your webpage surrounding your tags and tagsep will 
note what to seperate the tags by.

So, for example, if I have 
	py['pretext'] = '<span class="tags">Tags: '
	py['posttext'] = '</span>'
	py['tagsep'] = ', '

Then it would appear like:

	<span class="tags">Tags: biking, pennsylvania</span>

$relatedtags and $relatedstories will only be populated when there's a single entry in the 
page contents (e.g., you're viewing a story through it's permalink). 

$relatedtags and $relatedstories contain links to search that tag or view that story respectively.

Tags are considered to be related if there is a story that is shared between those tags. 
Relationships are weighted based on how many stories are shared between them. The related 
tags is a set of the top two related tags to each tag in your story.

Related stories are the two most recent stories from each related tag.

Folksonomy also creates tag clouds, stored in $tagcloud and $populartagcloud, which 
provide visual representations of your blog's subject matter, and navigational links into 
the tags. $populartagcloud is a rebalanced subset of $tagcloud, containing only those tags
which are ranked at least a "medium" in the full tagcloud.

To use related stories or tags, simply add $relatedstories or $relatedtags to your
flavour's story template. You can customize it's appearance by defining

	#relatedstores { }

in your CSS.

To use the tagcloud, simply add either $tagcloud or $popular tagcloud to your flavour in a 
location of your choice, and then define the following in your CSS:

        .smallestTag { font-size=10px; }
        .smallTag    { font-size=11px; }
        .mediumTag   { font-size=12px; }
        .bigTag      { font-size=13px; }
        .biggestTag  { font-size=14px; }
        .hugeTag     { font-size=15px; }
        .hugestTag   { font-size=16px; }
        .mostHugeTag { font-size=17px; }

        #tagcloud    { }

Customized for your site, of course. 

NOTE: As of 1.1.0, Folksonomy swallowed up my tag cloud plugin. Tag cloud will be 
maintained independantly, however it is no longer necessary to install it if you are 
using Folksonomy. Folksonomy and TagCloud will be kept in sync, and interchangeable 
as far as TagCloud functionality is concerned.

Folksonomy 1.1.0 contains all the functionality of Tag Cloud 1.3.1

NOTE: As of 1.2.0, Folksonomy no longer depends on Joe Topjian's Tags plugin. Folksonomy 
is now interchangable with Tags as far as basic tagging functionality is concerned. If you 
install this version of Folksonomy, you may safely remove Joe's Tags plugin. This was 
done because I was making frequent changes to Joe's plugin to support Folksonomy, and I 
didn't want to have to keep bombarding him with change requests for Folksonomy to work.

Folksonomy 1.2.0 contains all the functionality of Tags version "200510242045 TCF"

Folksonomy 1.3.0 fixes has a complete rewrite of the algorithm to choose related stories. 
                 Related stories are now ordered by how many tags they share with the story
				 being viewed.

Folksonomy 1.4 Introduces forced relationships for entries. This is extremely useful is you're 
               writing a series of a posts that share tags with other not-as-strongly-related 
               entries, of if you always want a story to show certain relationships that do not 
               change over time. To force a relationship to another entry, add a related tag to 
               your story's metadata section with a comma-separated list of entries, like so:

			#related category/filename

	       So if I have a post that I want to be related to "myotherpost.txt" in the 
               "general" category, I would add:

			#related general/myotherpost.txt

Folksonomy 1.4.1 This is just a bugfix release that fixes the createFolksonomy function to 
                 actually produce a proper folksonomy table no other functionality got added.

"""

__author__ = 'Timothy C. Fanelli <tim.fanelli@gmail.com>'
__version__ = '1.4.1'
__url__ = 'http://www.timfanelli.com'

# Variables

import os, re, sys, string
from Pyblosxom import entries

def cb_start(args):
	"""
	Initializes the entrymap and folksonomy tables.
	"""

	request = args['request']
	config  = request.getConfiguration()
	data    = request.getData()

	entrymap = {}
	maxcount = 0;

	ignoretags = []
	if config.has_key('ignore_tags'):
		ignoretags = config['ignore_tags']

	if not config.has_key('tag_url'):
		config['tag_url'] = "%s/%s/" % (config['base_url'],'tags')

	if not config.has_key('tag_url_display'):
		config['tag_url_display'] = config['tag_url']

	ignoredirectories = config[ 'ignore_directories' ]

        tagfileswithext = [ "txt" ]
        if config.has_key( 'taggable_files' ):
                tagfileswithext = config[ 'taggable_files' ]

	for root,dirs,files in os.walk( config['datadir'] ):
		for file in files:
                        #m = re.compile('.*\.([^.]+)$').search(file)
                        #if ( not m ) or ( not m.group(1) in tagfileswithext ):
			if not os.path.splitext(file)[1].strip('.') in tagfileswithext:
				continue
			
			entry_location = root + "/" + file

			directory = os.path.dirname(entry_location)
			if ( os.path.split( directory )[1] in ignoredirectories ):
				continue

			contents = open(entry_location,'r').read()

			m = re.compile( '\n#tags\s*(.*)\n' ).search(contents)
			if m:
				tagstring = m.group(1)
				tags = tagstring.split(',')

				first = True
				for tag in tags:
					if ( tag in ignoretags ):
						continue

					if not tag in entrymap.keys():
						entrymap[tag] = []

					entrymap[tag].append( entry_location )
					maxcount = max( maxcount, len(entrymap[tag]) )
			else:
				if not "untagged" in entrymap.keys():
					entrymap["untagged"] = []

				entrymap["untagged"].append( entry_location )

	data['entrytagmap'] = entrymap

	mincount = maxcount	
	for tag in entrymap.keys():
		mincount = min( mincount, min( mincount, len( entrymap[tag] ) ) )

	sortedtags = entrymap.keys()
	sortedtags.sort()

	data['sortedtags']  = sortedtags
	data['folksonomy']  = createFolksonomy( entrymap )
	data["tagcloud"] = createTagCloud( config, entrymap, mincount, maxcount )
	data["populartagcloud"] = createPopularTagCloud( config, entrymap, mincount, maxcount )

def cb_story(args):
	entry   = args['entry']
	request = args['request']
	data    = request.getData()
	config  = request.getConfiguration()

	if not entry.has_key('tags'):
		return

	# If we're showing more than one story, the do not populate relatedtags and relatedstories.
	renderer = args['renderer']
	if ( len(renderer.getContent()) == 1 ):
		relatedtags = getRelatedTags( entry, data, config )
		if relatedtags:
			entry['relatedtags']  = relatedtags

		relatedstories =  getRelatedStories( entry, request, data, config )
		if relatedstories:
			entry['relatedstories'] = relatedstories

	# Set the story tags and rss categories
	entry.setMetadata('rawtags', entry.getMetadata('tags'))
	storytags = "%s%s%s" % ( config['pretext'], config['tagsep'].join( [ "<a href='%s%s' rel='tag'>%s</a>" % ( config['tag_url'],tag,tag ) for tag in entry.getMetadata('tags').split(',')  ] ), config['posttext'] )	
	entry.setMetadata('rsscategories', "".join( ['<category>%s</category>' % tag for tag in entry.getMetadata('tags').split(',')]))
	entry.setMetadata('tags', storytags)

	return args['template']

def getEntryTitle( entry ):
	entry.getData()
	return entry['title']

def getRelatedStories( entry, request, data, config ):
	"""
	returns the set of stories that share tags with one or more tags in entry, sorted by decreasing order of number 
	of shared tags.
	"""
	ignoretags = config['ignore_tags']
	
	related = {}
	tags = entry.getMetadata('tags').split(',')
	for tag in tags:
		if tag in ignoretags:
			continue
		
		tmp = _getrelatedstories( tag,data )
		if tmp:
			for relationship in tmp:
				tag = relationship[0]
				stories = relationship[1]
				
				for story in stories:
					if related.has_key( story ):
						related[story] = (related[story][0] + 1, story)
					else:
						related[story] = (1,story)
						

	# Read force-related from meta.
	myentries = []
	if entry.has_key('related'):
		forcerelated = entry.getMetadata('related').split(',')
		myentries = [ os.path.join( config['datadir'], location ) for location in forcerelated ]
							
	if related:
		related = related.values()
		related.sort()
		related.reverse()
		
		myentries.extend( [ r[1] for r in related ] )
		myentries = myentries[ : min( len(myentries), 6 ) ]
		if myentries:	
			relatedstories = ""
			for entry_location in myentries:
				tmpentry = entries.fileentry.FileEntry(request, entry_location, data['root_datadir'])
				tmpentry.getData()
				
				if tmpentry._filename == entry._filename:
					continue

				relatedstories = "%s\n%s<br/>" % (relatedstories, "<a href='%s/%s/%s'>%s</a>" % (config['base_url'],tmpentry['absolute_path'],tmpentry['fn'], getEntryTitle(tmpentry)))
		
			if relatedstories:
				return "<div id='relatedstories'>%s<p>%s</p></div>" % ( config['relatedstories_header'], relatedstories )

def _getrelatedstories( tag, data ):
	""" 
	Returns the set of tuples (tag,sharedstories) that share stories with the specified tag sorted in 
	decreasing order of number of shared stories.
	"""
	sortedtags = data['sortedtags']
	folksonomy = data['folksonomy']

	if ( not tag in sortedtags ):
		return []

	tagindex = sortedtags.index(tag)

	relationship = []
	for t in sortedtags:
		entries = []
		position = sortedtags.index(t)

		if ( tagindex <= position ):
			entries = folksonomy[position][tagindex] 
		elif ( tagindex > position ):
			entries = folksonomy[tagindex][position] 

		if entries:
			relationship.append( (len(entries), entries, t ) )

	relationship.sort()
	relationship.reverse()
	
	return [ (r[2],r[1]) for r in relationship ]

def getRelatedTags( entry, data, config ):
	"""
	returns the set of tags that share at least 2 stories with one or more tags in entry.
	"""
	ignoretags = config['ignore_tags']

	related = []
	tags = entry.getMetadata('tags').split(',')
	for tag in tags:
		if tag in ignoretags:
			continue

		tmp = _getrelatedtags( tag, data )
		if ( tmp ):
			related.extend(tmp)

	related.sort()
	related.reverse()

	related = [ x[1] for x in related if x[0] > 1 ]
	taglinks = "<div id='relatedtags'>%s%s</div>" % ( "related tags: ", ", ".join( ['<a href="%s%s" rel="tag">%s</a>' % (config['tag_url'],tag,tag) for tag in related] ) )
	return related 

def _getrelatedtags( tag, data ):
	"""
	Returns the set of tuples (sharedentries,tag) that share stories with the specified tag, 
	sorted in decreasing order of number of entries shared.
	"""
	sortedtags = data['sortedtags']
	folksonomy = data['folksonomy']

	if ( not tag in sortedtags ):
		print >>sys.stderr, 'ERROR: ' + tag + ' not in sortedtags.'
		return []

	tagindex = sortedtags.index(tag)

	relationship = []
	for t in sortedtags:
		entries = []
		position = sortedtags.index(t)

		if ( tagindex <= position ):
			entries = folksonomy[position][tagindex] 
		elif ( tagindex > position ):
			entries = folksonomy[tagindex][position] 

		if entries:
			relationship.append( ( len(entries), t ) )

	relationship.sort()
	relationship.reverse()
	
	return relationship 
	
	
"""
Given tags [ A, B, C, D, E ] with entries T(A), T(B), T(C), T(D), and T(E) 
respectively, build table folksonomy:

  |	A		B		C		D		E
--+------------------------------------------
A |	T(A)	T(AB)	T(AC)	T(AD)	T(AE)
  |
B |	-		T(B)	T(BC)	T(BD)	T(BE)
  |
C |	-		-		T(C)	T(CD)	T(CE)
  |
D |	-		-		-		T(D)	T(DE)
  |
E |	-		-		-		-		T(E)

Such that for any tag x and any tag y, folksonomy[x,y] = set of entries in x and in y.
"""
def createFolksonomy( entrymap ):
	folksonomytable = []
	taglist = entrymap.keys()
	taglist.sort()

	for y in range( 0, len(taglist)  ):
		
		for i in range(0,y): # create empty columns
			folksonomytable.append('EMPTY')


		for x in range( y, len(taglist) ):
			folksonomytable.append([]) # create new column
			
			if x == y:
				folksonomytable[x].append( entrymap[ taglist[x] ] )
			else:
				xentries = entrymap[taglist[x]]
				yentries = entrymap[taglist[y]]
			
				xyentries = []
				for entry in xentries:
					if entry in yentries:
						xyentries.append( entry )

				folksonomytable[x].append(xyentries)
	return folksonomytable


def createPopularTagCloud( config, tagcount, mincount, maxcount ):
	distribution = ( maxcount - mincount ) / 6
	popcount = {}
	popmin = maxcount

	for tag in tagcount.keys():
		count = len( tagcount[tag] )
		if ( count > ( mincount + distribution ) ):
			popcount[tag] = tagcount[tag]
			popmin = min( popmin, count )
	
	return createTagCloud( config, popcount, popmin, maxcount )			

def createTagCloud( config, tagcount, mincount, maxcount ):
	if tagcount:
		tagurl = config['tag_url']
		if config.has_key('tag_url_display'):
			tagurl = config['tag_url_display']

		tagcloud = []
		tagcloud.append("<div id='tagcloud'>")
		distribution = ( maxcount - mincount ) / 6

		for tag in tagcount.keys():
			size = "mediumTag"

			if tag != "untagged":
				if ( len(tagcount[tag]) == maxcount ):
					size = "mostHugeTag"
				elif ( len(tagcount[tag]) > ( mincount + ( distribution * 5 ) ) ):
					size = "hugestTag"
				elif ( len(tagcount[tag]) > ( mincount + ( distribution * 4 ) ) ):
					size = "hugeTag"
				elif ( len(tagcount[tag]) > ( mincount + ( distribution * 3 ) ) ):
					size = "biggestTag"
				elif ( len(tagcount[tag]) > ( mincount + ( distribution * 2 ) ) ):
					size = "bigTag"
				elif ( len(tagcount[tag]) > ( mincount + distribution ) ):
					size = "mediumTag"
				elif ( len(tagcount[tag]) > mincount ):
					size = "smallTag"
				elif ( len(tagcount[tag]) == mincount ):
					size = "smallestTag"

			tagcloud.append( "<a href='%s' class='%s' title='There are %s entries tagged %s'>%s</a>\n" % ( '%s%s' % ( tagurl,tag ), size, str(len(tagcount[tag])), tag, tag  ) )
					
		tagcloud.append("</div>")
		result = "".join(tagcloud)
		return result

def cb_filelist(args):
        request = args['request']
	config = request.getConfiguration()
        data = request.getData()
	new_files = [ ]

	m = re.compile(r'^%s' % config['tag_url']).match(data['url'])
	if m:
		#tag = re.sub("%s" % config['tag_url'],'',data['url'])
		(tag,) = re.findall("%s/(\w*)" % (config['tag_url'].rstrip('/'),), data['url'])
		
		if tag in data['entrytagmap']:
			return getEntriesForTag( tag, args )
	
def getEntriesForTag(tag,args):
        request = args['request']
	config = request.getConfiguration()
        data = request.getData()

	new_files = []
	entrymap = data['entrytagmap']

	for entry_location in entrymap[tag]: 
		tmpentry = entries.fileentry.FileEntry(request, entry_location, data['root_datadir'])
		new_files.append(( tmpentry._mtime, tmpentry ))

	if new_files:
		new_files.sort()
		new_files.reverse()

		myentries = []
		for myentry in new_files:
			myentries.append( myentry[1] )

		return myentries
	
