# Image compression
#
# You'll need Python 3 and must install the 'numpy' package (just for its arrays).
#
# The code also uses the 'netpbm' package, which is included in this directory.
#
# You can also display a PNM image using the netpbm library as, for example:
#
#   python3 netpbm.py images/cortex.pnm
#
# NOTES:
#
#   - Use struct.pack( '>h', val ) to convert signed short int 'val' to a two-byte bytearray
#
#   - Use struct.pack( '>H', val ) to convert unsigned short int 'val' to a two-byte bytearray
#
#   - Use struct.unpack( '>H', twoBytes )[0] to convert a two-byte bytearray to an unsigned short int.  Note the [0].
#
#   - Use struct.unpack( '>' + 'H' * count, manyBytes ) to convert a bytearray of 2 * 'count' bytes to a tuple of 'count' unsigned short ints


import sys, os, math, time, struct, netpbm
import numpy as np


# Text at the beginning of the compressed file, to identify it

headerText = b'my compressed image - v1.0'



# Compress an image


def compress( inputFile, outputFile ):

  # Read the input file into a numpy array of 8-bit values
  #
  # The img.shape is a 3-type with rows,columns,channels, where
  # channels is the number of component in each pixel.  The img.dtype
  # is 'uint8', meaning that each component is an 8-bit unsigned
  # integer.

  img = netpbm.imread( inputFile ).astype('uint8')

  # Note that single-channel images will have a 'shape' with only two
  # components: the y dimensions and the x dimension.  So you will
  # have to detect whether the 'shape' has two or three components and
  # set the number of channels accordingly.  Furthermore,
  # single-channel images must be indexed as img[y,x] instead of
  # img[y,x,k].  You'll need two pieces of similar code: one piece for
  # the single-channel case and one piece for the multi-channel case.

  # Compress the image

  startTime = time.time()

  outputBytes = bytearray()

  # ---------------- [YOUR CODE HERE] ----------------
  #
  # REPLACE THE CODE BELOW WITH YOUR OWN CODE TO FILL THE 'outputBytes' ARRAY.

  stream = [] # hold differences for predictive encoding

  multi = False
  if len(img.shape) > 2:
      multi = True

  if multi:
      for y in range(img.shape[0]):
        for x in range(img.shape[1]):
          for c in range(img.shape[2]):
            # f'(x,y)=f(x,y)−(aw*f(x−1,y−1)+bw*f(x,y−1)+cw*f(x−1,y))
            out = int(img[y,x,c])
            if x > 0: # sub encoding
                out -= img[y,x-1,c]
            stream.append( out )

  else:
      for y in range(img.shape[0]):
        for x in range(img.shape[1]):
            # f'(x,y)=f(x,y)−(aw*f(x−1,y−1)+bw*f(x,y−1)+cw*f(x−1,y))
            out = int(img[y,x])
            if x > 0: # sub encoding
                out -= img[y,x-1]
            stream.append( out )

  # LZW
  entries = 0
  dict = {}
  S = ""

  # map initial dictionary
  for i in range(-255,256):
      dict[str(i)] = entries
      entries += 1
  
  for b in stream:
      t = S
      if S != "":
        t += 'x';

      t += str(int(b))

      if t in dict:
          S = t
      else:
          if entries < 65536:
                dict[t] = entries
                entries += 1
          if S != "":
              out = dict[ S ]
              out = struct.pack( '>H', out )
              outputBytes.append( out[0] )
              outputBytes.append( out[1] )
              S = str(int(b))

  out = struct.pack( '>H', dict[ S ] )
  outputBytes.append( out[1] )
  outputBytes.append( out[0] )

  # ---------------- [END OF YOUR CODE] ----------------

  endTime = time.time()

  # Output the bytes
  #
  # Include the 'headerText' to identify the type of file.  Include
  # the rows, columns, channels so that the image shape can be
  # reconstructed.

  outputFile.write( headerText + b'\n' )
  outputFile.write( bytes( '%d %d %d\n' % (img.shape[0], img.shape[1], img.shape[2]), encoding='utf8' ) )
  outputFile.write( outputBytes )

  # Print information about the compression
  
  inSize  = img.shape[0] * img.shape[1] * img.shape[2]
  outSize = len(outputBytes)

  sys.stderr.write( 'Input size:         %d bytes\n' % inSize )
  sys.stderr.write( 'Output size:        %d bytes\n' % outSize )
  sys.stderr.write( 'Compression factor: %.2f\n' % (inSize/float(outSize)) )
  sys.stderr.write( 'Compression time:   %.2f seconds\n' % (endTime - startTime) )
  


