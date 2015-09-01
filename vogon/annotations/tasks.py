

def tokenize(content):
    chunks = content.split(' ')
    return ' '.join(['<word id="{0}">{1}</word>'.format(i, chunks[i])
                     for i in xrange(len(chunks))])
