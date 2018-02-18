from PIL import Image
def compute(d):
  C = {}
  #C[0] = 0
  with d['input_file'] as f:
      I = Image.open(f)
      for pxl, hist in enumerate(I.histogram()):
          C[pxl] = hist
      #print(I.size)
  #C['input'] = I.size
  return C