# Uncompress an image

def uncompress( inputFile, outputFile ):

  # Check that it's a known file

  if inputFile.readline() != headerText + b'\n':
    sys.stderr.write( "Input is not in the '%s' format.\n" % headerText )
    sys.exit(1)
    
  # Read the rows, columns, and channels.  

  rows, columns, numChannels = [ int(x) for x in inputFile.readline().split() ]

  # Read the raw bytes.

  inputBytes = bytearray(inputFile.read())

  startTime = time.time()

  # ---------------- [YOUR CODE HERE] ----------------
  #
  # REPLACE THIS WITH YOUR OWN CODE TO CONVERT THE 'inputBytes' ARRAY INTO AN IMAGE IN 'img'.

  img = np.empty( [rows,columns,numChannels], dtype=np.uint8 )

  entries = 0
  dict = {}
  S = []

  stream = []

  # map initial dictionary
  for i in range(-255,256):
      dict[entries] = [ i ]
      entries += 1

  twoBytes = inputBytes[:2]
  key = struct.unpack( '>H', twoBytes )[0]
  S = dict[key]
  stream += S
  for i in range(2, len(inputBytes), 2):
      twoBytes = inputBytes[i:i+2]
      key = struct.unpack( '>H', twoBytes )[0]
      T = S
      
      if key < entries:
          T = dict[key]
          dict[entries] = S + [ T[0] ]
      else:
        T = S + [ S[0] ]
        dict[entries] = T
      
      entries += 1
      stream += T
      S = T

  i = 0
  for y in range(rows):
    for x in range(columns):
      for c in range(numChannels):
          if i >= len(stream):
            img[y,x,c] = 255
            print(i-len(stream))
          else:    
            img[y,x,c] = stream[i]

            if x > 0:
              img[y,x,c] += img[y,x-1,c]

          i += 1

  # ---------------- [END OF YOUR CODE] ----------------

  endTime = time.time()
  sys.stderr.write( 'Uncompression time %.2f seconds\n' % (endTime - startTime) )

  # Output the image

  netpbm.imsave( outputFile, img )
  

  
# The command line is 
#
#   main.py {flag} {input image filename} {output image filename}
#
# where {flag} is one of 'c' or 'u' for compress or uncompress and
# either filename can be '-' for standard input or standard output.


if len(sys.argv) < 4:
  sys.stderr.write( 'Usage: main.py c|u {input image filename} {output image filename}\n' )
  sys.exit(1)

# Get input file
 
if sys.argv[2] == '-':
  inputFile = sys.stdin
else:
  try:
    inputFile = open( sys.argv[2], 'rb' )
  except:
    sys.stderr.write( "Could not open input file '%s'.\n" % sys.argv[2] )
    sys.exit(1)

# Get output file

if sys.argv[3] == '-':
  outputFile = sys.stdout
else:
  try:
    outputFile = open( sys.argv[3], 'wb' )
  except:
    sys.stderr.write( "Could not open output file '%s'.\n" % sys.argv[3] )
    sys.exit(1)

# Run the algorithm

if sys.argv[1] == 'c':
  compress( inputFile, outputFile )
elif sys.argv[1] == 'u':
  uncompress( inputFile, outputFile )
else:
  sys.stderr.write( 'Usage: main.py c|u {input image filename} {output image filename}\n' )
  sys.exit(1)
